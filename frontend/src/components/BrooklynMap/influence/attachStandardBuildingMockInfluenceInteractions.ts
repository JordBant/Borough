import type { Map } from "mapbox-gl";
import type { GeoJSONFeature } from "mapbox-gl";

const BASEMAP_FRAGMENT_IMPORT_KEY = "basemap";
const STANDARD_BUILDING_FEATURESET_IDENTIFIER = "buildings";

/** Default Standard highlight cue (Mapbox demos); restored after hover clears. */
const BASELINE_BUILDING_HIGHLIGHT_HEX = "#2e89ff";

/** Slightly darker, desaturated cue when the pointer rests on any basemap building mass. */
const SUBDUED_HOVER_BUILDING_TINT_HEX = "#294a73";

export interface AttachStandardBuildingOptions {
  map: Map;
  minZoomInteractiveBuildings?: number;
}

export interface AttachStandardBuildingResult {
  detachInteractions: () => void;
  purgeTransientBuildingHighlights: () => void;
}

/**
 * GL JS ≥3.9 Interactions API: subtle darken Standard `buildings` on hover (`highlight`
 * feature-state + `colorBuildingHighlight`). Rooftop metric caps use a separate Streets layer.
 */
export function attachStandardBuildingMockInfluenceInteractions({
  map,
  minZoomInteractiveBuildings = 12.35,
}: AttachStandardBuildingOptions): AttachStandardBuildingResult {
  const interactionNamingPrefixMarker = "borough-building-hover";

  const mouseEnterInteractionHandle = `${interactionNamingPrefixMarker}-enter`;
  const mouseLeaveInteractionHandle = `${interactionNamingPrefixMarker}-leave`;

  let lastHoveredBasemapBuildingFeatureRecord: GeoJSONFeature | null = null;

  function restoreBaselineBuildingHighlightHueObservation(): void {
    try {
      map.setConfigProperty(BASEMAP_FRAGMENT_IMPORT_KEY, "colorBuildingHighlight", BASELINE_BUILDING_HIGHLIGHT_HEX);
    } catch {
      /* style churn */
    }
  }

  function purgeTransientBuildingHighlightsObservation(): void {
    if (lastHoveredBasemapBuildingFeatureRecord) {
      try {
        map.setFeatureState(lastHoveredBasemapBuildingFeatureRecord, { highlight: false });
      } catch {
        /* stale feature handle */
      }
      lastHoveredBasemapBuildingFeatureRecord = null;
    }
    restoreBaselineBuildingHighlightHueObservation();
  }

  map.addInteraction(mouseEnterInteractionHandle, {
    type: "mouseenter",
    target: {
      featuresetId: STANDARD_BUILDING_FEATURESET_IDENTIFIER,
      importId: BASEMAP_FRAGMENT_IMPORT_KEY,
    },
    handler: (interactionPayloadObservation) => {
      const feature = interactionPayloadObservation.feature;
      if (!feature) return undefined;

      if (map.getZoom() < minZoomInteractiveBuildings) {
        return undefined;
      }

      if (
        lastHoveredBasemapBuildingFeatureRecord &&
        lastHoveredBasemapBuildingFeatureRecord !== feature
      ) {
        try {
          map.setFeatureState(lastHoveredBasemapBuildingFeatureRecord, { highlight: false });
        } catch {
          /* stale */
        }
      }

      try {
        map.setConfigProperty(BASEMAP_FRAGMENT_IMPORT_KEY, "colorBuildingHighlight", SUBDUED_HOVER_BUILDING_TINT_HEX);
        map.setFeatureState(feature, { highlight: true });
        lastHoveredBasemapBuildingFeatureRecord = feature;
      } catch {
        /* ephemeral style race */
      }

      return undefined;
    },
  });

  map.addInteraction(mouseLeaveInteractionHandle, {
    type: "mouseleave",
    target: {
      featuresetId: STANDARD_BUILDING_FEATURESET_IDENTIFIER,
      importId: BASEMAP_FRAGMENT_IMPORT_KEY,
    },
    handler: (interactionPayloadObservation) => {
      const feature = interactionPayloadObservation.feature;
      if (!feature) {
        lastHoveredBasemapBuildingFeatureRecord = null;
        restoreBaselineBuildingHighlightHueObservation();
        return undefined;
      }

      try {
        map.setFeatureState(feature, { highlight: false });
      } catch {
        try {
          map.setFeatureState(feature, { highlight: false });
        } catch {
          /* stale */
        }
      }

      lastHoveredBasemapBuildingFeatureRecord = null;
      restoreBaselineBuildingHighlightHueObservation();

      return undefined;
    },
  });

  function detachInteractionsManifest(): void {
    map.removeInteraction(mouseEnterInteractionHandle);
    map.removeInteraction(mouseLeaveInteractionHandle);
    purgeTransientBuildingHighlightsObservation();
  }

  return {
    detachInteractions: detachInteractionsManifest,
    purgeTransientBuildingHighlights: purgeTransientBuildingHighlightsObservation,
  };
}
