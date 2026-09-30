# App Analyzer Plugin

> Comprehensive app analysis for Android (ADB) and web (Playwright MCP). Auto-detects platform. Phase 1 maps the full navigation structure with exhaustive BFS exploration. Phase 2 analyzes design system, UX patterns, psychology, business model, and generates competitive intelligence reports.

## Agents

### `app-analyzer`

Unified app analysis agent that auto-detects platform and runs a two-phase analysis pipeline.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Competitor app analysis, navigation mapping, design system extraction, UX audits |

**Invocation:**
```
Use the app-analyzer agent to analyze [app name or URL]
```

**Phase 0: Setup and platform detection**
- Runs `adb devices`: a listed device selects mobile mode (Android via ADB). Otherwise a provided URL with the Playwright MCP tools available selects web mode. With neither, it stops and asks for a device or a URL
- Web mode needs the Playwright MCP tools; when they are missing it stops and prints the install command for the `playwright` plugin
- Creates `.app-analyzer/screenshots/` and initializes `.app-analyzer/sitemap.json`, or loads it to resume a previous session
- Authentication: in web mode with credentials it fills and submits the login form itself and confirms the logged-in state; without credentials it asks the user to log in manually in the browser and waits. In mobile mode it asks the user to log in on the device

**Phase 1: Navigation Mapping**
- Exhaustive BFS exploration: every interactive element on every discovered screen is clicked before exploration may be declared complete, with overlays and modals explored depth-first as mini-screens
- Platform-specific operations (ADB for Android, Playwright MCP for web)
- Screenshots, UI hierarchy dumps or accessibility snapshots, and navigation flow documentation
- Safe by rule: forms get dummy data, nothing that permanently modifies real data is submitted, and destructive actions (delete, remove, log out, cancel subscription) are cataloged but never clicked
- SPA fingerprinting (URL, headings, active navigation, overlays) that ignores volatile content, so a timestamp or counter change never counts as a new screen
- Safety stop at 50 visited screens or 150 interactions: it asks whether to continue exploring or finalize the sitemap
- `sitemap.json` is updated incrementally after each screen, with the navigation graph and the shortest click path to each screen; a completeness self-audit runs before finalizing
- User can stop after Phase 1

**Phase 2: Competitive Intelligence**
- Design system extraction (colors, typography, spacing, components)
- UX pattern analysis and psychology
- Business model intelligence
- Key user journeys as Mermaid flowcharts
- Writes three reports: `docs/{APP}_ANALYSIS.md` (structured competitive analysis), `docs/{APP}_USER_FLOWS.md` (Mermaid flowcharts) and `docs/{APP}_REPORT.html` (visual report with a screenshot gallery)

**Output layout:**

```
.app-analyzer/
  sitemap.json              # Phase 1 output, also the resume state
  screenshots/
    screen_001_home.png
    ...
docs/
  {APP}_ANALYSIS.md         # Phase 2 output
  {APP}_USER_FLOWS.md       # Phase 2 output
  {APP}_REPORT.html         # Phase 2 output
```

The three Phase 2 reports follow the templates in the plugin's `app-analysis` skill (`references/report-templates.md`), which the agent reads when it writes them.

**Supported platforms:**

| Operation | ADB (Android) | Playwright MCP (Web) |
|-----------|---------------|---------------------|
| Screenshots | `adb exec-out screencap` | `browser_take_screenshot` |
| UI hierarchy | `adb shell uiautomator dump` | `browser_snapshot` (accessibility tree) |
| Tap | `adb shell input tap` | `browser_click` |
| Fill | `adb shell input text` | `browser_fill_form` |
| Back and scroll | `adb shell input keyevent` / `swipe` | `browser_press_key` |
| Wait | `sleep 1` | `browser_wait_for` |

---

**Related:** `playwright@claude-plugins-official` (Microsoft's Playwright MCP server, required for web app exploration; install: `claude plugin install playwright@claude-plugins-official`) | [tauri-development](tauri-development.md) (scaffolds Tauri 2 mobile apps from analysis output)
