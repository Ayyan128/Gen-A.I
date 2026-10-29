import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from datetime import datetime

try:
    import psutil
except ImportError:
    sys.exit("psutil is required: pip install psutil")

DEFAULT_LOG = "data/activity_log.csv"
HEADER = ["time", "event", "software", "duration_seconds"]

# Background / helper processes that clutter the log. Add more as you see them.
IGNORE = {
    "conhost.exe", "svchost.exe", "runtimebroker.exe", "backgroundtaskhost.exe",
    "searchhost.exe", "smartscreen.exe", "dllhost.exe", "taskhostw.exe",
    "python.exe", "pythonw.exe", "py.exe", "cmd.exe", "powershell.exe",
    "wmiprvse.exe", "audiodg.exe", "fontdrvhost.exe", "ctfmon.exe",
    "sihost.exe", "textinputhost.exe", "applicationframehost.exe",
    "defenderaiplatformhost.exe", "defendersessionhelper.exe",
    "gameinputrawinputproxy.exe", "gameinputredistservice.exe",
    "googleplaygamesservices.exe", "memcompression",
    "mpdefendercoreservice.exe", "msmpeng.exe", "nissrv.exe",
    "officeclicktorun.exe", "registry", "sdxhelper.exe",
    "taskbarx.exe", "translucenttb.exe", "video.ui.exe",
    "xboxpcappft.exe", "xboxservice.exe", "crashpad_handler.exe",
    "gamingservices.exe", "gamingservicesnet.exe", "mdnsresponder.exe",
    "pet.exe","git.exe",
    # added from your activity log
    "gamebar.exe", "gamebarftserver.exe", "xboxgamebarwidgets.exe",
    "spotifyxboxgamebarwebview.exe", "xboxpctray.exe", "gamelaunchhelper.exe",
    "gamingservicesui.exe", "microsoftedgeupdate.exe", "updater.exe",
    "update.exe", "officec2rclient.exe", "hxtsr.exe", "mpcmdrun.exe",
    "dismhost.exe", "actionsserver.exe", "onedrivelauncher.exe",
    "onedrivestandaloneupdater.exe", "onedrive.sync.service.exe",
    "filecoauth.exe", "plugscheduler.exe", "ruximics.exe", "service.exe", "msedgewebview2.exe", "phoneexperiencehost.exe",
    "gpu_check.exe", "storedesktopextension.exe",
    "windowspackagemanagerserver.exe", "elevation_service.exe",
    "identity_helper.exe", "pwahelper.exe", "git-lfs.exe",
    "git-remote-https.exe", "code-tunnel.exe","WhatsApp.Root.exe"
}

# ---------------------------------------------------------------------------
# TRACKING RULES
#   TRACK   -> always logged, even if the app is also in IGNORE or lives in C:\Windows
#   IGNORE  -> never logged
#   neither -> logged too (every app not mentioned is tracked by default)
# Names are not case sensitive.
# ---------------------------------------------------------------------------
TRACK = {
    "code.exe", "chrome.exe", "msedge.exe", "githubdesktop.exe",
    "minecraft.windows.exe", "whatsapp.exe",
}

# Apps found in C:\Windows that are in neither list are skipped when True
# (they are almost all background services). Set False to log those too.
SKIP_WINDOWS_FOLDER = True

TRACK = {n.lower() for n in TRACK}
IGNORE = {n.lower() for n in IGNORE}


def set_rules(track=None, ignore=None):
    """Add apps to the rules while the program runs.
    set_rules(track=["spotify.exe"], ignore=["notepad.exe"])
    An app moves out of the other list when you add it to one."""
    for n in (track or []):
        n = n.lower()
        TRACK.add(n)
        IGNORE.discard(n)
    for n in (ignore or []):
        n = n.lower()
        IGNORE.add(n)
        TRACK.discard(n)


def clear_rules(track=None, ignore=None):
    """Remove apps from a list, so they fall back to the default (tracked).
    clear_rules(ignore=["notepad.exe"])"""
    for n in (track or []):
        TRACK.discard(n.lower())
    for n in (ignore or []):
        IGNORE.discard(n.lower())


def should_track(name, exe="", include_system=False):
    if include_system:
        return True
    key = name.lower()
    if key in TRACK:
        return True
    if key in IGNORE:
        return False
    if (SKIP_WINDOWS_FOLDER and os.name == "nt"
            and exe.lower().startswith("c:\\windows")):
        return False
    return True      # not mentioned anywhere -> tracked


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fmt_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def get_running_apps(include_system=False):
    """Return {app_name: earliest_process_start_time} for user-level programs."""
    apps = {}
    for p in psutil.process_iter(["name", "exe", "create_time"]):
        try:
            name = p.info["name"]
            exe = p.info["exe"] or ""
            if not name or not exe:
                continue
            if not should_track(name, exe, include_system):
                continue
            started = p.info["create_time"] or time.time()
            if name not in apps or started < apps[name]:
                apps[name] = started
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return apps


def write_row(log_file, event, name, duration=""):
    folder = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(folder, exist_ok=True)
    is_new = not os.path.exists(log_file) or os.path.getsize(log_file) == 0
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(HEADER)
        w.writerow([now_str(), event, name, duration])


def run_monitor(log_file, interval, include_system):
    print(f"Activity monitor started. Logging to: {os.path.abspath(log_file)}")
    print("Press Ctrl+C to stop.\n")

    previous = get_running_apps(include_system)
    for name in sorted(previous):
        write_row(log_file, "already_running", name)
    print(f"[{now_str()}] {len(previous)} apps already running (logged)")

    while True:
        time.sleep(interval)
        current = get_running_apps(include_system)

        for name in sorted(set(current) - set(previous)):
            write_row(log_file, "opened", name)
            print(f"[{now_str()}] OPENED  {name}")

        for name in sorted(set(previous) - set(current)):
            duration = time.time() - previous[name]
            write_row(log_file, "closed", name, int(duration))
            print(f"[{now_str()}] CLOSED  {name}  (open for {fmt_duration(duration)})")

        previous = current


def print_summary(log_file, date_str):
    if not os.path.exists(log_file):
        print(f"No log file found at {log_file}")
        return

    opens = defaultdict(int)
    total = defaultdict(float)
    with open(log_file, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["time"].startswith(date_str):
                continue
            if row["event"] == "opened":
                opens[row["software"]] += 1
            elif row["event"] == "closed" and row["duration_seconds"]:
                total[row["software"]] += float(row["duration_seconds"])

    names = set(opens) | set(total)
    if not names:
        print(f"No activity recorded for {date_str}")
        return

    print(f"Activity summary for {date_str}\n")
    print(f"{'Software':35} {'Opened':>7}  {'Time open':>12}")
    print("-" * 58)
    for name in sorted(names, key=lambda n: total[n], reverse=True):
        print(f"{name[:35]:35} {opens[name]:>7}  {fmt_duration(total[name]):>12}")


def main():
    ap = argparse.ArgumentParser(description="Log when software is opened and closed.")
    ap.add_argument("--log", default=DEFAULT_LOG, help="CSV log file path")
    ap.add_argument("--interval", type=float, default=2.0,
                    help="seconds between checks (default 2)")
    ap.add_argument("--include-system", action="store_true",
                    help="also track Windows/system processes")
    ap.add_argument("--summary", action="store_true",
                    help="print a report from the log and exit")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                    help="date for --summary, YYYY-MM-DD (default today)")
    args = ap.parse_args()

    if args.summary:
        print_summary(args.log, args.date)
        return

    try:
        run_monitor(args.log, max(0.5, args.interval), args.include_system)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()