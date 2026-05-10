import { useEffect } from "react";
import type { RefObject } from "react";
import type { Map } from "mapbox-gl";

import {
  applyBasemapStandardToggles,
  type BasemapStandardToggles,
} from "../map/basemapStandardToggles";

/**
 * Applies Mapbox Standard basemap visibility (POIs, landmarks, place labels, pedestrian roads, etc.)
 * whenever `toggles` changes. Uses `map.setConfigProperty('basemap', …)`.
 */
export function useBasemapStandardToggles(
  mapRef: RefObject<Map | null>,
  mapReady: boolean,
  toggles: BasemapStandardToggles
): void {
  useEffect(() => {
    if (!mapReady) return;
    const map = mapRef.current;
    if (!map) return;

    const run = (): void => {
      applyBasemapStandardToggles(map, toggles);
    };

    if (map.isStyleLoaded()) {
      run();
    } else {
      map.once("style.load", run);
    }

    return () => {
      map.off("style.load", run);
    };
  }, [mapRef, mapReady, toggles]);
}
