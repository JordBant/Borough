const BASEMAP_FRAGMENT_IMPORT_KEY = "basemap";
const STANDARD_BUILDING_FEATURESET_IDENTIFIER = "buildings";

/** Default Standard highlight cue (Mapbox demos); restored after hover clears. */
const BASELINE_BUILDING_HIGHLIGHT_HEX = "#2e89ff";

/** Slightly darker, desaturated cue when the pointer rests on any basemap building mass. */
const SUBDUED_HOVER_BUILDING_TINT_HEX = "#294a73";

/**
 * GL JS ≥3.9 Interactions API: subtle darken Standard `buildings` on hover (`highlight`
 * feature-state + `colorBuildingHighlight`). Volatility greens/reds are applied on Streets
 * fill-extrusion contributors when zoomed in, not via hover coloring.
 *
 * @param {import('mapbox-gl').Map} map
 * @param {object} [options]
 * @param {number} [options.minZoomInteractiveBuildings=12.35]
 * @returns {{ detachInteractions: () => void, purgeTransientBuildingHighlights: () => void }}
 */
export function attachStandardBuildingMockInfluenceInteractions({ map, minZoomInteractiveBuildings = 12.35 }) {
  const interactionNamingPrefixMarker = "borough-building-hover";

  const mouseEnterInteractionHandle = `${interactionNamingPrefixMarker}-enter`;
  const mouseLeaveInteractionHandle = `${interactionNamingPrefixMarker}-leave`;

  /** @type {import('mapbox-gl').GeoJSONFeature | null} */
  let lastHoveredBasemapBuildingFeatureRecord = null;

  function restoreBaselineBuildingHighlightHueObservation() {
    try {
      map.setConfigProperty(BASEMAP_FRAGMENT_IMPORT_KEY, "colorBuildingHighlight", BASELINE_BUILDING_HIGHLIGHT_HEX);
    } catch {
      /* style churn */
    }
  }

  function purgeTransientBuildingHighlightsObservation() {
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
      if (map.getZoom() < minZoomInteractiveBuildings) {
        return undefined;
      }

      if (
        lastHoveredBasemapBuildingFeatureRecord &&
        lastHoveredBasemapBuildingFeatureRecord !== interactionPayloadObservation.feature
      ) {
        try {
          map.setFeatureState(lastHoveredBasemapBuildingFeatureRecord, { highlight: false });
        } catch {
          /* stale */
        }
      }

      try {
        map.setConfigProperty(BASEMAP_FRAGMENT_IMPORT_KEY, "colorBuildingHighlight", SUBDUED_HOVER_BUILDING_TINT_HEX);
        map.setFeatureState(interactionPayloadObservation.feature, { highlight: true });
        lastHoveredBasemapBuildingFeatureRecord = interactionPayloadObservation.feature;
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
      try {
        map.setFeatureState(interactionPayloadObservation.feature, { highlight: false });
      } catch {
        try {
          map.setFeatureState(interactionPayloadObservation.feature, { highlight: false });
        } catch {
          /* stale */
        }
      }

      lastHoveredBasemapBuildingFeatureRecord = null;
      restoreBaselineBuildingHighlightHueObservation();

      return undefined;
    },
  });

  function detachInteractionsManifest() {
    map.removeInteraction(mouseEnterInteractionHandle);
    map.removeInteraction(mouseLeaveInteractionHandle);
    purgeTransientBuildingHighlightsObservation();
  }

  return {
    detachInteractions: detachInteractionsManifest,
    purgeTransientBuildingHighlights: purgeTransientBuildingHighlightsObservation,
  };
}
