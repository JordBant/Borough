import type { Feature, Polygon, Position } from "geojson";

/**
 * Builds a world polygon with inner hole cut out (semi-transparent vignette overlay).
 */
export function buildOuterMaskGeoJson(inclusiveBrooklynFeature: Feature<Polygon>): Feature<Polygon> {
  const worldBounds: Position[] = [
    [-180, -90],
    [-180, 90],
    [180, 90],
    [180, -90],
    [-180, -90],
  ];

  const holeRing = inclusiveBrooklynFeature.geometry.coordinates[0];

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [worldBounds, holeRing],
    },
  };
}

/** Centroid of a closed lng/lat ring (first vertex repeated at end OK). */
function ringCentroid(ring: Position[]): [number, number] {
  const lastIndex = ring.length - 1;
  const dup =
    ring[0][0] === ring[lastIndex][0] && ring[0][1] === ring[lastIndex][1];
  const vertices = dup ? ring.slice(0, lastIndex) : ring;
  let sumLng = 0;
  let sumLat = 0;
  for (const coord of vertices) {
    sumLng += coord[0];
    sumLat += coord[1];
  }
  const n = Math.max(vertices.length, 1);
  return [sumLng / n, sumLat / n];
}

/**
 * Rough “buffer”: scale each vertex away from centroid so the hole grows.
 * Keeps the outer vignette gradual without GIS dependencies.
 */
export function scaleInclusiveBrooklynHole(brooklynFeature: Feature<Polygon>, scaleFactor: number): Feature<Polygon> {
  const ring = brooklynFeature.geometry.coordinates[0];
  const centroidPoint = ringCentroid(ring);

  const scaledRing = ring.map(([lngPart, latPart]) => [
    centroidPoint[0] + (lngPart - centroidPoint[0]) * scaleFactor,
    centroidPoint[1] + (latPart - centroidPoint[1]) * scaleFactor,
  ]) as Position[];

  const firstPoint = scaledRing[0];
  const lastPoint = scaledRing[scaledRing.length - 1];
  if (firstPoint[0] !== lastPoint[0] || firstPoint[1] !== lastPoint[1]) {
    scaledRing.push([...firstPoint]);
  }

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [scaledRing],
    },
  };
}

export interface FeatherMaskLayerSpec {
  id: string;
  data: Feature<Polygon>;
  fillOpacity: number;
  fillColor: string;
}

/**
 * Stacked feather masks — add layers in returned order before the cyan outline on top.
 * Overlap ramps darkness smoothly from borough edge outward.
 */
export function buildFeatherMaskLayerSpecs(referenceBrooklynFeature: Feature<Polygon>): FeatherMaskLayerSpec[] {
  return [
    {
      id: "outer-mask-feather-wide",
      data: buildOuterMaskGeoJson(scaleInclusiveBrooklynHole(referenceBrooklynFeature, 1.065)),
      fillOpacity: 0.32,
      fillColor: "#030712",
    },
    {
      id: "outer-mask-feather-mid",
      data: buildOuterMaskGeoJson(scaleInclusiveBrooklynHole(referenceBrooklynFeature, 1.038)),
      fillOpacity: 0.28,
      fillColor: "#0a1020",
    },
    {
      id: "outer-mask-feather-near",
      data: buildOuterMaskGeoJson(referenceBrooklynFeature),
      fillOpacity: 0.18,
      fillColor: "#0f172a",
    },
  ];
}
