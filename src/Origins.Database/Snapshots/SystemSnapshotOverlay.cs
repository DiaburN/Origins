using System.Text.Json;

namespace Origins.Database.Snapshots;

public sealed class SystemSnapshotOverlay
{
    public int SchemaVersion { get; set; } = 1;
    public string Name { get; set; } = string.Empty;
    public List<SystemSnapshotOperation> Operations { get; set; } = new();
}

public sealed class SystemSnapshotOperation
{
    public string Action { get; set; } = "upsert";
    public string AssemblyName { get; set; } = string.Empty;
    public string TypeName { get; set; } = string.Empty;
    public int Index { get; set; }

    /// <summary>
    /// Values use the same loss-aware JSON encoding produced by the exporter.
    /// DBObject references use {$refAssembly,$refType,Index}.
    /// </summary>
    public Dictionary<string, JsonElement> Set { get; set; } = new();
}
