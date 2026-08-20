# ORIGINS-DxR — Zircon Base Human Import

- Import gate: **FAIL**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Origins-DxR HEAD tested: `66b2e1f1b83fb26b438253075a470255bfc9dfe8`
- Primary patch host from Zircon: `https://mirfiles.com/resources/mir3/zircon/patch/`
- Fetch status: **PASS**

## CI

| Check | Result |
|---|---|
| Bootstrap pinned Zircon | success |
| Fetch M-Hum + WM-Hum | success |
| Build ZL exporter | success |
| Export browser atlases | failure |
| Validate generated pair | skipped |
| Build runnable preview | skipped |

## Downloaded ZL files

- `M_Hum` from `https://mirfiles.com/resources/mir3/zircon/patch/Data-M-Hum.Zl.gz` — 16229006 gzip bytes → 44084120 raw bytes — SHA-256 `691FF4CCFDC7D63DA72AB740910849E4C13409C1A7F80D53E57602F748E68169`
- `WM_Hum` from `https://mirfiles.com/resources/mir3/zircon/patch/Data-WM-Hum.Zl.gz` — 15691717 gzip bytes → 43736032 raw bytes — SHA-256 `B0CE4F4F14413FA2B934E2C85B8D93E886E70656206E05860CE40F2370B09A0A`

## Exporter error log

```text
Exporting M_Hum: D:\a\Origins\Origins\runtime-assets\zircon\Data\M-Hum.Zl
System.TypeInitializationException: The type initializer for 'ManagedSquish.Squish' threw an exception.
 ---> System.IO.FileNotFoundException: Could not load file or assembly 'D:\a\Origins\Origins\tools\zircon-web-asset-exporter\bin\Release\net10.0-windows8.0\win-x64\NativeSquish_x64.dll'. The specified module could not be found.
File name: 'D:\a\Origins\Origins\tools\zircon-web-asset-exporter\bin\Release\net10.0-windows8.0\win-x64\NativeSquish_x64.dll'
   at ManagedSquish.Squish.Getx64Delegates()
   at ManagedSquish.Squish.Getx64Delegates()
   at ManagedSquish.Squish..cctor()
   --- End of inner exception stack trace ---
   at ManagedSquish.Squish.GetStorageRequirements(Int32 width, Int32 height, SquishFlags flags)
   at LibraryEditor.Mir3Library.Mir3Image.DecodeBitmap(Byte[] bytes, Int32 width, Int32 height, ZlImageCodec codec) in D:\a\Origins\Origins\vendor\zircon\LibraryEditor\Mir3Library.cs:line 2807
   at LibraryEditor.Mir3Library.Mir3Image.CreateImage(BinaryReader reader, Func`2 payloadReader) in D:\a\Origins\Origins\vendor\zircon\LibraryEditor\Mir3Library.cs:line 2400
   at LibraryEditor.Mir3Library.ReadLibrary() in D:\a\Origins\Origins\vendor\zircon\LibraryEditor\Mir3Library.cs:line 115
   at LibraryEditor.Mir3Library..ctor(String fileName, Boolean useBlackKeyTransparency) in D:\a\Origins\Origins\vendor\zircon\LibraryEditor\Mir3Library.cs:line 72
   at ZirconWebAssetExporter.Program.ExportLibrary(LibraryRequirement requirement, String source, String outputRoot, Int32 atlasSize) in D:\a\Origins\Origins\tools\zircon-web-asset-exporter\Program.cs:line 134
   at ZirconWebAssetExporter.Program.Main(String[] args) in D:\a\Origins\Origins\tools\zircon-web-asset-exporter\Program.cs:line 53
```

## Boundary

- No real-import PASS is claimed until download, export and validation all succeed.
- No Crystal or placeholder art is substituted.
