using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Security.Cryptography;
using System.Text.Json;
using LibraryEditor;

namespace ZirconWebAssetExporter;

internal static class Program
{
    private const string Schema = "origins.zircon.web-atlas.v1";

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            Options options = Options.Parse(args);
            Contract contract = Contract.Load(options.ContractPath);

            if (options.Probe)
            {
                ProbeResult probe = ProbeResult.Build(contract, options.SourceRoot);
                string json = JsonSerializer.Serialize(probe, JsonOptions.Pretty);
                if (options.ReportPath is not null)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(options.ReportPath))!);
                    File.WriteAllText(options.ReportPath, json + Environment.NewLine);
                }
                Console.WriteLine(json);
                return 0;
            }

            if (options.OutputRoot is null)
                throw new ArgumentException("--output-root is required when exporting.");

            List<LibraryRequirement> selected = SelectLibraries(contract, options);
            if (selected.Count == 0)
                throw new ArgumentException("Select --all-player-libraries or at least one --library <LibraryFile>.");

            Directory.CreateDirectory(options.OutputRoot);
            List<MasterLibraryEntry> master = new();

            foreach (LibraryRequirement requirement in selected)
            {
                string source = ResolveSource(options.SourceRoot, requirement.SourcePath);
                if (!File.Exists(source))
                    throw new FileNotFoundException($"Required Zircon library is missing: {requirement.LibraryFile} -> {source}", source);

                Console.WriteLine($"Exporting {requirement.LibraryFile}: {source}");
                LibraryManifest manifest = ExportLibrary(requirement, source, options.OutputRoot, options.AtlasSize);
                master.Add(new MasterLibraryEntry
                {
                    LibraryFile = requirement.LibraryFile,
                    Manifest = $"{requirement.LibraryFile}/manifest.json",
                    ImageCount = manifest.ImageCount,
                    ExportedImageCount = manifest.ExportedImageCount,
                });
            }

            MasterManifest masterManifest = new()
            {
                Schema = Schema,
                ZirconCommit = contract.ZirconCommit,
                AtlasSize = options.AtlasSize,
                Libraries = master,
            };
            File.WriteAllText(
                Path.Combine(options.OutputRoot, "player-assets.json"),
                JsonSerializer.Serialize(masterManifest, JsonOptions.Pretty) + Environment.NewLine);

            Console.WriteLine($"Export complete: {master.Count} player libraries -> {options.OutputRoot}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.ToString());
            return 1;
        }
    }

    private static List<LibraryRequirement> SelectLibraries(Contract contract, Options options)
    {
        if (options.AllPlayerLibraries)
            return contract.PlayerLibraries.ToList();

        HashSet<string> requested = new(options.Libraries, StringComparer.OrdinalIgnoreCase);
        List<LibraryRequirement> selected = contract.PlayerLibraries
            .Where(row => requested.Contains(row.LibraryFile))
            .ToList();

        foreach (string name in requested)
        {
            if (selected.All(row => !row.LibraryFile.Equals(name, StringComparison.OrdinalIgnoreCase)))
                throw new ArgumentException($"Unknown player LibraryFile in contract: {name}");
        }
        return selected;
    }

    private static string ResolveSource(string sourceRoot, string contractPath)
    {
        string normalized = contractPath.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
        return Path.GetFullPath(Path.Combine(sourceRoot, normalized));
    }

    private static LibraryManifest ExportLibrary(
        LibraryRequirement requirement,
        string source,
        string outputRoot,
        int atlasSize)
    {
        string libraryOutput = Path.Combine(outputRoot, requirement.LibraryFile);
        if (Directory.Exists(libraryOutput)) Directory.Delete(libraryOutput, true);
        Directory.CreateDirectory(libraryOutput);

        Mir3Library library = new(source);
        try
        {
            LibraryManifest manifest = new()
            {
                Schema = Schema,
                LibraryFile = requirement.LibraryFile,
                SourcePath = requirement.SourcePath,
                SourceFileName = Path.GetFileName(source),
                SourceSha256 = FileSha256(source),
                LibraryVersion = library.Version,
                ImageCount = library.Images.Count,
                AtlasSize = atlasSize,
                Images = new FrameRecord?[library.Images.Count],
            };

            using AtlasWriter atlas = new(libraryOutput, atlasSize);
            for (int index = 0; index < library.Images.Count; index++)
            {
                Mir3Library.Mir3Image? image = library.GetImage(index);
                if (image?.Image is null || image.Width <= 0 || image.Height <= 0)
                    continue;

                AtlasPlacement placement = atlas.Place(image.Image);
                manifest.Images[index] = new FrameRecord
                {
                    Index = index,
                    Page = placement.Page,
                    X = placement.X,
                    Y = placement.Y,
                    Width = image.Width,
                    Height = image.Height,
                    OffsetX = image.OffSetX,
                    OffsetY = image.OffSetY,
                };
                manifest.ExportedImageCount++;
            }
            atlas.Flush();
            manifest.Pages = atlas.Pages.ToList();

            File.WriteAllText(
                Path.Combine(libraryOutput, "manifest.json"),
                JsonSerializer.Serialize(manifest, JsonOptions.Pretty) + Environment.NewLine);
            return manifest;
        }
        finally
        {
            foreach (Mir3Library.Mir3Image? image in library.Images)
                image?.Dispose();
            library.Close();
        }
    }

    private static string FileSha256(string path)
    {
        using FileStream stream = File.OpenRead(path);
        using SHA256 sha = SHA256.Create();
        return Convert.ToHexString(sha.ComputeHash(stream));
    }
}

internal sealed class AtlasWriter : IDisposable
{
    private readonly string _directory;
    private readonly int _size;
    private Bitmap? _bitmap;
    private Graphics? _graphics;
    private int _pageIndex;
    private int _x;
    private int _y;
    private int _rowHeight;
    private bool _dirty;

    public IReadOnlyList<string> Pages => _pages;
    private readonly List<string> _pages = new();

    public AtlasWriter(string directory, int size)
    {
        _directory = directory;
        _size = size;
        StartPage();
    }

    public AtlasPlacement Place(Bitmap source)
    {
        if (source.Width > _size || source.Height > _size)
            throw new InvalidDataException($"Image {source.Width}x{source.Height} exceeds atlas page {_size}x{_size}.");

        if (_x + source.Width > _size)
        {
            _x = 0;
            _y += _rowHeight;
            _rowHeight = 0;
        }

        if (_y + source.Height > _size)
        {
            SaveCurrentPage();
            _pageIndex++;
            StartPage();
        }

        int x = _x;
        int y = _y;
        _graphics!.DrawImageUnscaled(source, x, y);
        _dirty = true;

        _x += source.Width;
        _rowHeight = Math.Max(_rowHeight, source.Height);
        return new AtlasPlacement($"page_{_pageIndex:000}.png", x, y);
    }

    public void Flush() => SaveCurrentPage();

    private void StartPage()
    {
        _bitmap?.Dispose();
        _graphics?.Dispose();
        _bitmap = new Bitmap(_size, _size, PixelFormat.Format32bppArgb);
        _graphics = Graphics.FromImage(_bitmap);
        _graphics.CompositingMode = CompositingMode.SourceCopy;
        _graphics.InterpolationMode = InterpolationMode.NearestNeighbor;
        _graphics.PixelOffsetMode = PixelOffsetMode.Half;
        _graphics.Clear(Color.Transparent);
        _x = 0;
        _y = 0;
        _rowHeight = 0;
        _dirty = false;
    }

    private void SaveCurrentPage()
    {
        if (!_dirty || _bitmap is null) return;
        string name = $"page_{_pageIndex:000}.png";
        _bitmap.Save(Path.Combine(_directory, name), ImageFormat.Png);
        if (!_pages.Contains(name, StringComparer.Ordinal)) _pages.Add(name);
        _dirty = false;
    }

    public void Dispose()
    {
        SaveCurrentPage();
        _graphics?.Dispose();
        _bitmap?.Dispose();
    }
}

internal readonly record struct AtlasPlacement(string Page, int X, int Y);

internal sealed class Options
{
    public required string ContractPath { get; init; }
    public required string SourceRoot { get; init; }
    public string? OutputRoot { get; init; }
    public string? ReportPath { get; init; }
    public int AtlasSize { get; init; } = 2048;
    public bool Probe { get; init; }
    public bool AllPlayerLibraries { get; init; }
    public List<string> Libraries { get; init; } = new();

    public static Options Parse(string[] args)
    {
        string? contract = null;
        string? sourceRoot = null;
        string? outputRoot = null;
        string? report = null;
        int atlasSize = 2048;
        bool probe = false;
        bool all = false;
        List<string> libraries = new();

        for (int i = 0; i < args.Length; i++)
        {
            string arg = args[i];
            string NeedValue()
            {
                if (++i >= args.Length) throw new ArgumentException($"Missing value after {arg}");
                return args[i];
            }

            switch (arg)
            {
                case "--contract": contract = NeedValue(); break;
                case "--source-root": sourceRoot = NeedValue(); break;
                case "--output-root": outputRoot = NeedValue(); break;
                case "--report": report = NeedValue(); break;
                case "--atlas-size": atlasSize = int.Parse(NeedValue()); break;
                case "--library": libraries.Add(NeedValue()); break;
                case "--all-player-libraries": all = true; break;
                case "--probe": probe = true; break;
                default: throw new ArgumentException($"Unknown argument: {arg}");
            }
        }

        if (string.IsNullOrWhiteSpace(contract)) throw new ArgumentException("--contract is required.");
        if (string.IsNullOrWhiteSpace(sourceRoot)) throw new ArgumentException("--source-root is required.");
        if (atlasSize is < 256 or > 8192) throw new ArgumentOutOfRangeException(nameof(atlasSize));

        return new Options
        {
            ContractPath = Path.GetFullPath(contract),
            SourceRoot = Path.GetFullPath(sourceRoot),
            OutputRoot = outputRoot is null ? null : Path.GetFullPath(outputRoot),
            ReportPath = report is null ? null : Path.GetFullPath(report),
            AtlasSize = atlasSize,
            Probe = probe,
            AllPlayerLibraries = all,
            Libraries = libraries,
        };
    }
}

internal sealed class Contract
{
    public string ZirconCommit { get; set; } = string.Empty;
    public List<LibraryRequirement> PlayerLibraries { get; set; } = new();

    public static Contract Load(string path)
    {
        Contract? contract = JsonSerializer.Deserialize<Contract>(
            File.ReadAllText(path), JsonOptions.CaseInsensitive);
        if (contract is null || contract.PlayerLibraries.Count == 0)
            throw new InvalidDataException($"Invalid player asset contract: {path}");
        return contract;
    }
}

internal sealed class LibraryRequirement
{
    public string LibraryFile { get; set; } = string.Empty;
    public string SourcePath { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
}

internal sealed class ProbeResult
{
    public string Schema { get; set; } = "origins.zircon.web-asset-probe.v1";
    public string ZirconCommit { get; set; } = string.Empty;
    public string SourceRoot { get; set; } = string.Empty;
    public int Required { get; set; }
    public int Present { get; set; }
    public int Missing { get; set; }
    public string Status { get; set; } = string.Empty;
    public List<ProbeLibrary> Libraries { get; set; } = new();

    public static ProbeResult Build(Contract contract, string sourceRoot)
    {
        ProbeResult result = new()
        {
            ZirconCommit = contract.ZirconCommit,
            SourceRoot = Path.GetFullPath(sourceRoot),
            Required = contract.PlayerLibraries.Count,
        };
        foreach (LibraryRequirement requirement in contract.PlayerLibraries)
        {
            string fullPath = Path.GetFullPath(Path.Combine(
                sourceRoot,
                requirement.SourcePath.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar)));
            bool present = File.Exists(fullPath);
            result.Libraries.Add(new ProbeLibrary
            {
                LibraryFile = requirement.LibraryFile,
                SourcePath = requirement.SourcePath,
                Present = present,
            });
            if (present) result.Present++;
            else result.Missing++;
        }
        result.Status = result.Missing == 0 ? "READY" : "BLOCKED_MISSING_ZL";
        return result;
    }
}

internal sealed class ProbeLibrary
{
    public string LibraryFile { get; set; } = string.Empty;
    public string SourcePath { get; set; } = string.Empty;
    public bool Present { get; set; }
}

internal sealed class LibraryManifest
{
    public string Schema { get; set; } = string.Empty;
    public string LibraryFile { get; set; } = string.Empty;
    public string SourcePath { get; set; } = string.Empty;
    public string SourceFileName { get; set; } = string.Empty;
    public string SourceSha256 { get; set; } = string.Empty;
    public int LibraryVersion { get; set; }
    public int ImageCount { get; set; }
    public int ExportedImageCount { get; set; }
    public int AtlasSize { get; set; }
    public List<string> Pages { get; set; } = new();
    public FrameRecord?[] Images { get; set; } = Array.Empty<FrameRecord?>();
}

internal sealed class FrameRecord
{
    public int Index { get; set; }
    public string Page { get; set; } = string.Empty;
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; }
    public int Height { get; set; }
    public int OffsetX { get; set; }
    public int OffsetY { get; set; }
}

internal sealed class MasterManifest
{
    public string Schema { get; set; } = string.Empty;
    public string ZirconCommit { get; set; } = string.Empty;
    public int AtlasSize { get; set; }
    public List<MasterLibraryEntry> Libraries { get; set; } = new();
}

internal sealed class MasterLibraryEntry
{
    public string LibraryFile { get; set; } = string.Empty;
    public string Manifest { get; set; } = string.Empty;
    public int ImageCount { get; set; }
    public int ExportedImageCount { get; set; }
}

internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Pretty = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    };

    public static readonly JsonSerializerOptions CaseInsensitive = new()
    {
        PropertyNameCaseInsensitive = true,
    };
}
