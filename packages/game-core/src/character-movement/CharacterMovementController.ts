import { moveCell } from "./directions";
import {
  CharacterMovementSnapshot,
  CollisionQuery,
  DEFAULT_MOVEMENT_CONFIG,
  Direction8,
  Gait,
  GridPoint,
  LocomotionState,
  MovementConfig,
  MovementIntent,
  TraversalResult,
} from "./types";

function clonePoint(point: GridPoint): GridPoint {
  return { x: point.x, y: point.y };
}

function samePoint(a: GridPoint, b: GridPoint): boolean {
  return a.x === b.x && a.y === b.y;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export interface MovementHooks {
  onStepStarted?(snapshot: CharacterMovementSnapshot): void;
  onStepCompleted?(snapshot: CharacterMovementSnapshot): void;
  onBlocked?(direction: Direction8, gait: Gait): void;
  onTransitionRequested?(transitionId: string, snapshot: CharacterMovementSnapshot): void;
}

/**
 * Renderer-agnostic ORIGINS character locomotion controller.
 *
 * It deliberately owns only locomotion. Pathfinding, combat, networking,
 * camera and room switching live in other packages.
 */
export class CharacterMovementController {
  private readonly collision: CollisionQuery;
  private readonly config: MovementConfig;
  private readonly hooks: MovementHooks;

  private state: LocomotionState = "idle";
  private facing: Direction8;
  private currentCell: GridPoint;
  private stepStartCell: GridPoint;
  private targetCell: GridPoint | null = null;
  private gait: Gait | null = null;
  private heldIntent: MovementIntent | null = null;
  private elapsedMs = 0;
  private stepDurationMs = 0;
  private pendingTransitionId: string | undefined;

  constructor(
    startCell: GridPoint,
    collision: CollisionQuery,
    options?: {
      facing?: Direction8;
      config?: Partial<MovementConfig>;
      hooks?: MovementHooks;
    },
  ) {
    this.currentCell = clonePoint(startCell);
    this.stepStartCell = clonePoint(startCell);
    this.facing = options?.facing ?? Direction8.South;
    this.collision = collision;
    this.config = { ...DEFAULT_MOVEMENT_CONFIG, ...options?.config };
    this.hooks = options?.hooks ?? {};
  }

  /** Face a direction without changing cells. */
  turn(direction: Direction8): void {
    this.facing = direction;
  }

  /**
   * Start/continue a directional input. Calling this repeatedly is safe.
   * The current cell step finishes before the next one begins.
   */
  hold(intent: MovementIntent): void {
    this.facing = intent.direction;
    this.heldIntent = { ...intent };

    if (this.state === "idle" || this.state === "blocked") {
      this.tryBeginStep(intent);
    }
  }

  /** Stop continuous movement after the active interpolated step finishes. */
  release(): void {
    this.heldIntent = null;
    if (this.state === "blocked") this.state = "idle";
  }

  /** Execute one discrete movement request (useful for click/tap path queues). */
  step(intent: MovementIntent): boolean {
    this.facing = intent.direction;
    this.heldIntent = null;
    if (this.isMoving() || this.state === "transitioning") return false;
    return this.tryBeginStep(intent);
  }

  /** Advance interpolation and state by a frame delta in milliseconds. */
  update(deltaMs: number): void {
    if (deltaMs <= 0) return;

    if (this.state === "blocked") {
      if (this.heldIntent) this.tryBeginStep(this.heldIntent);
      return;
    }

    if (!this.isMoving() || !this.targetCell) return;

    this.elapsedMs += deltaMs;
    if (this.elapsedMs < this.stepDurationMs) return;

    this.currentCell = clonePoint(this.targetCell);
    this.stepStartCell = clonePoint(this.currentCell);
    this.targetCell = null;
    this.elapsedMs = 0;
    this.stepDurationMs = 0;
    this.gait = null;

    if (this.pendingTransitionId) {
      this.state = "transitioning";
      const transitionId = this.pendingTransitionId;
      this.pendingTransitionId = undefined;
      const snapshot = this.snapshot();
      this.hooks.onStepCompleted?.(snapshot);
      this.hooks.onTransitionRequested?.(transitionId, snapshot);
      return;
    }

    this.state = "idle";
    this.hooks.onStepCompleted?.(this.snapshot());

    if (this.heldIntent) {
      // Pick up the most recent direction/gait for natural held-input turning.
      this.facing = this.heldIntent.direction;
      this.tryBeginStep(this.heldIntent);
    }
  }

  /**
   * Called by gameplay after moving the actor into the next room/floor.
   * This prevents the movement package from owning dungeon progression.
   */
  completeTransition(spawnCell: GridPoint, facing: Direction8 = Direction8.North): void {
    this.currentCell = clonePoint(spawnCell);
    this.stepStartCell = clonePoint(spawnCell);
    this.targetCell = null;
    this.facing = facing;
    this.gait = null;
    this.elapsedMs = 0;
    this.stepDurationMs = 0;
    this.pendingTransitionId = undefined;
    this.state = "idle";
  }

  /** Used for spawn/teleport/recovery, not normal walking. */
  forcePosition(cell: GridPoint, facing = this.facing): void {
    this.heldIntent = null;
    this.completeTransition(cell, facing);
  }

  snapshot(): CharacterMovementSnapshot {
    const progress = this.progress();
    const destination = this.targetCell ?? this.currentCell;
    const renderCell = {
      x: lerp(this.stepStartCell.x, destination.x, progress),
      y: lerp(this.stepStartCell.y, destination.y, progress),
    };

    return {
      state: this.state,
      facing: this.facing,
      currentCell: clonePoint(this.currentCell),
      targetCell: this.targetCell ? clonePoint(this.targetCell) : null,
      renderCell,
      renderOffsetPx: {
        x: (renderCell.x - this.currentCell.x) * this.config.cellWidth,
        y: (renderCell.y - this.currentCell.y) * this.config.cellHeight,
      },
      gait: this.gait,
      progress,
      transitionId: this.pendingTransitionId,
    };
  }

  isMoving(): boolean {
    return this.state === "walking" || this.state === "running";
  }

  private progress(): number {
    if (!this.isMoving() || this.stepDurationMs <= 0) return 0;
    return Math.max(0, Math.min(1, this.elapsedMs / this.stepDurationMs));
  }

  private tryBeginStep(intent: MovementIntent): boolean {
    if (this.state === "transitioning") return false;

    const requestedCells = intent.gait === "run"
      ? this.config.runCellsPerStep
      : this.config.walkCellsPerStep;

    let cursor = clonePoint(this.currentCell);
    let acceptedCells = 0;
    let finalTraversal: TraversalResult = { allowed: true };

    for (let i = 0; i < requestedCells; i += 1) {
      const next = moveCell(cursor, intent.direction, 1);
      const traversal = this.canTraverse(cursor, next);
      if (!traversal.allowed) break;

      cursor = next;
      finalTraversal = traversal;
      acceptedCells += 1;

      // A door/room transition must end this movement command at its cell.
      if (traversal.transitionId) break;
    }

    if (acceptedCells === 0) {
      this.state = "blocked";
      this.targetCell = null;
      this.gait = null;
      this.hooks.onBlocked?.(intent.direction, intent.gait);
      return false;
    }

    if (
      intent.gait === "run" &&
      acceptedCells < requestedCells &&
      !this.config.allowPartialRun &&
      !finalTraversal.transitionId
    ) {
      this.state = "blocked";
      this.targetCell = null;
      this.gait = null;
      this.hooks.onBlocked?.(intent.direction, intent.gait);
      return false;
    }

    // If a 2-cell run can only safely advance one normal cell, degrade to the
    // walk clip rather than playing half a run cycle and looking broken.
    const effectiveGait: Gait =
      intent.gait === "run" && acceptedCells < requestedCells && !finalTraversal.transitionId
        ? "walk"
        : intent.gait;

    this.facing = intent.direction;
    this.stepStartCell = clonePoint(this.currentCell);
    this.targetCell = clonePoint(cursor);
    this.gait = effectiveGait;
    this.elapsedMs = 0;
    this.stepDurationMs = effectiveGait === "run"
      ? this.config.runStepMs
      : this.config.walkStepMs;
    this.pendingTransitionId = finalTraversal.transitionId;
    this.state = effectiveGait === "run" ? "running" : "walking";

    // Defensive assertion against accidental zero-distance accepted paths.
    if (samePoint(this.stepStartCell, this.targetCell)) {
      this.state = "idle";
      this.targetCell = null;
      this.gait = null;
      this.pendingTransitionId = undefined;
      return false;
    }

    this.hooks.onStepStarted?.(this.snapshot());
    return true;
  }

  private canTraverse(from: GridPoint, to: GridPoint): TraversalResult {
    if (this.collision.canTraverse) return this.collision.canTraverse(from, to);
    return { allowed: this.collision.canStandAt(to) };
  }
}
