export interface MapLibraryRef {
  slot: number;
  family: "WemadeMir2" | "ShandaMir2" | "WemadeMir3" | "ShandaMir3";
  relativePath: string;
}

const MIR3_STATES = ["", "wood/", "sand/", "snow/", "forest/"] as const;
const MIR3_NAMES = [
  "Tilesc",
  "Tiles30c",
  "Tiles5c",
  "Smtilesc",
  "Housesc",
  "Cliffsc",
  "Dungeonsc",
  "Innersc",
  "Furnituresc",
  "Wallsc",
  "smObjectsc",
  "Animationsc",
  "Object1c",
  "Object2c",
] as const;

/** Mirrors Crystal's map-library slot convention without depending on Crystal at runtime. */
export function resolveMapLibrary(slot: number): MapLibraryRef | null {
  // Wemade Mir2: 0-99
  if (slot === 0) return { slot, family: "WemadeMir2", relativePath: "Map/WemadeMir2/Tiles.Lib" };
  if (slot === 1) return { slot, family: "WemadeMir2", relativePath: "Map/WemadeMir2/Smtiles.Lib" };
  if (slot === 2) return { slot, family: "WemadeMir2", relativePath: "Map/WemadeMir2/Objects.Lib" };
  if (slot >= 3 && slot <= 28) {
    return { slot, family: "WemadeMir2", relativePath: `Map/WemadeMir2/Objects${slot - 1}.Lib` };
  }
  if (slot === 90) return { slot, family: "WemadeMir2", relativePath: "Map/WemadeMir2/Objects_32bit.Lib" };

  // Wemade Mir3: 200-299. Each environment state occupies 15 slots.
  if (slot >= 200 && slot < 275) {
    const state = Math.floor((slot - 200) / 15);
    const local = (slot - 200) % 15;
    if (state >= 0 && state < MIR3_STATES.length && local < MIR3_NAMES.length) {
      return {
        slot,
        family: "WemadeMir3",
        relativePath: `Map/WemadeMir3/${MIR3_STATES[state]}${MIR3_NAMES[local]}.Lib`,
      };
    }
  }

  return null;
}

export function isDungeonCandidate(slot: number): boolean {
  const ref = resolveMapLibrary(slot);
  if (!ref) return false;
  return /Dungeonsc|Innersc|Wallsc|Cliffsc|Object1c|Object2c|smObjectsc|Objects/i.test(ref.relativePath);
}
