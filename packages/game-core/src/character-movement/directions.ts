import { Direction8, GridPoint } from "./types";

export const DIRECTION_VECTORS: Record<Direction8, GridPoint> = {
  [Direction8.North]: { x: 0, y: -1 },
  [Direction8.NorthEast]: { x: 1, y: -1 },
  [Direction8.East]: { x: 1, y: 0 },
  [Direction8.SouthEast]: { x: 1, y: 1 },
  [Direction8.South]: { x: 0, y: 1 },
  [Direction8.SouthWest]: { x: -1, y: 1 },
  [Direction8.West]: { x: -1, y: 0 },
  [Direction8.NorthWest]: { x: -1, y: -1 },
};

export function moveCell(origin: GridPoint, direction: Direction8, distance = 1): GridPoint {
  const vector = DIRECTION_VECTORS[direction];
  return {
    x: origin.x + vector.x * distance,
    y: origin.y + vector.y * distance,
  };
}

export function directionFromDelta(dx: number, dy: number): Direction8 {
  const x = Math.sign(dx);
  const y = Math.sign(dy);

  if (x === 0 && y < 0) return Direction8.North;
  if (x > 0 && y < 0) return Direction8.NorthEast;
  if (x > 0 && y === 0) return Direction8.East;
  if (x > 0 && y > 0) return Direction8.SouthEast;
  if (x === 0 && y > 0) return Direction8.South;
  if (x < 0 && y > 0) return Direction8.SouthWest;
  if (x < 0 && y === 0) return Direction8.West;
  if (x < 0 && y < 0) return Direction8.NorthWest;

  return Direction8.South;
}

export function directionFromPoints(source: GridPoint, destination: GridPoint): Direction8 {
  return directionFromDelta(destination.x - source.x, destination.y - source.y);
}

export function rotateDirection(direction: Direction8, eighthTurns: number): Direction8 {
  return ((direction + eighthTurns + 8 * 8) % 8) as Direction8;
}

export function reverseDirection(direction: Direction8): Direction8 {
  return rotateDirection(direction, 4);
}

export function isDiagonal(direction: Direction8): boolean {
  return direction % 2 === 1;
}
