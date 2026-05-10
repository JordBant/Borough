/** ~35–45 m half-extent rectangles at Brooklyn latitude — mock tax-lot footprints. */
const PARCEL_DELTA_LNG = 0.00044;
const PARCEL_DELTA_LAT = 0.00032;

/** Streets `within` requires full containment; generous scale helps real footprints intersect mock corridors. */
const BUILDING_WITHIN_ZONE_SCALE = 5.55;

function rectangularLotRingAroundCenter(centerCoordinates, elongationMeterFactor = 1) {
  const [centerLongitude, centerLatitude] = centerCoordinates;
  const halfWidth = PARCEL_DELTA_LNG * elongationMeterFactor;
  const halfHeight = PARCEL_DELTA_LAT;

  return [
    [centerLongitude - halfWidth, centerLatitude - halfHeight],
    [centerLongitude + halfWidth, centerLatitude - halfHeight],
    [centerLongitude + halfWidth, centerLatitude + halfHeight],
    [centerLongitude - halfWidth, centerLatitude + halfHeight],
    [centerLongitude - halfWidth, centerLatitude - halfHeight],
  ];
}

function rectangularBuildingQueryPolygonAroundSample(sampleRowEntry) {
  const aspect = sampleRowEntry.footprintAspect ?? 1;
  const [longitude, latitude] = sampleRowEntry.coordinates;
  const halfWidth = PARCEL_DELTA_LNG * aspect * BUILDING_WITHIN_ZONE_SCALE;
  const halfHeight = PARCEL_DELTA_LAT * BUILDING_WITHIN_ZONE_SCALE;

  const ringCoordinates = [
    [longitude - halfWidth, latitude - halfHeight],
    [longitude + halfWidth, latitude - halfHeight],
    [longitude + halfWidth, latitude + halfHeight],
    [longitude - halfWidth, latitude + halfHeight],
    [longitude - halfWidth, latitude - halfHeight],
  ];

  return {
    type: "Polygon",
    coordinates: [ringCoordinates],
  };
}

// Mock sample points plus derived mock parcel footprints for block-level attribution at street zoom.
// `rentVolatilityIndex` drives both heat blobs and parcel extrusion hue / height.
export const MOCK_MARKET_SAMPLES = [
  {
    coordinates: [-73.9935, 40.6616],
    rentVolatilityIndex: 0.82,
    submarket: "Park Slope",
    mockParcelLotId: "PS-088A",
    footprintAspect: 1.15,
  },
  {
    coordinates: [-73.9885, 40.6715],
    rentVolatilityIndex: 0.71,
    submarket: "Park Slope",
    mockParcelLotId: "PS-074C",
    footprintAspect: 1.0,
  },
  {
    coordinates: [-73.9865, 40.6595],
    rentVolatilityIndex: 0.68,
    submarket: "Park Slope",
    mockParcelLotId: "PS-063B",
    footprintAspect: 0.92,
  },
  {
    coordinates: [-73.9955, 40.6735],
    rentVolatilityIndex: 0.76,
    submarket: "Park Slope",
    mockParcelLotId: "PS-091D",
    footprintAspect: 1.22,
  },
  {
    coordinates: [-73.9876, 40.6862],
    rentVolatilityIndex: 0.91,
    submarket: "Downtown Brooklyn",
    mockParcelLotId: "DTBK-042F",
    footprintAspect: 1.08,
  },
  {
    coordinates: [-73.983, 40.694],
    rentVolatilityIndex: 0.88,
    submarket: "Downtown Brooklyn",
    mockParcelLotId: "DTBK-036E",
    footprintAspect: 1.05,
  },
  {
    coordinates: [-73.9625, 40.713],
    rentVolatilityIndex: 0.89,
    submarket: "Williamsburg",
    mockParcelLotId: "WBG-029H",
    footprintAspect: 1.1,
  },
  {
    coordinates: [-73.957, 40.708],
    rentVolatilityIndex: 0.85,
    submarket: "Williamsburg",
    mockParcelLotId: "WBG-031K",
    footprintAspect: 0.97,
  },
  {
    coordinates: [-73.944, 40.718],
    rentVolatilityIndex: 0.79,
    submarket: "Williamsburg",
    mockParcelLotId: "WBG-018J",
    footprintAspect: 1.03,
  },
  {
    coordinates: [-73.9195, 40.6986],
    rentVolatilityIndex: 0.63,
    submarket: "Bushwick",
    mockParcelLotId: "BSW-112M",
    footprintAspect: 1.06,
  },
  {
    coordinates: [-73.924, 40.705],
    rentVolatilityIndex: 0.58,
    submarket: "Bushwick",
    mockParcelLotId: "BSW-108L",
    footprintAspect: 0.94,
  },
  {
    coordinates: [-73.932, 40.692],
    rentVolatilityIndex: 0.55,
    submarket: "Bushwick",
    mockParcelLotId: "BSW-101N",
    footprintAspect: 1.14,
  },
  {
    coordinates: [-73.953, 40.682],
    rentVolatilityIndex: 0.72,
    submarket: "Bedford-Stuyvesant",
    mockParcelLotId: "BDST-55P",
    footprintAspect: 1.02,
  },
  {
    coordinates: [-73.948, 40.689],
    rentVolatilityIndex: 0.69,
    submarket: "Bedford-Stuyvesant",
    mockParcelLotId: "BDST-61Q",
    footprintAspect: 0.91,
  },
  {
    coordinates: [-73.961, 40.694],
    rentVolatilityIndex: 0.74,
    submarket: "Clinton Hill",
    mockParcelLotId: "CLH-19R",
    footprintAspect: 1.07,
  },
  {
    coordinates: [-73.95, 40.672],
    rentVolatilityIndex: 0.66,
    submarket: "Crown Heights",
    mockParcelLotId: "CRH-084S",
    footprintAspect: 1.01,
  },
  {
    coordinates: [-73.937, 40.661],
    rentVolatilityIndex: 0.52,
    submarket: "Crown Heights",
    mockParcelLotId: "CRH-097T",
    footprintAspect: 0.93,
  },
  {
    coordinates: [-74.015, 40.627],
    rentVolatilityIndex: 0.42,
    submarket: "Bay Ridge",
    mockParcelLotId: "BGR-041U",
    footprintAspect: 1.09,
  },
  {
    coordinates: [-74.008, 40.635],
    rentVolatilityIndex: 0.38,
    submarket: "Bay Ridge",
    mockParcelLotId: "BGR-038V",
    footprintAspect: 0.96,
  },
  {
    coordinates: [-73.93, 40.628],
    rentVolatilityIndex: 0.35,
    submarket: "Flatlands",
    mockParcelLotId: "FLT-021W",
    footprintAspect: 1.04,
  },
  {
    coordinates: [-73.922, 40.642],
    rentVolatilityIndex: 0.41,
    submarket: "Flatbush",
    mockParcelLotId: "FLB-033X",
    footprintAspect: 1.18,
  },
  {
    coordinates: [-73.952, 40.659],
    rentVolatilityIndex: 0.59,
    submarket: "Prospect Lefferts",
    mockParcelLotId: "PLL-067Y",
    footprintAspect: 0.89,
  },
  {
    coordinates: [-73.978, 40.659],
    rentVolatilityIndex: 0.78,
    submarket: "Gowanus",
    mockParcelLotId: "GWN-024Z",
    footprintAspect: 1.13,
  },
  {
    coordinates: [-73.991, 40.693],
    rentVolatilityIndex: 0.84,
    submarket: "Brooklyn Heights",
    mockParcelLotId: "BKHT-009A",
    footprintAspect: 1.06,
  },
  {
    coordinates: [-73.984, 40.698],
    rentVolatilityIndex: 0.86,
    submarket: "DUMBO",
    mockParcelLotId: "DMB-014B",
    footprintAspect: 1.02,
  },
];

/** GeoJSON geometries for styling Streets `composite`/`building` features that lie inside expanded mock lots. */
export function mockMarketBuildingHighlightGeometries(samples) {
  return samples.map((sampleRowEntry) => rectangularBuildingQueryPolygonAroundSample(sampleRowEntry));
}

export function samplesToHeatmapGeoJSON(samples) {
  return {
    type: "FeatureCollection",
    features: samples.map((rowEntry, zeroBasedIndex) => ({
      type: "Feature",
      id: zeroBasedIndex,
      properties: {
        weight: rowEntry.rentVolatilityIndex,
        neighborhood: rowEntry.submarket,
      },
      geometry: {
        type: "Point",
        coordinates: rowEntry.coordinates,
      },
    })),
  };
}

/** Polygons for mock contributing parcels visible at street zoom alongside GLJS 3D massing. */
export function samplesToParcelContributionGeoJSON(samples) {
  return {
    type: "FeatureCollection",
    features: samples.map((rowEntry, zeroBasedIndex) => ({
      type: "Feature",
      id: `parcel-feature-${zeroBasedIndex}`,
      properties: {
        weight: rowEntry.rentVolatilityIndex,
        neighborhood: rowEntry.submarket,
        mockParcelLotId: rowEntry.mockParcelLotId,
        volatilityLabel: `${Math.round(rowEntry.rentVolatilityIndex * 100)}% mock signal`,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          rectangularLotRingAroundCenter(
            rowEntry.coordinates,
            rowEntry.footprintAspect ?? 1
          ),
        ],
      },
    })),
  };
}
