# scip-dotnet: i nomi con argomenti di tipo e i gruppi di metodi

**Stato:** In uso: Daodan costruisce scip-dotnet 0.2.16 con `daodan/core/indexers/scip-dotnet.patch` (la patch qui sotto più il commento che dichiara la modifica), da `daodan/core/indexers/csharp.py`. Aperta la scelta del proprietario di proporre issue e patch a scip-dotnet.

**Verifica delle fonti:** 16 novembre 2026. scip-dotnet 0.2.16 (tag `v0.2.16`, commit `fadd98aeb`) e il ramo `main`, dove `ScipCSharpSyntaxWalker.cs` è identico; Roslyn 5.3.0, quella di scip-dotnet 0.2.16. Le risposte di Roslyn e le occorrenze sono misurate su Modal (`tests/modal_pytest.py`), eShop al commit `913acea`. Nessuna issue di scip-dotnet tratta i due casi (ricerca del 16 novembre: "generic", "GenericName", "method group", "CandidateSymbols").

## In breve

- `ScipCSharpSyntaxWalker` scrive un'occorrenza per ogni `IdentifierNameSyntax` e legge solo `GetSymbolInfo(node).Symbol`. Restano senza occorrenza i nomi con argomenti di tipo (`GenericNameSyntax`: `new List<Order>()`, `AddSingleton<A, B>()`) e i gruppi di metodi convertiti in `System.Delegate` (`app.MapGet("/items", GetItems)`), dove Roslyn non dà un simbolo ma il metodo come unico candidato.
- Su eShop i riferimenti di C# con risposta passano dall'84,7% al 92,1%: dei 966 nomi con argomenti di tipo senza occorrenza ne restano 55, degli altri 997 ne restano 911. È il risultato del passo statico: il resto non è misurato dopo il passo dinamico.
- Daodan costruisce scip-dotnet dal sorgente del rilascio con la patch (`daodan/core/indexers/scip-dotnet.patch`, `daodan/core/indexers/csharp.py`) finché scip-dotnet non la integra. Daodan non invia niente: issue e patch qui sotto sono per il proprietario, se vuole proporle.

## Issue

**Title:** C#: no occurrence at names with type arguments, nor at method groups passed as a `Delegate`

scip-dotnet 0.2.16 (and `main`, whose `ScipCSharpSyntaxWalker.cs` is the same) writes no occurrence at:

1. a name written with type arguments: `new List<Order>()`, `Make<Order>()`, `services.AddSingleton<IFoo, Foo>()`, `typeof(Handler<,>)`. Its type arguments have occurrences; the name does not.
2. a method group converted to `System.Delegate`, the way ASP.NET Core minimal APIs take handlers: `app.MapGet("/items", GetItems)`.

Cause:

1. `ScipCSharpSyntaxWalker` overrides `VisitIdentifierName` only, and a `GenericNameSyntax` is not an `IdentifierNameSyntax`.
2. For a method group converted to `System.Delegate` through its natural type, `SemanticModel.GetSymbolInfo` has no `Symbol` but `CandidateReason.OverloadResolutionFailure` with the method as the only candidate, although the code compiles (Roslyn 5.3.0). `VisitIdentifierName` passes `GetSymbolInfo(node).Symbol`, and `ScipDocumentIndexer.VisitOccurrence` drops a null symbol.

Repro, in a `net10.0` project:

```csharp
static class Routes
{
    public static void MapGet(string pattern, Delegate handler) { }
    public static int Items(int page) => page;
    public static T Make<T>() where T : new() => new T();
    static void Use()
    {
        MapGet("/items", Items);            // no occurrence at Items
        var list = new List<int>();         // none at List
        var made = Make<List<int>>();       // none at Make, none at List
        Type open = typeof(Dictionary<,>);  // none at Dictionary
    }
}
```

On dotnet/eShop (commit 913acea), 966 names with type arguments have no occurrence. With the patch below 911 of them have one, and so do 86 other names, most of them minimal-API handlers such as `CatalogApi.GetAllItemsV1` and `OrdersApi.CancelOrderAsync`.

Suggested fix (the patch below, which applies to 0.2.16 and `main`): a `VisitGenericName` that writes the occurrence at the name's identifier, and in both visitors the bound symbol or, where binding picks none and names exactly one candidate, that candidate. Roslyn's IDE takes a candidate too (`SymbolInfoExtensions.GetAnySymbol`: `info.Symbol ?? info.CandidateSymbols.FirstOrDefault()`); taking it only when it is the only one leaves an ambiguous name without occurrence.

Related, not in the patch: `MethodDisambiguator` compares the referenced symbol with the members of its containing type, and a constructed generic method or a reduced extension method equals none of them, so the reference gets the first overload's symbol (`Make().` for a call of `Make<T>(int)`). With `VisitGenericName` this holds for every call written with type arguments; comparing the symbol's `OriginalDefinition` (`ReducedFrom` for an extension method) would fix it.

## Patch

```diff
--- a/ScipDotnet/ScipCSharpSyntaxWalker.cs
+++ b/ScipDotnet/ScipCSharpSyntaxWalker.cs
@@ -24,3 +24,3 @@
         {
-            _scipDocumentIndexer.VisitOccurrence(_semanticModel.GetSymbolInfo(node).Symbol, node.GetLocation(), false);
+            _scipDocumentIndexer.VisitOccurrence(Referenced(node), node.GetLocation(), false);
         }
@@ -173,2 +173,18 @@
     }
+
+    // A name with type arguments (`List<Order>`, `Make<T>()`) references, at its identifier, what it binds to.
+    public override void VisitGenericName(GenericNameSyntax node)
+    {
+        _scipDocumentIndexer.VisitOccurrence(Referenced(node), node.Identifier.GetLocation(), false);
+        base.VisitGenericName(node);
+    }
+
+    // The symbol a name binds to or, where binding picks none and names one candidate, that candidate: a method group
+    // converted to `System.Delegate` (`app.MapGet("/items", GetItems)`) has no symbol, and its method as the only
+    // candidate (CandidateReason.OverloadResolutionFailure).
+    private ISymbol? Referenced(SimpleNameSyntax node)
+    {
+        var info = _semanticModel.GetSymbolInfo(node);
+        return info.Symbol ?? (info.CandidateSymbols.Length == 1 ? info.CandidateSymbols[0] : null);
+    }
 }
\ No newline at end of file
```
