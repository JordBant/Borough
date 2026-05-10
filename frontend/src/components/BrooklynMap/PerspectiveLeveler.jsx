import { useState } from "react";

import CollapsiblePanel from "./CollapsiblePanel";

/** Bird's-eye / horizon controls: adjust camera pitch and compass bearing. */
export default function PerspectiveLeveler({
  mapRef,
  enabled,
  initialPitch = 60,
  initialBearing = -17,
}) {
  const [pitchDegrees, setPitchDegrees] = useState(initialPitch);
  const [bearingDegrees, setBearingDegrees] = useState(initialBearing);

  function applyPerspective(pitch, bearing) {
    const mapInstance = mapRef.current;
    if (!mapInstance) return;
    mapInstance.jumpTo({ pitch, bearing });
  }

  function handlePitchChange(event) {
    const value = Number(event.target.value);
    setPitchDegrees(value);
    applyPerspective(value, bearingDegrees);
  }

  function handleBearingChange(event) {
    const value = Number(event.target.value);
    setBearingDegrees(value);
    applyPerspective(pitchDegrees, value);
  }

  function resetToBirdsEyePlane() {
    setPitchDegrees(0);
    setBearingDegrees(0);
    applyPerspective(0, 0);
  }

  function resetBirdsEyeTilt() {
    setPitchDegrees(initialPitch);
    setBearingDegrees(initialBearing);
    applyPerspective(initialPitch, initialBearing);
  }

  return (
    <CollapsiblePanel
      title="Perspective"
      summaryCollapsed={`Pitch ${pitchDegrees}° · bearing ${bearingDegrees}°`}
      className="perspective-leveler"
      defaultExpanded
      disabled={!enabled}
    >
      <label className="perspective-leveler-label">
        <span>Bird&apos;s-eye tilt (pitch)</span>
        <div className="perspective-leveler-row">
          <input
            type="range"
            min="0"
            max="85"
            step="1"
            value={pitchDegrees}
            onChange={handlePitchChange}
          />
          <output className="perspective-value">{pitchDegrees}°</output>
        </div>
        <span className="perspective-leveler-hint">0° = overhead &middot; 85° = horizon</span>
      </label>

      <label className="perspective-leveler-label">
        <span>Rotation (bearing)</span>
        <div className="perspective-leveler-row">
          <input
            type="range"
            min="-180"
            max="180"
            step="1"
            value={bearingDegrees}
            onChange={handleBearingChange}
          />
          <output className="perspective-value">{bearingDegrees}°</output>
        </div>
      </label>

      <div className="perspective-leveler-buttons">
        <button type="button" onClick={resetToBirdsEyePlane} className="perspective-btn">
          Level (top-down)
        </button>
        <button type="button" onClick={resetBirdsEyeTilt} className="perspective-btn">
          Restore default tilt
        </button>
      </div>
    </CollapsiblePanel>
  );
}
