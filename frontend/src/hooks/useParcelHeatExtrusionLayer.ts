import { useEffect } from "react";
import type { RefObject } from "react";
import type { Map } from "mapbox-gl";

import {
  addParcelHeatIntensityExtrusionLayer,
  PARCEL_HEAT_EXTRUSION_LAYER_ID,
} from "../components/BrooklynMap/parcelMetricImpactLayer";

export interface UseParcelHeatExtrusionLayerOptions {
  /** GeoJSON source id that must already exist on the map. */
  parcelSourceId: string;
  /** When false, layer is removed / not added. */
  enabled?: boolean;
}

/**
 * Mounts the parcel `fill-extrusion` layer once the map and parcel source are ready.
 * 3D color / height follow `heatIntensity` on each parcel feature (see `computeParcelHeatMetadata`).
 */
export function useParcelHeatExtrusionLayer(
  mapRef: RefObject<Map | null>,
  mapReady: boolean,
  options: UseParcelHeatExtrusionLayerOptions = { parcelSourceId: "rent-market-parcels", enabled: true }
): void {
  const parcelSourceId = options.parcelSourceId ?? "rent-market-parcels";
  const enabled = options.enabled !== false;

  useEffect(() => {
    if (!mapReady || !enabled) return;
    const map = mapRef.current;
    if (!map) return;

    const attach = (): void => {
      if (!map.getSource(parcelSourceId)) return;
      if (map.getLayer(PARCEL_HEAT_EXTRUSION_LAYER_ID)) return;
      addParcelHeatIntensityExtrusionLayer(map);
    };

    if (map.isStyleLoaded()) attach();
    else map.once("load", attach);
    map.once("idle", attach);

    return () => {
      try {
        if (map.getLayer(PARCEL_HEAT_EXTRUSION_LAYER_ID)) {
          map.removeLayer(PARCEL_HEAT_EXTRUSION_LAYER_ID);
        }
      } catch {
        /* style teardown */
      }
    };
  }, [mapRef, mapReady, enabled, parcelSourceId]);
}

export { PARCEL_HEAT_EXTRUSION_LAYER_ID };
