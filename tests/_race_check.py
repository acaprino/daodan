import test_codebase_map_grammars as grammars

OLD = r'''
import os, shutil
def old_place(home, platform, user_home, fetch):
    digest, size = _treesitter.PACK_BUNDLES[platform]
    bundle = f"{platform}-{digest}.tar.zst"
    wanted = [("manifest.json", _treesitter.manifest_url(), *_treesitter.PACK_MANIFEST),
              (f"bundles/{bundle}", _treesitter.bundle_url(platform), digest, size)]
    (home / "libs").mkdir(parents=True, exist_ok=True)
    for rel, url, digest, size in wanted:
        target = home / rel
        if _treesitter._matches(target, digest, size):
            continue
        target.unlink(missing_ok=True)
        try:
            fetch(url, target, sha256=digest)
        except (OSError, ValueError) as error:
            target.unlink(missing_ok=True)
            return f"download failed: {error}"
        if not _treesitter._matches(target, digest, size):
            target.unlink(missing_ok=True)
            return f"download failed: checksum mismatch for {url}"
    return None
'''


def test_the_old_placing_fails_the_race(tmp_path, monkeypatch):
    placer = grammars.PLACER.replace("while not go.exists():", OLD + "\nwhile not go.exists():").replace(
        "_treesitter.place_grammars(home", "old_place(home")
    monkeypatch.setattr(grammars, "PLACER", placer)
    grammars.test_processes_placing_the_release_at_once_each_find_it_whole(tmp_path)
