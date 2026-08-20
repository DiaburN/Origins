using System.Text.Json;
using LibraryEditor;

namespace ZirconZlFrameProbe;

internal static class Program
{
    private static readonly string[] FishingAnimations = ["FishingCast", "FishingWait", "FishingReel"];

    [STAThread]
    private static int Main(string[] args)
    {
        try
        {
            Options options = Options.Parse(args);
            Contract contract = JsonSerializer.Deserialize<Contract>(File.ReadAllText(options.ContractPath), JsonOptions.CaseInsensitive)
                ?? throw new InvalidDataException("Invalid player asset contract.");

            Dictionary<string, LibraryRequirement> requirements = contract.PlayerLibraries
                .ToDictionary(x => x.LibraryFile, StringComparer.OrdinalIgnoreCase);
            List<string> selected = options.Libraries.Count > 0
                ? options.Libraries
                : requirements.Keys.Where(IsBodyLibrary).Order(StringComparer.Ordinal).ToList();

            List<LibraryResult> libraries = [];
            foreach (string name in selected)
            {
                if (!requirements.TryGetValue(name, out LibraryRequirement? requirement))
                    throw new ArgumentException($"Unknown player library in contract: {name}");

                string source = Path.GetFullPath(Path.Combine(options.SourceRoot,
                    requirement.SourcePath.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar)));
                if (!File.Exists(source))
                {
                    libraries.Add(new LibraryResult { LibraryFile = name, SourcePath = requirement.SourcePath, Status = "MISSING_FILE" });
                    continue;
                }

                libraries.Add(ProbeLibrary(name, requirement.SourcePath, source, contract.PlayerFrames));
            }

            ProbeReport report = new()
            {
                ZirconCommit = contract.ZirconCommit,
                Libraries = libraries,
                Selected = libraries.Count,
                Ready = libraries.Count(x => x.Status == "READY"),
                MissingFiles = libraries.Count(x => x.Status == "MISSING_FILE"),
                FullFishingBanks = libraries.Sum(x => x.Banks.Count(b => b.Status == "PASS")),
                MaleFullFishingBanks = libraries.Where(x => x.Gender == "Male").Sum(x => x.Banks.Count(b => b.Status == "PASS")),
                FemaleFullFishingBanks = libraries.Where(x => x.Gender == "Female").Sum(x => x.Banks.Count(b => b.Status == "PASS")),
            };
            report.Status = report.Ready == 0 ? "FAIL" : "PASS";

            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(options.OutputPath))!);
            File.WriteAllText(options.OutputPath, JsonSerializer.Serialize(report, JsonOptions.Pretty) + Environment.NewLine);
            Console.WriteLine(JsonSerializer.Serialize(new
            {
                report.Status,
                report.Selected,
                report.Ready,
                report.MissingFiles,
                report.FullFishingBanks,
                report.MaleFullFishingBanks,
                report.FemaleFullFishingBanks,
                Matches = report.Libraries.SelectMany(l => l.Banks.Where(b => b.Status == "PASS")
                    .Select(b => $"{l.LibraryFile}:{b.Bank}"))
            }, JsonOptions.Pretty));
            return report.Status == "PASS" ? 0 : 1;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            return 1;
        }
    }

    private static LibraryResult ProbeLibrary(string name, string sourcePath, string source, Dictionary<string, FrameDefinition> frames)
    {
        int bankOffset = IsAssassinBodyLibrary(name) ? 3000 : 5000;
        Mir3Library library = new(source);
        try
        {
            LibraryResult result = new()
            {
                LibraryFile = name,
                SourcePath = sourcePath,
                Status = "READY",
                Gender = name.StartsWith("WM_", StringComparison.OrdinalIgnoreCase) ? "Female" : "Male",
                PlayerClassFamily = IsAssassinBodyLibrary(name) ? "Assassin" : "WarriorWizardTaoist",
                ImageCount = library.Images.Count,
                BankOffset = bankOffset,
            };

            int maxRelativeIndex = FishingAnimations
                .Select(animation => frames[animation])
                .Max(frame => frame.StartIndex + frame.Offset * 7 + frame.FrameCount - 1);

            for (int bank = 0; bank * bankOffset + maxRelativeIndex < library.Images.Count; bank++)
            {
                int shift = bank * bankOffset;
                BankResult bankResult = new() { Bank = bank, Shift = shift };
                foreach (string animation in FishingAnimations)
                {
                    FrameDefinition frame = frames[animation];
                    AnimationResult animationResult = new() { Animation = animation };
                    for (int direction = 0; direction < 8; direction++)
                    {
                        for (int local = 0; local < frame.FrameCount; local++)
                        {
                            int index = shift + frame.StartIndex + frame.Offset * direction + local;
                            animationResult.References++;
                            Mir3Library.Mir3Image? image = library.GetImage(index);
                            bool present = image?.Image is not null && image.Width > 0 && image.Height > 0;
                            if (present) animationResult.Present++;
                            else animationResult.Missing++;
                        }
                    }
                    animationResult.Status = animationResult.Missing == 0 ? "PASS" :
                        animationResult.Present == 0 ? "EMPTY" : "PARTIAL";
                    bankResult.Animations.Add(animationResult);
                    bankResult.References += animationResult.References;
                    bankResult.Present += animationResult.Present;
                    bankResult.Missing += animationResult.Missing;
                }
                bankResult.Status = bankResult.Missing == 0 ? "PASS" : bankResult.Present == 0 ? "EMPTY" : "PARTIAL";
                result.Banks.Add(bankResult);
            }
            return result;
        }
        finally
        {
            foreach (Mir3Library.Mir3Image? image in library.Images)
                image?.Dispose();
            library.Close();
        }
    }

    private static bool IsBodyLibrary(string name) =>
        name.StartsWith("M_Hum", StringComparison.OrdinalIgnoreCase) ||
        name.StartsWith("WM_Hum", StringComparison.OrdinalIgnoreCase);

    private static bool IsAssassinBodyLibrary(string name) =>
        name.StartsWith("M_HumA", StringComparison.OrdinalIgnoreCase) ||
        name.StartsWith("WM_HumA", StringComparison.OrdinalIgnoreCase);
}

internal sealed class Options
{
    public required string ContractPath { get; init; }
    public required string SourceRoot { get; init; }
    public required string OutputPath { get; init; }
    public List<string> Libraries { get; init; } = [];

    public static Options Parse(string[] args)
    {
        string? contract = null, source = null, output = null;
        List<string> libraries = [];
        for (int i = 0; i < args.Length; i++)
        {
            string arg = args[i];
            string NeedValue() => ++i < args.Length ? args[i] : throw new ArgumentException($"Missing value after {arg}");
            switch (arg)
            {
                case "--contract": contract = NeedValue(); break;
                case "--source-root": source = NeedValue(); break;
                case "--output": output = NeedValue(); break;
                case "--library": libraries.Add(NeedValue()); break;
                default: throw new ArgumentException($"Unknown argument: {arg}");
            }
        }
        if (string.IsNullOrWhiteSpace(contract) || string.IsNullOrWhiteSpace(source) || string.IsNullOrWhiteSpace(output))
            throw new ArgumentException("--contract, --source-root and --output are required.");
        return new Options
        {
            ContractPath = Path.GetFullPath(contract),
            SourceRoot = Path.GetFullPath(source),
            OutputPath = Path.GetFullPath(output),
            Libraries = libraries,
        };
    }
}

internal sealed class Contract
{
    public string ZirconCommit { get; set; } = string.Empty;
    public Dictionary<string, FrameDefinition> PlayerFrames { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public List<LibraryRequirement> PlayerLibraries { get; set; } = [];
}
internal sealed class FrameDefinition
{
    public int StartIndex { get; set; }
    public int FrameCount { get; set; }
    public int Offset { get; set; }
}
internal sealed class LibraryRequirement
{
    public string LibraryFile { get; set; } = string.Empty;
    public string SourcePath { get; set; } = string.Empty;
}
internal sealed class ProbeReport
{
    public string Schema { get; set; } = "origins.zircon.body-fishing-probe.v1";
    public string Status { get; set; } = string.Empty;
    public string ZirconCommit { get; set; } = string.Empty;
    public int Selected { get; set; }
    public int Ready { get; set; }
    public int MissingFiles { get; set; }
    public int FullFishingBanks { get; set; }
    public int MaleFullFishingBanks { get; set; }
    public int FemaleFullFishingBanks { get; set; }
    public List<LibraryResult> Libraries { get; set; } = [];
}
internal sealed class LibraryResult
{
    public string LibraryFile { get; set; } = string.Empty;
    public string SourcePath { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Gender { get; set; } = string.Empty;
    public string PlayerClassFamily { get; set; } = string.Empty;
    public int ImageCount { get; set; }
    public int BankOffset { get; set; }
    public List<BankResult> Banks { get; set; } = [];
}
internal sealed class BankResult
{
    public int Bank { get; set; }
    public int Shift { get; set; }
    public int References { get; set; }
    public int Present { get; set; }
    public int Missing { get; set; }
    public string Status { get; set; } = string.Empty;
    public List<AnimationResult> Animations { get; set; } = [];
}
internal sealed class AnimationResult
{
    public string Animation { get; set; } = string.Empty;
    public int References { get; set; }
    public int Present { get; set; }
    public int Missing { get; set; }
    public string Status { get; set; } = string.Empty;
}
internal static class JsonOptions
{
    public static readonly JsonSerializerOptions Pretty = new() { WriteIndented = true };
    public static readonly JsonSerializerOptions CaseInsensitive = new() { PropertyNameCaseInsensitive = true };
}
