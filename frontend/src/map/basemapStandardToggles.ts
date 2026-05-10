import type { Map } from "mapbox-gl";

/**
 * Mapbox Standard `basemap` import keys for visibility (see Mapbox Standard API).
 * Finer POI categories (e.g. restaurants only) require feature-state on the `poi` featureset, not these globals.
 */
export type BasemapStandardToggles = {
  /** Footpaths, trails, pedestrian-only ways (disabled in Borough by default). */
  showPedestrianRoads: boolean;
  /** General POI icons and text (food, retail, services, etc.). */
  showPointOfInterestLabels: boolean;
  showLandmarkIcons: boolean;
  showLandmarkIconLabels: boolean;
  showPlaceLabels: boolean;
  showTransitLabels: boolean;
  /** Photoreal landmark massing in Standard. */
  show3dLandmarks: boolean;
};

export const DEFAULT_BASEMAP_STANDARD_TOGGLES: BasemapStandardToggles = {
  showPedestrianRoads: false,
  showPointOfInterestLabels: true,
  showLandmarkIcons: true,
  showLandmarkIconLabels: true,
  showPlaceLabels: true,
  showTransitLabels: true,
  show3dLandmarks: true,
};

/** Stable iteration order for `setConfigProperty` and hook dependency lists. */
export const BASEMAP_STANDARD_TOGGLE_KEYS = Object.keys(
  DEFAULT_BASEMAP_STANDARD_TOGGLES
) as (keyof BasemapStandardToggles)[];

export const BASEMAP_STANDARD_TOGGLE_UI: { key: keyof BasemapStandardToggles; label: string }[] = [
  { key: "showPedestrianRoads", label: "Pedestrian paths & walkways" },
  { key: "showPointOfInterestLabels", label: "Points of interest (food, shops, services, …)" },
  { key: "showLandmarkIcons", label: "Landmark icons" },
  { key: "showLandmarkIconLabels", label: "Landmark name labels" },
  { key: "showPlaceLabels", label: "Place names (cities, neighborhoods, …)" },
  { key: "showTransitLabels", label: "Transit labels" },
  { key: "show3dLandmarks", label: "3D landmark buildings" },
];

const BASEMAP_FRAGMENT = "basemap" as const;

export function applyBasemapStandardToggles(map: Map, toggles: BasemapStandardToggles): void {
  for (const key of BASEMAP_STANDARD_TOGGLE_KEYS) {
    try {
      map.setConfigProperty(BASEMAP_FRAGMENT, key, toggles[key]);
    } catch {
      /* Unsupported key in this GL/style build */
    }
  }
}
