export type MirMapFormat =
  | "MIR2_CLASSIC"
  | "MIR2_2010"
  | "SHANDA_MIR2"
  | "SHANDA_MIR2_2012"
  | "MIR2_ANTIHACK"
  | "WEMADE_MIR3"
  | "SHANDA_MIR3"
  | "HEROES"
  | "CSHARP_CUSTOM";

export interface MapCell {
  x: number;
  y: number;

  backIndex: number;
  backImage: number;
  middleIndex: number;
  middleImage: number;
  frontIndex: number;
  frontImage: number;

  doorIndex: number;
  doorOffset: number;

  frontAnimationFrame: number;
  frontAnimationTick: number;
  middleAnimationFrame: number;
  middleAnimationTick: number;

  light: number;
  fishingCell: boolean;

  /** Source-format collision hint. ORIGINS rooms author their own collision layer. */
  sourceBlocked: boolean;
}

export interface ParsedMap {
  format: MirMapFormat;
  width: number;
  height: number;
  cells: MapCell[];
}

export type ShapeType =
  | "FLOOR"
  | "WALL_TOP"
  | "WALL_BOTTOM"
  | "WALL_LEFT"
  | "WALL_RIGHT"
  | "CORNER_TL"
  | "CORNER_TR"
  | "CORNER_BL"
  | "CORNER_BR"
  | "DOOR_TOP"
  | "DOOR_BOTTOM"
  | "OBSTACLE"
  | "PILLAR"
  | "DECORATION"
  | "HAZARD"
  | "ALTAR"
  | "THRONE"
  | "PORTAL"
  | "KINGROOM_DECOR";

export interface ShapeSource {
  sourceFamily: "WemadeMir2" | "ShandaMir2" | "WemadeMir3" | "ShandaMir3";
  sourceLibrary: string;
  sourceImage: number;
  sourceMap?: string;
}

export interface ThemeShape extends ShapeSource {
  shapeId: string;
  themeId: string;
  type: ShapeType;
  widthCells: number;
  heightCells: number;
  anchorX: number;
  anchorY: number;
  collisionProfile: "WALKABLE" | "SOLID" | "CUSTOM";
  tags?: string[];
}

export type RoomType =
  | "STANDARD_LONG"
  | "STANDARD_NARROW"
  | "STANDARD_WIDE"
  | "OBSTACLE"
  | "PILLARS"
  | "ELITE"
  | "EVENT"
  | "KING_ROOM";

export interface RoomTemplate {
  roomId: string;
  roomType: RoomType;
  themeId: string;
  widthCells: number;
  heightCells: number;
  entry: { x: number; y: number };
  exit: { x: number; y: number };
  playableRect: { x: number; y: number; width: number; height: number };
}
