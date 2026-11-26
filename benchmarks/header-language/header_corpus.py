"""The corpus of the header-language benchmark: which projects, at which commit, which of their `.h` files, and the
label each one is declared to have. Pure data and rules, standard library only.

A header's declared label is its project's (C, C++, Objective-C), moved by a path prefix where the project mixes
languages (`include/leveldb/c.h` is the C API of a C++ project). The hand annotations of `labels.json` are the only
other source of a label: they say a header of a C++ or Objective-C project is `either` (nothing in it tells C from
C++), or correct the declared one. The sources are never kept here, only the paths and the sha256 of their content.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

SEED = "header-language-1"  # the fixed seed of every cap: the same files are picked every time
LABELS = ("c", "cpp", "objc")


@dataclass(frozen=True)
class Project:
    name: str
    url: str  # the archive: GitHub's `codeload` at the commit, or a release tarball
    pin: str  # the commit (40 hex) or the release the archive is
    license: str  # as the licence file of that commit says
    permissive: bool
    label: str  # the language of the project's headers: c | cpp | objc
    include: tuple[str, ...]  # path prefixes of what is read ("" is everything)
    exclude: tuple[str, ...] = ()  # path prefixes left out: vendored code of another language, tests, samples
    overrides: tuple[tuple[str, str], ...] = ()  # (path prefix, label): a part of the project in another language
    cap: int | None = None  # at most this many headers, picked by the seeded order of their paths
    ref: str = ""  # the tag the commit belongs to
    note: str = ""

    def accepts(self, path: str) -> bool:
        return (path.endswith(".h") and any(path.startswith(prefix) for prefix in self.include)
                and not any(path.startswith(prefix) for prefix in self.exclude))

    def label_of(self, path: str) -> str:
        best = ("", self.label)
        for prefix, label in self.overrides:
            if path.startswith(prefix) and len(prefix) >= len(best[0]):
                best = (prefix, label)
        return best[1]


def strip_root(member: str) -> str:
    """A tar member's path without the archive's own folder (`zlib-51b7f2/zlib.h` is `zlib.h`)."""
    return member.split("/", 1)[1] if "/" in member else ""


def select(project: Project, contents: dict[str, str], seed: str = SEED) -> list[str]:
    """The project's headers: those it accepts, one path for each content (the first by path), capped by the seeded order."""
    seen: set[str] = set()
    kept = []
    for path in sorted(p for p in contents if project.accepts(p)):
        if contents[path] not in seen:
            seen.add(contents[path])
            kept.append(path)
    if project.cap is not None and len(kept) > project.cap:
        kept = sorted(kept, key=lambda p: hashlib.sha256(f"{seed}:{p}".encode()).hexdigest())[:project.cap]
    return sorted(kept)


def fingerprint(contents: dict[str, str]) -> str:
    """One hash for a set of headers (path and content hash): the proof two runs read the same files."""
    digest = hashlib.sha256()
    for path in sorted(contents):
        digest.update(f"{path}\0{contents[path]}\n".encode())
    return digest.hexdigest()


def _gh(repo: str, sha: str) -> str:
    return f"https://codeload.github.com/{repo}/tar.gz/{sha}"


# Licences as the file of each commit says (checked with the GitHub API on 2026-11-24). `permissive` is False for the
# one project whose licence is a copyleft: its sources are only read on Modal, nothing of them is kept.
PROJECTS: tuple[Project, ...] = (
    # --- C -----------------------------------------------------------------------------------------------------
    Project("zlib", _gh("madler/zlib", "51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf"), "51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf",
            "Zlib", True, "c", ("",), exclude=("contrib/iostream", "contrib/testzlib/"), ref="v1.3.1",
            note="contrib/iostream* are C++ wrappers of zlib"),
    Project("redis", _gh("redis/redis", "d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7"), "d2c8a4b91e8c0e6aefd1f5bc0bf582cddbe046b7",
            "BSD-3-Clause", True, "c", ("src/",), ref="7.2.4", note="the last release under the BSD licence; deps/ left out"),
    Project("curl", _gh("curl/curl", "7eb8c048470ed2cc14dca75be9c1cdae7ac8498b"), "7eb8c048470ed2cc14dca75be9c1cdae7ac8498b",
            "curl (MIT-style)", True, "c", ("lib/", "include/", "src/"), ref="curl-8_10_1"),
    Project("libuv", _gh("libuv/libuv", "e1095c7a4373ce00cd8874d8e820de5afb25776e"), "e1095c7a4373ce00cd8874d8e820de5afb25776e",
            "MIT", True, "c", ("include/", "src/"), ref="v1.49.2"),
    Project("cjson", _gh("DaveGamble/cJSON", "acc76239bee01d8e9c858ae2cab296704e52d916"), "acc76239bee01d8e9c858ae2cab296704e52d916",
            "MIT", True, "c", ("",), exclude=("tests/", "fuzzing/"), ref="v1.7.18"),
    Project("jansson", _gh("akheron/jansson", "684e18c927e89615c2d501737e90018f4930d6c5"), "684e18c927e89615c2d501737e90018f4930d6c5",
            "MIT", True, "c", ("",), exclude=("test/",), ref="v2.14"),
    Project("musl", "https://musl.libc.org/releases/musl-1.2.5.tar.gz", "release musl-1.2.5",
            "MIT", True, "c", ("include/", "src/", "arch/"), cap=450, ref="1.2.5",
            note="the release tarball: musl is not on GitHub; arch/ headers are mostly near-copies, the content dedupe drops the exact ones"),
    Project("sqlite", _gh("sqlite/sqlite", "f3d536d37825302e31ed0eddd811c689f38f85a3"), "f3d536d37825302e31ed0eddd811c689f38f85a3",
            "public domain", True, "c", ("src/", "ext/"), ref="version-3.46.1"),
    Project("mbedtls", _gh("Mbed-TLS/mbedtls", "107ea89daaefb9867ea9121002fbbdf926780e98"), "107ea89daaefb9867ea9121002fbbdf926780e98",
            "Apache-2.0 OR GPL-2.0-or-later", True, "c", ("include/", "library/"), ref="v3.6.2"),
    Project("cpython", _gh("python/cpython", "60403a5409ff2c3f3b07dd2ca91a7a3e096839c7"), "60403a5409ff2c3f3b07dd2ca91a7a3e096839c7",
            "PSF-2.0", True, "c", ("Include/",), ref="v3.13.0", note="the headers the C++ extensions include"),
    Project("openssl", _gh("openssl/openssl", "98acb6b02839c609ef5b837794e08d906d965335"), "98acb6b02839c609ef5b837794e08d906d965335",
            "Apache-2.0", True, "c", ("include/", "ssl/", "crypto/"), cap=350, ref="openssl-3.4.0"),
    Project("nginx", _gh("nginx/nginx", "e24f7ccc161f1a2a759eb27263ec9af4fc7c8e96"), "e24f7ccc161f1a2a759eb27263ec9af4fc7c8e96",
            "BSD-2-Clause", True, "c", ("src/",), ref="release-1.27.2"),
    Project("zstd", _gh("facebook/zstd", "794ea1b0afca0f020f4e57b6732332231fb23c70"), "794ea1b0afca0f020f4e57b6732332231fb23c70",
            "BSD-3-Clause OR GPL-2.0", True, "c", ("lib/", "programs/"), ref="v1.5.6"),
    Project("linux", _gh("torvalds/linux", "adc218676eef25575469234709c2d87185ca223a"), "adc218676eef25575469234709c2d87185ca223a",
            "GPL-2.0 WITH Linux-syscall-note", False, "c", ("include/linux/",), cap=350, ref="v6.12",
            note="not permissive: read as text on Modal, only counts and paths are kept"),
    # --- C++ with `.h` headers ---------------------------------------------------------------------------------
    Project("abseil", _gh("abseil/abseil-cpp", "4447c7562e3bc702ade25105912dce503f0c4010"), "4447c7562e3bc702ade25105912dce503f0c4010",
            "Apache-2.0", True, "cpp", ("absl/",), cap=500, ref="20240722.0"),
    Project("leveldb", _gh("google/leveldb", "99b3c03b3284f5886f9ef9a4ef703d57373e61be"), "99b3c03b3284f5886f9ef9a4ef703d57373e61be",
            "BSD-3-Clause", True, "cpp", ("db/", "include/", "table/", "util/", "port/", "helpers/"),
            overrides=(("include/leveldb/c.h", "c"),), ref="1.23", note="c.h is the C API of the library"),
    Project("rocksdb", _gh("facebook/rocksdb", "3c27a3dde0993210c5cc30d99717093f7537916f"), "3c27a3dde0993210c5cc30d99717093f7537916f",
            "Apache-2.0 OR GPL-2.0", True, "cpp", ("include/", "db/", "util/", "table/", "utilities/", "cache/", "memtable/", "env/", "file/", "options/"),
            overrides=(("include/rocksdb/c.h", "c"),), cap=400, ref="v9.7.4", note="java/ (JNI headers) and third-party/ left out"),
    Project("googletest", _gh("google/googletest", "b514bdc898e2951020cbdca1304b75f5950d1f59"), "b514bdc898e2951020cbdca1304b75f5950d1f59",
            "BSD-3-Clause", True, "cpp", ("googletest/include/", "googletest/src/", "googlemock/include/", "googlemock/src/"), ref="v1.15.2"),
    Project("protobuf", _gh("protocolbuffers/protobuf", "5fda5abda3dee5f7a102c85860594bff8d8610bd"), "5fda5abda3dee5f7a102c85860594bff8d8610bd",
            "BSD-3-Clause", True, "cpp", ("src/google/protobuf/",), cap=450, ref="v28.3"),
    Project("llvm", _gh("llvm/llvm-project", "ab51eccf88f5321e7c60591c5546b254b6afab99"), "ab51eccf88f5321e7c60591c5546b254b6afab99",
            "Apache-2.0 WITH LLVM-exception", True, "cpp", ("llvm/include/llvm/", "llvm/include/llvm-c/"),
            overrides=(("llvm/include/llvm-c/", "c"),), cap=500, ref="llvmorg-19.1.3", note="llvm-c/ is the C API of LLVM"),
    Project("fmt", _gh("fmtlib/fmt", "0c9fce2ffefecfdce794e1859584e25877b7b592"), "0c9fce2ffefecfdce794e1859584e25877b7b592",
            "MIT", True, "cpp", ("include/", "src/"), ref="11.0.2"),
    Project("spdlog", _gh("gabime/spdlog", "27cb4c76708608465c413f6d0e6b8d99a4d84302"), "27cb4c76708608465c413f6d0e6b8d99a4d84302",
            "MIT", True, "cpp", ("include/",), ref="v1.14.1"),
    Project("cppwinrt", _gh("microsoft/cppwinrt", "d2a66776bb16e1da9dac60770c977e847485e24b"), "d2a66776bb16e1da9dac60770c977e847485e24b",
            "MIT", True, "cpp", ("cppwinrt/", "strings/", "test/"), cap=200, ref="2.0.240405.15", note="Windows C++"),
    Project("wil", _gh("microsoft/wil", "f0c6a81c0c9a4b23b6801f40554b8bec425a83b4"), "f0c6a81c0c9a4b23b6801f40554b8bec425a83b4",
            "MIT", True, "cpp", ("include/", "tests/"), ref="v1.0.240803.1", note="Windows C++"),
    Project("bitcoin", _gh("bitcoin/bitcoin", "110183746150428e6385880c79f8c5733b1361ba"), "110183746150428e6385880c79f8c5733b1361ba",
            "MIT", True, "cpp", ("src/",), exclude=("src/secp256k1/", "src/leveldb/", "src/crc32c/", "src/minisketch/", "src/univalue/", "src/crypto/ctaes/"),
            cap=450, ref="v28.0", note="the vendored C and C++ subtrees left out"),
    Project("snappy", _gh("google/snappy", "2c94e11145f0b7b184b831577c93e5a41c4c0346"), "2c94e11145f0b7b184b831577c93e5a41c4c0346",
            "BSD-3-Clause", True, "cpp", ("",), exclude=("third_party/",), ref="1.2.1"),
    # --- Objective-C -------------------------------------------------------------------------------------------
    Project("afnetworking", _gh("AFNetworking/AFNetworking", "ffae2391ab0c29dc88eb0a58d2f5b2c2c27cadbf"), "ffae2391ab0c29dc88eb0a58d2f5b2c2c27cadbf",
            "MIT", True, "objc", ("AFNetworking/", "UIKit+AFNetworking/"), ref="4.0.1"),
    Project("sdwebimage", _gh("SDWebImage/SDWebImage", "8a1be70a625683bc04d6903e2935bf23f3c6d609"), "8a1be70a625683bc04d6903e2935bf23f3c6d609",
            "MIT", True, "objc", ("SDWebImage/",), ref="5.19.7"),
    Project("reactiveobjc", _gh("ReactiveCocoa/ReactiveObjC", "27a7254837bb01122b51aac7c4c3961973351ca0"), "27a7254837bb01122b51aac7c4c3961973351ca0",
            "MIT", True, "objc", ("ReactiveObjC/",), ref="3.1.1"),
    Project("iglistkit", _gh("Instagram/IGListKit", "baf38ea4d438ef3cc6c6deb8615e1910e03f02bb"), "baf38ea4d438ef3cc6c6deb8615e1910e03f02bb",
            "MIT", True, "objc", ("Source/",), ref="5.0.0"),
    Project("mantle", _gh("Mantle/Mantle", "16f72bfe72a2ab29654ba894da1c32b17524e1a6"), "16f72bfe72a2ab29654ba894da1c32b17524e1a6",
            "MIT", True, "objc", ("Mantle/",), ref="2.2.0"),
)
