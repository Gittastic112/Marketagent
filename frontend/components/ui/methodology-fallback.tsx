import type { ReactNode } from "react";

export function MethodologyFallback({
  children,
  fallbackReason,
}: {
  children: ReactNode;
  fallbackReason: string;
}) {
  return (
    <div style={{ position: "relative" }}>
      <div style={{
        position: "absolute",
        top: 0,
        right: 0,
        zIndex: 10,
        background: "rgba(249, 115, 22, 0.9)",
        color: "white",
        padding: "4px 8px",
        fontSize: "0.75rem",
        borderBottomLeftRadius: "8px",
        borderTopRightRadius: "4px",
      }}>
        Fallback: {fallbackReason}
      </div>
      <div style={{ border: "1px dashed rgba(249, 115, 22, 0.5)", borderRadius: "4px", padding: "2px" }}>
        {children}
      </div>
    </div>
  );
}
