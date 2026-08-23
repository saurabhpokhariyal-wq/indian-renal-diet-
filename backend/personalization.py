"""CKD-stage-aware personalization + daily-limit resolution.

The tier the patient sees on a food card can differ from the base tier stored
on the food doc, because a `YELLOW` food for a dialysis patient may effectively
be `RED` (K/P/Fluid over their tighter targets) while a pre-dialysis patient
may treat that same food as `GREEN` (KDOQI 2020 individualizes K targets).

`limits_for_user` layers doctor-set overrides on top of stage defaults so a
nephrologist can tighten (or loosen) any of K / P / Na / Fluid per patient.
"""
from __future__ import annotations

from typing import Optional

from schemas import NutrientLimits, Stage

# Warning explanation shown next to `personal_tier=GREEN` when the base tier
# was YELLOW/POTASSIUM but the patient is pre-dialysis. See KDOQI 2020.
PRE_DIALYSIS_K_NOTE = (
    "Often fine before dialysis — confirm your serum potassium with your doctor. "
    "Portion sizes and lab values matter more than a blanket 'yellow' at this stage (KDOQI 2020)."
)

# Default daily limits by stage — used when the doctor hasn't set custom targets.
DEFAULT_LIMITS_BY_STAGE: dict = {
    "dialysis": {"potassium_mg": 2000, "phosphorus_mg": 1000, "sodium_mg": 2000, "fluid_ml": 1000},
    "pre_dialysis": {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300, "fluid_ml": 2000},
    "unknown": {"potassium_mg": 2400, "phosphorus_mg": 1200, "sodium_mg": 2300, "fluid_ml": 2000},
}


def personal_tier_for(food: dict, stage: Stage) -> str:
    """Compute the tier shown to the user based on their CKD stage.

    - dialysis + YELLOW + (K / P / Fluid) → tightened to RED
    - pre_dialysis + YELLOW + POTASSIUM → softened to GREEN
      (KDOQI 2020 recommends individualized K targets before dialysis;
       we never soften sodium or phosphorus items).
    - unknown stage never changes the tier.
    """
    base = food["safety_tier"]
    risk = food.get("primary_risk_factor")
    if stage == "dialysis" and base == "YELLOW" and risk in {"POTASSIUM", "PHOSPHORUS", "FLUID"}:
        return "RED"
    if stage == "pre_dialysis" and base == "YELLOW" and risk == "POTASSIUM":
        return "GREEN"
    return base


def personalized_note_for(food: dict, stage: Stage) -> Optional[str]:
    if (
        stage == "pre_dialysis"
        and food["safety_tier"] == "YELLOW"
        and food.get("primary_risk_factor") == "POTASSIUM"
    ):
        return PRE_DIALYSIS_K_NOTE
    return None


def limits_for_user(user: dict) -> NutrientLimits:
    """Doctor-set limits win; otherwise stage-based defaults.

    Fluid is included in the same doctor-override pattern as K/P/Na so a
    nephrologist can set a tighter (or looser) daily fluid target than the
    stage default — this matters clinically for dialysis patients where
    fluid restriction is often the tightest-managed constraint.
    """
    stage: Stage = user.get("stage", "unknown") or "unknown"  # type: ignore
    defaults = DEFAULT_LIMITS_BY_STAGE.get(stage, DEFAULT_LIMITS_BY_STAGE["unknown"])
    doc = user.get("doctor_limits") or {}
    return NutrientLimits(
        potassium_mg=float(doc.get("potassium_mg") or defaults["potassium_mg"]),
        phosphorus_mg=float(doc.get("phosphorus_mg") or defaults["phosphorus_mg"]),
        sodium_mg=float(doc.get("sodium_mg") or defaults["sodium_mg"]),
        fluid_ml=float(doc.get("fluid_ml") or defaults["fluid_ml"]),
    )
