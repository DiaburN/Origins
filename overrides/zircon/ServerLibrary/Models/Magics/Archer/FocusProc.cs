using Server.Envir;

namespace Server.Models.Magics
{
    public static class FocusProc
    {
        // Crystal HumanObject ranged attack:
        // Focus procs when Random.Next(5) <= magic.Level and levels on proc.
        public static bool TryProc(this Focus focus)
        {
            if (SEnvir.Random.Next(5) > focus.Magic.Level) return false;

            focus.Player.LevelMagic(focus.Magic);
            return true;
        }
    }
}
