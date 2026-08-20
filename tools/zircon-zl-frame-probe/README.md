# Zircon ZL frame probe

This helper is a read-only asset probe used by ORIGINS-DxR CI. It opens transient official Zircon `.Zl` body libraries and checks whether the exact frame windows referenced by the pinned player runtime contain real images.

Authority is pinned Zircon commit `cbf1aa919083bc13fc3f23f93772a8ab8370632d`.

Current fishing investigation follows the native contracts rather than assuming every `FrameSet.Players` slot is drawn identically:

- `Client/Models/MapObject.UpdateFrame()` forces player `MirAction.Pushed` to local frame `0`.
- `Client/Models/PlayerObject` draws the body through `BodyLibrary.GetImage(ArmourFrame)`.
- Warrior/Wizard/Taoist body shape banks use a `+5000` stride.
- Assassin fishing applies the pinned `ArmourShift = +80` rule.
- `FishingCast`, `FishingWait`, and `FishingReel` are checked for all 8 directions and every source-local frame.

The probe never substitutes Crystal art, mirrored male art, generated placeholders, or guessed frame offsets. A complete bank must exist in an official Zircon body library to be reported as `PASS`.
