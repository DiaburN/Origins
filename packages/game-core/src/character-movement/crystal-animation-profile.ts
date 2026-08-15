import { Direction8, Gait } from "./types";

export interface DirectionalAnimationClip {
  name: string;
  startFrame: number;
  framesPerDirection: number;
  skipPerDirection: number;
  frameIntervalMs: number;
  loop: boolean;
}

/**
 * Player locomotion layout taken from Suprcode/Crystal Client/MirObjects/Frames.cs.
 *
 * Crystal player frames:
 * Standing: start 0, count 4, skip 0, 500 ms
 * Walking:  start 32, count 6, skip 0, 100 ms
 * Running:  start 80, count 6, skip 0, 100 ms
 *
 * Direction order is the Mir 8-way clockwise order:
 * N, NE, E, SE, S, SW, W, NW.
 */
export const CRYSTAL_PLAYER_LOCOMOTION = {
  idle: {
    name: "standing",
    startFrame: 0,
    framesPerDirection: 4,
    skipPerDirection: 0,
    frameIntervalMs: 500,
    loop: true,
  },
  walk: {
    name: "walking",
    startFrame: 32,
    framesPerDirection: 6,
    skipPerDirection: 0,
    frameIntervalMs: 100,
    loop: true,
  },
  run: {
    name: "running",
    startFrame: 80,
    framesPerDirection: 6,
    skipPerDirection: 0,
    frameIntervalMs: 100,
    loop: true,
  },
} satisfies Record<"idle" | Gait, DirectionalAnimationClip>;

export function resolveDirectionalFrame(
  clip: DirectionalAnimationClip,
  direction: Direction8,
  localFrame: number,
): number {
  const directionalStride = clip.framesPerDirection + clip.skipPerDirection;
  const normalizedLocalFrame = Math.max(0, Math.min(clip.framesPerDirection - 1, localFrame));
  return clip.startFrame + directionalStride * direction + normalizedLocalFrame;
}

export function resolveLoopFrame(
  clip: DirectionalAnimationClip,
  direction: Direction8,
  elapsedMs: number,
): number {
  const local = Math.floor(Math.max(0, elapsedMs) / clip.frameIntervalMs) % clip.framesPerDirection;
  return resolveDirectionalFrame(clip, direction, local);
}

export function clipForGait(gait: Gait | null): DirectionalAnimationClip {
  if (gait === "walk") return CRYSTAL_PLAYER_LOCOMOTION.walk;
  if (gait === "run") return CRYSTAL_PLAYER_LOCOMOTION.run;
  return CRYSTAL_PLAYER_LOCOMOTION.idle;
}
