using Server.Models;
using System;
using System.Drawing;

namespace Server.Models.Magics
{
    internal static class ArcherLineOfSight
    {
        // Zircon represents non-walkable map tiles as null Cells. Crystal's
        // CanFly performs the same map-line validation before normal Archer
        // projectiles; Trickshot bypasses this helper at the caller.
        public static bool LineOfSight(this Map map, Point from, Point to)
        {
            if (map == null) return false;

            int x0 = from.X;
            int y0 = from.Y;
            int x1 = to.X;
            int y1 = to.Y;

            int dx = Math.Abs(x1 - x0);
            int sx = x0 < x1 ? 1 : -1;
            int dy = -Math.Abs(y1 - y0);
            int sy = y0 < y1 ? 1 : -1;
            int error = dx + dy;

            while (true)
            {
                if (!(x0 == from.X && y0 == from.Y) && map.GetCell(x0, y0) == null)
                    return false;

                if (x0 == x1 && y0 == y1)
                    return true;

                int e2 = 2 * error;
                if (e2 >= dy)
                {
                    error += dy;
                    x0 += sx;
                }
                if (e2 <= dx)
                {
                    error += dx;
                    y0 += sy;
                }
            }
        }
    }
}
