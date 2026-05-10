import { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import type {
  ExpressionSpecification,
  FilterSpecification,
  FillExtrusionLayerSpecification,
  GeoJSONFeature,
  HeatmapLayerSpecification,
} from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import { BROOKLYN_BOUNDARY, BROOKLYN_CENTER } from "../../data/brooklynBoundary";
import {
  computeMetricImpactScore,
  computeParcelHeatMetadata,
  deriveParcelTrendFields,
  MOCK_MARKET_SAMPLES,
  mockMarketBuildingHighlightGeometries,
  samplesToHeatmapGeoJSON,
  samplesToParcelContributionGeoJSON,
  type MockMarketSample,
} from "../../data/mockProperties";
import { attachStandardBuildingMockInfluenceInteractions } from "./influence/attachStandardBuildingMockInfluenceInteractions";
import {
  haversineLikeQuickLngLatDistanceSquaredDegrees,
  indicativeMetricContributorCapHsl,
} from "./influence/mockInfluenceBlend";
import { planarPolygonLikeCentroidLongitudeLatitude } from "./influence/polygonLngLatAnchor";
import CollapsiblePanel from "./CollapsiblePanel";
import PerspectiveLeveler from "./PerspectiveLeveler";
import "./BrooklynMap.css";
import { buildFeatherMaskLayerSpecs } from "./maskUtils";
import { buildParcelCollectionAlignedToRenderedBuildings } from "./parcelBuildingAlignment";
import { attachParcelFootprintZoomSync } from "./parcelFootprintZoom";
import { useBasemapStandardToggles } from "../../hooks/useBasemapStandardToggles";
import { useParcelHeatExtrusionLayer } from "../../hooks/useParcelHeatExtrusionLayer";
import {
  BASEMAP_STANDARD_TOGGLE_UI,
  DEFAULT_BASEMAP_STANDARD_TOGGLES,
  type BasemapStandardToggles,
} from "../../map/basemapStandardToggles";
import { applyBoroughNoirBasemapTheme, getBoroughMapInitialConfig } from "../../map/boroughBasemapTheme";

const MAPBOX_ACCESS_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

/** Standard style exposes photorealistic 3D buildings when `show3dObjects` is enabled. */
const MAP_STYLE_STANDARD = "mapbox://styles/mapbox/standard";

const DEFAULT_PITCH = 60;
const DEFAULT_BEARING = -17;

type BoroughMaskHud = {
  setVeilVisible: (phaseVeilObservationVisible: boolean) => void;
  purgeInfluenceGlow: () => void;
};

interface ParcelPopupFields {
  mockParcelLotId?: string;
  neighborhood?: string;
  volatilityLabel?: string;
  trendDeltaLabel?: string;
  priorVolatilityLabel?: string;
  metricImpactLabel?: string;
}

export default function BrooklynMap() {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<mapboxgl.Map | null>(null);
  const boroughHeatMaskGateRef = useRef(true);
  const boroughMaskHudRef = useRef<BoroughMaskHud>({
    setVeilVisible: () => {},
    purgeInfluenceGlow: () => {},
  });

  const [controlsReady, setControlsReady] = useState(false);
  const [boroughHeatVeilOn, setBoroughHeatVeilOn] = useState(true);
  const [basemapToggles, setBasemapToggles] = useState<BasemapStandardToggles>(() => ({
    ...DEFAULT_BASEMAP_STANDARD_TOGGLES,
  }));

  useParcelHeatExtrusionLayer(mapInstanceRef, controlsReady, {
    parcelSourceId: "rent-market-parcels",
    enabled: true,
  });

  useBasemapStandardToggles(mapInstanceRef, controlsReady, basemapToggles);

  useEffect(() => {
    boroughHeatMaskGateRef.current = boroughHeatVeilOn;
  }, [boroughHeatVeilOn]);

  useEffect(() => {
    if (!MAPBOX_ACCESS_TOKEN) {
      console.error("Missing VITE_MAPBOX_ACCESS_TOKEN in .env");
      return undefined;
    }

    if (!mapContainerRef.current) {
      return undefined;
    }

    mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE_STANDARD,
      config: getBoroughMapInitialConfig(),
      center: BROOKLYN_CENTER,
      zoom: 11.5,
      pitch: DEFAULT_PITCH,
      bearing: DEFAULT_BEARING,
      antialias: true,
    });

    mapInstanceRef.current = map;

    let detachInfluenceGlowHandlers: () => void = () => {};

    map.addControl(
      new mapboxgl.NavigationControl({
        showCompass: true,
        showZoom: true,
        visualizePitch: true,
      }),
      "top-right"
    );

    map.on("load", () => {
      applyBoroughNoirBasemapTheme(map);

      map.setFog({
        color: "#000000",
        "high-color": "#0c1424",
        "horizon-blend": 0.35,
        "space-color": "#000000",
        "star-intensity": 0.06,
      });

      map.addSource("brooklyn-boundary", {
        type: "geojson",
        data: BROOKLYN_BOUNDARY,
      });

      addRentMarketHeatLayers(map);

      const outerVeilDescriptors = buildFeatherMaskLayerSpecs(BROOKLYN_BOUNDARY);

      function applyOuterVeilLayerOpacityObservation(phaseVeilObservationVisible: boolean): void {
        outerVeilDescriptors.forEach((maskSpecItem) => {
          if (!map.getLayer(maskSpecItem.id)) {
            return;
          }
          map.setPaintProperty(
            maskSpecItem.id,
            "fill-opacity",
            phaseVeilObservationVisible ? maskSpecItem.fillOpacity : 0
          );
        });
      }

      outerVeilDescriptors.forEach((maskSpecItem) => {
        const featherSourceIdentifier = `${maskSpecItem.id}-source`;
        map.addSource(featherSourceIdentifier, {
          type: "geojson",
          data: maskSpecItem.data,
        });

        map.addLayer({
          id: maskSpecItem.id,
          type: "fill",
          slot: "top",
          source: featherSourceIdentifier,
          paint: {
            "fill-color": maskSpecItem.fillColor,
            "fill-opacity": maskSpecItem.fillOpacity,
          },
        });
      });

      const hoverDimBundleObservation = attachStandardBuildingMockInfluenceInteractions({
        map,
      });

      detachInfluenceGlowHandlers = hoverDimBundleObservation.detachInteractions;

      boroughMaskHudRef.current.setVeilVisible = (phaseVeilObservationVisible) => {
        applyOuterVeilLayerOpacityObservation(phaseVeilObservationVisible);
        if (!phaseVeilObservationVisible) {
          hoverDimBundleObservation.purgeTransientBuildingHighlights();
        }
      };

      boroughMaskHudRef.current.purgeInfluenceGlow = hoverDimBundleObservation.purgeTransientBuildingHighlights;

      applyOuterVeilLayerOpacityObservation(boroughHeatMaskGateRef.current);

      map.addLayer({
        id: "brooklyn-boundary-outline",
        type: "line",
        slot: "top",
        source: "brooklyn-boundary",
        paint: {
          "line-color": "#67e8f9",
          "line-width": 2,
          "line-opacity": 0.92,
        },
      });

      setControlsReady(true);
    });

    return () => {
      setControlsReady(false);
      detachInfluenceGlowHandlers();
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  return (
    <div className="brooklyn-map-wrapper">
      <div ref={mapContainerRef} className="brooklyn-map-container" />
      <PerspectiveLeveler
        mapRef={mapInstanceRef}
        enabled={controlsReady}
        initialPitch={DEFAULT_PITCH}
        initialBearing={DEFAULT_BEARING}
      />
      <CollapsiblePanel
        title="Rent fluctuation"
        summaryCollapsed="Heatmap legend — tap to expand"
        className="brooklyn-map-legend"
        defaultExpanded
      >
        <p className="legend-desc">
          At street zoom, vivid rooftop caps mark contributor footprints (metrics via hue). Photoreal Standard
          massing tint is not overridden globally; hovering a basemap mesh only applies a subtle darken cue.
          Turn the vignette off to hide the outer heat mask and clear any hover cue.
        </p>
        <label className="legend-heat-veil-toggle">
          <input
            type="checkbox"
            checked={boroughHeatVeilOn}
            disabled={!controlsReady}
            onChange={(interactionEventObservation) => {
              const veilPhaseObservationEnabled = interactionEventObservation.target.checked;
              setBoroughHeatVeilOn(veilPhaseObservationEnabled);
              boroughHeatMaskGateRef.current = veilPhaseObservationEnabled;
              boroughMaskHudRef.current.setVeilVisible(veilPhaseObservationEnabled);
            }}
          />{" "}
          <span>Borough heat mask (dims vignette; clears hover darken when off)</span>
        </label>
        <p className="legend-metric-buildings-caption">Basemap (Mapbox Standard)</p>
        <div className="basemap-toggle-list" aria-label="Basemap layer visibility">
          {BASEMAP_STANDARD_TOGGLE_UI.map(({ key, label }) => (
            <label key={key} className="basemap-toggle-label">
              <input
                type="checkbox"
                checked={basemapToggles[key]}
                disabled={!controlsReady}
                onChange={(ev) => {
                  const checked = ev.target.checked;
                  setBasemapToggles((prev) => ({ ...prev, [key]: checked }));
                }}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
        <p className="legend-metric-buildings-caption">
          Dense pockets: several parcels within ~1–2 short blocks raise shared heat weight; 3D prisms track that
          intensity per lot.
        </p>
        <p className="legend-metric-buildings-caption">
          Lot impact columns (street zoom): taller, brighter prisms = higher mock metric impact (volatility + Δ).
        </p>
        <p className="legend-metric-buildings-caption">
          Mock lots: each parcel uses a distinct accent; fill/outline strength shows mock volatility{" "}
          <em>increase</em> (↑), decrease (↓), or steady. Same data powers the heat layer.
        </p>
        <p className="legend-metric-buildings-caption">Contributor rooftop caps · metric hue (zoom toward 3D)</p>
        <div className="legend-gradient legend-gradient-metric-buildings" />
        <div className="legend-scale legend-scale-tall">
          <span className="legend-low">Stable</span>
          <div className="legend-gradient legend-gradient-heatmap" />
          <span className="legend-high">Volatile</span>
        </div>
      </CollapsiblePanel>
    </div>
  );
}

function addRentMarketHeatLayers(map: mapboxgl.Map): void {
  const pointGeojson = samplesToHeatmapGeoJSON(MOCK_MARKET_SAMPLES);
  const parcelGeojson = samplesToParcelContributionGeoJSON(MOCK_MARKET_SAMPLES);
  const highlightGeometries = mockMarketBuildingHighlightGeometries(MOCK_MARKET_SAMPLES);

  map.addSource("rent-market-flux", {
    type: "geojson",
    data: pointGeojson,
  });

  map.addSource("rent-market-parcels", {
    type: "geojson",
    data: parcelGeojson,
  });

  const parcelTemplateForAlignment = parcelGeojson;
  const parcelFootprintBaseRef: { current: typeof parcelGeojson } = { current: parcelGeojson };

  const refreshParcelFootprints = attachParcelFootprintZoomSync(map, "rent-market-parcels", () => parcelFootprintBaseRef.current);

  const tryAlignParcelsToBuildings = (): void => {
    const aligned = buildParcelCollectionAlignedToRenderedBuildings(map, MOCK_MARKET_SAMPLES, parcelTemplateForAlignment);
    if (!aligned) return;
    parcelFootprintBaseRef.current = aligned;
    refreshParcelFootprints();
  };

  map.once("idle", tryAlignParcelsToBuildings);
  map.on("zoomend", tryAlignParcelsToBuildings);

  map.addLayer({
    id: "rent-market-flux-heat",
    type: "heatmap",
    slot: "middle",
    source: "rent-market-flux",
    maxzoom: 18,
    paint: {
      "heatmap-weight": [
        "interpolate",
        ["linear"],
        ["get", "weight"],
        0,
        0,
        1,
        1.65,
      ] as ExpressionSpecification,
      // Softer blobs when zoomed out; taper before parcel extrusions take over.
      "heatmap-intensity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        8,
        0.55,
        11,
        0.95,
        13.5,
        1.35,
        15,
        0.45,
        16.5,
        0.15,
      ] as ExpressionSpecification,
      "heatmap-color": [
        "interpolate",
        ["linear"],
        ["heatmap-density"],
        0,
        "rgba(56, 189, 248, 0)",
        0.12,
        "rgba(110, 231, 183, 0.45)",
        0.38,
        "rgba(251, 191, 36, 0.7)",
        0.65,
        "rgba(249, 115, 22, 0.85)",
        1,
        "rgba(239, 68, 68, 0.95)",
      ] as ExpressionSpecification,
      "heatmap-radius": [
        "interpolate",
        ["linear"],
        ["zoom"],
        7,
        85,
        10,
        120,
        12,
        95,
        13.5,
        55,
        15,
        28,
      ] as ExpressionSpecification,
      "heatmap-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        8,
        0.88,
        11,
        0.92,
        13.5,
        0.55,
        14.5,
        0.22,
        16,
        0.06,
      ] as ExpressionSpecification,
      /** Runtime-supported; omitted from bundled style spec typings. */
      "heatmap-blur": [
        "interpolate",
        ["linear"],
        ["zoom"],
        8,
        1.35,
        12,
        1.05,
        15,
        0.55,
      ] as ExpressionSpecification,
    } as HeatmapLayerSpecification["paint"],
  });

  /*
   * Standard renders photoreal 3 *above* `middle`-slot extrusions — full-prism washes were invisible.
   * Rooftop **beacons** (`base` = roof `height`, `height` prop = roof + cap) live in **`top`** slot so they paint
   * over meshes as soon as you zoom into dense 3D.
   */
  const rooftopElevationMetersExpressionObservation = [
    "coalesce",
    ["get", "height"],
    14,
  ] as ExpressionSpecification;
  /* Tall billboard caps (~8–34 m): obvious from pitched street views alongside Standard landmarks. */
  const rooftopBeaconCapElevationSpanMetersExpressionObservation = [
    "interpolate",
    ["linear"],
    ["zoom"],
    12.65,
    0,
    12.92,
    6,
    13.22,
    18,
    13.95,
    28,
    16.75,
    34,
  ] as ExpressionSpecification;
  /* Snap opaque quickly once roofs read in 3D; hold at photographic full strength. */
  const rooftopBeaconRevealOpacityRampObservation = [
    "interpolate",
    ["linear"],
    ["zoom"],
    12.72,
    0,
    12.94,
    0.92,
    13.15,
    1,
    17,
    1,
  ] as ExpressionSpecification;

  const metricContributorHallmarkHueCaseObservation: unknown[] = ["case"];
  const beaconEmissiveBurstCaseObservation: unknown[] = ["case"];

  MOCK_MARKET_SAMPLES.forEach((sampleRowObservation, corridorIndexObservation) => {
    const perimeterGeometryLiteralObservation = highlightGeometries[corridorIndexObservation];
    const weightObservation = sampleRowObservation.rentVolatilityIndex;

    metricContributorHallmarkHueCaseObservation.push(
      ["within", perimeterGeometryLiteralObservation],
      indicativeMetricContributorCapHsl(weightObservation, corridorIndexObservation)
    );
    beaconEmissiveBurstCaseObservation.push(
      ["within", perimeterGeometryLiteralObservation],
      Number((1.12 + weightObservation * 0.92).toFixed(3))
    );
  });

  metricContributorHallmarkHueCaseObservation.push(["hsl", 218, 5, 8]);
  beaconEmissiveBurstCaseObservation.push(0);

  const footprintWithinEnvelope: unknown[] = ["any"];
  highlightGeometries.forEach((polygonGeometryLiteral) => {
    footprintWithinEnvelope.push(["within", polygonGeometryLiteral]);
  });

  const streetsBuildingExtrudeFilterExpression: FilterSpecification = [
    "all",
    footprintWithinEnvelope as ExpressionSpecification,
    [
      "any",
      ["==", ["get", "extrude"], true],
      ["==", ["to-string", ["get", "extrude"]], "true"],
    ] as ExpressionSpecification,
  ] as FilterSpecification;

  const fluxBuildingLayerSpecification: FillExtrusionLayerSpecification = {
    id: "rent-market-streets-building-flux",
    type: "fill-extrusion",
    slot: "top",
    source: "composite",
    "source-layer": "building",
    filter: streetsBuildingExtrudeFilterExpression,
    minzoom: 12,
    layout: {
      "fill-extrusion-edge-radius": 0.22,
    },
    paint: {
      "fill-extrusion-color": metricContributorHallmarkHueCaseObservation as ExpressionSpecification,
      "fill-extrusion-base": rooftopElevationMetersExpressionObservation,
      "fill-extrusion-height": [
        "+",
        rooftopElevationMetersExpressionObservation,
        rooftopBeaconCapElevationSpanMetersExpressionObservation,
      ] as ExpressionSpecification,
      "fill-extrusion-opacity": rooftopBeaconRevealOpacityRampObservation,
      "fill-extrusion-emissive-strength": [
        "*",
        [
          "interpolate",
          ["linear"],
          ["zoom"],
          12.72,
          0,
          13.05,
          0.92,
          13.35,
          1,
        ] as ExpressionSpecification,
        beaconEmissiveBurstCaseObservation as ExpressionSpecification,
      ] as ExpressionSpecification,
      "fill-extrusion-vertical-gradient": false,
      "fill-extrusion-ambient-occlusion-intensity": 0.04,
      "fill-extrusion-flood-light-intensity": 0.52,
      "fill-extrusion-flood-light-wall-radius": 18,
    },
  };

  map.addLayer(fluxBuildingLayerSpecification);

  addParcelTrendStylingLayers(map);

  map.addLayer({
    id: "rent-market-parcel-hit",
    type: "fill",
    slot: "top",
    source: "rent-market-parcels",
    minzoom: 12,
    paint: {
      "fill-color": "#000000",
      "fill-opacity": 0,
    },
  });

  const parcelPopup = new mapboxgl.Popup({
    closeButton: true,
    closeOnClick: true,
    maxWidth: "280px",
  });

  const openFluxPopupTitle = (
    mapClickEventLngLatCoordinates: mapboxgl.LngLat,
    parcelFeatureProperties: ParcelPopupFields
  ): mapboxgl.Popup =>
    parcelPopup
      .setLngLat(mapClickEventLngLatCoordinates)
      .setHTML(
        `<div class="parcel-popup">
          <strong>${parcelFeatureProperties.mockParcelLotId ?? "Mock lot"}</strong>
          <div class="parcel-popup-meta">${parcelFeatureProperties.neighborhood ?? ""}</div>
          <div class="parcel-popup-meta">${parcelFeatureProperties.volatilityLabel ?? ""}</div>
          ${
            parcelFeatureProperties.trendDeltaLabel
              ? `<div class="parcel-popup-delta">${parcelFeatureProperties.trendDeltaLabel}</div>`
              : ""
          }
          ${
            parcelFeatureProperties.priorVolatilityLabel
              ? `<div class="parcel-popup-meta">${parcelFeatureProperties.priorVolatilityLabel}</div>`
              : ""
          }
          ${
            parcelFeatureProperties.metricImpactLabel
              ? `<div class="parcel-popup-meta parcel-popup-impact">${parcelFeatureProperties.metricImpactLabel}</div>`
              : ""
          }
        </div>`
      )
      .addTo(map);

  const rentClickLayers = ["rent-market-parcel-hit", "rent-market-streets-building-flux"];

  map.on("click", (e) => {
    const hits = map.queryRenderedFeatures(e.point, { layers: rentClickLayers });
    const top = hits[0];
    if (!top?.layer?.id) return;

    if (top.layer.id === "rent-market-parcel-hit") {
      const parcelPick = pickParcelFields(top as GeoJSONFeature);
      if (parcelPick?.mockParcelLotId) openFluxPopupTitle(e.lngLat, parcelPick);
      return;
    }

    const parcelOverlayPickList = map.queryRenderedFeatures(e.point, {
      layers: ["rent-market-parcel-hit"],
    });
    const parcelOverlayObservation = pickParcelFields(parcelOverlayPickList[0]);

    const firstMeshFeature = top as GeoJSONFeature;
    const centroidObservation = planarPolygonLikeCentroidLongitudeLatitude(firstMeshFeature.geometry);
    const referenceLngLongitude = centroidObservation?.lng ?? e.lngLat.lng;
    const referenceLatLatitude = centroidObservation?.lat ?? e.lngLat.lat;

    if (parcelOverlayObservation?.mockParcelLotId != null && parcelOverlayObservation.volatilityLabel != null) {
      openFluxPopupTitle(e.lngLat, parcelOverlayObservation);
      return;
    }

    const nearest = nearestMarketSampleForLngLat(
      referenceLngLongitude,
      referenceLatLatitude,
      MOCK_MARKET_SAMPLES
    );
    openFluxPopupTitle(e.lngLat, synthesizeNearestSamplePopupFields(nearest.sample, nearest.index));
  });

  const setRentMarketPointer = (active: boolean) => {
    map.getCanvas().style.cursor = active ? "pointer" : "";
  };

  map.on("mouseenter", "rent-market-parcel-hit", () => setRentMarketPointer(true));
  map.on("mouseleave", "rent-market-parcel-hit", () => setRentMarketPointer(false));
  map.on("mouseenter", "rent-market-streets-building-flux", () => setRentMarketPointer(true));
  map.on("mouseleave", "rent-market-streets-building-flux", () => setRentMarketPointer(false));
}

/** Programmatic parcel/lot chrome from mock heat sample props: distinct accent + rising vs falling band. */
function addParcelTrendStylingLayers(map: mapboxgl.Map): void {
  map.addLayer({
    id: "rent-market-parcel-trend-fill",
    type: "fill",
    slot: "top",
    source: "rent-market-parcels",
    minzoom: 12,
    paint: {
      "fill-color": [
        "match",
        ["get", "trendBand"],
        "rising",
        ["to-color", ["get", "parcelAccent"]],
        "falling",
        "#38bdf8",
        "#94a3b8",
      ] as ExpressionSpecification,
      "fill-opacity": [
        "match",
        ["get", "trendBand"],
        "rising",
        0.42,
        "falling",
        0.2,
        0.14,
      ] as ExpressionSpecification,
    },
  });

  map.addLayer({
    id: "rent-market-parcel-trend-outline",
    type: "line",
    slot: "top",
    source: "rent-market-parcels",
    minzoom: 12,
    paint: {
      "line-color": [
        "match",
        ["get", "trendBand"],
        "rising",
        ["to-color", ["get", "parcelAccent"]],
        "falling",
        "#7dd3fc",
        "#cbd5e1",
      ] as ExpressionSpecification,
      "line-width": [
        "match",
        ["get", "trendBand"],
        "rising",
        2.5,
        "falling",
        1.2,
        1.6,
      ] as ExpressionSpecification,
      "line-opacity": [
        "interpolate",
        ["linear"],
        ["zoom"],
        12,
        0.55,
        13,
        0.95,
      ] as ExpressionSpecification,
    },
  });

  map.addLayer({
    id: "rent-market-parcel-trend-labels",
    type: "symbol",
    slot: "top",
    source: "rent-market-parcels",
    minzoom: 12.4,
    layout: {
      "text-field": ["get", "mapLabel"] as ExpressionSpecification,
      "text-size": 11,
      "text-offset": [0, 1.15],
      "text-anchor": "top",
      "text-max-width": 14,
    },
    paint: {
      "text-color": "#e2e8f0",
      "text-halo-color": "#0f172a",
      "text-halo-width": 1.5,
      "text-halo-blur": 0.5,
    },
  });
}

function pickParcelFields(feature: GeoJSONFeature | undefined): ParcelPopupFields | undefined {
  if (!feature?.properties) return undefined;
  const p = feature.properties as Record<string, unknown>;
  const prior = p.priorVolatility;
  const priorNum = typeof prior === "number" ? prior : prior != null ? Number(prior) : NaN;
  const mi = p.metricImpact;
  const miNum = typeof mi === "number" ? mi : mi != null ? Number(mi) : NaN;
  const hi = p.heatIntensity;
  const hiNum = typeof hi === "number" ? hi : hi != null ? Number(hi) : NaN;
  const neighbors = p.neighborsInRadius;
  const neighNum = typeof neighbors === "number" ? neighbors : neighbors != null ? Number(neighbors) : NaN;

  const heatParts: string[] = [];
  if (Number.isFinite(miNum)) heatParts.push(`Impact ${Math.round(miNum * 100)}%`);
  if (Number.isFinite(hiNum)) heatParts.push(`Heat ${Math.round(hiNum * 100)}%`);
  if (Number.isFinite(neighNum)) heatParts.push(`${Math.round(neighNum)} nearby ≤130m`);

  return {
    mockParcelLotId: p.mockParcelLotId != null ? String(p.mockParcelLotId) : undefined,
    neighborhood: p.neighborhood != null ? String(p.neighborhood) : undefined,
    volatilityLabel: p.volatilityLabel != null ? String(p.volatilityLabel) : undefined,
    trendDeltaLabel: p.trendDeltaLabel != null ? String(p.trendDeltaLabel) : undefined,
    priorVolatilityLabel: Number.isFinite(priorNum)
      ? `Prior mock signal ${Math.round(priorNum * 100)}%`
      : undefined,
    metricImpactLabel: heatParts.length > 0 ? heatParts.join(" · ") : undefined,
  };
}

function nearestMarketSampleForLngLat(
  referenceLongitudeDegrees: number,
  referenceLatitudeDegrees: number,
  marketSampleObservationList: MockMarketSample[]
): { sample: MockMarketSample; index: number } {
  let shortestSeparationSquared = Infinity;
  let closestIndex = 0;

  marketSampleObservationList.forEach((sampleObservation, index) => {
    const planarSeparationSquared = haversineLikeQuickLngLatDistanceSquaredDegrees(
      referenceLongitudeDegrees,
      referenceLatitudeDegrees,
      sampleObservation.coordinates[0],
      sampleObservation.coordinates[1]
    );
    if (planarSeparationSquared < shortestSeparationSquared) {
      shortestSeparationSquared = planarSeparationSquared;
      closestIndex = index;
    }
  });

  return { sample: marketSampleObservationList[closestIndex]!, index: closestIndex };
}

function synthesizeNearestSamplePopupFields(sampleObservation: MockMarketSample, index: number): ParcelPopupFields {
  const t = deriveParcelTrendFields(sampleObservation, index);
  const impact = computeMetricImpactScore(sampleObservation, t);
  const heatMeta = computeParcelHeatMetadata(MOCK_MARKET_SAMPLES)[index]!;
  return {
    mockParcelLotId: sampleObservation.mockParcelLotId ?? "Nearest mock parcel",
    neighborhood: sampleObservation.submarket ?? "",
    volatilityLabel: `${Math.round((sampleObservation.rentVolatilityIndex ?? 0) * 100)}% mock signal`,
    trendDeltaLabel: t.trendDeltaLabel,
    priorVolatilityLabel: `Prior mock signal ${Math.round(t.priorVolatility * 100)}%`,
    metricImpactLabel: `Impact ${Math.round(impact * 100)}% · Heat ${Math.round(heatMeta.heatIntensity * 100)}% (${heatMeta.neighborsInRadius} parcels ≤130m)`,
  };
}
