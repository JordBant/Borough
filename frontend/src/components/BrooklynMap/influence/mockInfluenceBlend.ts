import type { ExpressionSpecification } from "mapbox-gl";

/**
 * Distance helpers and metric→color ramps for mocked parcel-driven building tints.
 */

/** ~Plate-carree planar distance squared in degree² terms (longitude scaled by latitude). */
export function haversineLikeQuickLngLatDistanceSquaredDegrees(
  lngFirst: number,
  latFirst: number,
  lngSecond: number,
  latSecond: number
): number {
  const differentialLongitudeScaled = (lngSecond - lngFirst) * Math.cos(((latFirst + latSecond) * Math.PI) / 360);
  const differentialLatitudeDegrees = latSecond - latFirst;
  return (
    differentialLongitudeScaled * differentialLongitudeScaled + differentialLatitudeDegrees * differentialLatitudeDegrees
  );
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

/**
 * Loud rooftop beacons: each mock corridor lands on a **golden-angle hue** (~137.5°) so neighbors stay
 * maximally distinguishable at street zoom; volatility nudges the wheel toward greener (stable) vs
 * redder (hot) without collapsing separation.
 *
 * Caps use high saturation/lightness so they read clearly against Standard night lighting + emissive.
 */
export function indicativeMetricContributorCapHsl(
  volatilityObservation: number | undefined,
  corridorIndexObservation: number
): ExpressionSpecification {
  const volatilityCoefficient = volatilityObservation ?? 0.56;
  const normalizedStressObservation = clamp01((volatilityCoefficient - 0.35) / 0.62);

  const goldenHueCorridorFingerprintObservation = ((corridorIndexObservation * 137.508369) % 360 + 360) % 360;
  /** Small swing toward warm hues as volatility ramps; golden spacing keeps corridors apart even when mocks cluster. */
  const volatilityThermalHueSkewObservation = normalizedStressObservation * 58 - 29;
  const compositeHueCircularDegreesObservation = Math.round(
    (goldenHueCorridorFingerprintObservation + volatilityThermalHueSkewObservation + 360) % 360
  );
  /** Near full chroma — caps should read like LED markers above photoreal meshes. */
  const chromaSaturationSweepPercentObservation = Math.round(93 + volatilityCoefficient * 7);
  const luminanceSweepPercentObservation = Math.round(48 + volatilityCoefficient * 22);

  return [
    "hsl",
    compositeHueCircularDegreesObservation,
    chromaSaturationSweepPercentObservation,
    luminanceSweepPercentObservation,
  ];
}
