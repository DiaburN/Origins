import type { ParsedMap } from "./types";
import { isDungeonCandidate, resolveMapLibrary, type MapLibraryRef } from "./libraryRegistry";

export interface MapDependencyReport {
  allSlots: number[];
  resolvedLibraries: MapLibraryRef[];
  unresolvedSlots: number[];
  dungeonCandidateLibraries: MapLibraryRef[];
}

/**
 * Finds every graphics-library slot referenced by a parsed map.
 * This is the mechanism ORIGINS will use to request only the .Lib files needed
 * by one cave instead of moving an entire Crystal client Data directory.
 */
export function analyzeMapDependencies(map: ParsedMap): MapDependencyReport {
  const slots = new Set<number>();

  for (const cell of map.cells) {
    if (cell.backIndex >= 0) slots.add(cell.backIndex);
    if (cell.middleIndex >= 0) slots.add(cell.middleIndex);
    if (cell.frontIndex >= 0) slots.add(cell.frontIndex);
  }

  const allSlots = [...slots].sort((a, b) => a - b);
  const resolvedLibraries: MapLibraryRef[] = [];
  const unresolvedSlots: number[] = [];

  for (const slot of allSlots) {
    const lib = resolveMapLibrary(slot);
    if (lib) resolvedLibraries.push(lib);
    else unresolvedSlots.push(slot);
  }

  return {
    allSlots,
    resolvedLibraries,
    unresolvedSlots,
    dungeonCandidateLibraries: resolvedLibraries.filter((lib) => isDungeonCandidate(lib.slot)),
  };
}
