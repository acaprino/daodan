# Daodan's window on a real WebView2, on a runner of GitHub Actions (desktop.yml). It starts and ends Daodan, and ends whatever
# of Daodan it finds in the folder it makes: not for a machine somebody works on.
#   -Folder  the folder of the program as it is shipped: Daodan.exe and its Python in runtime\
#   -Probe   the same program, built with WebView2's debugging port open (9333)
#   -Fake    the fake server (src-tauri/examples/fake_server.rs), in place of the Python
#   -Work    an empty folder to work in
param([string]$Folder, [string]$Probe, [string]$Fake, [string]$Work)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System; using System.Collections.Generic; using System.Runtime.InteropServices; using System.Text;
public static class W {
  public delegate bool Visit(IntPtr h, IntPtr l);
  [StructLayout(LayoutKind.Sequential)] public struct R { public int L, T, Rr, B; }
  [DllImport("user32.dll")] static extern bool EnumWindows(Visit v, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr h, Visit v, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsZoomed(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  [StructLayout(LayoutKind.Sequential)] public struct P { public int X, Y; }
  [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out R r);
  [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h, ref P p);
  public static int Caption(IntPtr h) { R r; P p = new P(); GetWindowRect(h, out r); ClientToScreen(h, ref p); return p.Y - r.T; }
  [DllImport("user32.dll")] public static extern bool PostMessageW(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
  [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr h, int a, out int v, int n);
  public static string Text(IntPtr h) { var s = new StringBuilder(2000); GetWindowTextW(h, s, 2000); return s.ToString(); }
  static string Class(IntPtr h) { var s = new StringBuilder(400); GetClassNameW(h, s, 400); return s.ToString(); }
  public static IntPtr Find(int pid, string cls, bool visible) {
    IntPtr found = IntPtr.Zero;
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
      if (p == (uint)pid && Class(h) == cls && (!visible || IsWindowVisible(h))) { found = h; return false; } return true; }, IntPtr.Zero);
    return found; }
  public static string Said(IntPtr h) {
    var all = new StringBuilder();
    EnumChildWindows(h, (c, l) => { if (Class(c) == "Static") all.Append(Text(c)); return true; }, IntPtr.Zero);
    return all.ToString(); }
  public static bool Has(IntPtr h, string cls) {
    bool found = false;
    EnumChildWindows(h, (c, l) => { if (Class(c) == cls && IsWindowVisible(c)) { found = true; return false; } return true; }, IntPtr.Zero);
    return found; }
  public static int Dark(IntPtr h) { int v; return DwmGetWindowAttribute(h, 20, out v, 4) == 0 ? v : -1; }
}
'@
$script:bad = 0
function Say($ok, $what) { if ($ok) { Write-Host "PASS  $what" } else { Write-Host "FAIL  $what"; $script:bad++ } }
function Wait-For([scriptblock]$done, [int]$seconds) {
  $end = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $end) { $value = & $done; if ($value) { return $value }; Start-Sleep -Milliseconds 50 }
}
$node = (Get-Command node).Source
$data = Join-Path ([Environment]::GetFolderPath('ApplicationData')) 'dev.daodan.desktop'

# The folder moves to another path than the one its Python was staged in, with a space and an accent in its name.
$Work = [IO.Path]::GetFullPath($Work)
$real = Join-Path $Work 'Daodan prova è'; $fakes = Join-Path $Work 'Daodan finto'
$null = New-Item -ItemType Directory -Force $Work, "$fakes\runtime"
Copy-Item $Folder $real -Recurse
Copy-Item $Probe "$real\Probe.exe"
Copy-Item "$real\Daodan.exe" "$fakes\Daodan.exe"
Copy-Item $Fake "$fakes\runtime\python.exe"

# No Python and no uv, for what is started from here on: Windows alone.
$env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
Say (-not (Get-Command python, python3, py, uv -ErrorAction SilentlyContinue)) 'the PATH has no Python and no uv'

# What is left of Daodan: the programs of the two folders, and the engine on its profile.
function Left {
  @(Get-CimInstance Win32_Process | Where-Object {
    ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($Work, 'OrdinalIgnoreCase')) -or
    ($_.Name -eq 'msedgewebview2.exe' -and $_.CommandLine -and $_.CommandLine.Contains('dev.daodan.desktop')) })
}
function Server { Left | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match '--desktop' } | Select-Object -First 1 }
function Start-It([string]$exe) {
  $script:clock = [Diagnostics.Stopwatch]::StartNew()
  $p = Start-Process $exe -PassThru; $null = $p.Handle
  $p
}
function Window($p) { [W]::Find($p.Id, 'Tauri Window', $true) }
function Wait-Window($p) {
  $null = Wait-For { if ($p.HasExited) { 'gone' } elseif ((Window $p) -ne [IntPtr]::Zero) { 'here' } } 70
  Window $p
}
function Ask([string]$expression) {
  $said = & $node "$PSScriptRoot/smoke-page.mjs" 9333 $expression
  if ($LASTEXITCODE) { Say $false "the page answers: $expression"; return }
  if ($said) { $said | ConvertFrom-Json }
}
# A command of the window, called by the page; its answer, or why it was refused.
function Invoke-Page([string]$command, [string]$arguments = '{}') {
  Ask "window.__TAURI_INTERNALS__.invoke('$command', $arguments).then((value) => ({ ok: true, value: value ?? null }), (error) => ({ ok: false, value: String(error) }))"
}
function Close-Window($p) { $null = [W]::PostMessageW((Window $p), 0x10, [IntPtr]::Zero, [IntPtr]::Zero) }
function Say-Ended($p, $code, $what) {
  $sw = [Diagnostics.Stopwatch]::StartNew()
  $ended = $p.WaitForExit(20000)
  Say ($ended -and $p.ExitCode -eq $code) "${what}: the program ends with code $code ($(if ($ended) { "$($p.ExitCode), after $($sw.ElapsedMilliseconds) ms" } else { 'it goes on' }))"
  if (-not $ended) { Stop-Process -Id $p.Id -Force }
  $null = Wait-For { -not (Left) } 10
  $left = Left
  Say (-not $left) "${what}: no process of Daodan is left $(($left | ForEach-Object { "$($_.Name) $($_.ProcessId) $($_.CommandLine)" }) -join '; ')"
  $left | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
# The native message of `p`, with the log's place in it; it is closed.
function Say-Message($p, [string]$words, [int]$seconds, $what) {
  $null = Wait-For { if ($p.HasExited) { 'gone' } elseif ([W]::Find($p.Id, '#32770', $true) -ne [IntPtr]::Zero) { 'here' } } $seconds
  $message = [W]::Find($p.Id, '#32770', $true)
  $said = [W]::Said($message)
  Say ($said.Contains($words) -and $said.Contains("$data\server.log")) "${what}: a native message with the log's place after $($script:clock.ElapsedMilliseconds) ms: $($said -replace '\s+', ' ')"
  $null = [W]::PostMessageW($message, 0x10, [IntPtr]::Zero, [IntPtr]::Zero)
}

Write-Host '--- the window opens on the page of the server'
$p = Start-It "$real\Probe.exe"
$h = Wait-Window $p
$shown = $script:clock.ElapsedMilliseconds
Say ($h -ne [IntPtr]::Zero) "a window is on screen after $shown ms"
$page = Ask '({ href: location.origin + location.pathname, token: location.search.length > 10, title: document.title, drawn: document.body.innerText.trim().length, internals: typeof __TAURI_INTERNALS__ })'
Write-Host "      $($page | ConvertTo-Json -Compress)"
$origin = ([Uri]$page.href).GetLeftPart('Authority')
Say ($page.href -match '^http://127\.0\.0\.1:\d+/app/$' -and $page.token -and $page.drawn -gt 20) 'the window shows the page of the server, with its token, and the page is drawn'
Say ("$(Get-Content "$data\server-port")" -eq ([Uri]$origin).Port) "the port is kept: $(Get-Content "$data\server-port")"
Say ([W]::Caption($h) -lt 10) "the window has no title bar of Windows: the page begins $([W]::Caption($h)) pixels under its edge"
Say ([bool](Server)) 'the server is the private Python of the folder'
Say (-not (Get-Content "$data\server.log")) "the log of the server is empty: $(Get-Content "$data\server.log" -Raw)"
$answer = Ask "fetch('/api/app/state', { headers: { 'X-Daodan-Token': new URLSearchParams(location.search).get('token') } }).then((r) => r.status)"
Say ($answer -eq 200) "the page reads the server ($answer)"
$answer = Ask "fetch('/api/app/check', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Daodan-Token': new URLSearchParams(location.search).get('token') }, body: '{}' }).then((r) => r.status)"
Say ($answer -ne 403) "the posts of the page reach the server ($answer)"

Write-Host '--- the window commands answer the page on 127.0.0.1'
foreach ($theme in 'light', 'dark') {
  $answer = Invoke-Page 'plugin:imago-shell|set_theme' "{ theme: '$theme', resolved: '$theme' }"
  $dark = [int]($theme -eq 'dark')
  Say ($answer.ok -and (Get-Content "$data\window-theme") -eq $theme -and [W]::Dark($h) -eq $dark) "set_theme ${theme}: kept $(Get-Content "$data\window-theme"), DWM $([W]::Dark($h)), $($answer.value)"
}
$null = Invoke-Page 'plugin:imago-shell|set_theme' "{ theme: 'light', resolved: 'light' }"
$answer = Invoke-Page 'plugin:imago-shell|kept_theme'
Say ($answer.ok -and $answer.value -eq 'light') "kept_theme: $($answer.value)"
$answer = Invoke-Page 'plugin:imago-shell|caption' '{ x: 900, y: 0, width: 46, height: 40 }'
Say ($answer.ok -and [W]::Has($h, 'ImagoMaximizeOverlay')) "caption: the overlay is there, $($answer.value)"
$answer = Invoke-Page 'plugin:imago-shell|ready'
Say $answer.ok "ready: $($answer.value)"
$answer = Invoke-Page 'plugin:imago-shell|chrome' "{ title: 'Analisi – Daodan', progress: 40 }"
Say ($answer.ok -and [W]::Text($h) -eq 'Analisi – Daodan') "chrome: the title is '$([W]::Text($h))', $($answer.value)"
$answer = Invoke-Page 'plugin:imago-shell|chrome' "{ title: 'Daodan', progress: null }"
$before = Invoke-Page 'plugin:window|is_maximized' "{ label: 'main' }"
$answer = Invoke-Page 'plugin:window|toggle_maximize' "{ label: 'main' }"
$null = Wait-For { [W]::IsZoomed($h) } 5
$after = Invoke-Page 'plugin:window|is_maximized' "{ label: 'main' }"
Say ($answer.ok -and -not $before.value -and $after.value -and [W]::IsZoomed($h)) "the maximize button's command maximizes: $($answer.value)"
$null = Invoke-Page 'plugin:window|toggle_maximize' "{ label: 'main' }"
$null = Wait-For { -not [W]::IsZoomed($h) } 5
Say (-not [W]::IsZoomed($h)) 'and restores'
$answer = Invoke-Page 'plugin:window|minimize' "{ label: 'main' }"
$null = Wait-For { [W]::IsIconic($h) } 5
Say ($answer.ok -and [W]::IsIconic($h)) "the minimize button's command minimizes: $($answer.value)"
$ratio = Ask 'devicePixelRatio'
$answer = Invoke-Page 'plugin:webview|set_webview_zoom' "{ label: 'main', value: 1.25 }"
$null = Wait-For { (Ask 'devicePixelRatio') -gt $ratio } 5
Say ($answer.ok -and (Ask 'devicePixelRatio') -gt $ratio) "the zoom: $($answer.value)"
$null = Invoke-Page 'plugin:webview|set_webview_zoom' "{ label: 'main', value: 1 }"
foreach ($refused in 'plugin:window|set_title', 'plugin:app|version', 'plugin:webview|create_webview_window', 'plugin:shell|execute') {
  $answer = Invoke-Page $refused "{ label: 'main' }"
  Say (-not $answer.ok) "what is not granted is refused: ${refused}: $($answer.value)"
}
$calls = Ask "performance.getEntriesByType('resource').filter(({ name }) => name.includes('ipc.localhost')).map(({ responseStatus }) => responseStatus)"
Say (@($calls).Count -gt 10 -and @($calls | Where-Object { $_ -eq 200 }).Count -gt 10) "the calls go by ipc.localhost, not by the fall-back ($(@($calls).Count) calls, $(@($calls | Where-Object { $_ -eq 200 }).Count) answered 200)"
$null = Ask "location.href = 'https://example.com/', 1"
Start-Sleep 2
$at = Ask 'location.origin'
Say ($at -eq $origin) "the window leaves the server for no other address ($at)"

Write-Host '--- started again while it runs'
$other = Start-It "$real\Daodan.exe"
$ended = $other.WaitForExit(10000)
Say ($ended -and -not $p.HasExited) 'a second start ends and the first one stays'
$null = Wait-For { -not [W]::IsIconic($h) } 5
Say (-not [W]::IsIconic($h)) 'and the window is brought back'
if (-not $ended) { Stop-Process -Id $other.Id -Force }

Write-Host '--- the page closes the window'
$null = Ask "localStorage.setItem('smoke', 'kept'), 1"
Start-Sleep 12 # WebView2 writes the storage to the disk some seconds late
$null = & $node "$PSScriptRoot/smoke-page.mjs" 9333 "window.__TAURI_INTERNALS__.invoke('plugin:window|close', { label: 'main' }), 1" 2>&1
Say-Ended $p 0 'closed by the page'
Say (-not (Get-Content "$data\server.log")) "the log of the server is empty: $(Get-Content "$data\server.log" -Raw)"

Write-Host '--- the next start: the same address, what the page kept, the theme'
$p = Start-It "$real\Probe.exe"
$h = Wait-Window $p
Say ([W]::Dark($h) -eq 0) 'the first frame has the theme that was kept (light)'
Say ((Ask 'location.origin') -eq $origin) 'the same origin'
Say ((Ask "localStorage.getItem('smoke')") -eq 'kept') 'what the page kept is there'

Write-Host '--- the server is killed'
$script:clock.Restart()
Stop-Process -Id (Server).ProcessId -Force
Say-Message $p 'si è chiuso' 20 'a killed server'
Say-Ended $p 1 'a killed server'

Write-Host '--- the port is taken'
$taken = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, ([Uri]$origin).Port)
$taken.Start()
$p = Start-It "$real\Probe.exe"
$null = Wait-Window $p
$at = Ask 'location.origin'
Say ($at -and $at -ne $origin) "another port, and the window opens ($at)"
$taken.Stop()
Close-Window $p
Say-Ended $p 0 'the port taken'

Write-Host '--- the program is killed'
$p = Start-It "$real\Probe.exe"
$null = Wait-Window $p
Stop-Process -Id $p.Id -Force
$null = Wait-For { -not (Left) } 15
Say (-not (Left)) 'the server ends with it'

Write-Host '--- the program as it is shipped'
$p = Start-It "$real\Daodan.exe"
$h = Wait-Window $p
$shipped = $script:clock.ElapsedMilliseconds
Say ($h -ne [IntPtr]::Zero) "a window is on screen after $shipped ms"
$open = [Net.Sockets.TcpClient]::new()
try { $open.Connect('127.0.0.1', 9333); $listens = $true } catch { $listens = $false }
Say (-not $listens) 'it opens no debugging port'
Close-Window $p
Say-Ended $p 0 'the shipped program, closed by Windows'

Write-Host '--- an analysis goes on when the window closes: the fake server and its two children'
$env:FAKE_PIDS = Join-Path $Work 'pids'
$env:FAKE_SERVER = 'children'
$p = Start-It "$fakes\Daodan.exe"
$h = Wait-Window $p
$own, $kept, $free = (Get-Content $env:FAKE_PIDS) -split ' ' | ForEach-Object { [int]$_ }
$alive = { param($id) [bool](Get-Process -Id $id -ErrorAction SilentlyContinue) }
Say ($h -ne [IntPtr]::Zero -and (& $alive $own) -and (& $alive $kept) -and (& $alive $free)) "the window, the server and its two children are there ($own $kept $free)"
Close-Window $p
$ended = $p.WaitForExit(20000)
Start-Sleep 2
Say ($ended -and $p.ExitCode -eq 0) 'the program ends'
Say (-not (& $alive $own) -and -not (& $alive $kept)) 'the server and the child in its job are gone'
Say (& $alive $free) 'the child that left the job on purpose goes on'
Stop-Process -Id $free -Force -ErrorAction SilentlyContinue

Write-Host '--- a server that fails gives a message'
foreach ($case in @('die', 'si è chiuso (codice 3)'), @('other', 'non ha dato il suo indirizzo'), @('twice', 'ha dato più del suo indirizzo'), @('never', 'non ha risposto in 60 secondi')) {
  $env:FAKE_SERVER = $case[0]
  $p = Start-It "$fakes\Daodan.exe"
  Say-Message $p $case[1] 75 "a server that does '$($case[0])'"
  Say-Ended $p 1 "a server that does '$($case[0])'"
}
Remove-Item "$fakes\runtime\python.exe"
$p = Start-It "$fakes\Daodan.exe"
Say-Message $p 'non si avvia' 10 'no Python in the folder'
Say-Ended $p 1 'no Python in the folder'

if ($env:GITHUB_STEP_SUMMARY) {
  "Window on screen: $shown ms at the first start (the bytecode is not written yet), $shipped ms later. Failures: $script:bad." >> $env:GITHUB_STEP_SUMMARY
}
Write-Host "failures: $script:bad"
exit $script:bad
