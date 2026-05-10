import { useId, useState, type ReactNode } from "react";

export interface CollapsiblePanelProps {
  title: string;
  summaryCollapsed?: string;
  defaultExpanded?: boolean;
  className?: string;
  disabled?: boolean;
  children?: ReactNode;
}

/**
 * Collapsible chrome: expanded shows full content; collapsed keeps a compact header strip.
 */
export default function CollapsiblePanel({
  title,
  summaryCollapsed,
  defaultExpanded = true,
  className = "",
  disabled = false,
  children,
}: CollapsiblePanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const bodySectionId = useId();

  if (disabled) {
    return null;
  }

  return (
    <div
      className={`collapsible-panel ${expanded ? "collapsible-panel--expanded" : "collapsible-panel--collapsed"} ${className}`.trim()}
    >
      <button
        type="button"
        className="collapsible-panel-header"
        onClick={() => setExpanded((previous) => !previous)}
        aria-expanded={expanded}
        aria-controls={bodySectionId}
      >
        <span className="collapsible-panel-heading">
          <span className="collapsible-panel-title">{title}</span>
          {!expanded && summaryCollapsed ? (
            <span className="collapsible-panel-summary">{summaryCollapsed}</span>
          ) : null}
        </span>
        <span className="collapsible-panel-chevron" aria-hidden>
          {expanded ? "▾" : "▸"}
        </span>
      </button>
      {expanded ? (
        <div className="collapsible-panel-body" id={bodySectionId}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
