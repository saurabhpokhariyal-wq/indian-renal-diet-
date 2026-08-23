"""Curated guides (fruit, beverage, vegetable, snack, protein, grain)."""
from fastapi import APIRouter

from beverage_guide import get_beverage_guide
from fruit_guide import get_fruit_guide
from grain_guide import get_grain_guide
from oil_guide import get_oil_guide
from protein_guide import get_protein_guide
from snack_guide import get_snack_guide
from vegetable_guide import get_vegetable_guide

router = APIRouter()


@router.get("/fruits/guide")
async def fruits_guide():
    """Patient-facing curated fruit reference for CKD/dialysis."""
    return get_fruit_guide()


@router.get("/beverages/guide")
async def beverages_guide():
    """Patient-facing curated beverage reference for CKD/dialysis."""
    return get_beverage_guide()


@router.get("/vegetables/guide")
async def vegetables_guide():
    """Patient-facing curated vegetable reference for CKD/dialysis."""
    return get_vegetable_guide()


@router.get("/snacks/guide")
async def snacks_guide():
    """Patient-facing curated snack reference for CKD/dialysis."""
    return get_snack_guide()


@router.get("/proteins/guide")
async def proteins_guide():
    """Patient-facing curated protein reference for CKD/dialysis."""
    return get_protein_guide()


@router.get("/grains/guide")
async def grains_guide():
    """Patient-facing curated grains & rotis reference for CKD/dialysis."""
    return get_grain_guide()


@router.get("/oils/guide")
async def oils_guide():
    """Patient-facing curated fats & oils reference for CKD/dialysis."""
    return get_oil_guide()
