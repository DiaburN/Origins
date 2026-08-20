# ORIGINS-DxR — Bichon Real Render Diagnostic

- Gate: **FAIL**
- HEAD: `5e7fd50afeab3f46a3774f87d8c78bfb3cb7f702`

## Steps

- BOOTSTRAP: **success**
- DXT: **success**
- FETCH: **success**
- BUILD: **success**
- RENDER: **failure**

## Fetch

- `Data/Map Data/Tilesc.Zl`: **READY**; bytes `33484507`
- `Data/Map Data/Tiles30c.Zl`: **READY**; bytes `2899880`
- `Data/Map Data/Tiles5c.Zl`: **READY**; bytes `10673688`
- `Data/Map Data/SmTilesc.Zl`: **READY**; bytes `770956`
- `Data/Map Data/Housesc.Zl`: **READY**; bytes `29850809`
- `Data/Map Data/Cliffsc.Zl`: **READY**; bytes `8917280`
- `Data/Map Data/Dungeonsc.Zl`: **READY**; bytes `11683647`
- `Data/Map Data/Innersc.Zl`: **READY**; bytes `208560`
- `Data/Map Data/Furnituresc.Zl`: **READY**; bytes `1984163`
- `Data/Map Data/Wallsc.Zl`: **READY**; bytes `39287002`
- `Data/Map Data/SmObjectsc.Zl`: **READY**; bytes `21322908`
- `Data/Map Data/Animationsc.Zl`: **READY**; bytes `17278768`
- `Data/Map Data/Object1c.Zl`: **READY**; bytes `35432235`
- `Data/Map Data/Object2c.Zl`: **READY**; bytes `24844067`

## build.log

```text
  Determining projects to restore...
  Restored D:\a\Origins\Origins\vendor\zircon\RenderingCore\RenderingCore.csproj (in 3.43 sec).
  Restored D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj (in 3.29 sec).
  Restored D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj (in 3.43 sec).
  RenderingCore -> D:\a\Origins\Origins\vendor\zircon\RenderingCore\bin\Release\net10.0-windows8.0\RenderingCore.dll
C:\Program Files\dotnet\sdk\10.0.400\Microsoft.CSharp.CurrentVersion.targets(130,9): warning MSB3884: Could not find rule set file "MinimumRecommendedRules.ruleset". [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LMain.cs(158,13): warning CS0162: Unreachable code detected [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
  LibraryEditor -> D:\a\Origins\Origins\vendor\Release\LibraryEditor\Mir3LibraryEditor.dll
  ZirconMapRenderer -> D:\a\Origins\Origins\tools\zircon-map-renderer\bin\Release\net10.0-windows8.0\win-x64\ZirconMapRenderer.dll

Build succeeded.

C:\Program Files\dotnet\sdk\10.0.400\Microsoft.CSharp.CurrentVersion.targets(130,9): warning MSB3884: Could not find rule set file "MinimumRecommendedRules.ruleset". [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LMain.cs(158,13): warning CS0162: Unreachable code detected [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
    2 Warning(s)
    0 Error(s)

Time Elapsed 00:00:11.86
```

## render.log

```text
System.IO.InvalidDataException: Map uses unsupported KROrder library id 15; renderer refuses to guess.
   at ZirconMapRenderer.Program.Main(String[] args) in D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs:line 43
```
