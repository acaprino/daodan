// What the rewritten assemblies call (`Rewrite.cs`). Base library only, for netstandard2.0, so a test process of
// any .NET from Core 3.0 on loads it. The host loads it into every process started with DOTNET_STARTUP_HOOKS naming
// it, before Main (`StartupHook`), and its handler resolves the rewritten assemblies' reference to it, which no
// deps.json lists.
//
// A thread's `pending` is the call site whose instruction is running. A method that starts takes it, the first
// time for that pair, when the site names a name the method answers to (its own, the interface method it
// implements, `Invoke` for a delegate made of it) and the frame under it is the site's method: a method reached
// through a library frame is not the site's callee. A pair that fails once is not checked again. A site that
// returns still pending ran outside the rewritten code. Each new fact is one line, written and flushed at once:
// a killed process loses nothing.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Runtime.CompilerServices;

public static class StartupHook
{
    public static void Initialize()
    {
        Assembly self = typeof(StartupHook).Assembly;
        string name = self.GetName().Name;
        AppDomain.CurrentDomain.AssemblyResolve += (sender, args) =>
            new AssemblyName(args.Name).Name == name ? self : null;
    }
}

namespace Daodan
{
    public static class Record
    {
        [ThreadStatic] private static int pending;
        [ThreadStatic] private static bool busy;
        private static readonly object Lock = new object();
        private static readonly HashSet<long> Seen = new HashSet<long>();
        private static readonly HashSet<long> Refused = new HashSet<long>();
        private static readonly HashSet<int> Outside = new HashSet<int>();
        // From the table, by id: a site's name and method; a method's name, module, token and other names.
        private static int[] siteSig = new int[0], siteMethod = new int[0], methodSig = new int[0];
        private static int[] methodToken = new int[0];
        private static Guid[] methodModule = new Guid[0];
        private static int[][] methodAlias = new int[0][];
        private static bool loaded, off;
        private static StreamWriter output;

        /// <summary>Before a call instruction: the site is pending; the caller keeps what was.</summary>
        public static int Call(int site)
        {
            int before = pending;
            pending = site;
            return before;
        }

        /// <summary>After a call instruction returned.</summary>
        public static void After(int before, int site)
        {
            if (pending == site && !busy)
            {
                busy = true;
                try
                {
                    lock (Lock)
                    {
                        if (Load() && Outside.Add(site))
                        {
                            Write("{\"outside\":" + site + "}");
                        }
                    }
                }
                finally
                {
                    busy = false;
                }
            }
            pending = before;
        }

        /// <summary>A method starts.</summary>
        [MethodImpl(MethodImplOptions.NoInlining)]
        public static void Enter(int method)
        {
            int site = pending;
            if (site == 0 || busy)
            {
                return;
            }
            long pair = ((long)site << 32) | (uint)method;
            busy = true;
            try
            {
                lock (Lock)
                {
                    if (Seen.Contains(pair))
                    {
                        pending = 0;
                        return;
                    }
                    if (Refused.Contains(pair) || !Load())
                    {
                        return;
                    }
                }
                // Frames: this method, the method that starts, its caller.
                MethodBase caller = new StackFrame(2, false).GetMethod();
                bool called = site < siteSig.Length && method < methodSig.Length && Answers(method, siteSig[site])
                              && caller != null && caller.MetadataToken == methodToken[siteMethod[site]]
                              && caller.Module.ModuleVersionId == methodModule[siteMethod[site]];
                lock (Lock)
                {
                    if (!called)
                    {
                        Refused.Add(pair);
                        return;
                    }
                    pending = 0;
                    if (Seen.Add(pair))
                    {
                        Write("{\"call\":[" + site + "," + method + "]}");
                    }
                }
            }
            catch (Exception error)
            {
                Fail(error);
            }
            finally
            {
                busy = false;
            }
        }

        private static bool Answers(int method, int sig)
        {
            if (methodSig[method] == sig)
            {
                return true;
            }
            foreach (int alias in methodAlias[method] ?? new int[0])
            {
                if (alias == sig)
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>The table and the output file, once; false when either is missing (nothing is recorded).</summary>
        private static bool Load()
        {
            if (loaded)
            {
                return !off;
            }
            loaded = off = true;
            string table = Environment.GetEnvironmentVariable("DAODAN_RECORD_TABLE");
            string folder = Environment.GetEnvironmentVariable("DAODAN_RECORD");
            if (string.IsNullOrEmpty(table) || string.IsNullOrEmpty(folder))
            {
                return false;
            }
            Directory.CreateDirectory(folder);
            string path = Path.Combine(folder, Process.GetCurrentProcess().Id.ToString(CultureInfo.InvariantCulture) + ".jsonl");
            output = new StreamWriter(new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.ReadWrite));
            output.AutoFlush = true;
            try
            {
                Read(table);
            }
            catch (Exception error)
            {
                Write("{\"error\":\"" + Escape(error.GetType().Name + ": " + error.Message) + "\"}");
                return false;
            }
            off = false;
            return true;
        }

        private static void Read(string table)
        {
            List<string[]> methods = new List<string[]>(), sites = new List<string[]>();
            int lastMethod = 0, lastSite = 0;
            foreach (string line in File.ReadAllLines(table))
            {
                string[] cells = line.Split('\t');
                if (cells[0] == "m" && cells.Length >= 6)
                {
                    methods.Add(cells);
                    lastMethod = Math.Max(lastMethod, Number(cells[1]));
                }
                else if (cells[0] == "s" && cells.Length >= 4)
                {
                    sites.Add(cells);
                    lastSite = Math.Max(lastSite, Number(cells[1]));
                }
            }
            methodSig = new int[lastMethod + 1];
            methodToken = new int[lastMethod + 1];
            methodModule = new Guid[lastMethod + 1];
            methodAlias = new int[lastMethod + 1][];
            foreach (string[] cells in methods)
            {
                int id = Number(cells[1]);
                methodSig[id] = Number(cells[2]);
                methodModule[id] = new Guid(cells[3]);
                methodToken[id] = Number(cells[4]);
                string[] aliases = cells[5].Length == 0 ? new string[0] : cells[5].Split(',');
                methodAlias[id] = Array.ConvertAll(aliases, Number);
            }
            siteSig = new int[lastSite + 1];
            siteMethod = new int[lastSite + 1];
            foreach (string[] cells in sites)
            {
                int id = Number(cells[1]);
                siteMethod[id] = Number(cells[2]);
                siteSig[id] = Number(cells[3]);
            }
        }

        private static int Number(string text)
        {
            return int.Parse(text, CultureInfo.InvariantCulture);
        }

        private static void Write(string line)
        {
            output.WriteLine(line);
        }

        private static void Fail(Exception error)
        {
            lock (Lock)
            {
                if (!off && output != null)
                {
                    Write("{\"error\":\"" + Escape(error.GetType().Name + ": " + error.Message) + "\"}");
                }
                off = true;
            }
        }

        private static string Escape(string text)
        {
            return text.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", " ").Replace("\r", " ");
        }
    }
}
