import type { FeatureCollection, Geometry, Position } from "geojson";
import type { GeoJSONFeature, Map } from "mapbox-gl";

import { buildCylinderFootprintRing, distanceMetersLngLat, type MockMarketSample } from "../../data/mockProperties";
import { planarPolygonLikeCentroidLongitudeLatitude } from "./influence/polygonLngLatAnchor";

/** Minimum zoom where `composite` / `building` is typically painted for queries. */
const MIN_ZOOM_BUILDING_QUERY = 11.5;

/** Screen padding (px) around sample point when collecting candidate building meshes. */
const QUERY_PAD_PX = 18;

/** Hug the tiled footprint slightly so the prism reads centered on the extruded mesh. */
const BUILDING_FOOTPRINT_RADIUS_SCALE = 0.94;

function layerSourceLayer(layer: GeoJSONFeature["layer"]): string | undefined {
  if (!layer) return undefined;
  const l = layer as { sourceLayer?: string; "source-layer"?: string };
  return l.sourceLayer ?? l["source-layer"];
}

function isCompositeBuildingFeature(f: GeoJSONFeature): boolean {
  if (f.source !== "composite") return false;
  return layerSourceLayer(f.layer) === "building";
}

function ringContainsLngLat(ring: Position[], lng: number, lat: number): boolean {
  if (ring.length < 3) return false;
  const xi = lng;
  const yi = lat;
  let inside = false;
  const n = ring.length;
  const lastDup =
    n > 1 &&
    ring[0]![0] === ring[n - 1]![0] &&
    ring[0]![1] === ring[n - 1]![1];
  const m = lastDup ? n - 1 : n;
  for (let i = 0, j = m - 1; i < m; j = i++) {
    const a = ring[i]!;
    const b = ring[j]!;
    const intersect =
      a[1] > yi !== b[1] > yi &&
      xi < ((b[0] - a[0]) * (yi - a[1])) / (b[1] - a[1] + 1e-20) + a[0];
    if (intersect) inside = !inside;
  }
  return inside;
}

function geometryCoversLngLat(geometry: Geometry, lng: number, lat: number): boolean {
  if (geometry.type === "Polygon") {
    if (!geometry.coordinates[0]) return false;
    return ringContainsLngLat(geometry.coordinates[0], lng, lat);
  }
  if (geometry.type === "MultiPolygon") {
    for (const poly of geometry.coordinates) {
      const outer = poly?.[0];
      if (outer && ringContainsLngLat(outer, lng, lat)) return true;
    }
  }
  return false;
}

function maxOuterRingRadiusMeters(geometry: Geometry, anchor: [number, number]): number {
  let max = 0;
  const walkRing = (ring: Position[]): void => {
    for (const pt of ring) {
      const d = distanceMetersLngLat(anchor, pt as [number, number]);
      if (d > max) max = d;
    }
  };

  if (geometry.type === "Polygon") {
    const outer = geometry.coordinates[0];
    if (outer) walkRing(outer);
  } else if (geometry.type === "MultiPolygon") {
    for (const poly of geometry.coordinates) {
      const outer = poly[0];
      if (outer) walkRing(outer);
    }
  }
  return max;
}

function pickBuildingForSample(map: Map, lng: number, lat: number): GeoJSONFeature | null {
  const p = map.project([lng, lat]);
  const pad = QUERY_PAD_PX;
  const queryBbox: [[number, number], [number, number]] = [
    [p.x - pad, p.y - pad],
    [p.x + pad, p.y + pad],
  ];

  let candidates: GeoJSONFeature[];
  try {
    candidates = map.queryRenderedFeatures(queryBbox, {}) as GeoJSONFeature[];
  } catch {
    return null;
  }

  const buildings = candidates.filter(isCompositeBuildingFeature);
  if (buildings.length === 0) return null;

  for (const f of buildings) {
    if (f.geometry && geometryCoversLngLat(f.geometry as Geometry, lng, lat)) {
      return f;
    }
  }

  let best: GeoJSONFeature | null = null;
  let bestD = Infinity;
  for (const f of buildings) {
    const cc = planarPolygonLikeCentroidLongitudeLatitude(f.geometry as Geometry);
    if (!cc) continue;
    const d = distanceMetersLngLat([lng, lat], [cc.lng, cc.lat]);
    if (d < bestD) {
      bestD = d;
      best = f;
    }
  }
  return best;
}

/**
 * Rebuilds parcel polygons using Streets `building` footprints under each mock coordinate when available,
 * so custom fill-extrusions sit on the same 3D massing as Mapbox Standard.
 */
export function buildParcelCollectionAlignedToRenderedBuildings(
  map: Map,
  samples: MockMarketSample[],
  staticCollection: FeatureCollection
): FeatureCollection | null {
  if (!map || map.getZoom() < MIN_ZOOM_BUILDING_QUERY) {
    return null;
  }

  let changed = false;
  const features = staticCollection.features.map((feat, index) => {
    const sample = samples[index];
    if (!sample || feat.geometry?.type !== "Polygon") {
      return feat;
    }

    const building = pickBuildingForSample(map, sample.coordinates[0], sample.coordinates[1]);
    if (!building?.geometry) {
      return feat;
    }

    const g = building.geometry as Geometry;
    const centroid = planarPolygonLikeCentroidLongitudeLatitude(g);
    if (!centroid) {
      return feat;
    }

    const anchor: [number, number] = [centroid.lng, centroid.lat];
    let radiusM = maxOuterRingRadiusMeters(g, anchor);
    radiusM = Math.max(radiusM * BUILDING_FOOTPRINT_RADIUS_SCALE, 2.5);

    const ring = buildCylinderFootprintRing(anchor, radiusM);
    changed = true;
    return {
      ...feat,
      geometry: { type: "Polygon" as const, coordinates: [ring] },
    };
  });

  if (!changed) return null;
  return { type: "FeatureCollection", features };
}
