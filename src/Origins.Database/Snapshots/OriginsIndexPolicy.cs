namespace Origins.Database.Snapshots;

public sealed class OriginsIndexPolicy
{
    public int SchemaVersion { get; set; } = 1;
    public string Description { get; set; } = string.Empty;
    public List<OriginsIndexRange> Ranges { get; set; } = new();
}

public sealed class OriginsIndexRange
{
    public string AssemblyName { get; set; } = string.Empty;
    public string TypeName { get; set; } = string.Empty;
    public int LegacyCollectionIndex { get; set; }
    public int OriginsStart { get; set; }
    public string? Notes { get; set; }
}
