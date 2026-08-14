# ORIGINS CHARACTER MOVEMENT V1

Branch: `character-movement-v1`

This subsystem is intentionally developed in parallel with `map-engine-v1` so map work and character work do not overwrite one another. It will be merged only after both sides are stable.

## Scope

Movement V1 means complete **locomotion**, not combat actions.

Included:
- idle/standing animation;
- turn in place;
- 8 directions;
- walk;
- run;
- held-input continuous movement;
- discrete click/tap step requests;
- walk/run switching;
- smooth interpolation between grid cells;
- wall/obstacle/door collision contract;
- safe intermediate-cell checks while running;
- room/floor transition hand-off;
- renderer-independent Crystal frame selection.

Not included in this milestone:
- attacks;
- spells;
- struck/knockback;
- death/revive;
- mounts;
- networking;
- AI/pathfinding.

Those action states will plug into the same character state machine after locomotion is visually approved.

## Crystal source reference

Authoritative reference: `Suprcode/Crystal`.

Relevant source files:
- `Client/MirObjects/Frames.cs`
- `Client/MirObjects/PlayerObject.cs`
- `Shared/Functions/Functions.cs`
- `Client/MirGraphics/MLibrary.cs`
- `Client/Settings.cs`

Crystal player locomotion frame layout:

| Action | Start | Frames/direction | Frame interval |
|---|---:|---:|---:|
| Standing | 0 | 4 | 500 ms |
| Walking | 32 | 6 | 100 ms |
| Running | 80 | 6 | 100 ms |

Directions use Mir's clockwise 8-way order:

`N -> NE -> E -> SE -> S -> SW -> W -> NW`

Crystal moves:
- walk = 1 cell;
- run = 2 cells;
- sprint = 3 cells.

ORIGINS V1 keeps walk = 1 and run = 2. Sprint is deliberately excluded until normal room movement is approved.

## ORIGINS design rules

### 1. Natural facing
The character immediately faces the requested direction. If movement is blocked, the character still turns toward that direction instead of sliding or facing the old direction.

### 2. Grid-authoritative, visually smooth
Gameplay position remains cell-based so collision stays deterministic. Rendering interpolates smoothly between cells during the six movement frames.

### 3. No obstacle skipping while running
A two-cell run checks each intermediate cell. Running cannot jump through a wall, pillar, closed door or blocked cell.

If the first cell is free but the second is blocked, V1 may degrade that request to a one-cell walk. This behavior is configurable.

### 4. Doors belong to gameplay/map-engine
Movement detects a `transitionId` on traversal and stops in `transitioning` state. It does **not** decide which floor comes next.

Example:

`F1 NORTH door -> movement reaches transition cell -> gameplay loads F2 -> movement.completeTransition(F2 SOUTH spawn)`

### 5. Standard floor entry
On arrival from the previous floor, the character appears just inside the SOUTH entrance, facing NORTH.

### 6. KingRoom entry
Same SOUTH-entry rule. There is no NORTH transition in KR.

## Desktop/mobile input contract

The core package does not import browser APIs.

Recommended adapters:

Desktop:
- left mouse = walk command/path;
- right mouse = run command/path;
- keyboard/joystick can map directly to held `MovementIntent`.

Mobile:
- virtual stick or drag produces a held direction;
- UI decides whether that intent is walk or run;
- the movement core receives the same `MovementIntent` as desktop.

This means control style can change without rewriting character movement.

## Runtime API

Primary controller:

`packages/game-core/src/character-movement/CharacterMovementController.ts`

Core calls:

```ts
controller.turn(Direction8.North);
controller.hold({ direction: Direction8.North, gait: "walk" });
controller.update(deltaMs);
controller.release();
```

For click/tap pathfinding, the external path system can feed discrete commands:

```ts
controller.step({ direction: Direction8.NorthEast, gait: "run" });
```

Renderer reads:

```ts
const movement = controller.snapshot();
```

It gets:
- logical current cell;
- interpolated render cell;
- facing;
- locomotion state;
- gait;
- 0..1 step progress;
- transition state.

## Animation frame selection

Use `crystal-animation-profile.ts`.

Directional frame formula is equivalent to Crystal's:

`start + ((count + skip) * directionIndex) + localFrame`

The renderer combines this with the source `.Lib` image offset metadata. Never reposition body frames by eye.

## Next visual milestone

Extract one real `Data/CArmour/00.Lib` from the public Crystal/Mir2 assets and create a browser preview showing:

- Standing N/NE/E/SE/S/SW/W/NW
- Walking N/NE/E/SE/S/SW/W/NW
- Running N/NE/E/SE/S/SW/W/NW

After visual approval, connect the movement controller to the `zuma_gray` Standard Room.
