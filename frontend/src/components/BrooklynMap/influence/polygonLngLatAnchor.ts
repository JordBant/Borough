import type { Geometry } from "geojson";

export interface LngLatCentroid {
  lng: number;
  lat: number;
}

/** Planar centroid of Polygon / MultiPolygon (first polygon only for multipoly). */
export function planarPolygonLikeCentroidLongitudeLatitude(
  geometryObservation: Geometry | null | undefined
): LngLatCentroid | null {
  if (!geometryObservation) return null;
  if (geometryObservation.type === "Polygon") {
    return polygonOuterRingLongitudeLatitudeAvg(geometryObservation.coordinates?.[0]);
  }
  if (geometryObservation.type === "MultiPolygon") {
    const prioritizedPolygonRing = geometryObservation.coordinates?.[0]?.[0];
    return polygonOuterRingLongitudeLatitudeAvg(prioritizedPolygonRing);
  }
  return null;
}

/** Optional Feature wrapper from Interactions handlers. */
export function planarFeatureGeometryCentroidLongitudeLatitude(featureObservation: {
  geometry?: Geometry | null;
} | null): LngLatCentroid | null {
  return planarPolygonLikeCentroidLongitudeLatitude(featureObservation?.geometry);
}

function polygonOuterRingLongitudeLatitudeAvg(outerRingCoordinates: number[][] | undefined): LngLatCentroid | null {
  if (!outerRingCoordinates?.length) return null;

  let sumLongitudeAccumulation = 0;
  let sumLatitudeAccumulation = 0;
  let vertexCountExcludedClosingDuplicate = 0;

  const lastVertexIndexInclusive = outerRingCoordinates.length - 1;
  for (let vertexIndexScanner = 0; vertexIndexScanner < lastVertexIndexInclusive; vertexIndexScanner += 1) {
    sumLongitudeAccumulation += outerRingCoordinates[vertexIndexScanner][0];
    sumLatitudeAccumulation += outerRingCoordinates[vertexIndexScanner][1];
    vertexCountExcludedClosingDuplicate += 1;
  }

  if (!vertexCountExcludedClosingDuplicate) return null;
  return {
    lng: sumLongitudeAccumulation / vertexCountExcludedClosingDuplicate,
    lat: sumLatitudeAccumulation / vertexCountExcludedClosingDuplicate,
  };
}
