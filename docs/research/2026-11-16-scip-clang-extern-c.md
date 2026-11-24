# scip-clang: i nomi dichiarati in `extern "C"`

**Stato:** In uso: il buco è dichiarato dal passo statico (`daodan/core/indexers/clang.py`, `EXTERN_C`), e la PR upstream che lo chiude non è in un rilascio.

**Verifica delle fonti:** 16 novembre 2026, scip-clang v0.4.1; occorrenze misurate su Modal (`tests/modal_pytest.py`).

- In C++ scip-clang v0.4.1 non scrive occorrenze per ciò che è dichiarato in un blocco `extern "C"`: le funzioni della libreria C (`printf`, `fopen`, `strlen`: glibc le dichiara in `__BEGIN_DECLS`) e il C del progetto. `SymbolFormatter::getContextSymbol` non tratta `LinkageSpecDecl` ("Pending: LinkageSpecDecl") e restituisce `nullopt`. Su tinyxml2 sono 91 chiamate.
- Upstream: issue [#544](https://github.com/sourcegraph/scip-clang/issues/544), correzione nella PR [#548](https://github.com/sourcegraph/scip-clang/pull/548) (aperta). Il cambiamento è di quattro righe: un `LinkageSpecDecl` è un contesto trasparente.
- Daodan non compila una scip-clang con la patch, perché costerebbe troppo a ogni utente: l'LLVM 21.1.8 di Bazel pesa 2,02 GB e servono circa 20 GB di disco e da 40 a 70 minuti su 8 core. Il buco resta dichiarato (`daodan/core/indexers/clang.py`, `EXTERN_C`). Quando esce un rilascio con #548, va adottato quello.
- Dopo il passo dinamico: su tinyxml2 l'osservatore di C e C++ registra 552 siti e chiude 26 buchi ([`benchmarks/project-model`, «Il grafo completo sul corpus»](../../benchmarks/project-model/README.md#il-grafo-completo-sul-corpus)); quante delle 91 chiamate sono fra quei 26 non è misurato.
