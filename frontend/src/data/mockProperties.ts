import type { FeatureCollection, Polygon, Position } from "geojson";

/** Expand visual lot half-size in meters for Streets `within` building queries (concentric with on-screen cylinder). */
const BUILDING_WITHIN_ZONE_SCALE = 4.15;

/**
 * Tighter on-map lot overlays (~26×22 m half-extent), with per-lot wobble so neighboring mocks don’t align on one grid.
 */
const VISUAL_LOT_HALF_WIDTH_M = 26;
const VISUAL_LOT_HALF_DEPTH_M = 22;

const EARTH_METERS_PER_DEG = 111_320;

function metersPerDegreeLongitude(latitude: number): number {
  return EARTH_METERS_PER_DEG * Math.cos((latitude * Math.PI) / 180);
}

/** Half-sizes in meters: aspect stretches width; index wobbles ~±8% so nearby lots aren’t identical. */
function visualLotHalfMeters(aspect: number, lotIndex: number): { halfWidthM: number; halfDepthM: number } {
  const wobble = 1 + ((lotIndex * 53) % 11) * 0.015 - 0.075;
  return {
    halfWidthM: VISUAL_LOT_HALF_WIDTH_M * aspect * wobble,
    halfDepthM: VISUAL_LOT_HALF_DEPTH_M * wobble,
  };
}

/**
 * Regular polygon approximating a circle: N segments, closed ring, centered on sample coordinates.
 * Radius uses √(halfWidth·halfDepth) so cylinder footprint matches prior rectangular lot scale.
 */
const CYLINDER_FACET_COUNT = 48;

/** Planar centroid of a closed ring (duplicate closing vertex excluded when present). */
function ringCentroidLngLat(ring: Position[]): [number, number] {
  const n = ring.length;
  if (!n) return [0, 0];
  const closingDup =
    n > 1 &&
    ring[0]![0] === ring[n - 1]![0] &&
    ring[0]![1] === ring[n - 1]![1];
  const m = closingDup ? n - 1 : n;
  let sx = 0;
  let sy = 0;
  for (let i = 0; i < m; i += 1) {
    sx += ring[i]![0];
    sy += ring[i]![1];
  }
  const inv = 1 / m;
  return [sx * inv, sy * inv];
}

/** Translates a ring so its centroid matches `anchor` (fixes meter→degree skew on small circles). */
function recenterRingLngLat(ring: Position[], anchor: [number, number]): Position[] {
  const [acx, acy] = anchor;
  const [ccx, ccy] = ringCentroidLngLat(ring);
  const dx = acx - ccx;
  const dy = acy - ccy;
  if (dx === 0 && dy === 0) return ring;
  return ring.map((p) => [p[0] + dx, p[1] + dy]);
}

/**
 * Closed lng/lat ring: circle in local meters, then nudged so the footprint centroid matches
 * `centerCoordinates` on the map (horizontal + north–south alignment on the lot anchor).
 */
function cylinderLotRingMeters(centerCoordinates: [number, number], radiusMeters: number, segments: number): Position[] {
  const [cx, cy] = centerCoordinates;
  const mLng = metersPerDegreeLongitude(cy);
  const mLat = EARTH_METERS_PER_DEG;
  const ring: Position[] = [];
  for (let i = 0; i <= segments; i += 1) {
    const angle = (i / segments) * 2 * Math.PI;
    const xm = Math.cos(angle) * radiusMeters;
    const ym = Math.sin(angle) * radiusMeters;
    ring.push([cx + xm / mLng, cy + ym / mLat]);
  }
  return recenterRingLngLat(ring, centerCoordinates);
}

/** Cylinder footprint for runtime zoom-size sync (`parcelFootprintZoom.ts`). */
export function buildCylinderFootprintRing(centerCoordinates: [number, number], radiusMeters: number): Position[] {
  return cylinderLotRingMeters(centerCoordinates, radiusMeters, CYLINDER_FACET_COUNT);
}

/** Cylindrical column footprint on the lot center (symmetric in plan). */
function cylinderLotRingAroundCenter(
  centerCoordinates: [number, number],
  elongationMeterFactor: number,
  lotIndex: number
): Position[] {
  const aspect = elongationMeterFactor;
  const { halfWidthM, halfDepthM } = visualLotHalfMeters(aspect, lotIndex);
  const radiusM = Math.sqrt(halfWidthM * halfDepthM);
  return cylinderLotRingMeters(centerCoordinates, radiusM, CYLINDER_FACET_COUNT);
}

/** Mock volatility Δ below this reads as “steady” for parcel overlays. */
export const MOCK_VOLATILITY_TREND_THRESHOLD = 0.035;

/** Distinct accent per parcel slot (lot identity at street zoom). */
const PARCEL_ACCENT_PALETTE = [
  "#f472b6",
  "#c084fc",
  "#22d3ee",
  "#fbbf24",
  "#34d399",
  "#fb923c",
  "#818cf8",
  "#f87171",
];

export type TrendBand = "rising" | "steady" | "falling";

export interface MockMarketSample {
  coordinates: [number, number];
  rentVolatilityIndex: number;
  submarket: string;
  mockParcelLotId: string;
  footprintAspect?: number;
  /** Optional mock “prior period” index; when omitted, a deterministic fallback is used for demo Δ. */
  priorRentVolatilityIndex?: number;
  /** When set, parcels in the same id are expected to sit within ~1–2 short blocks to co-strengthen heat. */
  heatClusterId?: string;
}

/** Neighbor search radius (~130 m): multiple parcels inside this ring boost shared heat intensity. */
export const PARCEL_HEAT_NEIGHBOR_RADIUS_M = 132;

/** Cap for `heatWeight` used by the heatmap layer. */
export const PARCEL_HEAT_WEIGHT_CAP = 1.88;

export interface ParcelHeatMeta {
  /** Heatmap point weight (volatility × co-location boost). */
  heatWeight: number;
  /** Other parcels within `PARCEL_HEAT_NEIGHBOR_RADIUS_M` (not counting self). */
  neighborsInRadius: number;
  /** 0–1 normalized for 3D extrusion styling. */
  heatIntensity: number;
}

/** Quick planar distance in meters (adequate for borough-scale lot spacing). */
export function distanceMetersLngLat(a: [number, number], b: [number, number]): number {
  const latMid = ((a[1] + b[1]) / 2) * (Math.PI / 180);
  const mx = (b[0] - a[0]) * 111_320 * Math.cos(latMid);
  const my = (b[1] - a[1]) * 111_320;
  return Math.sqrt(mx * mx + my * my);
}

/**
 * Per-parcel heat contribution: isolated lots use base volatility; dense 1–2 block pockets amplify `heatWeight`
 * so the heatmap intensifies where several contributing parcels overlap in influence.
 */
export function computeParcelHeatMetadata(samples: MockMarketSample[]): ParcelHeatMeta[] {
  const n = samples.length;
  const result: ParcelHeatMeta[] = [];

  for (let i = 0; i < n; i++) {
    let neighborsInRadius = 0;
    let peerVolSum = 0;
    for (let j = 0; j < n; j++) {
      if (i === j) continue;
      if (distanceMetersLngLat(samples[i]!.coordinates, samples[j]!.coordinates) <= PARCEL_HEAT_NEIGHBOR_RADIUS_M) {
        neighborsInRadius += 1;
        peerVolSum += samples[j]!.rentVolatilityIndex;
      }
    }

    const base = samples[i]!.rentVolatilityIndex;
    const coPresence =
      neighborsInRadius >= 1
        ? 1 + 0.13 * neighborsInRadius + 0.045 * Math.min(peerVolSum, 4)
        : 1;
    const heatWeight = Math.min(PARCEL_HEAT_WEIGHT_CAP, base * coPresence);
    const heatIntensity = Math.min(1, Math.max(0, heatWeight / PARCEL_HEAT_WEIGHT_CAP));

    result.push({
      heatWeight,
      neighborsInRadius,
      heatIntensity,
    });
  }

  return result;
}

/**
 * Six mock parcels in a ~1–2 short-block pocket (Gowanus); metrics stack with `computeParcelHeatMetadata`.
 */
const GOWANUS_BLOCK_CLUSTER: MockMarketSample[] = [
  {
    coordinates: [-73.97935, 40.65872],
    rentVolatilityIndex: 0.76,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C01",
    footprintAspect: 1.06,
    heatClusterId: "gowanus-2bk-n",
  },
  {
    coordinates: [-73.97872, 40.65905],
    rentVolatilityIndex: 0.83,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C02",
    footprintAspect: 1.0,
    heatClusterId: "gowanus-2bk-n",
  },
  {
    coordinates: [-73.9782, 40.65938],
    rentVolatilityIndex: 0.7,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C03",
    footprintAspect: 0.95,
    heatClusterId: "gowanus-2bk-n",
  },
  {
    coordinates: [-73.9791, 40.65948],
    rentVolatilityIndex: 0.79,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C04",
    footprintAspect: 1.12,
    heatClusterId: "gowanus-2bk-n",
  },
  {
    coordinates: [-73.97778, 40.65895],
    rentVolatilityIndex: 0.73,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C05",
    footprintAspect: 1.08,
    heatClusterId: "gowanus-2bk-n",
  },
  {
    coordinates: [-73.97845, 40.6585],
    rentVolatilityIndex: 0.8,
    submarket: "Gowanus Pocket",
    mockParcelLotId: "GWC-C06",
    footprintAspect: 0.99,
    heatClusterId: "gowanus-2bk-n",
  },
];

/** Second pocket — East Williamsburg / Broadway Triangle-ish spacing. */
const WBURG_BLOCK_CLUSTER: MockMarketSample[] = [
  {
    coordinates: [-73.9556, 40.70825],
    rentVolatilityIndex: 0.84,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C01",
    footprintAspect: 1.02,
    heatClusterId: "wburg-2bk-e",
  },
  {
    coordinates: [-73.95495, 40.70858],
    rentVolatilityIndex: 0.78,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C02",
    footprintAspect: 1.1,
    heatClusterId: "wburg-2bk-e",
  },
  {
    coordinates: [-73.95435, 40.70892],
    rentVolatilityIndex: 0.72,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C03",
    footprintAspect: 0.96,
    heatClusterId: "wburg-2bk-e",
  },
  {
    coordinates: [-73.95525, 40.7093],
    rentVolatilityIndex: 0.88,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C04",
    footprintAspect: 1.05,
    heatClusterId: "wburg-2bk-e",
  },
  {
    coordinates: [-73.95605, 40.70885],
    rentVolatilityIndex: 0.75,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C05",
    footprintAspect: 1.14,
    heatClusterId: "wburg-2bk-e",
  },
  {
    coordinates: [-73.95572, 40.7080],
    rentVolatilityIndex: 0.81,
    submarket: "Williamsburg Pocket",
    mockParcelLotId: "WBG-C06",
    footprintAspect: 1.0,
    heatClusterId: "wburg-2bk-e",
  },
];

/** Expanded circular zone (same center as the mock lot) for Streets `within` building queries. */
function circularBuildingQueryPolygonAroundSample(sampleRowEntry: MockMarketSample, lotIndex: number): Polygon {
  const aspect = sampleRowEntry.footprintAspect ?? 1;
  const center = sampleRowEntry.coordinates;
  const { halfWidthM, halfDepthM } = visualLotHalfMeters(aspect, lotIndex);
  const halfW = halfWidthM * BUILDING_WITHIN_ZONE_SCALE;
  const halfD = halfDepthM * BUILDING_WITHIN_ZONE_SCALE;
  const radiusM = Math.sqrt(halfW * halfD);
  const ring = cylinderLotRingMeters(center, radiusM, CYLINDER_FACET_COUNT);
  return {
    type: "Polygon",
    coordinates: [ring],
  };
}

// Mock sample points plus derived mock parcel footprints for block-level attribution at street zoom.
// `rentVolatilityIndex` drives both heat blobs and parcel extrusion hue / height.
export const MOCK_MARKET_SAMPLES: MockMarketSample[] = [
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
    priorRentVolatilityIndex: 0.62,
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
    priorRentVolatilityIndex: 0.9,
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
    priorRentVolatilityIndex: 0.58,
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
  ...GOWANUS_BLOCK_CLUSTER,
  ...WBURG_BLOCK_CLUSTER,
];

/**
 * Deterministic “prior” when omitted — spreads mock parcels across rising / steady / falling.
 */
function mockPriorVolatilityFallback(sample: MockMarketSample, index: number): number {
  const drift = ((index * 23) % 10) / 100 - 0.02;
  return Math.min(1, Math.max(0, sample.rentVolatilityIndex - 0.06 + drift));
}

export interface ParcelTrendFields {
  priorVolatility: number;
  volatilityDelta: number;
  trendBand: TrendBand;
  parcelAccent: string;
  trendDeltaLabel: string;
  mapLabel: string;
}

/** Trend + per-parcel accent for overlays, popups, and labels. */
export function deriveParcelTrendFields(sample: MockMarketSample, index: number): ParcelTrendFields {
  const priorVolatility =
    sample.priorRentVolatilityIndex !== undefined && sample.priorRentVolatilityIndex !== null
      ? Math.min(1, Math.max(0, sample.priorRentVolatilityIndex))
      : mockPriorVolatilityFallback(sample, index);
  const volatilityDelta = sample.rentVolatilityIndex - priorVolatility;
  let trendBand: TrendBand = "steady";
  if (volatilityDelta > MOCK_VOLATILITY_TREND_THRESHOLD) trendBand = "rising";
  else if (volatilityDelta < -MOCK_VOLATILITY_TREND_THRESHOLD) trendBand = "falling";

  const parcelAccent = PARCEL_ACCENT_PALETTE[index % PARCEL_ACCENT_PALETTE.length]!;
  const sign = volatilityDelta >= 0 ? "+" : "";
  const trendDeltaLabel = `${sign}${(volatilityDelta * 100).toFixed(1)} pts mock Δ`;
  const mapLabel =
    trendBand === "rising"
      ? `${sample.mockParcelLotId} ↑`
      : trendBand === "falling"
        ? `${sample.mockParcelLotId} ↓`
        : sample.mockParcelLotId;

  return {
    priorVolatility,
    volatilityDelta,
    trendBand,
    parcelAccent,
    trendDeltaLabel,
    mapLabel,
  };
}

/** GeoJSON geometries for styling Streets `composite`/`building` features that lie inside expanded mock lots. */
export function mockMarketBuildingHighlightGeometries(samples: MockMarketSample[]): Polygon[] {
  return samples.map((sampleRowEntry, index) => circularBuildingQueryPolygonAroundSample(sampleRowEntry, index));
}

export function samplesToHeatmapGeoJSON(samples: MockMarketSample[]): FeatureCollection {
  const heatMeta = computeParcelHeatMetadata(samples);
  return {
    type: "FeatureCollection",
    features: samples.map((rowEntry, zeroBasedIndex) => {
      const h = heatMeta[zeroBasedIndex]!;
      return {
        type: "Feature",
        id: zeroBasedIndex,
        properties: {
          weight: h.heatWeight,
          neighborhood: rowEntry.submarket,
          heatClusterId: rowEntry.heatClusterId ?? "",
          neighborsInRadius: h.neighborsInRadius,
        },
        geometry: {
          type: "Point",
          coordinates: rowEntry.coordinates,
        },
      };
    }),
  };
}

/** 0–1 composite for 3D lot styling: base volatility + mock Δ magnitude (+ small rising nudge). */
export function computeMetricImpactScore(sample: MockMarketSample, trend: ParcelTrendFields): number {
  const w = sample.rentVolatilityIndex;
  const deltaBoost = Math.min(0.42, Math.abs(trend.volatilityDelta) * 2.4);
  const trendNudge = trend.trendBand === "rising" ? 0.07 : trend.trendBand === "falling" ? 0.02 : 0.04;
  return Math.min(1, Math.max(0, Number((w * 0.62 + deltaBoost + trendNudge).toFixed(4))));
}

/** Polygons for mock contributing parcels visible at street zoom alongside GLJS 3D massing. */
export function samplesToParcelContributionGeoJSON(samples: MockMarketSample[]): FeatureCollection {
  const heatMeta = computeParcelHeatMetadata(samples);
  return {
    type: "FeatureCollection",
    features: samples.map((rowEntry, zeroBasedIndex) => {
      const trend = deriveParcelTrendFields(rowEntry, zeroBasedIndex);
      const metricImpact = computeMetricImpactScore(rowEntry, trend);
      const h = heatMeta[zeroBasedIndex]!;
      return {
        type: "Feature",
        id: `parcel-feature-${zeroBasedIndex}`,
        properties: {
          weight: rowEntry.rentVolatilityIndex,
          heatWeight: h.heatWeight,
          heatIntensity: h.heatIntensity,
          neighborsInRadius: h.neighborsInRadius,
          heatClusterId: rowEntry.heatClusterId ?? "",
          metricImpact,
          neighborhood: rowEntry.submarket,
          mockParcelLotId: rowEntry.mockParcelLotId,
          volatilityLabel: `${Math.round(rowEntry.rentVolatilityIndex * 100)}% mock signal`,
          priorVolatility: trend.priorVolatility,
          volatilityDelta: trend.volatilityDelta,
          trendBand: trend.trendBand,
          parcelAccent: trend.parcelAccent,
          trendDeltaLabel: trend.trendDeltaLabel,
          mapLabel: trend.mapLabel,
        },
        geometry: {
          type: "Polygon",
          coordinates: [
            cylinderLotRingAroundCenter(
              rowEntry.coordinates,
              rowEntry.footprintAspect ?? 1,
              zeroBasedIndex
            ),
          ],
        },
      };
    }),
  };
}
