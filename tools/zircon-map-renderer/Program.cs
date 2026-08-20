using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Security.Cryptography;
using System.Text.Json;
using LibraryEditor;

namespace ZirconMapRenderer;

internal static class Program
{
    private const int CellWidth = 48;
    private const int CellHeight = 32;

    private static readonly Dictionary<int, string> LibraryPaths = new()
    {
        [0] = @"Data\Map Data\Tilesc.Zl",
        [1] = @"Data\Map Data\Tiles30c.Zl",
        [2] = @"Data\Map Data\Tiles5c.Zl",
        [3] = @"Data\Map Data\SmTilesc.Zl",
        [4] = @"Data\Map Data\Housesc.Zl",
        [5] = @"Data\Map Data\Cliffsc.Zl",
        [6] = @"Data\Map Data\Dungeonsc.Zl",
        [7] = @"Data\Map Data\Innersc.Zl",
        [8] = @"Data\Map Data\Furnituresc.Zl",
        [9] = @"Data\Map Data\Wallsc.Zl",
        [10] = @"Data\Map Data\SmObjectsc.Zl",
        [11] = @"Data\Map Data\Animationsc.Zl",
        [12] = @"Data\Map Data\Object1c.Zl",
        [13] = @"Data\Map Data\Object2c.Zl",
    };

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            Options options = Options.Parse(args);
            NativeMap map = NativeMap.Load(options.MapPath);
            HashSet<int> used = map.GetUsedLibraryIds();
            foreach (int id in used)
                if (!LibraryPaths.ContainsKey(id))
                    throw new InvalidDataException($"Map uses unsupported KROrder library id {id}; renderer refuses to guess.");

            Dictionary<int, Mir3Library> libraries = new();
            try
            {
                foreach (int id in used.Order())
                {
                    string source = Path.GetFullPath(Path.Combine(options.SourceRoot, LibraryPaths[id]));
                    if (!File.Exists(source))
                        throw new FileNotFoundException($"Missing official Zircon map library id {id}: {source}", source);
                    libraries[id] = new Mir3Library(source);
                }

                Directory.CreateDirectory(options.OutputDirectory);

                var overview = new RenderSpec("overview", 0, 0, map.Width, map.Height, 0.20f);
                int detailX0 = Math.Max(0, 82);
                int detailY0 = Math.Max(0, 120);
                int detailX1 = Math.Min(map.Width, 278);
                int detailY1 = Math.Min(map.Height, 330);
                var detail = new RenderSpec("detail", detailX0, detailY0, detailX1 - detailX0, detailY1 - detailY0, 0.45f);

                List<RenderResult> renders = new();
                renders.Add(RenderMap(map, libraries, overview, Path.Combine(options.OutputDirectory, "bichon-cataclysm-real-overview.png")));
                renders.Add(RenderMap(map, libraries, detail, Path.Combine(options.OutputDirectory, "bichon-cataclysm-real-detail.png")));

                var report = new
                {
                    schema = "origins.zircon.native-map-render.v1",
                    status = "PASS",
                    map = new
                    {
                        path = options.MapPath.Replace('\\', '/'),
                        width = map.Width,
                        height = map.Height,
                        sha256 = Sha256(options.MapPath),
                        bytes = new FileInfo(options.MapPath).Length,
                    },
                    exactViewerSemantics = new
                    {
                        back = "x/y even only; draw BackImage at x*48,y*32",
                        middleFront = "same Y-major cell ordering as Zircon Server/Views/MapViewer.cs",
                        tallObjectAnchor = "drawY=(y+1)*32-height",
                        cellSizedAnchor = "drawY=y*32 for 48x32/96x64 assets",
                        useOffset = false,
                        animationFrame = 0,
                    },
                    libraries = used.Order().Select(id => new
                    {
                        krOrder = id,
                        sourcePath = LibraryPaths[id].Replace('\\', '/'),
                        sha256 = Sha256(Path.Combine(options.SourceRoot, LibraryPaths[id])),
                    }).ToArray(),
                    renders,
                };

                string reportPath = Path.Combine(options.OutputDirectory, "render-report.json");
                File.WriteAllText(reportPath, JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
                Console.WriteLine(JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
                return 0;
            }
            finally
            {
                foreach (Mir3Library library in libraries.Values)
                {
                    foreach (Mir3Library.Mir3Image? image in library.Images)
                        image?.Dispose();
                    library.Close();
                }
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            return 1;
        }
    }

    private static RenderResult RenderMap(NativeMap map, IReadOnlyDictionary<int, Mir3Library> libraries, RenderSpec spec, string outputPath)
    {
        int pixelWidth = Math.Max(1, (int)Math.Ceiling(spec.Width * CellWidth * spec.Scale));
        int pixelHeight = Math.Max(1, (int)Math.Ceiling(spec.Height * CellHeight * spec.Scale));

        using Bitmap canvas = new(pixelWidth, pixelHeight, PixelFormat.Format32bppArgb);
        using Graphics g = Graphics.FromImage(canvas);
        g.Clear(Color.Black);
        g.CompositingMode = CompositingMode.SourceOver;
        g.CompositingQuality = CompositingQuality.HighSpeed;
        g.InterpolationMode = InterpolationMode.NearestNeighbor;
        g.PixelOffsetMode = PixelOffsetMode.Half;
        g.SmoothingMode = SmoothingMode.None;

        int minX = Math.Max(0, spec.X - 1);
        int maxX = Math.Min(map.Width - 1, spec.X + spec.Width);
        int minY = Math.Max(0, spec.Y - 1);
        int maxYBack = Math.Min(map.Height - 1, spec.Y + spec.Height);

        for (int y = minY; y <= maxYBack; y++)
        {
            if ((y & 1) != 0) continue;
            for (int x = minX; x <= maxX; x++)
            {
                if ((x & 1) != 0) continue;
                Cell cell = map.Cells[x, y];
                DrawImage(g, libraries, cell.BackFile, cell.BackImage,
                    x * CellWidth, y * CellHeight, spec, false);
            }
        }

        int maxYObjects = Math.Min(map.Height - 1, spec.Y + spec.Height + 20);
        for (int y = minY; y <= maxYObjects; y++)
        {
            for (int x = minX; x <= maxX; x++)
            {
                Cell cell = map.Cells[x, y];
                DrawLayer(g, libraries, cell.MiddleFile, cell.MiddleImageRaw, cell.MiddleAnimationFrame,
                    x, y, spec);
                DrawLayer(g, libraries, cell.FrontFile, cell.FrontImageRaw, cell.FrontAnimationFrame,
                    x, y, spec);
            }
        }

        canvas.Save(outputPath, ImageFormat.Png);
        return new RenderResult(
            spec.Name,
            outputPath.Replace('\\', '/'),
            spec.X,
            spec.Y,
            spec.Width,
            spec.Height,
            spec.Scale,
            pixelWidth,
            pixelHeight,
            new FileInfo(outputPath).Length,
            Sha256(outputPath));
    }

    private static void DrawLayer(Graphics g, IReadOnlyDictionary<int, Mir3Library> libraries,
        int fileId, int index, int animationFrame, int cellX, int cellY, RenderSpec spec)
    {
        if (fileId == 0) return; // Zircon MapViewer skips Tilesc for middle/front.
        if (!libraries.TryGetValue(fileId, out Mir3Library? library)) return;

        Mir3Library.Mir3Image? image = library.GetImage(index);
        if (image?.Image is null || image.Width <= 0 || image.Height <= 0) return;

        int drawX = cellX * CellWidth;
        int drawY = (cellY + 1) * CellHeight;
        bool cellSized = (image.Width == CellWidth && image.Height == CellHeight) ||
                         (image.Width == CellWidth * 2 && image.Height == CellHeight * 2);
        drawY -= cellSized ? CellHeight : image.Height;
        bool blend = (animationFrame & 0x80) != 0;
        DrawBitmap(g, image.Image, drawX, drawY, spec, blend ? 0.5f : 1f);
    }

    private static void DrawImage(Graphics g, IReadOnlyDictionary<int, Mir3Library> libraries,
        int fileId, int index, int worldX, int worldY, RenderSpec spec, bool blend)
    {
        if (!libraries.TryGetValue(fileId, out Mir3Library? library)) return;
        Mir3Library.Mir3Image? image = library.GetImage(index);
        if (image?.Image is null || image.Width <= 0 || image.Height <= 0) return;
        DrawBitmap(g, image.Image, worldX, worldY, spec, blend ? 0.5f : 1f);
    }

    private static void DrawBitmap(Graphics g, Bitmap source, int worldX, int worldY, RenderSpec spec, float opacity)
    {
        float dx = (worldX - spec.X * CellWidth) * spec.Scale;
        float dy = (worldY - spec.Y * CellHeight) * spec.Scale;
        float dw = source.Width * spec.Scale;
        float dh = source.Height * spec.Scale;
        if (dx >= g.VisibleClipBounds.Right || dy >= g.VisibleClipBounds.Bottom || dx + dw <= 0 || dy + dh <= 0)
            return;

        RectangleF dest = new(dx, dy, dw, dh);
        if (opacity >= 0.999f)
        {
            g.DrawImage(source, dest, 0, 0, source.Width, source.Height, GraphicsUnit.Pixel);
            return;
        }

        using ImageAttributes attributes = new();
        ColorMatrix matrix = new() { Matrix33 = opacity };
        attributes.SetColorMatrix(matrix, ColorMatrixFlag.Default, ColorAdjustType.Bitmap);
        g.DrawImage(source, Rectangle.Round(dest), 0, 0, source.Width, source.Height, GraphicsUnit.Pixel, attributes);
    }

    private static string Sha256(string path)
    {
        using FileStream stream = File.OpenRead(path);
        using SHA256 sha = SHA256.Create();
        return Convert.ToHexString(sha.ComputeHash(stream));
    }
}

internal sealed record RenderSpec(string Name, int X, int Y, int Width, int Height, float Scale);
internal sealed record RenderResult(string name, string path, int x, int y, int widthCells, int heightCells, float scale,
    int pixelWidth, int pixelHeight, long bytes, string sha256);

internal sealed class Options
{
    public required string MapPath { get; init; }
    public required string SourceRoot { get; init; }
    public required string OutputDirectory { get; init; }

    public static Options Parse(string[] args)
    {
        string? map = null, root = null, output = null;
        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--map": map = args[++i]; break;
                case "--source-root": root = args[++i]; break;
                case "--output-dir": output = args[++i]; break;
                default: throw new ArgumentException($"Unknown argument: {args[i]}");
            }
        }
        if (string.IsNullOrWhiteSpace(map) || string.IsNullOrWhiteSpace(root) || string.IsNullOrWhiteSpace(output))
            throw new ArgumentException("Required: --map <0.map> --source-root <Zircon data root> --output-dir <directory>");
        return new Options { MapPath = Path.GetFullPath(map), SourceRoot = Path.GetFullPath(root), OutputDirectory = Path.GetFullPath(output) };
    }
}

internal sealed class NativeMap
{
    public required int Width { get; init; }
    public required int Height { get; init; }
    public required Cell[,] Cells { get; init; }

    public static NativeMap Load(string path)
    {
        byte[] bytes = File.ReadAllBytes(path);
        if (bytes.Length < 28) throw new InvalidDataException("Map is shorter than Zircon header.");
        int width = BitConverter.ToUInt16(bytes, 22);
        int height = BitConverter.ToUInt16(bytes, 24);
        int expected = 28 + width * height / 4 * 3 + width * height * 14;
        if (bytes.Length != expected)
            throw new InvalidDataException($"Unexpected native map length: {bytes.Length}, expected {expected} for {width}x{height}.");

        Cell[,] cells = new Cell[width, height];
        for (int x = 0; x < width; x++)
            for (int y = 0; y < height; y++)
                cells[x, y] = new Cell();

        int offset = 28;
        for (int x = 0; x < width / 2; x++)
        {
            for (int y = 0; y < height / 2; y++)
            {
                int cx = x * 2, cy = y * 2;
                cells[cx, cy].BackFile = bytes[offset];
                cells[cx, cy].BackImage = BitConverter.ToUInt16(bytes, offset + 1);
                offset += 3;
            }
        }

        for (int x = 0; x < width; x++)
        {
            for (int y = 0; y < height; y++)
            {
                Cell cell = cells[x, y];
                cell.FlagByte = bytes[offset];
                cell.MiddleAnimationFrame = bytes[offset + 1];
                cell.FrontAnimationFrame = bytes[offset + 2] == 255 ? 0 : bytes[offset + 2];
                cell.FrontFile = bytes[offset + 3];
                cell.MiddleFile = bytes[offset + 4];
                cell.MiddleImageRaw = BitConverter.ToUInt16(bytes, offset + 5);
                cell.FrontImageRaw = BitConverter.ToUInt16(bytes, offset + 7);
                cell.Light = (byte)(bytes[offset + 12] & 0x0F);
                offset += 14;
            }
        }
        return new NativeMap { Width = width, Height = height, Cells = cells };
    }

    public HashSet<int> GetUsedLibraryIds()
    {
        HashSet<int> ids = new();
        for (int x = 0; x < Width; x++)
        {
            for (int y = 0; y < Height; y++)
            {
                Cell c = Cells[x, y];
                if ((x & 1) == 0 && (y & 1) == 0) ids.Add(c.BackFile);
                if (c.MiddleFile != 0) ids.Add(c.MiddleFile);
                if (c.FrontFile != 0) ids.Add(c.FrontFile);
            }
        }
        return ids;
    }
}

internal sealed class Cell
{
    public int BackFile;
    public int BackImage;
    public int MiddleFile;
    public int MiddleImageRaw;
    public int FrontFile;
    public int FrontImageRaw;
    public int FrontAnimationFrame;
    public int MiddleAnimationFrame;
    public byte FlagByte;
    public byte Light;
}
