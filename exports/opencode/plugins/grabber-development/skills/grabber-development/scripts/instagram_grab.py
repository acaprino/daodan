#!/usr/bin/env python3
"""Download every photo and video from an Instagram profile.

The collection strategy is capture-and-replay, never a forged request. The
script drives a real logged-in browser to the profile, keeps one genuine
PolarisProfilePostsTabContentQuery_connection request that Instagram's own
client issues, and then walks the whole timeline by re-posting that request with
only the cursor swapped. No doc_id, fb_dtsg, lsd or jazoest value is ever
invented here: every one of them comes from a request that was actually
observed.

Media files are served by the fbcdn edge with a signed URL that needs no
authentication, so the download stage is plain HTTP and runs concurrently.

Usage:
    python instagram_grab.py <username> [--out DIR] [--limit N] ...

Requires: playwright (with the Chrome channel or bundled chromium).
Optional: curl_cffi for TLS impersonation on the CDN download stage.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is required: pip install playwright && playwright install chromium")

# ---------------------------------------------------------------------------
# Constants discovered by observation, not by guessing. See
# references/instagram-media.md for the capture that produced each one.
# ---------------------------------------------------------------------------

GRAPHQL_PATH = "/graphql/query"
PROFILE_POSTS_OP = "PolarisProfilePostsTabContentQuery_connection"
CONNECTION_KEY = "xdt_api__v1__feed__user_timeline_graphql_connection"
PAGE_SIZE = 12

MEDIA_IMAGE = 1
MEDIA_VIDEO = 2
MEDIA_CAROUSEL = 8

LOGIN_URL = "https://www.instagram.com/accounts/login/"
DEFAULT_SESSION = Path(os.path.expanduser("~/.instagram-grabber/session.json"))

# The login page dropped name="username" and name="password" in 2026. These are
# the attributes the form actually carries, and the submit control is a div with
# role=button rather than a submit input.
LOGIN_USER_SELECTOR = 'input[name="email"]'
LOGIN_PASS_SELECTOR = 'input[name="pass"]'
COOKIE_BUTTONS = (
    "Consenti tutti i cookie",
    "Allow all cookies",
    "Rifiuta cookie facoltativi",
    "Decline optional cookies",
)
SUBMIT_LABELS = ("Accedi", "Log in", "Log In")
DISMISS_LABELS = ("Non ora", "Not now")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)

MANIFEST_NAME = "_manifest.json"
WINDOWS_RESERVED = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Exit codes, so a caller can tell a truncated archive from a complete one.
EXIT_OK = 0
EXIT_DOWNLOAD_FAILURES = 1
EXIT_BAD_ARGUMENTS = 2
EXIT_NO_SESSION = 3
EXIT_NO_PROFILE = 4
EXIT_INCOMPLETE_WALK = 5

STOP = threading.Event()


def log(msg: str) -> None:
    print(f"[ig] {msg}", flush=True)


def chmod_private(path: Path) -> None:
    """Best effort. On Windows the bits are advisory, but the call is harmless
    and on any POSIX host it is what keeps a live session cookie private."""
    try:
        os.chmod(path, 0o600 if path.is_file() else 0o700)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def launch_browser(pw, headless: bool):
    """Prefer the installed Chrome. Its fingerprint survives Instagram far
    better than the bundled chromium build does."""
    args = ["--disable-blink-features=AutomationControlled"]
    try:
        return pw.chromium.launch(channel="chrome", headless=headless, args=args)
    except Exception:
        return pw.chromium.launch(headless=headless, args=args)


def save_session(ctx, path: Path) -> None:
    try:
        ctx.storage_state(path=str(path))
        chmod_private(path)
    except Exception as exc:
        log(f"could not save the session: {exc}")


def click_by_label(page, labels, timeout=2500) -> str | None:
    for label in labels:
        try:
            button = page.get_by_role("button", name=label, exact=False).first
            if button.is_visible(timeout=timeout):
                button.click(timeout=8000)
                page.wait_for_timeout(2000)
                return label
        except Exception:
            continue
    return None


def do_login(ctx, page, username: str | None, password: str | None, wait_seconds: int) -> bool:
    """Interactive login. Credentials are optional: without them the user types
    into the visible window instead, which is also the path a two-factor
    challenge takes."""
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    # The Meta cookie dialog is an overlay that swallows every click underneath
    # it, so it has to go first or the submit control is unreachable.
    dismissed = click_by_label(page, COOKIE_BUTTONS)
    log(f"cookie dialog: {dismissed or 'not shown'}")

    if username and password:
        try:
            page.fill(LOGIN_USER_SELECTOR, username, timeout=20000)
            page.fill(LOGIN_PASS_SELECTOR, password, timeout=20000)
            if not click_by_label(page, SUBMIT_LABELS, timeout=6000):
                page.locator(LOGIN_PASS_SELECTOR).press("Enter")
            log("credentials submitted")
        except Exception as exc:
            log(f"could not fill the form, falling back to manual login: {exc}")
    else:
        log("no credentials supplied, waiting for a manual login in the browser window")

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if "sessionid" in {c["name"] for c in ctx.cookies()}:
            click_by_label(page, DISMISS_LABELS, timeout=2500)
            return True
        page.wait_for_timeout(3000)
    return False


PROFILE_OK = "ok"
PROFILE_TIMEOUT = "timeout"
PROFILE_SESSION_DEAD = "session-dead"


def wait_for_profile(page, username: str, wait_seconds: int) -> str:
    """Reach the profile grid, parking on anything that blocks the way.

    In the EU a logged-in account is pushed to
    /consent/?flow=ad_free_subscription before it may browse. That is a
    pay-or-consent decision belonging to the account owner, so the script waits
    for a human to answer it rather than clicking through on their behalf.

    A stored session that has been revoked lands on /accounts/login instead, and
    that case is reported separately so the caller can log in again rather than
    waiting out the whole timeout on a page that will never change.
    """
    profile_url = f"https://www.instagram.com/{username}/"
    page.goto(profile_url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)

    announced = False
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        url = page.url
        if "/accounts/login" in url:
            return PROFILE_SESSION_DEAD
        if "/consent/" in url or "/accounts/onetap" in url:
            if not announced:
                log("blocked by a consent or one-tap screen: answer it in the browser window")
                announced = True
            page.wait_for_timeout(4000)
            continue
        if username not in url:
            try:
                page.goto(profile_url, wait_until="domcontentloaded", timeout=45000)
            except Exception:
                pass
            page.wait_for_timeout(4000)
        try:
            links = page.evaluate(
                "() => document.querySelectorAll('a[href*=\"/p/\"],a[href*=\"/reel/\"]').length"
            )
        except Exception:
            links = 0
        if username in page.url and links >= 1:
            return PROFILE_OK
        page.wait_for_timeout(4000)
    return PROFILE_TIMEOUT


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------

REPLAY_JS = """
async (args) => {
  const params = new URLSearchParams(args.body);
  const variables = JSON.parse(params.get('variables'));
  variables.after = args.after;
  variables.before = null;
  variables.first = args.first;
  variables.last = null;
  params.set('variables', JSON.stringify(variables));
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const res = await fetch(args.path, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'content-type': 'application/x-www-form-urlencoded',
      'x-csrftoken': csrf,
      'x-fb-friendly-name': params.get('fb_api_req_friendly_name') || '',
      'x-requested-with': 'XMLHttpRequest',
    },
    body: params.toString(),
  });
  return { status: res.status, text: await res.text() };
}
"""

WALK_COMPLETE = "complete"
WALK_LIMIT = "limit-reached"
WALK_NO_TEMPLATE = "no-template"
WALK_HTTP_ERROR = "http-error"
WALK_UNPARSABLE = "unparsable-page"
WALK_CURSOR_LOOP = "cursor-loop"
WALK_NOT_RUN = "not-run"


class Collector:
    """Captures one genuine profile-posts request, then walks the timeline with it.

    Two rules keep this honest, and both exist because breaking either produces a
    truncated archive that looks complete.

    First, pagination starts from a null cursor. Instagram ships the newest 24
    posts inside the initial page payload and only issues
    PolarisProfilePostsTabContentQuery_connection from post 25 onward, so a
    collector that merely listens never sees the most recent posts.

    Second, the response listener never writes into self.nodes. Its only job is
    to capture a replay template. The loop measures its own progress by what each
    page returned, and a background listener racing into the same dict, including
    on the loop's own replayed fetches, makes a page of brand new posts look like
    a page of duplicates.
    """

    def __init__(self, page, username: str):
        self.page = page
        self.username = username
        self.nodes: dict[str, dict] = {}
        self.template: str | None = None
        self.status: str = WALK_NOT_RUN
        self.pages_walked = 0
        page.on("response", self._on_response)

    def _on_response(self, response) -> None:
        if self.template is not None:
            return
        try:
            if GRAPHQL_PATH not in urlparse(response.url).path:
                return
            body = response.request.post_data or ""
            if PROFILE_POSTS_OP in body:
                self.template = body
        except Exception:
            return

    def _stop_listening(self) -> None:
        try:
            self.page.remove_listener("response", self._on_response)
        except Exception:
            pass

    def _ingest(self, text: str) -> tuple[bool, int, int, str | None, bool]:
        """Returns (parsed_ok, edges_on_page, newly_added, end_cursor, has_next)."""
        try:
            payload = json.loads(text)
        except Exception:
            return False, 0, 0, None, False
        connection = (payload.get("data") or {}).get(CONNECTION_KEY)
        if not isinstance(connection, dict):
            return False, 0, 0, None, False
        edges = connection.get("edges") or []
        added = 0
        for edge in edges:
            node = (edge or {}).get("node") or {}
            code = node.get("code")
            if code and code not in self.nodes:
                self.nodes[code] = node
                added += 1
        info = connection.get("page_info") or {}
        return True, len(edges), added, info.get("end_cursor"), bool(info.get("has_next_page"))

    def prime(self, attempts: int = 6) -> None:
        """Wait for the page to issue one genuine paginated query, which is what
        hands us a replay template. The profile normally fires it during the
        initial load, so this usually returns without scrolling at all."""
        for _ in range(attempts):
            if self.template:
                return
            try:
                self.page.mouse.wheel(0, 3000)
            except Exception:
                return
            self.page.wait_for_timeout(2500)

    def walk(self, limit: int | None, delay: float) -> str:
        if not self.template:
            # A profile with 24 or fewer posts never makes the client paginate,
            # so no template exists to replay. Say so rather than returning an
            # empty archive that reads as an empty profile.
            self.status = WALK_NO_TEMPLATE
            return self.status

        self._stop_listening()
        cursor: str | None = None      # None asks for page one, the newest posts
        seen_cursors: set[str] = set()

        while True:
            if STOP.is_set():
                self.status = WALK_LIMIT
                return self.status
            try:
                result = self.page.evaluate(
                    REPLAY_JS,
                    {"body": self.template, "after": cursor,
                     "first": PAGE_SIZE, "path": GRAPHQL_PATH},
                )
            except Exception as exc:
                log(f"replay failed on page {self.pages_walked + 1}: {exc}")
                self.status = WALK_HTTP_ERROR
                return self.status

            if result.get("status") != 200:
                log(f"replay returned HTTP {result.get('status')} on page {self.pages_walked + 1}")
                self.status = WALK_HTTP_ERROR
                return self.status

            text = result.get("text") or ""
            ok, edges, added, next_cursor, has_next = self._ingest(text)
            if not ok:
                log(f"page {self.pages_walked + 1} had no connection object: {text[:200]}")
                self.status = WALK_UNPARSABLE
                return self.status

            self.pages_walked += 1
            log(f"page {self.pages_walked}: {edges} posts, +{added} new, {len(self.nodes)} total")

            if limit and len(self.nodes) >= limit:
                self.status = WALK_LIMIT
                return self.status
            if edges == 0 or not has_next or not next_cursor:
                self.status = WALK_COMPLETE
                return self.status
            if next_cursor in seen_cursors:
                log("the cursor repeated, so the feed is looping rather than advancing")
                self.status = WALK_CURSOR_LOOP
                return self.status

            seen_cursors.add(next_cursor)
            cursor = next_cursor
            time.sleep(delay)


# ---------------------------------------------------------------------------
# Media selection
# ---------------------------------------------------------------------------

def _area(entry: dict) -> int:
    return (entry.get("width") or 0) * (entry.get("height") or 0)


def best_image(media: dict) -> dict | None:
    candidates = [
        c for c in ((media.get("image_versions2") or {}).get("candidates") or [])
        if isinstance(c, dict) and c.get("url")
    ]
    if not candidates:
        return None
    return max(candidates, key=_area)


def best_video(media: dict) -> dict | None:
    versions = [v for v in (media.get("video_versions") or []) if isinstance(v, dict) and v.get("url")]
    if not versions:
        return None

    def rank(version: dict) -> tuple[int, int]:
        kind = version.get("type")
        # One resolution is often published under several type ids. The lowest
        # id is the progressive mp4, so prefer it, and sort a missing id last
        # rather than letting it win by accident.
        ordinal = -int(kind) if isinstance(kind, int) else -(10 ** 9)
        return _area(version), ordinal

    return max(versions, key=rank)


def extension_for(url: str, fallback: str) -> str:
    ext = os.path.splitext(urlparse(url).path)[1].lower()
    return ext if ext in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".heic") else fallback


def safe_name(text: str) -> str:
    return WINDOWS_RESERVED.sub("_", text).strip(". ")


def plan_downloads(node: dict, want_photos: bool, want_videos: bool, want_covers: bool) -> list[dict]:
    """Flatten one post into the files it should produce."""
    code = node.get("code")
    taken_at = node.get("taken_at") or 0
    day = (
        datetime.fromtimestamp(taken_at, tz=timezone.utc).strftime("%Y-%m-%d")
        if taken_at else "0000-00-00"
    )

    children = node.get("carousel_media") or []
    if node.get("media_type") == MEDIA_CAROUSEL and children:
        parts = list(enumerate(children, start=1))
    else:
        parts = [(0, node)]

    items: list[dict] = []
    for index, media in parts:
        suffix = f"_{index:02d}" if index else ""
        is_video = (media.get("media_type") == MEDIA_VIDEO) or bool(media.get("video_versions"))

        def add(kind: str, chosen: dict | None, tail: str, fallback_ext: str) -> None:
            if not chosen:
                return
            items.append({
                "code": code, "index": index, "kind": kind, "url": chosen["url"],
                "name": safe_name(f"{day}_{code}{suffix}{tail}{extension_for(chosen['url'], fallback_ext)}"),
                "width": chosen.get("width"), "height": chosen.get("height"),
            })

        if is_video:
            if want_videos:
                chosen = best_video(media)
                if chosen is None:
                    log(f"{code}#{index}: marked as video but carries no video_versions")
                add("video", chosen, "", ".mp4")
            # A cover is a still, so it is independent of whether the video
            # stream itself was wanted.
            if want_covers:
                add("cover", best_image(media), "_cover", ".jpg")
        elif want_photos:
            chosen = best_image(media)
            if chosen is None:
                log(f"{code}#{index}: no image candidate carried a url")
            add("photo", chosen, "", ".jpg")
    return items


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def make_fetcher():
    """curl_cffi when available for a real TLS fingerprint, urllib otherwise.

    The fetcher streams into the destination handle rather than returning bytes,
    so a 200 MB archive never sits in memory and a stalled transfer is a stall
    rather than a hard cap on total duration.
    """
    headers = {"User-Agent": UA, "Referer": "https://www.instagram.com/", "Accept": "*/*"}
    try:
        from curl_cffi import requests as cffi

        session = cffi.Session(impersonate="chrome")
        session.headers.update(headers)

        def fetch(url: str, handle) -> tuple[int, int | None]:
            with session.get(url, stream=True, timeout=(30, 300)) as response:
                response.raise_for_status()
                declared = response.headers.get("content-length")
                written = 0
                for chunk in response.iter_content(chunk_size=262144):
                    if STOP.is_set():
                        raise RuntimeError("interrupted")
                    if chunk:
                        handle.write(chunk)
                        written += len(chunk)
                return written, int(declared) if declared and declared.isdigit() else None

        return fetch, "curl_cffi"
    except ImportError:
        import urllib.request

        def fetch(url: str, handle) -> tuple[int, int | None]:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=120) as response:
                declared = response.headers.get("Content-Length")
                shutil.copyfileobj(response, handle, 262144)
                return handle.tell(), int(declared) if declared and declared.isdigit() else None

        return fetch, "urllib"


PERMANENT = ("403", "404", "410")


def download_one(fetch, item: dict, out_dir: Path, retries: int = 3) -> tuple[str, str, int]:
    target = out_dir / item["name"]
    if target.exists() and target.stat().st_size > 0:
        return item["name"], "skipped", target.stat().st_size

    # A per-thread temp name, because two workers sharing one .part file would
    # interleave their bytes into a single corrupt result.
    part = target.with_suffix(f"{target.suffix}.{os.getpid()}.{threading.get_ident()}.part")
    last_error: Exception | None = None

    for attempt in range(retries):
        if STOP.is_set():
            part.unlink(missing_ok=True)
            return item["name"], "cancelled", 0
        try:
            with part.open("wb") as handle:
                written, declared = fetch(item["url"], handle)
            if written == 0:
                raise ValueError("empty response")
            if declared is not None and written != declared:
                raise ValueError(f"short read: {written} of {declared} bytes")
            part.replace(target)
            return item["name"], "downloaded", written
        except Exception as exc:
            last_error = exc
            part.unlink(missing_ok=True)
            message = str(exc)
            if any(code in message for code in PERMANENT):
                break
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))

    return item["name"], f"failed: {last_error}", 0


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def load_manifest(path: Path) -> dict:
    empty = {"version": 1, "posts": {}}
    if not path.exists():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        broken = path.with_suffix(".json.corrupt")
        log(f"manifest is unreadable ({exc}), keeping it at {broken.name} and starting a new one")
        try:
            path.replace(broken)
        except OSError:
            pass
        return empty
    if not isinstance(data, dict) or not isinstance(data.get("posts"), dict):
        log("manifest has an unexpected shape, starting a new one")
        return empty
    return data


def save_manifest(path: Path, manifest: dict, username: str, walk_status: str) -> None:
    manifest["username"] = username
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest["last_walk"] = walk_status
    manifest["complete"] = walk_status in (WALK_COMPLETE, WALK_LIMIT)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return number


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="instagram_grab",
        description="Download every photo and video from an Instagram profile.",
    )
    parser.add_argument("username", help="profile to grab, without the @")
    parser.add_argument("--out", type=Path, default=None, help="output directory (default ./ig-<username>)")
    parser.add_argument("--session", type=Path, default=DEFAULT_SESSION, help="browser storage state file")
    parser.add_argument("--login", action="store_true", help="force the login flow even if a session exists")
    parser.add_argument("--limit", type=positive_int, default=None, help="stop after N posts")
    parser.add_argument("--since", default=None, help="keep only posts newer than YYYY-MM-DD")
    parser.add_argument("--no-photos", action="store_true", help="skip still images")
    parser.add_argument("--no-videos", action="store_true", help="skip videos and reels")
    parser.add_argument("--covers", action="store_true", help="also save each video's cover image")
    parser.add_argument("--metadata", action="store_true", help="record captions and permalinks in the manifest")
    parser.add_argument("--concurrency", type=positive_int, default=5, help="parallel downloads (default 5)")
    parser.add_argument("--delay", type=float, default=1.2, help="seconds between pagination calls")
    parser.add_argument("--headless", action="store_true", help="run the browser headless (login needs headful)")
    parser.add_argument("--wait", type=int, default=300, help="seconds allowed for login and consent screens")
    parser.add_argument("--dry-run", action="store_true", help="collect and report, download nothing")
    return parser.parse_args(argv)


def collect(args, username: str) -> tuple[dict[str, dict], str, int]:
    """Returns (nodes, walk_status, exit_code_if_fatal)."""
    with sync_playwright() as pw:
        browser = launch_browser(pw, args.headless)
        state = str(args.session) if args.session.exists() and not args.login else None

        def new_context(bro):
            return bro.new_context(
                storage_state=state, locale="it-IT", timezone_id="Europe/Rome",
                user_agent=UA, viewport={"width": 1440, "height": 960},
            )

        ctx = new_context(browser)
        page = ctx.new_page()
        try:
            if state is None:
                if args.headless:
                    log("a login is needed and it cannot run headless, reopening with a window")
                    ctx.close(); browser.close()
                    browser = launch_browser(pw, headless=False)
                    ctx = new_context(browser)
                    page = ctx.new_page()
                if not do_login(ctx, page, os.environ.get("IG_USER"), os.environ.get("IG_PASS"), args.wait):
                    log("login did not complete")
                    return {}, WALK_NOT_RUN, EXIT_NO_SESSION
                save_session(ctx, args.session)
                log(f"session saved to {args.session}")

            collector = Collector(page, username)
            outcome = wait_for_profile(page, username, args.wait)

            if outcome == PROFILE_SESSION_DEAD:
                log("the stored session is no longer valid, logging in again")
                if not do_login(ctx, page, os.environ.get("IG_USER"), os.environ.get("IG_PASS"), args.wait):
                    return {}, WALK_NOT_RUN, EXIT_NO_SESSION
                save_session(ctx, args.session)
                outcome = wait_for_profile(page, username, args.wait)

            # Persist before collecting, so an answered consent screen is kept
            # even when the walk itself goes on to fail.
            save_session(ctx, args.session)

            if outcome != PROFILE_OK:
                log(f"could not reach the profile grid of @{username}")
                return {}, WALK_NOT_RUN, EXIT_NO_PROFILE

            collector.prime()
            status = collector.walk(args.limit, args.delay)
            save_session(ctx, args.session)
            return collector.nodes, status, EXIT_OK
        finally:
            try:
                browser.close()
            except Exception:
                pass


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    username = args.username.lstrip("@")
    out_dir = args.out or Path(f"ig-{username}")
    out_dir.mkdir(parents=True, exist_ok=True)
    args.session.parent.mkdir(parents=True, exist_ok=True)
    chmod_private(args.session.parent)

    since_ts = None
    if args.since:
        try:
            since_ts = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            log("--since needs the form YYYY-MM-DD")
            return EXIT_BAD_ARGUMENTS

    want_photos = not args.no_photos
    want_videos = not args.no_videos
    if not want_photos and not want_videos and not args.covers:
        log("nothing to do: photos, videos and covers are all switched off")
        return EXIT_BAD_ARGUMENTS

    nodes, walk_status, fatal = collect(args, username)
    if fatal:
        return fatal

    if walk_status == WALK_NO_TEMPLATE:
        log("Instagram never issued the timeline query for this profile, so nothing could be "
            "collected. This happens on profiles with 24 or fewer posts, whose entire grid "
            "arrives in the initial page payload.")
        return EXIT_INCOMPLETE_WALK

    log(f"{len(nodes)} posts collected, walk ended as: {walk_status}")
    if walk_status not in (WALK_COMPLETE, WALK_LIMIT):
        log("WARNING: this archive is INCOMPLETE. Re-run to finish the timeline.")
    if not nodes:
        return EXIT_INCOMPLETE_WALK

    manifest = load_manifest(out_dir / MANIFEST_NAME)
    ordered = sorted(nodes.values(), key=lambda n: n.get("taken_at") or 0, reverse=True)
    if since_ts:
        ordered = [n for n in ordered if (n.get("taken_at") or 0) >= since_ts]
    if args.limit:
        ordered = ordered[: args.limit]

    items: list[dict] = []
    planned_by_code: dict[str, list[str]] = {}
    for node in ordered:
        planned = plan_downloads(node, want_photos, want_videos, args.covers)
        items.extend(planned)
        planned_by_code[node["code"]] = [i["name"] for i in planned]

    photos = sum(1 for i in items if i["kind"] == "photo")
    videos = sum(1 for i in items if i["kind"] == "video")
    covers = sum(1 for i in items if i["kind"] == "cover")
    log(f"{len(items)} files planned: {photos} photos, {videos} videos, {covers} covers")

    if args.dry_run:
        for item in items[:20]:
            log(f"  would fetch {item['name']} ({item['width']}x{item['height']})")
        if len(items) > 20:
            log(f"  ... and {len(items) - 20} more")
        log("dry run, nothing was downloaded and the manifest was left untouched")
        return EXIT_OK

    fetch, backend = make_fetcher()
    log(f"downloading with {backend}, {args.concurrency} workers, into {out_dir}")

    done = failed = skipped = 0
    total_bytes = 0
    landed: set[str] = set()
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {pool.submit(download_one, fetch, item, out_dir): item for item in items}
            try:
                for future in as_completed(futures):
                    name, status, size = future.result()
                    if status == "downloaded":
                        done += 1; total_bytes += size; landed.add(name)
                    elif status == "skipped":
                        skipped += 1; landed.add(name)
                    elif status == "cancelled":
                        pass
                    else:
                        failed += 1
                        log(f"  {name}: {status}")
                    if (done + skipped + failed) % 50 == 0:
                        log(f"  progress {done + skipped + failed}/{len(items)}")
            except KeyboardInterrupt:
                STOP.set()
                log("interrupted, cancelling queued downloads")
                pool.shutdown(wait=False, cancel_futures=True)
                raise
    except KeyboardInterrupt:
        pass

    # The manifest records what is actually on disk, never what was merely planned.
    for node in ordered:
        got = [name for name in planned_by_code.get(node["code"], []) if name in landed]
        entry = manifest["posts"].setdefault(node["code"], {})
        entry.update({
            "taken_at": node.get("taken_at"),
            "media_type": node.get("media_type"),
            "product_type": node.get("product_type"),
            "files": sorted(set(entry.get("files") or []) | set(got)),
        })
        if args.metadata:
            caption = node.get("caption")
            entry["caption"] = caption.get("text") if isinstance(caption, dict) else None
            entry["permalink"] = f"https://www.instagram.com/p/{node['code']}/"
            entry["accessibility_caption"] = node.get("accessibility_caption")

    save_manifest(out_dir / MANIFEST_NAME, manifest, username, walk_status)
    log(f"done: {done} downloaded, {skipped} already present, {failed} failed, "
        f"{total_bytes / 1_048_576:.1f} MB, in {out_dir}")

    if walk_status not in (WALK_COMPLETE, WALK_LIMIT):
        return EXIT_INCOMPLETE_WALK
    return EXIT_OK if failed == 0 else EXIT_DOWNLOAD_FAILURES


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
