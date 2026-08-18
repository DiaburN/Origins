namespace Origins.Database.Snapshots;

public sealed class SystemSnapshotManifest
{
    public int SchemaVersion { get; set; } = 1;
    public string SourceSystemDbSha256 { get; set; } = string.Empty;
    public string? SourceSystemVersion { get; set; }
    public DateTime ExportedUtc { get; set; }
    public List<SystemSnapshotCollection> Collections { get; set; } = new();
}

public sealed class SystemSnapshotCollection
{
    public string AssemblyName { get; set; } = string.Empty;
    public string TypeName { get; set; } = string.Empty;
    public string FileName { get; set; } = string.Empty;
    public int Count { get; set; }

    /// <summary>
    /// Preserves Zircon DBCollection.Index even when deleted rows have left gaps.
    /// </summary>
    public int CollectionIndex { get; set; }
}
