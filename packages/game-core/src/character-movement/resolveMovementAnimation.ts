import { clipForGait, resolveDirectionalFrame, resolveLoopFrame } from "./crystal-animation-profile";
import { CharacterMovementSnapshot } from "./types";

/**
 * Resolve the body frame for the current movement snapshot.
 *
 * Moving clips are synchronized to movement progress so the 6-frame Crystal
 * cycle starts and finishes exactly with a logical movement step. Idle uses a
 * free-running clock supplied by the renderer/game loop.
 */
export function resolveMovementBodyFrame(
  snapshot: CharacterMovementSnapshot,
  idleElapsedMs: number,
): number {
  const clip = clipForGait(snapshot.gait);

  if (snapshot.state !== "walking" && snapshot.state !== "running") {
    return resolveLoopFrame(clip, snapshot.facing, idleElapsedMs);
  }

  const localFrame = Math.min(
    clip.framesPerDirection - 1,
    Math.floor(snapshot.progress * clip.framesPerDirection),
  );

  return resolveDirectionalFrame(clip, snapshot.facing, localFrame);
}
