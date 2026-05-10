import type { Map } from "mapbox-gl";

import { DEFAULT_BASEMAP_STANDARD_TOGGLES } from "./basemapStandardToggles";

/** Noir palette: black land, grey water, light grey arteries, subdued blue-grey 3D massing. */
export const BOROUGH_BASEMAP_THEME = {
  land: "#000000",
  water: "#a3aabe",
  /** Through-ways (motorways, trunks, other roads share this light grey). */
  road: "#c6ccd6",
  /** 2D + 3D building massing (`colorBuildings` on Standard basemap). */
  building: "#5d6d84",
  greenspace: "#030303",
  landuseFill: "#050505",
  /** Labels readable on dark ground. */
  placeLabels: "#94a3b8",
  roadLabels: "#a8adb8",
  /** Synced with `attachStandardBuildingMockInfluenceInteractions` baseline / hover. */
  buildingHighlight: "#7e93ab",
  buildingHover: "#677a90",
} as const;

/**
 * Single basemap fragment payload for `map.setConfig('basemap', …)` and the map constructor.
 * We avoid `theme: 'monochrome'` here — it applies a LUT that can override `colorWater`
 * so the configured grey never appears.
 */
function getBasemapNoirFragment(lightPreset: "night" | "dusk"): Record<string, string | boolean> {
  return {
    ...DEFAULT_BASEMAP_STANDARD_TOGGLES,
    lightPreset,
    show3dObjects: true,
    colorLand: BOROUGH_BASEMAP_THEME.land,
    colorWater: BOROUGH_BASEMAP_THEME.water,
    colorBuildings: BOROUGH_BASEMAP_THEME.building,
    colorRoads: BOROUGH_BASEMAP_THEME.road,
    colorTrunks: BOROUGH_BASEMAP_THEME.road,
    colorMotorways: BOROUGH_BASEMAP_THEME.road,
    colorGreenspace: BOROUGH_BASEMAP_THEME.greenspace,
    colorCommercial: BOROUGH_BASEMAP_THEME.landuseFill,
    colorIndustrial: BOROUGH_BASEMAP_THEME.landuseFill,
    colorEducation: BOROUGH_BASEMAP_THEME.landuseFill,
    colorMedical: BOROUGH_BASEMAP_THEME.landuseFill,
    colorPlaceLabels: BOROUGH_BASEMAP_THEME.placeLabels,
    colorRoadLabels: BOROUGH_BASEMAP_THEME.roadLabels,
    colorBuildingHighlight: BOROUGH_BASEMAP_THEME.buildingHighlight,
    colorBuildingSelect: BOROUGH_BASEMAP_THEME.buildingHighlight,
    colorAdminBoundaries: "#1a2332",
  };
}

/** Pass to `new mapboxgl.Map({ config: getBoroughMapInitialConfig(), … })` so water/land colors apply with the first style resolve. */
export function getBoroughMapInitialConfig(): { basemap: Record<string, string | boolean> } {
  return {
    basemap: getBasemapNoirFragment("night"),
  };
}

/**
 * Push paint on any loaded style layers that look like water polygons.
 * Standard imports can scope ids; this is a reliable belt-and-suspenders path when `colorWater`
 * alone does not win (e.g. late fragment resolve).
 */
function paintWaterLayersFromStyle(map: Map, color: string): void {
  const style = map.getStyle();
  if (!style?.layers) return;

  for (const layer of style.layers) {
    const lay = layer as {
      id: string;
      type: string;
      "source-layer"?: string;
    };
    const id = lay.id;
    const sourceLayer = lay["source-layer"];
    const looksLikeWaterFeature = sourceLayer === "water" || sourceLayer === "ocean";
    const looksLikeWaterId = /(water|ocean|marine|sea|dock|ferry)/i.test(id);
    if (!looksLikeWaterFeature && !looksLikeWaterId) continue;
    if (/(label|shield|poi|symbol|text)/i.test(id) && !looksLikeWaterFeature) continue;

    try {
      if (lay.type === "fill") {
        map.setPaintProperty(id, "fill-color", color);
      } else if (lay.type === "fill-extrusion") {
        map.setPaintProperty(id, "fill-extrusion-color", color);
      }
    } catch {
      /* Layer may be locked or not paintable in this style revision. */
    }
  }
}

/** Re-apply `colorWater` and paint fallbacks so the configured water grey reliably shows after Standard finishes loading. */
function reinforceBasemapWaterColor(map: Map): void {
  const hex = BOROUGH_BASEMAP_THEME.water;
  const run = (): void => {
    try {
      map.setConfigProperty("basemap", "colorWater", hex);
    } catch {
      /* optional */
    }
    paintWaterLayersFromStyle(map, hex);
  };

  run();
  map.once("idle", run);
  if (typeof requestAnimationFrame !== "undefined") {
    requestAnimationFrame(() => requestAnimationFrame(run));
  }
}

/**
 * Mapbox Standard fragment (`basemap`) color configuration.
 * See https://docs.mapbox.com/map-styles/standard/api/
 */
export function applyBoroughNoirBasemapTheme(map: Map): void {
  let lightPreset: "night" | "dusk" = "night";
  try {
    map.setConfigProperty("basemap", "lightPreset", "night");
  } catch {
    lightPreset = "dusk";
    try {
      map.setConfigProperty("basemap", "lightPreset", "dusk");
    } catch {
      /* optional */
    }
  }

  const fragment = getBasemapNoirFragment(lightPreset);
  try {
    map.setConfig("basemap", fragment);
  } catch {
    for (const [key, value] of Object.entries(fragment)) {
      try {
        map.setConfigProperty("basemap", key, value);
      } catch {
        /* optional */
      }
    }
  }

  reinforceBasemapWaterColor(map);
}
