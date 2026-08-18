namespace Origins.Database.Snapshots;

public sealed class SystemSnapshotManifest
{
    public int SchemaVersion { get; init; } = 1;
    public string SourceSystemDbSha256 { get; init; } = string.Empty;
    public string? SourceSystemVersion { get; init; }
    public DateTime ExportedUtc { get; init; }
    public List<SystemSnapshotCollection> Collections { get; init; } = new();
}

public sealed class SystemSnapshotCollection
{
    public string AssemblyName { get; init; } = string.Empty;
    public string TypeName { get; init; } = string.Empty;
    public string FileName { get; init; } = string.Empty;
    public int Count { get; init; }

    /// <summary>
    /// Preserves Zircon DBCollection.Index even when deleted rows have left gaps.
    /// </summary>
    public int CollectionIndex { get; init; }
}
