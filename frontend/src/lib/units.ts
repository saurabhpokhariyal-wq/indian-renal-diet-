/**
 * Unit conversion helpers for renal nutrition display.
 *
 * The database stores everything canonically in milligrams (mg). At the display
 * layer we optionally convert Potassium (K) and Sodium (Na) to milliequivalents
 * (mEq) based on the user's `nutrient_unit` preference. Phosphorus and other
 * nutrients always render in mg — the user selected "K + Na only".
 *
 * Conversion (monovalent ions, so mEq = mmol):
 *   1 mEq K  = 39.1 mg   (atomic mass of K+)
 *   1 mEq Na = 23   mg   (atomic mass of Na+)
 */

export type NutrientUnit = "mg" | "mEq";
export type UnitNutrient = "K" | "Na";

export const K_MG_PER_MEQ = 39.1;
export const NA_MG_PER_MEQ = 23;

/** How many mg a single mEq of the given nutrient represents. */
export function mgPerMeq(nutrient: UnitNutrient): number {
  return nutrient === "K" ? K_MG_PER_MEQ : NA_MG_PER_MEQ;
}

/** Convert a canonical mg value into the user's display unit. */
export function mgToUserUnit(
  nutrient: UnitNutrient,
  mg: number,
  unit: NutrientUnit,
): number {
  if (!Number.isFinite(mg)) return 0;
  if (unit === "mg") return mg;
  return mg / mgPerMeq(nutrient);
}

/** Convert a user-entered value (in `unit`) back to canonical mg. */
export function userUnitToMg(
  nutrient: UnitNutrient,
  value: number,
  unit: NutrientUnit,
): number {
  if (!Number.isFinite(value)) return 0;
  if (unit === "mg") return value;
  return value * mgPerMeq(nutrient);
}

/** Trailing unit label ("mg" or "mEq"). */
export function unitLabel(unit: NutrientUnit): string {
  return unit;
}

interface FormatOptions {
  /** Include the unit suffix ("mg" or "mEq"). Default true. */
  withUnit?: boolean;
  /** Include a leading space between number and unit. Default true. */
  space?: boolean;
}

/**
 * Format a mg value for display in the user's chosen unit.
 * - mg  → rounded integer  (e.g. "158 mg")
 * - mEq → one decimal      (e.g. "4.0 mEq")
 */
export function formatValue(
  nutrient: UnitNutrient,
  mg: number,
  unit: NutrientUnit,
  opts: FormatOptions = {},
): string {
  const { withUnit = true, space = true } = opts;
  const converted = mgToUserUnit(nutrient, mg, unit);
  const numeric =
    unit === "mg" ? String(Math.round(converted)) : converted.toFixed(1);
  if (!withUnit) return numeric;
  return `${numeric}${space ? " " : ""}${unit}`;
}

export function formatK(
  mg: number,
  unit: NutrientUnit,
  opts?: FormatOptions,
): string {
  return formatValue("K", mg, unit, opts);
}

export function formatNa(
  mg: number,
  unit: NutrientUnit,
  opts?: FormatOptions,
): string {
  return formatValue("Na", mg, unit, opts);
}

/**
 * Format that always shows both units, e.g. "158 mg (4.0 mEq)". Used in the
 * weekly PDF report where the user requested full clinical clarity.
 */
export function formatBoth(nutrient: UnitNutrient, mg: number): string {
  const meq = mg / mgPerMeq(nutrient);
  return `${Math.round(mg)} mg (${meq.toFixed(1)} mEq)`;
}

/** Rounded display integer count used by <NutrientBar/> - handles decimals. */
export function displayNumeric(value: number, unit: NutrientUnit): string {
  return unit === "mg" ? String(Math.round(value)) : value.toFixed(1);
}
