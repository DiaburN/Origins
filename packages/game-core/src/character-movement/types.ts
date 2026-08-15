export enum Direction8 {
  North = 0,
  NorthEast = 1,
  East = 2,
  SouthEast = 3,
  South = 4,
  SouthWest = 5,
  West = 6,
  NorthWest = 7,
}

export type LocomotionState = "idle" | "walking" | "running" | "blocked" | "transitioning";
export type Gait = "walk" | "run";

export interface GridPoint {
  x: number;
  y: number;
}

export interface WorldPoint {
  x: number;
  y: number;
}

export interface MovementIntent {
  direction: Direction8;
  gait: Gait;
}

export interface TraversalResult {
  allowed: boolean;
  /** Optional room/floor transition attached to the final cell. */
  transitionId?: string;
}

export interface CollisionQuery {
  /** True when the character may occupy this cell. */
  canStandAt(cell: GridPoint): boolean;
  /**
   * Optional stricter traversal check. Use this for doors, one-way links or
   * diagonal corner rules. If omitted, canStandAt(to) is used.
   */
  canTraverse?(from: GridPoint, to: GridPoint): TraversalResult;
}

export interface MovementConfig {
  cellWidth: number;
  cellHeight: number;
  walkCellsPerStep: number;
  runCellsPerStep: number;
  walkStepMs: number;
  runStepMs: number;
  allowPartialRun: boolean;
}

export interface CharacterMovementSnapshot {
  state: LocomotionState;
  facing: Direction8;
  currentCell: GridPoint;
  targetCell: GridPoint | null;
  renderCell: { x: number; y: number };
  renderOffsetPx: WorldPoint;
  gait: Gait | null;
  progress: number;
  transitionId?: string;
}

export const DEFAULT_MOVEMENT_CONFIG: MovementConfig = {
  // Crystal/Mir source-map cell convention used by ORIGINS Map Engine V1.
  cellWidth: 48,
  cellHeight: 32,
  walkCellsPerStep: 1,
  // Crystal Running advances two cells. We preserve that feel while checking
  // every intermediate cell so obstacles cannot be skipped.
  runCellsPerStep: 2,
  // Crystal player walking/running both use 6 frames at 100 ms per frame.
  walkStepMs: 600,
  runStepMs: 600,
  allowPartialRun: true,
};
