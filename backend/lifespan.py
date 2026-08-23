"""FastAPI lifespan — seed reconciliation, index creation, guide sourcing dump."""
from __future__ import annotations

import csv
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from beverage_guide import BEVERAGE_GUIDE
from db import client, db
from fruit_guide import FRUIT_GUIDE
from grain_guide import GRAIN_GUIDE
from guide_utils import collect_needs_sourcing, write_needs_sourcing_csv
from oil_guide import OIL_GUIDE
from protein_guide import PROTEIN_GUIDE
from reconciliation import reconcile_seed
from seed_data import SEED_FOODS, SEED_SWAPS
from seed_data_indb import SEED_FOODS_INDB
from snack_guide import SNACK_GUIDE
from vegetable_guide import VEGETABLE_GUIDE

logger = logging.getLogger("renal-diet")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # ---- Startup ----
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.foods.create_index("id", unique=True)
    await db.foods.create_index("name")
    await db.swaps.create_index("trigger_food_id")
    await db.meal_logs.create_index([("user_id", 1), ("date", 1)])
    await db.favorites.create_index([("user_id", 1), ("food_id", 1)], unique=True)

    all_foods, recon_stats = reconcile_seed(SEED_FOODS, SEED_FOODS_INDB, logger=logger)
    reconciled_ids = {food["id"] for food in all_foods}
    for food in all_foods:
        # replace_one (not $set) so fields no longer applicable in the current
        # reconciliation (e.g. a stale auto_rescaled from an earlier run whose
        # bucket rules were looser) are removed on write.
        await db.foods.replace_one({"id": food["id"]}, food, upsert=True)
    # Purge stale seed rows from earlier iterations (e.g. dropped duplicates,
    # renamed IDs). Preserve barcode-persisted user data via source filter.
    purge = await db.foods.delete_many(
        {"id": {"$nin": list(reconciled_ids)}, "source": {"$ne": "barcode"}}
    )
    if purge.deleted_count:
        logger.info("Purged %d stale seed rows no longer in reconciled catalog", purge.deleted_count)
    for swap in SEED_SWAPS:
        await db.swaps.update_one({"id": swap["id"]}, {"$set": swap}, upsert=True)
    logger.info("Seeded %d foods, %d swaps", len(all_foods), len(SEED_SWAPS))

    # Write sanity-ceiling violations to a review CSV (Step 7 output).
    if recon_stats["sanity_violations"]:
        review_path = Path(__file__).parent / "needs_manual_review.csv"
        with open(review_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["id", "name", "violations"])
            for _id, _name, _vio in recon_stats["sanity_violations"]:
                w.writerow([_id, _name, "; ".join(_vio)])
        logger.info(
            "Wrote %d rows to %s for manual review",
            len(recon_stats["sanity_violations"]), review_path,
        )

    # Write guide_needs_sourcing.csv — every guide entry missing sodium_mg plus
    # the explicitly-flagged dishes we chose not to add without a real number.
    try:
        missing_rows = collect_needs_sourcing([
            ("fruit",     FRUIT_GUIDE,     "fruits"),
            ("vegetable", VEGETABLE_GUIDE, "vegetables"),
            ("snack",     SNACK_GUIDE,     "snacks"),
            ("beverage",  BEVERAGE_GUIDE,  "beverages"),
            ("protein",   PROTEIN_GUIDE,   "proteins"),
            ("grain",     GRAIN_GUIDE,     "grains"),
            ("oil",       OIL_GUIDE,       "oils"),
        ])
        write_needs_sourcing_csv(
            Path(__file__).parent / "guide_needs_sourcing.csv",
            missing_rows,
        )
    except Exception:
        logger.exception("Failed to write guide_needs_sourcing.csv")
    yield

    # ---- Shutdown ----
    client.close()
