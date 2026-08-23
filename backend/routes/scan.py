"""Vision (`/scan/food`) + barcode (`/scan/barcode`) endpoints.

The vision endpoint asks Claude Sonnet 4.5 to identify the dish, then
authoritatively re-classifies from `db.foods` if a match exists. If nothing
matches we return `safety_tier="UNVERIFIED"` so the UI shows a neutral badge
instead of guessing a colored tier (iter-24 grounding fix).

The barcode endpoint mirrors the same grounding rule against Open Food Facts.
"""
import base64
import logging
import re
import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from config import EMERGENT_LLM_KEY
from db import db
from scan_service import (
    _SCAN_SYSTEM,
    UNVERIFIED_PORTION,
    UNVERIFIED_TIER,
    UNVERIFIED_TIP,
    _classify_from_nutrients,
    _extract_json,
)
from personalization import personal_tier_for
from schemas import BarcodeScanRequest, FoodScanRequest, FoodScanResponse, Stage
from security import _rate_key_user, get_current_user, limiter

router = APIRouter()
logger = logging.getLogger("renal-diet")


@router.post("/scan/food", response_model=FoodScanResponse)
@limiter.limit("5/minute", key_func=_rate_key_user)
async def scan_food(request: Request, body: FoodScanRequest, current_user=Depends(get_current_user)):
    # Late import via server module so tests that `patch.object(server_mod,
    # "_extract_json", ...)` continue to work — see iter-24 test.
    import server as _server
    _extract = _server._extract_json

    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="Vision service not configured")
    raw = (body.image_base64 or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="image_base64 is required")
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[-1]
    try:
        decoded = base64.b64decode(raw, validate=True)
        if len(decoded) < 200:
            raise HTTPException(status_code=400, detail="Image is empty or too small")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    try:
        from emergentintegrations.llm.chat import ImageContent, LlmChat, UserMessage

        chat = (
            LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"scan-{current_user['id']}-{uuid.uuid4().hex[:8]}",
                system_message=_SCAN_SYSTEM,
            )
            .with_model("anthropic", "claude-sonnet-4-5-20250929")
        )
        image_content = ImageContent(image_base64=raw)
        reply = await chat.send_message(
            UserMessage(text="Identify this Indian dish and classify its CKD safety.",
                        file_contents=[image_content])
        )
        text = str(reply).strip()
    except Exception:
        logger.exception("Vision scan failed")
        raise HTTPException(status_code=502, detail="Vision service temporarily unavailable")

    data = _extract(text)
    # Parse failure or empty result → same patient-facing situation as no match:
    # the app doesn't know, so we say so instead of falling through to YELLOW.
    if not data:
        return FoodScanResponse(
            food_name="Unknown dish",
            hindi_name=None,
            safety_tier=UNVERIFIED_TIER,
            primary_risk_factor="NONE",
            portion_limit_text=UNVERIFIED_PORTION,
            clinical_tip=UNVERIFIED_TIP,
            matched_food_id=None,
            raw=text,
        )

    food_name = str(data.get("food_name") or "").strip() or "Unknown dish"
    # We DO NOT trust the model's own safety_tier here — it will be overwritten
    # from the DB match below. If no match, we return UNVERIFIED (not the
    # model's guess). See iter 24 grounding fix.
    hindi_name = data.get("hindi_name")

    # Placeholders — set only when a DB match provides authoritative values.
    tier: Optional[str] = None
    primary_risk: Optional[str] = None
    portion_limit_text: Optional[str] = None
    clinical_tip: Optional[str] = None

    matched_id: Optional[str] = None
    if food_name and food_name.lower() not in {"unknown", "unknown dish"}:
        match = await db.foods.find_one(
            {"name": {"$regex": re.escape(food_name), "$options": "i"}}, {"_id": 0}
        )
        if match:
            matched_id = match["id"]
            stage: Stage = current_user.get("stage", "unknown") or "unknown"  # type: ignore
            tier = personal_tier_for(match, stage)
            primary_risk = match.get("primary_risk_factor", "NONE")
            portion_limit_text = match.get("portion_limit_text", "")
            clinical_tip = match.get("actionable_clinical_tip", "")
            hindi_name = match.get("hindi_name", hindi_name)
            food_name = match["name"]

    # No confident DB match → refuse to render a colored tier.
    if not matched_id:
        tier = UNVERIFIED_TIER
        primary_risk = "NONE"
        portion_limit_text = UNVERIFIED_PORTION
        clinical_tip = UNVERIFIED_TIP

    return FoodScanResponse(
        food_name=food_name,
        hindi_name=hindi_name,
        safety_tier=tier or UNVERIFIED_TIER,
        primary_risk_factor=primary_risk or "NONE",
        portion_limit_text=portion_limit_text or UNVERIFIED_PORTION,
        clinical_tip=clinical_tip or UNVERIFIED_TIP,
        matched_food_id=matched_id,
        raw=text if not matched_id else None,
    )


@router.post("/scan/barcode", response_model=FoodScanResponse)
@limiter.limit("15/minute", key_func=_rate_key_user)
async def scan_barcode(request: Request, body: BarcodeScanRequest, current_user=Depends(get_current_user)):
    barcode = re.sub(r"\D", "", body.barcode)
    if len(barcode) < 6:
        raise HTTPException(status_code=400, detail="Invalid barcode")

    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "IndianRenalDiet/1.0"}) as hc:
            r = await hc.get(url)
    except Exception:
        logger.exception("Open Food Facts request failed")
        raise HTTPException(status_code=502, detail="Barcode lookup temporarily unavailable")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Barcode lookup temporarily unavailable")
    doc = r.json() or {}
    if int(doc.get("status", 0)) != 1 or not doc.get("product"):
        raise HTTPException(status_code=404, detail="Product not found for this barcode")

    product = doc["product"]
    product_name = (product.get("product_name") or product.get("product_name_en") or "").strip() or "Unknown packaged food"
    brand = (product.get("brands") or "").split(",")[0].strip() or None
    nutriments = product.get("nutriments") or {}

    def _val(key: str) -> float:
        v = nutriments.get(key)
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    portion_g = 0.0
    try:
        portion_g = float(product.get("serving_quantity") or 0)
    except (TypeError, ValueError):
        portion_g = 0.0

    # Prefer per-serving values when available, else per-100g.
    if portion_g and _val("potassium_serving"):
        k_mg = _val("potassium_serving") * 1000  # OFF stores in grams
        p_mg = _val("phosphorus_serving") * 1000
        na_mg = _val("sodium_serving") * 1000 if _val("sodium_serving") else _val("salt_serving") * 400  # salt→Na
        protein_g = _val("proteins_serving")
    else:
        # per-100g, scale to serving if we know it, else use 100g as reference portion
        ref = portion_g if portion_g else 100.0
        k_mg = _val("potassium_100g") * 1000 * ref / 100
        p_mg = _val("phosphorus_100g") * 1000 * ref / 100
        na_mg = (_val("sodium_100g") * 1000 * ref / 100) if _val("sodium_100g") else (_val("salt_100g") * 400 * ref / 100)
        protein_g = _val("proteins_100g") * ref / 100
        if not portion_g:
            portion_g = 100.0

    tier, primary_risk = _classify_from_nutrients(k_mg, p_mg, na_mg)
    is_unverified = (tier == "UNVERIFIED")
    if is_unverified:
        portion_limit_text = UNVERIFIED_PORTION
        clinical_tip = (
            "Open Food Facts had no nutrient data for this pack. We can't classify it safely. "
            "Try scanning a different pack or ask your care team."
        )
    else:
        portion_limit_text = f"Serving size: {int(portion_g)}g"
        clinical_tip = (
            f"Per serving: potassium {int(k_mg)}mg, phosphorus {int(p_mg)}mg, sodium {int(na_mg)}mg. "
            "Always cross-check with the pack label; some manufacturers under-report additives."
        )
    hindi_name: Optional[str] = None

    # Authoritative DB override: if the product name matches a seeded food.
    matched_id: Optional[str] = None
    if product_name and product_name.lower() != "unknown packaged food":
        match = await db.foods.find_one(
            {"name": {"$regex": re.escape(product_name), "$options": "i"}, "source": {"$ne": "barcode"}},
            {"_id": 0},
        )
        if match:
            matched_id = match["id"]
            stage: Stage = current_user.get("stage", "unknown") or "unknown"  # type: ignore
            tier = personal_tier_for(match, stage)
            primary_risk = match.get("primary_risk_factor", primary_risk)
            portion_limit_text = match.get("portion_limit_text", portion_limit_text)
            clinical_tip = match.get("actionable_clinical_tip", clinical_tip)
            hindi_name = match.get("hindi_name")
            portion_g = float(match.get("portion_g") or portion_g)
            k_mg = float(match.get("potassium_mg") or k_mg)
            p_mg = float(match.get("phosphorus_mg") or p_mg)
            na_mg = float(match.get("sodium_mg") or na_mg)
            protein_g = float(match.get("protein_g") or protein_g)
            product_name = match["name"]

    # If no authoritative seed match, upsert the scanned pack as a barcode-sourced food
    # so users can favorite it and log it directly via existing endpoints. Idempotent by barcode.
    # SKIP the upsert entirely for UNVERIFIED packs — writing a synthetic food doc with
    # zeroed nutrients would let the patient favorite/log a phantom entry the app can't
    # actually classify. See iter-24 scan grounding fix.
    if not matched_id and not is_unverified:
        display_name = f"{product_name} ({brand})" if brand else product_name
        food_id = f"bc_{barcode}"
        food_doc = {
            "id": food_id,
            "name": display_name,
            "hindi_name": hindi_name or "",
            "category": "Packaged",
            "safety_tier": tier,
            "primary_risk_factor": primary_risk,
            "portion_limit_text": portion_limit_text,
            "actionable_clinical_tip": clinical_tip,
            "portion_g": round(portion_g, 1),
            "potassium_mg": round(k_mg, 1),
            "phosphorus_mg": round(p_mg, 1),
            "sodium_mg": round(na_mg, 1),
            "protein_g": round(protein_g, 1),
            "fluid_ml": 0,
            "source": "barcode",
            "barcode": barcode,
            "brand": brand,
            "swaps": [],
        }
        await db.foods.update_one({"id": food_id}, {"$set": food_doc}, upsert=True)
        matched_id = food_id

    return FoodScanResponse(
        food_name=product_name,
        hindi_name=hindi_name,
        safety_tier=tier,
        primary_risk_factor=primary_risk,
        portion_limit_text=portion_limit_text,
        clinical_tip=clinical_tip,
        matched_food_id=matched_id,
        barcode=barcode,
        brand=brand,
        portion_g=round(portion_g, 1),
        potassium_mg=round(k_mg, 1),
        phosphorus_mg=round(p_mg, 1),
        sodium_mg=round(na_mg, 1),
        protein_g=round(protein_g, 1),
    )
