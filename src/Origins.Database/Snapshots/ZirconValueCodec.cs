using System.Collections;
using System.Drawing;
using System.Text.Json;
using Library;
using MirDB;

namespace Origins.Database.Snapshots;

/// <summary>
/// Loss-aware JSON representation for the exact scalar types supported by
/// Zircon MirDB.DBValue. DBObject references and DBBindingList associations are
/// handled by the snapshot exporter/importer outside this codec.
/// </summary>
public static class ZirconValueCodec
{
    /// <summary>
    /// Mirrors the inclusion rule used by Zircon DBMapping: a persisted
    /// property is either a supported DBValue scalar, an enum, or a DBObject
    /// reference. DBBindingList associations and unsupported/calculated
    /// properties are not persisted in System.db.
    /// </summary>
    public static bool IsPersistedPropertyType(Type type)
    {
        return type.IsEnum ||
               typeof(DBObject).IsAssignableFrom(type) ||
               type == typeof(bool) ||
               type == typeof(byte) ||
               type == typeof(byte[]) ||
               type == typeof(char) ||
               type == typeof(Color) ||
               type == typeof(DateTime) ||
               type == typeof(decimal) ||
               type == typeof(double) ||
               type == typeof(short) ||
               type == typeof(int) ||
               type == typeof(int[]) ||
               type == typeof(long) ||
               type == typeof(Point) ||
               type == typeof(sbyte) ||
               type == typeof(float) ||
               type == typeof(Size) ||
               type == typeof(string) ||
               type == typeof(TimeSpan) ||
               type == typeof(ushort) ||
               type == typeof(uint) ||
               type == typeof(ulong) ||
               type == typeof(Point[]) ||
               type == typeof(Stats) ||
               type == typeof(BitArray);
    }

    public static object? Encode(object? value, Type declaredType)
    {
        if (value == null)
            return null;

        if (declaredType.IsEnum)
        {
            var underlying = Enum.GetUnderlyingType(declaredType);
            return Convert.ChangeType(value, underlying);
        }

        if (declaredType == typeof(byte[]))
            return Convert.ToBase64String((byte[])value);

        if (declaredType == typeof(Color))
            return ((Color)value).ToArgb();

        if (declaredType == typeof(DateTime))
            return ((DateTime)value).ToBinary();

        if (declaredType == typeof(int[]))
            return (int[])value;

        if (declaredType == typeof(Point))
        {
            var point = (Point)value;
            return new[] { point.X, point.Y };
        }

        if (declaredType == typeof(Size))
        {
            var size = (Size)value;
            return new[] { size.Width, size.Height };
        }

        if (declaredType == typeof(TimeSpan))
            return ((TimeSpan)value).Ticks;

        if (declaredType == typeof(Point[]))
        {
            return ((Point[])value)
                .Select(point => new[] { point.X, point.Y })
                .ToArray();
        }

        if (declaredType == typeof(Stats))
        {
            return ((Stats)value).Values
                .Select(pair => new[] { (int)pair.Key, pair.Value })
                .ToArray();
        }

        if (declaredType == typeof(BitArray))
        {
            var bits = (BitArray)value;
            var bytes = new byte[(int)Math.Ceiling(bits.Length / 8d)];
            bits.CopyTo(bytes, 0);
            return Convert.ToBase64String(bytes);
        }

        if (IsMirDbPrimitive(declaredType))
            return value;

        throw new NotSupportedException($"Zircon snapshot codec does not support persisted type {declaredType.FullName}.");
    }

    public static object? Decode(JsonElement element, Type declaredType)
    {
        if (element.ValueKind == JsonValueKind.Null)
            return null;

        if (declaredType.IsEnum)
        {
            var underlying = Enum.GetUnderlyingType(declaredType);
            var raw = JsonSerializer.Deserialize(element.GetRawText(), underlying)
                ?? throw new InvalidOperationException($"Cannot decode enum {declaredType.FullName}.");
            return Enum.ToObject(declaredType, raw);
        }

        if (declaredType == typeof(byte[]))
            return Convert.FromBase64String(element.GetString() ?? string.Empty);

        if (declaredType == typeof(Color))
            return Color.FromArgb(element.GetInt32());

        if (declaredType == typeof(DateTime))
            return DateTime.FromBinary(element.GetInt64());

        if (declaredType == typeof(int[]))
            return JsonSerializer.Deserialize<int[]>(element.GetRawText());

        if (declaredType == typeof(Point))
        {
            var pair = JsonSerializer.Deserialize<int[]>(element.GetRawText())
                ?? throw new InvalidOperationException("Cannot decode Point.");
            if (pair.Length != 2) throw new InvalidOperationException("Point requires exactly two integers.");
            return new Point(pair[0], pair[1]);
        }

        if (declaredType == typeof(Size))
        {
            var pair = JsonSerializer.Deserialize<int[]>(element.GetRawText())
                ?? throw new InvalidOperationException("Cannot decode Size.");
            if (pair.Length != 2) throw new InvalidOperationException("Size requires exactly two integers.");
            return new Size(pair[0], pair[1]);
        }

        if (declaredType == typeof(TimeSpan))
            return TimeSpan.FromTicks(element.GetInt64());

        if (declaredType == typeof(Point[]))
        {
            var values = JsonSerializer.Deserialize<int[][]>(element.GetRawText()) ?? Array.Empty<int[]>();
            return values.Select(pair =>
            {
                if (pair.Length != 2) throw new InvalidOperationException("Point[] entry requires exactly two integers.");
                return new Point(pair[0], pair[1]);
            }).ToArray();
        }

        if (declaredType == typeof(Stats))
        {
            var values = JsonSerializer.Deserialize<int[][]>(element.GetRawText()) ?? Array.Empty<int[]>();
            var stats = new Stats();
            foreach (var pair in values)
            {
                if (pair.Length != 2) throw new InvalidOperationException("Stats entry requires [stat, amount].");
                stats.Values[(Stat)pair[0]] = pair[1];
            }
            return stats;
        }

        if (declaredType == typeof(BitArray))
            return new BitArray(Convert.FromBase64String(element.GetString() ?? string.Empty));

        if (IsMirDbPrimitive(declaredType))
            return JsonSerializer.Deserialize(element.GetRawText(), declaredType);

        throw new NotSupportedException($"Zircon snapshot codec does not support persisted type {declaredType.FullName}.");
    }

    private static bool IsMirDbPrimitive(Type type)
    {
        return type == typeof(bool) ||
               type == typeof(byte) ||
               type == typeof(char) ||
               type == typeof(decimal) ||
               type == typeof(double) ||
               type == typeof(short) ||
               type == typeof(int) ||
               type == typeof(long) ||
               type == typeof(sbyte) ||
               type == typeof(float) ||
               type == typeof(string) ||
               type == typeof(ushort) ||
               type == typeof(uint) ||
               type == typeof(ulong);
    }
}
