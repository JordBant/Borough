import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import { BROOKLYN_BOUNDARY, BROOKLYN_CENTER } from "../../data/brooklynBoundary";
import { MOCK_PROPERTIES } from "../../data/mockProperties";
import { buildOuterMaskGeoJson } from "./maskUtils";
import "./BrooklynMap.css";

const MAPBOX_ACCESS_TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

export default function BrooklynMap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!MAPBOX_ACCESS_TOKEN) {
      console.error("Missing VITE_MAPBOX_ACCESS_TOKEN in .env");
      return;
    }

    mapboxgl.accessToken = MAPBOX_ACCESS_TOKEN;

    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: "mapbox://styles/mapbox/standard",
      center: BROOKLYN_CENTER,
      zoom: 11.5,
      pitch: 60,
      bearing: -17,
      antialias: true,
    });

    mapInstanceRef.current = map;

    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    map.on("style.load", () => {
      map.setConfigProperty("basemap", "lightPreset", "dusk");
      map.setConfigProperty("basemap", "show3dObjects", true);

      addBrooklynBoundaryLayer(map);
      addOuterMaskLayer(map);
      addPropertyMarkers(map);
    });

    return () => map.remove();
  }, []);

  return (
    <div className="brooklyn-map-wrapper">
      <div ref={mapContainerRef} className="brooklyn-map-container" />
      <div className="brooklyn-map-legend">
        <h3>Brooklyn Rental Pressure</h3>
        <div className="legend-scale">
          <span className="legend-low">Low</span>
          <div className="legend-gradient" />
          <span className="legend-high">High</span>
        </div>
      </div>
    </div>
  );
}

function addBrooklynBoundaryLayer(map) {
  map.addSource("brooklyn-boundary", {
    type: "geojson",
    data: BROOKLYN_BOUNDARY,
  });

  map.addLayer({
    id: "brooklyn-boundary-outline",
    type: "line",
    source: "brooklyn-boundary",
    paint: {
      "line-color": "#4fc3f7",
      "line-width": 2.5,
      "line-opacity": 0.8,
    },
  });
}

function addOuterMaskLayer(map) {
  const maskGeoJson = buildOuterMaskGeoJson(BROOKLYN_BOUNDARY);

  map.addSource("outer-mask", {
    type: "geojson",
    data: maskGeoJson,
  });

  map.addLayer({
    id: "outer-mask-fill",
    type: "fill",
    source: "outer-mask",
    paint: {
      "fill-color": "#1a1a2e",
      "fill-opacity": 0.7,
    },
  });
}

function addPropertyMarkers(map) {
  MOCK_PROPERTIES.forEach((property) => {
    const markerColor = rentPressureToColor(property.rentPressureScore);

    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="property-popup">
        <h4>${property.address}</h4>
        <p><strong>Submarket:</strong> ${property.submarket}</p>
        <p><strong>Median Rent:</strong> $${property.medianRent.toLocaleString()}</p>
        <p><strong>RPS:</strong> ${property.rentPressureScore}/100</p>
        <p><strong>Built:</strong> ${property.yearBuilt}</p>
      </div>
    `);

    new mapboxgl.Marker({ color: markerColor })
      .setLngLat(property.coordinates)
      .setPopup(popup)
      .addTo(map);
  });
}

function rentPressureToColor(score) {
  if (score >= 80) return "#ef4444";
  if (score >= 60) return "#f59e0b";
  if (score >= 40) return "#eab308";
  return "#22c55e";
}
