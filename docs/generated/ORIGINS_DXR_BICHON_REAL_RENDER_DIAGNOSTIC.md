# ORIGINS-DxR — Bichon Real Render Diagnostic

- Gate: **PASS**
- HEAD: `d1f6b6df2830aab7c9bf5eed705a296ebffb3c45`

## Steps

- BOOTSTRAP: **success**
- DXT: **success**
- FETCH: **success**
- BUILD: **success**
- RENDER: **success**

## Fetch

- `Data/Map Data/Tilesc.Zl`: **READY**; bytes `33484507`
- `Data/Map Data/Tiles30c.Zl`: **READY**; bytes `2899880`
- `Data/Map Data/Housesc.Zl`: **READY**; bytes `29850809`
- `Data/Map Data/SmObjectsc.Zl`: **READY**; bytes `21322908`
- `Data/Map Data/Object2c.Zl`: **READY**; bytes `24844067`
- `Data/Map Data/Wood/Tilesc.Zl`: **READY**; bytes `80192342`
- `Data/Map Data/Wood/Housesc.Zl`: **READY**; bytes `21723636`
- `Data/Map Data/Wood/SmObjectsc.Zl`: **READY**; bytes `19811316`

## build.log

```text
  Determining projects to restore...
  Restored D:\a\Origins\Origins\vendor\zircon\RenderingCore\RenderingCore.csproj (in 4.65 sec).
  Restored D:\a\Origins\Origins\tools\zircon-map-renderer\ZirconMapRenderer.csproj (in 4.65 sec).
  Restored D:\a\Origins\Origins\vendor\zircon\LibraryEditor\LibraryEditor.csproj (in 4.65 sec).
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

Time Elapsed 00:00:17.30
```

## render.log

```text
    {
      "krOrder": 13,
      "sourcePath": "Data/Map Data/Object2c.Zl",
      "sha256": "38ED135FC8004906BAD3064DDE02FE6B145974F48709E64AA600ECA880BF38FA"
    },
    {
      "krOrder": 15,
      "sourcePath": "Data/Map Data/Wood/Tilesc.Zl",
      "sha256": "271A95A40A231D7F9423C5E1CA575A8D57274D4902C16E3D0E97F6A6D5E88BCA"
    },
    {
      "krOrder": 19,
      "sourcePath": "Data/Map Data/Wood/Housesc.Zl",
      "sha256": "DEC900A51AC90C2B1B07240575479CB42A6E48435D6D7D1D34A122DF2B653A40"
    },
    {
      "krOrder": 25,
      "sourcePath": "Data/Map Data/Wood/SmObjectsc.Zl",
      "sha256": "2DF57B433E494080A517FC031DDD1B6B8F2481FCCF93AC15C1C72CF86A04FA1D"
    }
  ],
  "renders": [
    {
      "name": "overview",
      "path": "D:/a/Origins/Origins/artifacts/bichon-real-render-diagnostic/bichon-cataclysm-real-overview.png",
      "x": 0,
      "y": 0,
      "widthCells": 350,
      "heightCells": 350,
      "scale": 0.2,
      "pixelWidth": 3360,
      "pixelHeight": 2240,
      "bytes": 3470212,
      "sha256": "B2DF858E57852D85151DC290CF0C0CF2A9233A0C328E5E67B5EABC524BEA6336"
    },
    {
      "name": "detail",
      "path": "D:/a/Origins/Origins/artifacts/bichon-real-render-diagnostic/bichon-cataclysm-real-detail.png",
      "x": 82,
      "y": 120,
      "widthCells": 196,
      "heightCells": 210,
      "scale": 0.45,
      "pixelWidth": 4234,
      "pixelHeight": 3024,
      "bytes": 14470411,
      "sha256": "36A3EAE91AD4755C9FDA261E622FA9B5F0BABF8455E10BA0EC945BC23C383DA1"
    }
  ]
}
```

## Render report

- Map SHA-256: `83C6D36556576FDFFFA343892F3205BF31BEE5C3AFEF81293D15A591728978A8`
- overview: **3360×2240**, `3470212` bytes, SHA `B2DF858E57852D85151DC290CF0C0CF2A9233A0C328E5E67B5EABC524BEA6336`
- detail: **4234×3024**, `14470411` bytes, SHA `36A3EAE91AD4755C9FDA261E622FA9B5F0BABF8455E10BA0EC945BC23C383DA1`
