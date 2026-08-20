# ORIGINS-DxR — Bichon Renderer Compile Check

- Gate: **FAIL**
- HEAD: `2407cd3b383c3ab3c37ec993c0c13ab2cac6b7df`
- Bootstrap: **success**
- Managed DXT: **success**
- Renderer build: **failure**

## Compiler tail

`	ext
  Determining projects to restore...
  Restored D:\a\Origins\Origins\vendor\zircon\RenderingCore\RenderingCore.csproj (in 3.28 sec).
  Restored D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj (in 3.28 sec).
  Restored D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj (in 3.28 sec).
  RenderingCore -> D:\a\Origins\Origins\vendor\zircon\RenderingCore\bin\Release\net10.0-windows8.0\RenderingCore.dll
C:\Program Files\dotnet\sdk\10.0.400\Microsoft.CSharp.CurrentVersion.targets(130,9): warning MSB3884: Could not find rule set file "MinimumRecommendedRules.ruleset". [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LMain.cs(158,13): warning CS0162: Unreachable code detected [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
  LibraryEditor -> D:\a\Origins\Origins\vendor\Release\LibraryEditor\Mir3LibraryEditor.dll
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,33): error CS1503: Argument 2: cannot convert from 'System.Drawing.RectangleF' to 'System.Drawing.PointF[]' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,39): error CS1503: Argument 3: cannot convert from 'int' to 'System.Drawing.RectangleF' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,45): error CS1503: Argument 5: cannot convert from 'int' to 'System.Drawing.Imaging.ImageAttributes?' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,59): error CS1503: Argument 6: cannot convert from 'int' to 'System.Drawing.Graphics.DrawImageAbort?' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,74): error CS1503: Argument 7: cannot convert from 'System.Drawing.GraphicsUnit' to 'int' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]

Build FAILED.

C:\Program Files\dotnet\sdk\10.0.400\Microsoft.CSharp.CurrentVersion.targets(130,9): warning MSB3884: Could not find rule set file "MinimumRecommendedRules.ruleset". [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LMain.cs(158,13): warning CS0162: Unreachable code detected [D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,33): error CS1503: Argument 2: cannot convert from 'System.Drawing.RectangleF' to 'System.Drawing.PointF[]' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,39): error CS1503: Argument 3: cannot convert from 'int' to 'System.Drawing.RectangleF' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,45): error CS1503: Argument 5: cannot convert from 'int' to 'System.Drawing.Imaging.ImageAttributes?' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,59): error CS1503: Argument 6: cannot convert from 'int' to 'System.Drawing.Graphics.DrawImageAbort?' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
D:\a\Origins\Origins\tools\zircon-map-renderer\Program.cs(219,74): error CS1503: Argument 7: cannot convert from 'System.Drawing.GraphicsUnit' to 'int' [D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj]
    2 Warning(s)
    5 Error(s)

Time Elapsed 00:00:13.17
`
