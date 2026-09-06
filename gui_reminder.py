print('loading packages of routine....')
import sys
import json
import os
import re
import winreg
from urllib.parse import urlparse

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTimeEdit, QFileDialog, QDialog, QDialogButtonBox,
    QCheckBox
)
from PyQt5.QtCore import QTime

DAYS_OF_WEEK = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/tasks.json')


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, 'r') as f:
        return json.load(f)


def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=4)


# ============================================================
# Installed-software lookup (Windows registry)
# ============================================================

UNINSTALL_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _read_value(key, name, default=""):
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return value
    except FileNotFoundError:
        return default


def _best_guess_path(display_icon, install_location):
    """DisplayIcon often points at the actual .exe (sometimes with a
    trailing ',0' icon-index suffix). Fall back to InstallLocation if
    DisplayIcon isn't usable."""
    if display_icon:
        path = display_icon.split(",")[0].strip('"')
        if path.lower().endswith(".exe") and os.path.exists(path):
            return path
    if install_location and os.path.isdir(install_location):
        return install_location
    return ""


def scan_installed_software():
    """Returns a list of dicts: name, version, publisher, path.
    Source: the registry Uninstall keys (same list Control Panel uses)."""
    results = []
    seen = set()

    for hive, path in UNINSTALL_KEYS:
        try:
            root_key = winreg.OpenKey(hive, path)
        except FileNotFoundError:
            continue

        subkey_count = winreg.QueryInfoKey(root_key)[0]
        for i in range(subkey_count):
            try:
                subkey_name = winreg.EnumKey(root_key, i)
                with winreg.OpenKey(root_key, subkey_name) as subkey:
                    name = _read_value(subkey, "DisplayName")
                    if not name:
                        continue

                    version = _read_value(subkey, "DisplayVersion", "Unknown")
                    publisher = _read_value(subkey, "Publisher", "Unknown")
                    display_icon = _read_value(subkey, "DisplayIcon")
                    install_location = _read_value(subkey, "InstallLocation")
                    app_path = _best_guess_path(display_icon, install_location)

                    dedupe_key = (name, version)
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)

                    results.append({
                        "name": name,
                        "publisher": publisher,
                        "path": app_path,
                        "source": "registry"
                    })
            except OSError:
                continue

        root_key.Close()

    results.sort(key=lambda x: x["name"].lower())
    return results


# ============================================================
# Deep system scan: walks common install folders for .exe files.
# Catches apps that don't register cleanly (VS Code, Photoshop, GIMP,
# etc.) or built-in tools (Paint, Notepad, Calculator).
# ============================================================

# Filenames that are almost never the "main" app you'd want to launch
_SKIP_SUBSTRINGS = (
    "uninstall", "unins0", "setup", "installer", "update", "updater",
    "crashpad", "crashhandler", "helper", "vc_redist", "redist",
    "elevate", "maintenancetool"
)

KNOWN_SYSTEM_APPS = {
    "Paint": r"C:\Windows\System32\mspaint.exe",
    "Notepad": r"C:\Windows\System32\notepad.exe",
    "Calculator": r"C:\Windows\System32\calc.exe",
    "WordPad": r"C:\Program Files\Windows NT\Accessories\wordpad.exe",
    "Command Prompt": r"C:\Windows\System32\cmd.exe",
    "PowerShell": r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    "File Explorer": r"C:\Windows\explorer.exe",
    "Snipping Tool": r"C:\Windows\System32\SnippingTool.exe",
    "Task Manager": r"C:\Windows\System32\Taskmgr.exe",
    "VS Code": r"D:\AppData\Microsoft VS Code\Code.exe",
}


def _walk_limited(root, max_depth=3):
    """Yield .exe paths under root, without descending past max_depth."""
    root_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
        if depth >= max_depth:
            dirnames[:] = []  # stop descending further from here
        for f in filenames:
            if f.lower().endswith(".exe"):
                yield os.path.join(dirpath, f)


def scan_common_folders():
    """Returns a list of dicts: name, publisher(''), path, source.
    Scans Program Files, Program Files (x86), and the per-user
    Programs folder for standalone .exe files."""
    roots = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("Appdata", r"D:\AppData")
    ]
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        roots.append(os.path.join(local_appdata, "Programs"))

    results = []
    seen_paths = set()

    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for exe_path in _walk_limited(root, max_depth=3):
            key = exe_path.lower()
            if key in seen_paths:
                continue
            seen_paths.add(key)

            name = os.path.splitext(os.path.basename(exe_path))[0]
            if any(skip in name.lower() for skip in _SKIP_SUBSTRINGS):
                continue

            results.append({
                "name": name,
                "publisher": "",
                "path": exe_path,
                "source": "folder scan"
            })

    return results


def scan_full_system():
    """Merges registry entries + deep folder scan + known built-in
    Windows tools (Paint, Notepad, etc.) into one deduped list."""
    combined = {}

    for app in scan_installed_software():
        if app["path"]:
            combined[app["path"].lower()] = app

    for app in scan_common_folders():
        combined.setdefault(app["path"].lower(), app)

    for name, path in KNOWN_SYSTEM_APPS.items():
        if os.path.exists(path) and path.lower() not in combined:
            combined[path.lower()] = {
                "name": name,
                "publisher": "Microsoft (built-in)",
                "path": path,
                "source": "built-in"
            }

    results = list(combined.values())
    results.sort(key=lambda x: x["name"].lower())
    return results


class AppPickerDialog(QDialog):
    """Modal dialog: search installed programs, pick one, return its path."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Installed App")
        self.setMinimumSize(480, 450)
        self.selected_path = ""
        self.selected_name = ""
        self.all_apps = []

        layout = QVBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search apps...")
        self.search_box.textChanged.connect(self.filter_list)
        layout.addWidget(self.search_box)

        scan_btn_layout = QHBoxLayout()
        rescan_btn = QPushButton("Rescan (Registry)")
        rescan_btn.clicked.connect(self.load_apps)
        deep_scan_btn = QPushButton("Scan Whole System")
        deep_scan_btn.setToolTip(
            "Also searches Program Files, Program Files (x86), and your "
            "user Programs folder, plus built-in tools like Paint and "
            "Notepad. Catches apps like VS Code or Photoshop that don't "
            "show up cleanly in the registry. Takes a few seconds longer."
        )
        deep_scan_btn.clicked.connect(self.deep_scan)
        scan_btn_layout.addWidget(rescan_btn)
        scan_btn_layout.addWidget(deep_scan_btn)
        layout.addLayout(scan_btn_layout)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.list_widget)

        self.status_label = QLabel("Scanning installed apps...")
        layout.addWidget(self.status_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.load_apps()

    def load_apps(self):
        try:
            self.all_apps = [a for a in scan_installed_software() if a["path"]]
        except Exception as e:
            QMessageBox.critical(self, "Scan failed", str(e))
            self.all_apps = []
        self.populate_list(self.all_apps)
        self.status_label.setText(f"{len(self.all_apps)} apps found (registry only)")

    def deep_scan(self):
        self.status_label.setText("Scanning whole system... this may take a moment")
        QApplication.processEvents()
        try:
            self.all_apps = scan_full_system()
        except Exception as e:
            QMessageBox.critical(self, "Scan failed", str(e))
            self.all_apps = []
        self.populate_list(self.all_apps)
        self.status_label.setText(f"{len(self.all_apps)} apps found (whole-system scan)")

    def populate_list(self, apps):
        self.list_widget.clear()
        for app in apps:
            label = app["name"]
            if app.get("publisher"):
                label += f"  ({app['publisher']})"
            item = QListWidgetItem(label)
            item.setData(1000, app["path"])  # stash the path on the item
            self.list_widget.addItem(item)

    def filter_list(self, text):
        text = text.lower().strip()
        if not text:
            self.populate_list(self.all_apps)
            return
        filtered = [a for a in self.all_apps if text in a["name"].lower()]
        self.populate_list(filtered)

    def accept(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "No selection", "Select an app from the list first.")
            return
        self.selected_path = item.data(1000)
        self.selected_name = item.text()
        super().accept()


# ============================================================
# Reminder Manager
# ============================================================

class ReminderTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = load_tasks()
        self.init_ui()
        self.refresh_list()

    def init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Current Reminders:"))
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_task)
        layout.addWidget(delete_btn)

        layout.addWidget(self.divider())

        layout.addWidget(QLabel("Add New Reminder:"))

        time_layout = QHBoxLayout()
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH")
        self.start_time.setTime(QTime(9, 0))

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH")
        self.end_time.setTime(QTime(10, 0))

        time_layout.addWidget(QLabel("Start:"))
        time_layout.addWidget(self.start_time)
        time_layout.addWidget(QLabel("End:"))
        time_layout.addWidget(self.end_time)
        layout.addLayout(time_layout)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Reminder message")
        layout.addWidget(self.message_input)

        layout.addWidget(QLabel("Days:"))
        days_layout = QHBoxLayout()

        self.every_day_checkbox = QCheckBox("Every day")
        self.every_day_checkbox.setChecked(True)
        self.every_day_checkbox.stateChanged.connect(self.toggle_every_day)
        days_layout.addWidget(self.every_day_checkbox)

        self.day_checkboxes = {}
        for day in DAYS_OF_WEEK:
            cb = QCheckBox(day)
            cb.setEnabled(False)  # disabled while "Every day" is checked
            self.day_checkboxes[day] = cb
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)

        path_btn_layout = QHBoxLayout()
        select_app_btn = QPushButton("Select Installed App...")
        select_app_btn.clicked.connect(self.select_installed_app)
        browse_btn = QPushButton("Browse for File...")
        browse_btn.clicked.connect(self.browse_path)
        path_btn_layout.addWidget(select_app_btn)
        path_btn_layout.addWidget(browse_btn)
        layout.addLayout(path_btn_layout)

        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter a URL (e.g. https://example.com)")
        self.url_input.returnPressed.connect(self.add_url)
        add_url_btn = QPushButton("Add URL")
        add_url_btn.clicked.connect(self.add_url)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(add_url_btn)
        layout.addLayout(url_layout)

        layout.addWidget(QLabel("Apps/files/URLs for this reminder:"))
        self.paths_list = QListWidget()
        self.paths_list.setMaximumHeight(90)
        layout.addWidget(self.paths_list)

        remove_path_btn = QPushButton("Remove Selected")
        remove_path_btn.clicked.connect(self.remove_path_from_list)
        layout.addWidget(remove_path_btn)

        add_btn = QPushButton("Add Reminder")
        add_btn.clicked.connect(self.add_task)
        layout.addWidget(add_btn)

        self.setLayout(layout)

    def divider(self):
        line = QLabel()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #ccc;")
        return line

    def toggle_every_day(self, state):
        every_day = self.every_day_checkbox.isChecked()
        for cb in self.day_checkboxes.values():
            cb.setEnabled(not every_day)
            if every_day:
                cb.setChecked(False)

    def select_installed_app(self):
        dialog = AppPickerDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_path:
            self.paths_list.addItem(dialog.selected_path)

    def browse_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select a file/program to open")
        if path:
            self.paths_list.addItem(path)

    def add_url(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "No URL", "Type a URL first.")
            return

        # Add a scheme if the user typed something like "example.com"
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
            url = "https://" + url

        parsed = urlparse(url)
        if not parsed.netloc:
            QMessageBox.warning(self, "Invalid URL", "That doesn't look like a valid URL.")
            return

        self.paths_list.addItem(url)
        self.url_input.clear()

    def remove_path_from_list(self):
        row = self.paths_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No selection", "Select an entry to remove first.")
            return
        self.paths_list.takeItem(row)

    def refresh_list(self):
        self.list_widget.clear()
        for task in self.tasks:
            days = task.get('days', [])
            days_text = ", ".join(days) if days else "Every day"
            text = f"[{days_text}]  {task['start']} - {task['end']}  |  {task['message']}"
            paths = task.get('paths', [])
            if not paths and task.get('path'):  # backward compatibility
                paths = [task['path']]
            if paths:
                text += "  ->  " + ", ".join(paths)
            item = QListWidgetItem(text)
            self.list_widget.addItem(item)

    def add_task(self):
        start_time = self.start_time.time().toString("HH")
        end_time = self.end_time.time().toString("HH")
        message = self.message_input.text().strip()

        if not message:
            QMessageBox.warning(self, "Missing message", "Please enter a reminder message.")
            return

        if self.start_time.time().hour() >= self.end_time.time().hour():
            QMessageBox.warning(self, "Invalid time range", "Start hour must be before end hour.")
            return

        new_task = {
            "start": start_time,
            "end": end_time,
            "message": message,
            "days": [] if self.every_day_checkbox.isChecked() else
                     [day for day, cb in self.day_checkboxes.items() if cb.isChecked()],
            "paths": [self.paths_list.item(i).text() for i in range(self.paths_list.count())]
        }

        if not self.every_day_checkbox.isChecked() and not new_task["days"]:
            QMessageBox.warning(self, "No days selected", "Pick at least one day, or check 'Every day'.")
            return

        self.tasks.append(new_task)
        save_tasks(self.tasks)
        self.refresh_list()
        self.message_input.clear()
        self.paths_list.clear()
        self.every_day_checkbox.setChecked(True)

    def delete_task(self):
        selected_row = self.list_widget.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No selection", "Select a reminder to delete first.")
            return

        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Delete: {self.tasks[selected_row]['message']}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            del self.tasks[selected_row]
            save_tasks(self.tasks)
            self.refresh_list()


def main():
    app = QApplication(sys.argv)
    window = ReminderTab()
    window.setWindowTitle("Reminder Manager")
    window.setMinimumSize(480, 550)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()