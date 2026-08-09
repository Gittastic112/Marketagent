"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

type DataHealthContextType = {
  staleSegments: Record<string, boolean>;
  setStaleSegment: (segment: string, isStale: boolean) => void;
};

const DataHealthContext = createContext<DataHealthContextType | undefined>(undefined);

export function DataHealthProvider({ children }: { children: ReactNode }) {
  const [staleSegments, setStaleSegments] = useState<Record<string, boolean>>({});

  const setStaleSegment = (segment: string, isStale: boolean) => {
    setStaleSegments((prev) => {
      if (prev[segment] === isStale) return prev;
      return { ...prev, [segment]: isStale };
    });
  };

  return (
    <DataHealthContext.Provider value={{ staleSegments, setStaleSegment }}>
      {children}
    </DataHealthContext.Provider>
  );
}

export function useDataHealth() {
  const context = useContext(DataHealthContext);
  if (!context) {
    throw new Error("useDataHealth must be used within a DataHealthProvider");
  }
  return context;
}
