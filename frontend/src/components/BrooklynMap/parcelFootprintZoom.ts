import type { Feature, FeatureCollection, Polygon, Position } from "geojson";
import type { GeoJSONSource, Map as MapboxMap } from "mapbox-gl";

import { buildCylinderFootprintRing, distanceMetersLngLat } from "../../data/mockProperties";

/** Screen diameter of the footprint at full zoom-in (pixels). */
const TARGET_FOOTPRINT_DIAMETER_PX = 10;

/** Zoom where footprint is still full size (see `parcelMetricImpactLayer` minzoom). */
const ZOOM_BLEND_START = 12;

/** Zoom past which the footprint matches `TARGET_FOOTPRINT_DIAMETER_PX` in screen space. */
const ZOOM_BLEND_END = 17.5;

interface ParcelCylinderMeta {
  anchor: [number, number];
  fullRadiusM: number;
}

function ringCentroidLngLat(ring: Position[]): [number, number] | null {
  const n = ring.length;
  if (!n) return null;
  const closingDup =
    n > 1 &&
    ring[0]![0] === ring[n - 1]![0] &&
    ring[0]![1] === ring[n - 1]![1];
  const m = closingDup ? n - 1 : n;
  if (m < 1) return null;
  let sx = 0;
  let sy = 0;
  for (let i = 0; i < m; i += 1) {
    sx += ring[i]![0];
    sy += ring[i]![1];
  }
  const inv = 1 / m;
  return [sx * inv, sy * inv];
}

function extractCylinderMeta(collection: FeatureCollection): ParcelCylinderMeta[] {
  return collection.features.map((featureItem) => {
    if (featureItem.geometry?.type !== "Polygon") {
      return { anchor: [0, 0], fullRadiusM: 0 };
    }
    const ring = (featureItem.geometry as Polygon).coordinates[0]!;
    const anchor = ringCentroidLngLat(ring) ?? ([0, 0] as [number, number]);
    const fullRadiusM = distanceMetersLngLat(anchor, ring[0] as [number, number]);
    return { anchor, fullRadiusM };
  });
}

/** Average meters covered by one pixel at `lng`/`lat` using map projection (handles pitch & latitude). */
function metersPerPixelAt(map: MapboxMap, lng: number, lat: number): number {
  const mLat = 111_320;
  const mLng = 111_320 * Math.cos((lat * Math.PI) / 180);
  const p0 = map.project([lng, lat]);
  const pN = map.project([lng, lat + 1 / mLat]);
  const pE = map.project([lng + 1 / mLng, lat]);
  const pixPerM_N = Math.hypot(pN.x - p0.x, pN.y - p0.y);
  const pixPerM_E = Math.hypot(pE.x - p0.x, pE.y - p0.y);
  if (pixPerM_N < 1e-6 || pixPerM_E < 1e-6) {
    return 0.25;
  }
  return (1 / pixPerM_N + 1 / pixPerM_E) / 2;
}

function zoomBlendFactor(zoom: number): number {
  if (zoom <= ZOOM_BLEND_START) return 0;
  if (zoom >= ZOOM_BLEND_END) return 1;
  return (zoom - ZOOM_BLEND_START) / (ZOOM_BLEND_END - ZOOM_BLEND_START);
}

function buildSizedCollection(
  map: MapboxMap,
  baseParcels: FeatureCollection,
  meta: ParcelCylinderMeta[],
  blendT: number
): FeatureCollection {
  if (blendT <= 0.001) {
    return baseParcels;
  }

  const radiusPx = TARGET_FOOTPRINT_DIAMETER_PX / 2;

  const features: Feature[] = baseParcels.features.map((featureItem, index) => {
    if (featureItem.geometry?.type !== "Polygon") {
      return featureItem;
    }
    const m = meta[index]!;
    const mpp = metersPerPixelAt(map, m.anchor[0], m.anchor[1]);
    const radiusScreenM = radiusPx * mpp;
    const r = m.fullRadiusM * (1 - blendT) + radiusScreenM * blendT;
    const ring = buildCylinderFootprintRing(m.anchor, Math.max(r, 0.02));
    return {
      ...featureItem,
      geometry: { type: "Polygon", coordinates: [ring] },
    };
  });

  return { type: "FeatureCollection", features };
}

/**
 * Shrinks each parcel’s horizontal footprint while zooming in until it matches {@link TARGET_FOOTPRINT_DIAMETER_PX}
 * in on-screen diameter (meters derived from `map.project` at each lot anchor).
 *
 * @param getBaseParcels Latest parcel GeoJSON (e.g. after alignment to `composite` / `building` footprints).
 * @returns `refresh` — call after updating the base collection so the current zoom sizing is reapplied.
 */
export function attachParcelFootprintZoomSync(
  map: MapboxMap,
  sourceId: string,
  getBaseParcels: () => FeatureCollection
): () => void {
  let rafId = 0;
  let lastSignature = "";
  let forceNextApply = false;

  const apply = (): void => {
    const baseParcels = getBaseParcels();
    const meta = extractCylinderMeta(baseParcels);
    const center = map.getCenter();
    const z = map.getZoom();
    const blendRaw = zoomBlendFactor(z);
    const blendT = Math.round(blendRaw * 120) / 120;

    const signature = `${z.toFixed(2)}_${center.lng.toFixed(5)}_${center.lat.toFixed(5)}_${blendT.toFixed(3)}`;
    if (!forceNextApply && signature === lastSignature) return;
    forceNextApply = false;
    lastSignature = signature;

    const src = map.getSource(sourceId) as GeoJSONSource | undefined;
    if (!src || src.type !== "geojson") return;

    src.setData(buildSizedCollection(map, baseParcels, meta, blendT));
  };

  const schedule = (): void => {
    if (rafId) return;
    rafId = requestAnimationFrame(() => {
      rafId = 0;
      apply();
    });
  };

  map.on("zoom", schedule);
  map.on("moveend", apply);
  map.on("pitchend", apply);
  map.on("rotateend", apply);
  map.once("idle", apply);

  return () => {
    forceNextApply = true;
    apply();
  };
}
