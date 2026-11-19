// Rewrites in place, with Mono.Cecil, each assembly of the project under the folders it is given: one whose PDB
// names a document of the checkout outside obj/. A probe at each method's entry (`Record.Enter`), and around each
// call, callvirt and newobj (`Record.Call` before, `Record.After` once it returned); each method entered is
// NoInlining, so the frame under a method is its caller's. The ids and what they name go to the table, which
// `Record` and `dynamic/dotnet.py` read:
//
//     m  id  name  module  token  other names  kind  kickoff  file  line  method name  type  assembly
//     s  id  method  name  file  line  column  end line  end column  called name  called type  its assembly
//     a  file  module  assembly       (an assembly rewritten)
//     x  file  why                    (an assembly of the project left as built)
//
// `name` is a number per name; a site's place is its statement's (the sequence point that holds it), lines and
// columns from 1, columns in UTF-16 units; files are from the checkout. A method's token is the one written, its
// kickoff the async or iterator method whose state machine it is. A copy of an assembly (same module id) in
// another folder takes the same ids. Usage: dotnet Daodan.Rewrite.dll <checkout> <table> <folder>...
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;
using Mono.Cecil.Rocks;

static class Rewrite
{
    static readonly Dictionary<string, int> Names = new Dictionary<string, int>();
    static readonly Dictionary<(Guid, int), int> Methods = new Dictionary<(Guid, int), int>();
    static readonly Dictionary<(Guid, int, int), int> Sites = new Dictionary<(Guid, int, int), int>();
    static readonly HashSet<Guid> Listed = new HashSet<Guid>();
    static readonly Dictionary<string, string> Documents = new Dictionary<string, string>();
    static readonly string[] Skipped = { "obj", ".git", "node_modules", "ref", "refint" };
    static string root;
    static TextWriter table;

    static int Main(string[] args)
    {
        root = Path.GetFullPath(args[0]).TrimEnd('/') + "/";
        using (table = new StreamWriter(args[1], true))
        {
            foreach (string folder in args.Skip(2))
            {
                foreach (string path in Files(Path.GetFullPath(folder)).OrderBy(path => path, StringComparer.Ordinal))
                {
                    Assembly1(path);
                }
            }
        }
        return 0;
    }

    static IEnumerable<string> Files(string folder)
    {
        foreach (string path in Directory.EnumerateFiles(folder, "*.dll"))
        {
            yield return path;
        }
        foreach (string inner in Directory.EnumerateDirectories(folder))
        {
            if (!Skipped.Contains(Path.GetFileName(inner)))
            {
                foreach (string path in Files(inner))
                {
                    yield return path;
                }
            }
        }
    }

    /// <summary>A document's path from the checkout, null outside it, under obj/ (generated there) or missing: a
    /// deterministic build names its sources from `/_/`, as the packages it uses do theirs.</summary>
    static string Rel(string url)
    {
        if (url == null)
        {
            return null;
        }
        if (!Documents.TryGetValue(url, out string rel))
        {
            rel = url.StartsWith(root, StringComparison.Ordinal) ? url.Substring(root.Length)
                : url.StartsWith("/_/", StringComparison.Ordinal) ? url.Substring(3) : null;
            Documents[url] = rel = rel == null || ("/" + rel).Contains("/obj/") || !File.Exists(root + rel) ? null : rel;
        }
        return rel;
    }

    static void Assembly1(string path)
    {
        ModuleDefinition module;
        try
        {
            module = ModuleDefinition.ReadModule(path, new ReaderParameters
            {
                ReadSymbols = true, SymbolReaderProvider = new DefaultSymbolReaderProvider(false), InMemory = true
            });
        }
        catch (Exception)
        {
            return;  // no .NET assembly, or one Cecil cannot read: none the project builds
        }
        string temp = Path.Combine(Path.GetDirectoryName(path), ".daodan-rewrite");
        string written = Path.Combine(temp, Path.GetFileName(path));
        try
        {
            using (module)
            {
                List<MethodDefinition> methods = module.GetTypes().SelectMany(type => type.Methods)
                    .Where(method => method.HasBody).ToList();
                if (!module.HasSymbols || module.AssemblyReferences.Any(item => item.Name == "Daodan.Record")
                    || !methods.Any(method => method.DebugInformation.SequencePoints.Any(point => Rel(point.Document.Url) != null)))
                {
                    return;
                }
                try
                {
                    var lines = new List<string>();
                    Dictionary<MethodDefinition, HashSet<int>> aliases = Instrument(module, methods, lines);
                    module.Attributes &= ~ModuleAttributes.StrongNameSigned;  // .NET checks no signature
                    Directory.CreateDirectory(temp);
                    module.Write(written, new WriterParameters { WriteSymbols = true });
                    if (Listed.Add(module.Mvid))
                    {
                        lines.ForEach(table.WriteLine);
                        foreach (MethodDefinition method in methods)
                        {
                            table.WriteLine(MethodLine(module, method, aliases));
                        }
                    }
                }
                catch (Exception error)
                {
                    table.WriteLine($"x\t{Rel(path) ?? path}\t{error.GetType().Name}: {Clean(error.Message)}");
                    return;
                }
            }
            File.Copy(written, path, true);
            string pdb = Path.ChangeExtension(written, ".pdb");
            if (File.Exists(pdb))
            {
                File.Copy(pdb, Path.ChangeExtension(path, ".pdb"), true);
            }
            table.WriteLine($"a\t{Rel(path) ?? path}\t{module.Mvid}\t{module.Assembly.Name.Name}");
        }
        finally
        {
            if (Directory.Exists(temp))
            {
                Directory.Delete(temp, true);
            }
        }
    }

    static string Clean(string text)
    {
        return (text ?? "").Replace('\t', ' ').Replace('\n', ' ').Replace('\r', ' ');
    }

    static int Name(string name)
    {
        if (!Names.TryGetValue(name, out int id))
        {
            Names[name] = id = Names.Count + 1;
        }
        return id;
    }

    /// <summary>A method's id, by the token it was read with: every copy of the assembly reads the same.</summary>
    static int MethodId(Guid module, int token)
    {
        if (!Methods.TryGetValue((module, token), out int id))
        {
            Methods[(module, token)] = id = Methods.Count + 1;
        }
        return id;
    }

    static string Scope(TypeReference type)
    {
        IMetadataScope scope = type.Scope;
        return scope is ModuleDefinition own ? own.Assembly.Name.Name
            : scope is AssemblyNameReference other ? other.Name : scope?.Name ?? "";
    }

    static string Kind(MethodDefinition method)
    {
        if (method.IsConstructor)
        {
            return "constructor";
        }
        if (method.IsGetter || method.IsSetter)
        {
            return "accessor";
        }
        if (method.Name.StartsWith("<", StringComparison.Ordinal))
        {
            return method.Name.Contains(">b__") ? "lambda" : method.Name.Contains(">g__") ? "local" : "generated";
        }
        return "method";
    }

    /// <summary>The method that a delegate made with ldftn or ldvirtftn runs, when it is of this module.</summary>
    static MethodDefinition Target(Instruction instruction)
    {
        if ((instruction.OpCode != OpCodes.Ldftn && instruction.OpCode != OpCodes.Ldvirtftn)
            || !(instruction.Operand is MethodReference reference))
        {
            return null;
        }
        try
        {
            MethodDefinition method = reference.Resolve();
            return method != null && method.Module == reference.Module ? method : null;
        }
        catch (Exception)
        {
            return null;
        }
    }

    static void Alias(Dictionary<MethodDefinition, HashSet<int>> aliases, MethodDefinition method, int name)
    {
        if (!aliases.TryGetValue(method, out HashSet<int> names))
        {
            aliases[method] = names = new HashSet<int>();
        }
        names.Add(name);
    }

    /// <summary>The probes of each method (its id and its sites' in `Ids`); the sites' table lines into `lines`.
    /// Returns the other names each method answers to.</summary>
    static Dictionary<MethodDefinition, HashSet<int>> Instrument(ModuleDefinition module, List<MethodDefinition> methods,
                                                                 List<string> lines)
    {
        var scope = new AssemblyNameReference("Daodan.Record", new Version(1, 0, 0, 0));
        module.AssemblyReferences.Add(scope);
        var record = new TypeReference("Daodan", "Record", module, scope);
        TypeReference number = module.TypeSystem.Int32, none = module.TypeSystem.Void;
        var call = new MethodReference("Call", number, record);
        call.Parameters.Add(new ParameterDefinition(number));
        var after = new MethodReference("After", none, record);
        after.Parameters.Add(new ParameterDefinition(number));
        after.Parameters.Add(new ParameterDefinition(number));
        var enter = new MethodReference("Enter", none, record);
        enter.Parameters.Add(new ParameterDefinition(number));

        var aliases = new Dictionary<MethodDefinition, HashSet<int>>();
        Ids.Clear();
        foreach (MethodDefinition method in methods)
        {
            Ids[method] = MethodId(module.Mvid, method.MetadataToken.ToInt32());
            foreach (MethodReference other in method.Overrides)  // an explicit implementation answers to its name
            {
                Alias(aliases, method, Name(other.Name));
            }
            foreach (Instruction instruction in method.Body.Instructions)
            {
                MethodDefinition target = Target(instruction);
                if (target != null)
                {
                    Alias(aliases, target, Name("Invoke"));
                }
            }
        }
        foreach (MethodDefinition method in methods)
        {
            Sites1(module, method, Ids[method], call, after, lines);
            // A class initializer runs when the runtime asks, a state machine's MoveNext from the library: neither is
            // a site's callee, so neither takes a pending site.
            if (!(method.IsConstructor && method.IsStatic) && method.DebugInformation.StateMachineKickOffMethod == null)
            {
                ILProcessor il = method.Body.GetILProcessor();
                Instruction start = method.Body.Instructions[0];
                il.InsertBefore(start, il.Create(OpCodes.Ldc_I4, Ids[method]));  // a branch to the start skips it
                il.InsertBefore(start, il.Create(OpCodes.Call, enter));
                method.NoInlining = true;
                method.AggressiveInlining = false;
            }
            method.Body.OptimizeMacros();
        }
        return aliases;
    }

    static readonly Dictionary<MethodDefinition, int> Ids = new Dictionary<MethodDefinition, int>();

    static string MethodLine(ModuleDefinition module, MethodDefinition method,
                             Dictionary<MethodDefinition, HashSet<int>> aliases)
    {
        SequencePoint first = method.DebugInformation.SequencePoints.FirstOrDefault(point => !point.IsHidden);
        MethodDefinition kickoff = method.DebugInformation.StateMachineKickOffMethod;
        string others = aliases.TryGetValue(method, out HashSet<int> names) ? string.Join(",", names) : "";
        return string.Join("\t", "m", Ids[method], Name(method.Name), module.Mvid, method.MetadataToken.ToInt32(),
            others, Kind(method), kickoff == null ? "" : Ids[kickoff].ToString(),
            first == null ? "" : Rel(first.Document.Url) ?? "", first?.StartLine.ToString() ?? "",
            method.Name, method.DeclaringType.FullName, module.Assembly.Name.Name);
    }

    /// <summary>The probes around each call of a method, and the table's line of each site.</summary>
    static void Sites1(ModuleDefinition module, MethodDefinition method, int owner, MethodReference call,
                       MethodReference after, List<string> lines)
    {
        MethodBody body = method.Body;
        body.SimplifyMacros();
        List<SequencePoint> points = method.DebugInformation.SequencePoints.OrderBy(point => point.Offset).ToList();
        List<Instruction> calls = body.Instructions.Where(instruction => (instruction.OpCode == OpCodes.Call
            || instruction.OpCode == OpCodes.Callvirt || instruction.OpCode == OpCodes.Newobj)
            && instruction.Operand is MethodReference).ToList();
        if (calls.Count == 0)
        {
            return;
        }
        var before = new VariableDefinition(module.TypeSystem.Int32);
        body.Variables.Add(before);
        body.InitLocals = true;
        ILProcessor il = body.GetILProcessor();
        foreach (Instruction instruction in calls)
        {
            var target = (MethodReference)instruction.Operand;
            Instruction first = instruction;
            while (first.Previous != null && first.Previous.OpCode.OpCodeType == OpCodeType.Prefix)
            {
                first = first.Previous;
            }
            if (Prefixed(first, instruction, OpCodes.Tail))
            {
                continue;  // a tail call returns with its callee: nothing can run after it
            }
            var key = (module.Mvid, method.MetadataToken.ToInt32(), instruction.Offset);
            if (!Sites.TryGetValue(key, out int site))
            {
                Sites[key] = site = Sites.Count + 1;
            }
            SequencePoint point = points.LastOrDefault(item => item.Offset <= instruction.Offset);
            bool known = point != null && !point.IsHidden;
            lines.Add(string.Join("\t", "s", site, owner, Name(target.Name),
                known ? Rel(point.Document.Url) ?? "" : "", known ? point.StartLine.ToString() : "",
                known ? point.StartColumn.ToString() : "", known ? point.EndLine.ToString() : "",
                known ? point.EndColumn.ToString() : "", target.Name, target.DeclaringType.FullName,
                Scope(target.DeclaringType)));
            // The first instruction becomes the probe, so a branch to the call runs it; its copy follows.
            Instruction copy = Copy(il, first);
            Instruction done = first == instruction ? copy : instruction;
            first.OpCode = OpCodes.Ldc_I4;
            first.Operand = site;
            Instruction probe = il.Create(OpCodes.Call, call), keep = il.Create(OpCodes.Stloc, before);
            il.InsertAfter(first, probe);
            il.InsertAfter(probe, keep);
            il.InsertAfter(keep, copy);
            Instruction load = il.Create(OpCodes.Ldloc, before), id = il.Create(OpCodes.Ldc_I4, site);
            il.InsertAfter(done, load);
            il.InsertAfter(load, id);
            il.InsertAfter(id, il.Create(OpCodes.Call, after));
        }
    }

    static bool Prefixed(Instruction first, Instruction call, OpCode prefix)
    {
        for (Instruction item = first; item != call; item = item.Next)
        {
            if (item.OpCode == prefix)
            {
                return true;
            }
        }
        return false;
    }

    static Instruction Copy(ILProcessor il, Instruction instruction)
    {
        switch (instruction.Operand)
        {
            case null:
                return il.Create(instruction.OpCode);
            case MethodReference method:
                return il.Create(instruction.OpCode, method);
            case TypeReference type:
                return il.Create(instruction.OpCode, type);
            case byte value:
                return il.Create(instruction.OpCode, value);
            default:
                throw new NotSupportedException($"{instruction.OpCode} before a call");
        }
    }
}
