/**
 * Creates an inverted polygon (world extent minus Brooklyn) to use as
 * a visual mask. Areas outside Brooklyn render with a dark, blurred overlay.
 */
export function buildOuterMaskGeoJson(brooklynFeature) {
  const worldBounds = [
    [-180, -90],
    [-180, 90],
    [180, 90],
    [180, -90],
    [-180, -90],
  ];

  const brooklynCoordinates = brooklynFeature.geometry.coordinates[0];

  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [worldBounds, brooklynCoordinates],
    },
  };
}
