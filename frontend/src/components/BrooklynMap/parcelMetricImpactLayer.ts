import type {
  ExpressionSpecification,
  FillExtrusionLayerSpecification,
  Map,
} from "mapbox-gl";

/**
 * `fill-extrusion` on the parcel GeoJSON source.
 * Paint is driven by `heatIntensity` (0–1), with fallback to `metricImpact` for older data.
 */
export const PARCEL_HEAT_EXTRUSION_LAYER_ID = "rent-market-parcel-metric-impact-3d";

/** Expression that prefers heat-linked intensity from `computeParcelHeatMetadata`. */
const parcelHeatDriverExpr: ExpressionSpecification = [
  "coalesce",
  ["get", "heatIntensity"],
  ["get", "metricImpact"],
  0,
];

/**
 * Registers bright 3D lot prisms: color, height, emissive follow the same driver as heatmap weight.
 * Expects layer source (e.g. `rent-market-parcels`) to exist.
 */
export function addParcelHeatIntensityExtrusionLayer(map: Map): void {
  const spec: FillExtrusionLayerSpecification = {
    id: PARCEL_HEAT_EXTRUSION_LAYER_ID,
    type: "fill-extrusion",
    slot: "top",
    source: "rent-market-parcels",
    minzoom: 12,
    layout: {
      // Spec: 0–1; rounds wall joints so the faceted circle reads cylindrical in 3D Standard lighting.
      "fill-extrusion-edge-radius": 1,
    },
    paint: {
      "fill-extrusion-color": [
        "interpolate",
        ["linear"],
        parcelHeatDriverExpr,
        0,
        "#22c55e",
        0.28,
        "#06b6d4",
        0.48,
        "#a855f7",
        0.68,
        "#fb923c",
        0.88,
        "#f43f5e",
        1,
        "#fbbf24",
      ] as ExpressionSpecification,
      "fill-extrusion-height": [
        "interpolate",
        ["linear"],
        parcelHeatDriverExpr,
        0,
        14,
        1,
        56,
      ] as ExpressionSpecification,
      "fill-extrusion-base": 0,
      // Long, gradual ramp while zooming in; plateaus at 0.7 (fill-extrusion-opacity is layer-wide).
      "fill-extrusion-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        11.85,
        0,
        12,
        0.06,
        12.75,
        0.16,
        13.5,
        0.26,
        14.25,
        0.36,
        15,
        0.45,
        15.75,
        0.53,
        16.5,
        0.6,
        17.25,
        0.66,
        18,
        0.7,
      ] as ExpressionSpecification,
      "fill-extrusion-emissive-strength": [
        "interpolate",
        ["linear"],
        parcelHeatDriverExpr,
        0,
        0.5,
        1,
        1.12,
      ] as ExpressionSpecification,
      "fill-extrusion-vertical-gradient": true,
      "fill-extrusion-ambient-occlusion-intensity": 0.06,
      "fill-extrusion-flood-light-intensity": 0.55,
      "fill-extrusion-flood-light-wall-radius": 20,
    },
  };

  map.addLayer(spec);
}
