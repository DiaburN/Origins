# ORIGINS-DxR — M-Hum + WM-Hum Animation Coverage

- Coverage gate: **FAIL**
- Zircon authority: `cbf1aa919083bc13fc3f23f93772a8ab8370632d`
- Coverage commit: `8e5e3cd397013f910e07141728cd5517fafb5741`
- Source import run: **32392632203**
- Source preview commit: `cbe40cbde1efea9b9c0dd423a41b97607907851d`
- Animations audited: **42**
- Directions per animation: **8**
- Runtime-draw frame references checked: **3680**
- Missing runtime-draw references: **352**

## Native runtime semantics

- Player `Pushed`: pinned `MapObject.UpdateFrame()` forces local frame(s) **[0]**.
- Fishing body draw: `Client/Models/PlayerObject.cs DrawBody: BodyLibrary.GetImage(ArmourFrame)`.
- Normal W/W/T body bank offset: **5000**; banks per `.Zl`: **11**.

## Per-animation result

| Animation | Source Frames | Runtime Local Frames | References M+F / 8 dirs | Missing | Result |
|---|---:|---:|---:|---:|---|
| Standing | 4 | 4 | 64 | 0 | PASS |
| Walking | 6 | 6 | 96 | 0 | PASS |
| Running | 6 | 6 | 96 | 0 | PASS |
| CreepStanding | 4 | 4 | 64 | 0 | PASS |
| CreepWalkFast | 6 | 6 | 96 | 0 | PASS |
| CreepWalkSlow | 6 | 6 | 96 | 0 | PASS |
| Pushed | 6 | 1 | 16 | 0 | PASS |
| Stance | 3 | 3 | 48 | 0 | PASS |
| Harvest | 2 | 2 | 32 | 0 | PASS |
| Combat1 | 5 | 5 | 80 | 0 | PASS |
| Combat2 | 5 | 5 | 80 | 0 | PASS |
| Combat3 | 6 | 6 | 96 | 0 | PASS |
| Combat4 | 6 | 6 | 96 | 0 | PASS |
| Combat5 | 10 | 10 | 160 | 0 | PASS |
| Combat6 | 10 | 10 | 160 | 0 | PASS |
| Combat7 | 10 | 10 | 160 | 0 | PASS |
| Combat8 | 6 | 6 | 96 | 0 | PASS |
| Combat9 | 10 | 10 | 160 | 0 | PASS |
| Combat10 | 10 | 10 | 160 | 0 | PASS |
| Combat11 | 10 | 10 | 160 | 0 | PASS |
| Combat12 | 10 | 10 | 160 | 0 | PASS |
| Combat13 | 6 | 6 | 96 | 0 | PASS |
| Combat14 | 8 | 8 | 128 | 0 | PASS |
| Combat15 | 3 | 3 | 48 | 0 | PASS |
| DragonRepulseStart | 6 | 6 | 96 | 0 | PASS |
| DragonRepulseMiddle | 1 | 1 | 16 | 0 | PASS |
| DragonRepulseEnd | 2 | 2 | 32 | 0 | PASS |
| Struck | 3 | 3 | 48 | 0 | PASS |
| Die | 10 | 10 | 160 | 0 | PASS |
| Dead | 1 | 1 | 16 | 0 | PASS |
| FishingCast | 8 | 8 | 128 | 128 | FAIL |
| FishingWait | 6 | 6 | 96 | 96 | FAIL |
| FishingReel | 8 | 8 | 128 | 128 | FAIL |
| HorseStanding | 4 | 4 | 64 | 0 | PASS |
| HorseWalking | 6 | 6 | 96 | 0 | PASS |
| HorseRunning | 6 | 6 | 96 | 0 | PASS |
| HorseStruck | 3 | 3 | 48 | 0 | PASS |
| ChannellingStart | 4 | 4 | 64 | 0 | PASS |
| ChannellingMiddle | 1 | 1 | 16 | 0 | PASS |
| ChannellingEnd | 1 | 1 | 16 | 0 | PASS |
| TamingCast | 6 | 6 | 96 | 0 | PASS |
| TamingWait | 1 | 1 | 16 | 0 | PASS |

## Fishing coverage across the 11 internal body-shape banks

| Library | ArmourShape % 11 | Shift | References | Missing | Result |
|---|---:|---:|---:|---:|---|
| M_Hum | 0 | 0 | 176 | 176 | EMPTY |
| M_Hum | 1 | 5000 | 176 | 176 | EMPTY |
| M_Hum | 2 | 10000 | 176 | 176 | EMPTY |
| M_Hum | 3 | 15000 | 176 | 176 | EMPTY |
| M_Hum | 4 | 20000 | 176 | 176 | EMPTY |
| M_Hum | 5 | 25000 | 176 | 0 | PASS |
| M_Hum | 6 | 30000 | 176 | 176 | EMPTY |
| M_Hum | 7 | 35000 | 176 | 176 | EMPTY |
| M_Hum | 8 | 40000 | 176 | 176 | EMPTY |
| M_Hum | 9 | 45000 | 176 | 176 | EMPTY |
| M_Hum | 10 | 50000 | 176 | 176 | EMPTY |
| WM_Hum | 0 | 0 | 176 | 176 | EMPTY |
| WM_Hum | 1 | 5000 | 176 | 176 | EMPTY |
| WM_Hum | 2 | 10000 | 176 | 176 | EMPTY |
| WM_Hum | 3 | 15000 | 176 | 176 | EMPTY |
| WM_Hum | 4 | 20000 | 176 | 176 | EMPTY |
| WM_Hum | 5 | 25000 | 176 | 176 | EMPTY |
| WM_Hum | 6 | 30000 | 176 | 176 | EMPTY |
| WM_Hum | 7 | 35000 | 176 | 176 | EMPTY |
| WM_Hum | 8 | 40000 | 176 | 176 | EMPTY |
| WM_Hum | 9 | 45000 | 176 | 176 | EMPTY |
| WM_Hum | 10 | 50000 | 176 | 176 | EMPTY |

## Missing runtime-draw references

- `M_Hum` / `FishingCast` / dir 0 / local 0 → index **2000**
- `M_Hum` / `FishingCast` / dir 0 / local 1 → index **2001**
- `M_Hum` / `FishingCast` / dir 0 / local 2 → index **2002**
- `M_Hum` / `FishingCast` / dir 0 / local 3 → index **2003**
- `M_Hum` / `FishingCast` / dir 0 / local 4 → index **2004**
- `M_Hum` / `FishingCast` / dir 0 / local 5 → index **2005**
- `M_Hum` / `FishingCast` / dir 0 / local 6 → index **2006**
- `M_Hum` / `FishingCast` / dir 0 / local 7 → index **2007**
- `M_Hum` / `FishingCast` / dir 1 / local 0 → index **2010**
- `M_Hum` / `FishingCast` / dir 1 / local 1 → index **2011**
- `M_Hum` / `FishingCast` / dir 1 / local 2 → index **2012**
- `M_Hum` / `FishingCast` / dir 1 / local 3 → index **2013**
- `M_Hum` / `FishingCast` / dir 1 / local 4 → index **2014**
- `M_Hum` / `FishingCast` / dir 1 / local 5 → index **2015**
- `M_Hum` / `FishingCast` / dir 1 / local 6 → index **2016**
- `M_Hum` / `FishingCast` / dir 1 / local 7 → index **2017**
- `M_Hum` / `FishingCast` / dir 2 / local 0 → index **2020**
- `M_Hum` / `FishingCast` / dir 2 / local 1 → index **2021**
- `M_Hum` / `FishingCast` / dir 2 / local 2 → index **2022**
- `M_Hum` / `FishingCast` / dir 2 / local 3 → index **2023**
- `M_Hum` / `FishingCast` / dir 2 / local 4 → index **2024**
- `M_Hum` / `FishingCast` / dir 2 / local 5 → index **2025**
- `M_Hum` / `FishingCast` / dir 2 / local 6 → index **2026**
- `M_Hum` / `FishingCast` / dir 2 / local 7 → index **2027**
- `M_Hum` / `FishingCast` / dir 3 / local 0 → index **2030**
- `M_Hum` / `FishingCast` / dir 3 / local 1 → index **2031**
- `M_Hum` / `FishingCast` / dir 3 / local 2 → index **2032**
- `M_Hum` / `FishingCast` / dir 3 / local 3 → index **2033**
- `M_Hum` / `FishingCast` / dir 3 / local 4 → index **2034**
- `M_Hum` / `FishingCast` / dir 3 / local 5 → index **2035**
- `M_Hum` / `FishingCast` / dir 3 / local 6 → index **2036**
- `M_Hum` / `FishingCast` / dir 3 / local 7 → index **2037**
- `M_Hum` / `FishingCast` / dir 4 / local 0 → index **2040**
- `M_Hum` / `FishingCast` / dir 4 / local 1 → index **2041**
- `M_Hum` / `FishingCast` / dir 4 / local 2 → index **2042**
- `M_Hum` / `FishingCast` / dir 4 / local 3 → index **2043**
- `M_Hum` / `FishingCast` / dir 4 / local 4 → index **2044**
- `M_Hum` / `FishingCast` / dir 4 / local 5 → index **2045**
- `M_Hum` / `FishingCast` / dir 4 / local 6 → index **2046**
- `M_Hum` / `FishingCast` / dir 4 / local 7 → index **2047**
- `M_Hum` / `FishingCast` / dir 5 / local 0 → index **2050**
- `M_Hum` / `FishingCast` / dir 5 / local 1 → index **2051**
- `M_Hum` / `FishingCast` / dir 5 / local 2 → index **2052**
- `M_Hum` / `FishingCast` / dir 5 / local 3 → index **2053**
- `M_Hum` / `FishingCast` / dir 5 / local 4 → index **2054**
- `M_Hum` / `FishingCast` / dir 5 / local 5 → index **2055**
- `M_Hum` / `FishingCast` / dir 5 / local 6 → index **2056**
- `M_Hum` / `FishingCast` / dir 5 / local 7 → index **2057**
- `M_Hum` / `FishingCast` / dir 6 / local 0 → index **2060**
- `M_Hum` / `FishingCast` / dir 6 / local 1 → index **2061**
- `M_Hum` / `FishingCast` / dir 6 / local 2 → index **2062**
- `M_Hum` / `FishingCast` / dir 6 / local 3 → index **2063**
- `M_Hum` / `FishingCast` / dir 6 / local 4 → index **2064**
- `M_Hum` / `FishingCast` / dir 6 / local 5 → index **2065**
- `M_Hum` / `FishingCast` / dir 6 / local 6 → index **2066**
- `M_Hum` / `FishingCast` / dir 6 / local 7 → index **2067**
- `M_Hum` / `FishingCast` / dir 7 / local 0 → index **2070**
- `M_Hum` / `FishingCast` / dir 7 / local 1 → index **2071**
- `M_Hum` / `FishingCast` / dir 7 / local 2 → index **2072**
- `M_Hum` / `FishingCast` / dir 7 / local 3 → index **2073**
- `M_Hum` / `FishingCast` / dir 7 / local 4 → index **2074**
- `M_Hum` / `FishingCast` / dir 7 / local 5 → index **2075**
- `M_Hum` / `FishingCast` / dir 7 / local 6 → index **2076**
- `M_Hum` / `FishingCast` / dir 7 / local 7 → index **2077**
- `WM_Hum` / `FishingCast` / dir 0 / local 0 → index **2000**
- `WM_Hum` / `FishingCast` / dir 0 / local 1 → index **2001**
- `WM_Hum` / `FishingCast` / dir 0 / local 2 → index **2002**
- `WM_Hum` / `FishingCast` / dir 0 / local 3 → index **2003**
- `WM_Hum` / `FishingCast` / dir 0 / local 4 → index **2004**
- `WM_Hum` / `FishingCast` / dir 0 / local 5 → index **2005**
- `WM_Hum` / `FishingCast` / dir 0 / local 6 → index **2006**
- `WM_Hum` / `FishingCast` / dir 0 / local 7 → index **2007**
- `WM_Hum` / `FishingCast` / dir 1 / local 0 → index **2010**
- `WM_Hum` / `FishingCast` / dir 1 / local 1 → index **2011**
- `WM_Hum` / `FishingCast` / dir 1 / local 2 → index **2012**
- `WM_Hum` / `FishingCast` / dir 1 / local 3 → index **2013**
- `WM_Hum` / `FishingCast` / dir 1 / local 4 → index **2014**
- `WM_Hum` / `FishingCast` / dir 1 / local 5 → index **2015**
- `WM_Hum` / `FishingCast` / dir 1 / local 6 → index **2016**
- `WM_Hum` / `FishingCast` / dir 1 / local 7 → index **2017**
- `WM_Hum` / `FishingCast` / dir 2 / local 0 → index **2020**
- `WM_Hum` / `FishingCast` / dir 2 / local 1 → index **2021**
- `WM_Hum` / `FishingCast` / dir 2 / local 2 → index **2022**
- `WM_Hum` / `FishingCast` / dir 2 / local 3 → index **2023**
- `WM_Hum` / `FishingCast` / dir 2 / local 4 → index **2024**
- `WM_Hum` / `FishingCast` / dir 2 / local 5 → index **2025**
- `WM_Hum` / `FishingCast` / dir 2 / local 6 → index **2026**
- `WM_Hum` / `FishingCast` / dir 2 / local 7 → index **2027**
- `WM_Hum` / `FishingCast` / dir 3 / local 0 → index **2030**
- `WM_Hum` / `FishingCast` / dir 3 / local 1 → index **2031**
- `WM_Hum` / `FishingCast` / dir 3 / local 2 → index **2032**
- `WM_Hum` / `FishingCast` / dir 3 / local 3 → index **2033**
- `WM_Hum` / `FishingCast` / dir 3 / local 4 → index **2034**
- `WM_Hum` / `FishingCast` / dir 3 / local 5 → index **2035**
- `WM_Hum` / `FishingCast` / dir 3 / local 6 → index **2036**
- `WM_Hum` / `FishingCast` / dir 3 / local 7 → index **2037**
- `WM_Hum` / `FishingCast` / dir 4 / local 0 → index **2040**
- `WM_Hum` / `FishingCast` / dir 4 / local 1 → index **2041**
- `WM_Hum` / `FishingCast` / dir 4 / local 2 → index **2042**
- `WM_Hum` / `FishingCast` / dir 4 / local 3 → index **2043**
- `WM_Hum` / `FishingCast` / dir 4 / local 4 → index **2044**
- `WM_Hum` / `FishingCast` / dir 4 / local 5 → index **2045**
- `WM_Hum` / `FishingCast` / dir 4 / local 6 → index **2046**
- `WM_Hum` / `FishingCast` / dir 4 / local 7 → index **2047**
- `WM_Hum` / `FishingCast` / dir 5 / local 0 → index **2050**
- `WM_Hum` / `FishingCast` / dir 5 / local 1 → index **2051**
- `WM_Hum` / `FishingCast` / dir 5 / local 2 → index **2052**
- `WM_Hum` / `FishingCast` / dir 5 / local 3 → index **2053**
- `WM_Hum` / `FishingCast` / dir 5 / local 4 → index **2054**
- `WM_Hum` / `FishingCast` / dir 5 / local 5 → index **2055**
- `WM_Hum` / `FishingCast` / dir 5 / local 6 → index **2056**
- `WM_Hum` / `FishingCast` / dir 5 / local 7 → index **2057**
- `WM_Hum` / `FishingCast` / dir 6 / local 0 → index **2060**
- `WM_Hum` / `FishingCast` / dir 6 / local 1 → index **2061**
- `WM_Hum` / `FishingCast` / dir 6 / local 2 → index **2062**
- `WM_Hum` / `FishingCast` / dir 6 / local 3 → index **2063**
- `WM_Hum` / `FishingCast` / dir 6 / local 4 → index **2064**
- `WM_Hum` / `FishingCast` / dir 6 / local 5 → index **2065**
- `WM_Hum` / `FishingCast` / dir 6 / local 6 → index **2066**
- `WM_Hum` / `FishingCast` / dir 6 / local 7 → index **2067**
- `WM_Hum` / `FishingCast` / dir 7 / local 0 → index **2070**
- `WM_Hum` / `FishingCast` / dir 7 / local 1 → index **2071**
- `WM_Hum` / `FishingCast` / dir 7 / local 2 → index **2072**
- `WM_Hum` / `FishingCast` / dir 7 / local 3 → index **2073**
- `WM_Hum` / `FishingCast` / dir 7 / local 4 → index **2074**
- `WM_Hum` / `FishingCast` / dir 7 / local 5 → index **2075**
- `WM_Hum` / `FishingCast` / dir 7 / local 6 → index **2076**
- `WM_Hum` / `FishingCast` / dir 7 / local 7 → index **2077**
- `M_Hum` / `FishingWait` / dir 0 / local 0 → index **2080**
- `M_Hum` / `FishingWait` / dir 0 / local 1 → index **2081**
- `M_Hum` / `FishingWait` / dir 0 / local 2 → index **2082**
- `M_Hum` / `FishingWait` / dir 0 / local 3 → index **2083**
- `M_Hum` / `FishingWait` / dir 0 / local 4 → index **2084**
- `M_Hum` / `FishingWait` / dir 0 / local 5 → index **2085**
- `M_Hum` / `FishingWait` / dir 1 / local 0 → index **2090**
- `M_Hum` / `FishingWait` / dir 1 / local 1 → index **2091**
- `M_Hum` / `FishingWait` / dir 1 / local 2 → index **2092**
- `M_Hum` / `FishingWait` / dir 1 / local 3 → index **2093**
- `M_Hum` / `FishingWait` / dir 1 / local 4 → index **2094**
- `M_Hum` / `FishingWait` / dir 1 / local 5 → index **2095**
- `M_Hum` / `FishingWait` / dir 2 / local 0 → index **2100**
- `M_Hum` / `FishingWait` / dir 2 / local 1 → index **2101**
- `M_Hum` / `FishingWait` / dir 2 / local 2 → index **2102**
- `M_Hum` / `FishingWait` / dir 2 / local 3 → index **2103**
- `M_Hum` / `FishingWait` / dir 2 / local 4 → index **2104**
- `M_Hum` / `FishingWait` / dir 2 / local 5 → index **2105**
- `M_Hum` / `FishingWait` / dir 3 / local 0 → index **2110**
- `M_Hum` / `FishingWait` / dir 3 / local 1 → index **2111**
- `M_Hum` / `FishingWait` / dir 3 / local 2 → index **2112**
- `M_Hum` / `FishingWait` / dir 3 / local 3 → index **2113**
- `M_Hum` / `FishingWait` / dir 3 / local 4 → index **2114**
- `M_Hum` / `FishingWait` / dir 3 / local 5 → index **2115**
- `M_Hum` / `FishingWait` / dir 4 / local 0 → index **2120**
- `M_Hum` / `FishingWait` / dir 4 / local 1 → index **2121**
- `M_Hum` / `FishingWait` / dir 4 / local 2 → index **2122**
- `M_Hum` / `FishingWait` / dir 4 / local 3 → index **2123**
- `M_Hum` / `FishingWait` / dir 4 / local 4 → index **2124**
- `M_Hum` / `FishingWait` / dir 4 / local 5 → index **2125**
- `M_Hum` / `FishingWait` / dir 5 / local 0 → index **2130**
- `M_Hum` / `FishingWait` / dir 5 / local 1 → index **2131**
- `M_Hum` / `FishingWait` / dir 5 / local 2 → index **2132**
- `M_Hum` / `FishingWait` / dir 5 / local 3 → index **2133**
- `M_Hum` / `FishingWait` / dir 5 / local 4 → index **2134**
- `M_Hum` / `FishingWait` / dir 5 / local 5 → index **2135**
- `M_Hum` / `FishingWait` / dir 6 / local 0 → index **2140**
- `M_Hum` / `FishingWait` / dir 6 / local 1 → index **2141**
- `M_Hum` / `FishingWait` / dir 6 / local 2 → index **2142**
- `M_Hum` / `FishingWait` / dir 6 / local 3 → index **2143**
- `M_Hum` / `FishingWait` / dir 6 / local 4 → index **2144**
- `M_Hum` / `FishingWait` / dir 6 / local 5 → index **2145**
- `M_Hum` / `FishingWait` / dir 7 / local 0 → index **2150**
- `M_Hum` / `FishingWait` / dir 7 / local 1 → index **2151**
- `M_Hum` / `FishingWait` / dir 7 / local 2 → index **2152**
- `M_Hum` / `FishingWait` / dir 7 / local 3 → index **2153**
- `M_Hum` / `FishingWait` / dir 7 / local 4 → index **2154**
- `M_Hum` / `FishingWait` / dir 7 / local 5 → index **2155**
- `WM_Hum` / `FishingWait` / dir 0 / local 0 → index **2080**
- `WM_Hum` / `FishingWait` / dir 0 / local 1 → index **2081**
- `WM_Hum` / `FishingWait` / dir 0 / local 2 → index **2082**
- `WM_Hum` / `FishingWait` / dir 0 / local 3 → index **2083**
- `WM_Hum` / `FishingWait` / dir 0 / local 4 → index **2084**
- `WM_Hum` / `FishingWait` / dir 0 / local 5 → index **2085**
- `WM_Hum` / `FishingWait` / dir 1 / local 0 → index **2090**
- `WM_Hum` / `FishingWait` / dir 1 / local 1 → index **2091**
- `WM_Hum` / `FishingWait` / dir 1 / local 2 → index **2092**
- `WM_Hum` / `FishingWait` / dir 1 / local 3 → index **2093**
- `WM_Hum` / `FishingWait` / dir 1 / local 4 → index **2094**
- `WM_Hum` / `FishingWait` / dir 1 / local 5 → index **2095**
- `WM_Hum` / `FishingWait` / dir 2 / local 0 → index **2100**
- `WM_Hum` / `FishingWait` / dir 2 / local 1 → index **2101**
- `WM_Hum` / `FishingWait` / dir 2 / local 2 → index **2102**
- `WM_Hum` / `FishingWait` / dir 2 / local 3 → index **2103**
- `WM_Hum` / `FishingWait` / dir 2 / local 4 → index **2104**
- `WM_Hum` / `FishingWait` / dir 2 / local 5 → index **2105**
- `WM_Hum` / `FishingWait` / dir 3 / local 0 → index **2110**
- `WM_Hum` / `FishingWait` / dir 3 / local 1 → index **2111**
- `WM_Hum` / `FishingWait` / dir 3 / local 2 → index **2112**
- `WM_Hum` / `FishingWait` / dir 3 / local 3 → index **2113**
- `WM_Hum` / `FishingWait` / dir 3 / local 4 → index **2114**
- `WM_Hum` / `FishingWait` / dir 3 / local 5 → index **2115**
- … 152 additional missing references are in the JSON artifact.

## Boundary

- `Pushed` is evaluated using the exact pinned Zircon player special case, not by requiring unused source-frame slots.
- Fishing is not waived: the report probes the actual `BodyLibrary/ArmourFrame` banks used by Zircon so empty source banks remain visible as evidence.
- PASS means every body frame that the pinned Zircon player runtime can actually request from base bank 0 exists for both genders.
- No Crystal or placeholder frames are accepted.
