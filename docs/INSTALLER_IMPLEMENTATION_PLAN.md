# Professional Installer & Update System - Implementation Plan

**Datum:** 2025-11-05
**Status:** Research & Planning - NIET GEÏMPLEMENTEERD
**Versie:** Planning Tool v0.6.26

---

## Executive Summary

Dit document bevat een compleet implementatieplan voor een professioneel Windows installer systeem met auto-update functionaliteit en automatische database migraties voor Planning Tool.

**Aanbevolen Aanpak:**
- **Installer Tool:** Inno Setup (gratis, proven, makkelijk te onderhouden)
- **Update Mechanisme:** GitHub Releases API + in-app notificatie
- **Database Locatie:** `C:\Program Files\Planning Tool\data\` (huidige structuur behouden)
- **Exports Locatie:** `C:\Program Files\Planning Tool\exports\`
- **Geschatte Effort:** 16-22 uur

**Belangrijkste Voordelen:**
- ✅ Professionele installer ervaring (Start Menu, Desktop shortcuts, Uninstaller)
- ✅ Automatische database backup voor elke migratie
- ✅ Semi-geautomatiseerde updates (in-app notificatie → download → install)
- ✅ Geen server kosten (GitHub Releases als distributie)
- ✅ Data blijft behouden bij updates
- ✅ Minimale code changes (database blijft op huidige locatie)

---

## Table of Contents

1. [Installer Tool Vergelijking](#1-installer-tool-vergelijking)
2. [Data Storage Strategie](#2-data-storage-strategie)
3. [Inno Setup Implementation](#3-inno-setup-implementation)
4. [Auto-Update Systeem](#4-auto-update-systeem)
5. [Database Migration Manager](#5-database-migration-manager)
6. [GitHub Release Workflow](#6-github-release-workflow)
7. [Implementatie Roadmap](#7-implementatie-roadmap)
8. [Risico's & Mitigaties](#8-risicos--mitigaties)
9. [Code Examples](#9-code-examples)

---

## 1. Installer Tool Vergelijking

### Opties Analyse

| Feature | Inno Setup | NSIS | WiX |
|---------|-----------|------|-----|
| **Learning Curve** | Easy (INI-like syntax) | Medium (custom scripting) | Steep (XML-based) |
| **Output Format** | EXE | EXE | MSI |
| **Visual Designer** | Yes (ISTool, free) | Limited | No (3rd party expensive) |
| **Documentation** | Excellent | Good | Complex |
| **Python/PyInstaller Support** | Excellent | Good | Good |
| **Maintenance Effort** | Low | Medium | High |
| **Enterprise Deployment** | Good (EXE) | Good (EXE) | Best (MSI/GPO) |

### Aanbeveling: **Inno Setup** ✅

**Rationale:**
1. **Ease of Use:** INI-file based syntax is intuitive voor solo developers
2. **Industry Adoption:** Gebruikt door Microsoft (VS Code), Skype, 7-Zip, WinSCP
3. **Python-Friendly:** Excellente PyInstaller integratie voorbeelden
4. **Maintenance:** Lage overhead, snel te updaten voor nieuwe versies
5. **Healthcare Context:** 20-50 gebruikers hebben geen MSI/GPO deployment nodig
6. **Free & Open Source:** Geen licensing kosten

**Wanneer Heroverwegen:**
- Als IT afdeling MSI format eist → gebruik WiX
- Als Group Policy deployment nodig is → gebruik WiX
- Bij 200+ gebruikers across domain → gebruik WiX

**Download:** https://jrsoftware.org/isdl.php

---

## 2. Data Storage Strategie

### Gekozen Aanpak: Database in Installatiemap

**Huidige structuur BEHOUDEN:**
```
C:\Program Files\Planning Tool\
├── PlanningTool.exe          # Applicatie binary (overschreven bij update)
├── Handleiding.html          # Help documentatie (overschreven)
├── PROJECT_INFO.md           # Read-only resources (overschreven)
├── data\
│   ├── planning.db           # SQLite database (BEHOUDEN bij update)
│   ├── planning.backup_*.db  # Automatische backups (BEHOUDEN)
│   └── theme_preference.json # User settings (BEHOUDEN)
└── exports\
    └── *.xlsx                # Excel exports (BEHOUDEN)
```

### Voordelen van deze Aanpak

✅ **Geen code changes:** Database blijft op huidige locatie (`data/planning.db`)
✅ **Simpele installer:** Alleen .exe overschrijven, data folders behouden
✅ **Makkelijk testen:** Development setup identiek aan production
✅ **Backup simpel:** Hele `data\` folder is de backup unit
✅ **Exports persistent:** Blijven beschikbaar na updates

### Installer Strategie

**Bij EERSTE installatie:**
- Maak `data\` folder aan met lege database
- Maak `exports\` folder aan
- Seed database met default data (via `database/connection.py`)

**Bij UPDATE (herinstallatie):**
- Overschrijf `PlanningTool.exe` (nieuwe versie)
- Overschrijf `Handleiding.html`, `PROJECT_INFO.md`
- **BEHOUD** `data\` folder (alle bestanden)
- **BEHOUD** `exports\` folder (alle bestanden)
- Run database migratie op eerste start (indien nodig)

**Inno Setup Flags:**
```pascal
; Altijd overschrijven
Source: "dist\PlanningTool.exe"; Flags: ignoreversion

; Alleen aanmaken als niet bestaat
Source: "data\planning.db"; Flags: onlyifdoesntexist
```

---

## 3. Inno Setup Implementation

### 3.1 Installer Script

**Bestand:** `installer/PlanningTool.iss`

```pascal
; Planning Tool Installer Script
; Version: 0.6.26+

#define MyAppName "Planning Tool"
#define MyAppVersion "0.6.26"
#define MyAppPublisher "Your Organization"
#define MyAppExeName "PlanningTool.exe"

[Setup]
AppId={{GENERATE-UNIQUE-GUID-HERE}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=admin
OutputDir=dist\installer
OutputBaseFilename=PlanningTool_v{#MyAppVersion}_Setup
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=resources\icon.ico
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"

[Tasks]
Name: "desktopicon"; Description: "Maak snelkoppeling op bureaublad"; Flags: unchecked

[Files]
; Main executable - always overwrite
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Documentation - always overwrite
Source: "Handleiding.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "PROJECT_INFO.md"; DestDir: "{app}"; Flags: ignoreversion

; Data folder - only create if doesn't exist
Source: "data\planning.db"; DestDir: "{app}\data"; Flags: onlyifdoesntexist

[Dirs]
; Create directories with proper permissions
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\exports"; Permissions: users-modify

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Handleiding"; Filename: "{app}\Handleiding.html"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch application after install
Filename: "{app}\{#MyAppExeName}"; Description: "Start {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if application is running
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if CheckForMutexes('PlanningTool_SingleInstance') then
  begin
    Result := 'Planning Tool is nog actief. Sluit de applicatie eerst af.';
  end;
end;

// Before uninstall: ask about data
function InitializeUninstall(): Boolean;
begin
  Result := True;
  if MsgBox('Wilt u de gebruikersgegevens (database, exports) behouden?' + #13#10 +
            'Klik Ja om gegevens te behouden voor toekomstige installaties.' + #13#10 +
            'Klik Nee om alles te verwijderen.',
            mbConfirmation, MB_YESNO or MB_DEFBUTTON1) = IDNO then
  begin
    // User wants to delete all data
    DelTree(ExpandConstant('{app}\data'), True, True, True);
    DelTree(ExpandConstant('{app}\exports'), True, True, True);
  end;
end;
```

**Key Features:**
- Admin privileges vereist (voor Program Files schrijfrechten)
- Data folders alleen aanmaken indien niet bestaat
- Uninstaller vraagt of data behouden moet worden
- Check of app running is voor installatie
- Nederlands als default taal

### 3.2 Build Automation Script

**Bestand:** `scripts/build_installer.py`

```python
#!/usr/bin/env python
"""
Build script for Planning Tool installer
Automates: PyInstaller build → Inno Setup compile → Output cleanup
"""

import subprocess
import shutil
from pathlib import Path
import sys

# Import version from config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import APP_VERSION

def run_command(cmd, cwd=None):
    """Run shell command and check for errors"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"ERROR: Command failed with code {result.returncode}")
        sys.exit(1)

def main():
    print(f"Building Planning Tool v{APP_VERSION} Installer...")
    print("=" * 60)

    # Paths
    root_dir = Path(__file__).parent.parent
    dist_dir = root_dir / "dist"
    installer_dir = root_dir / "installer"

    # Step 1: Clean old builds
    print("\n[1/4] Cleaning old builds...")
    if (dist_dir / "PlanningTool.exe").exists():
        (dist_dir / "PlanningTool.exe").unlink()

    # Step 2: Build with PyInstaller
    print("\n[2/4] Building executable with PyInstaller...")
    run_command(
        f'pyinstaller --noconfirm --onefile --windowed '
        f'--name "PlanningTool" '
        f'--icon "resources/icon.ico" '
        f'--add-data "Handleiding.html;." '
        f'--add-data "PROJECT_INFO.md;." '
        f'main.py',
        cwd=root_dir
    )

    # Step 3: Compile installer with Inno Setup
    print("\n[3/4] Compiling installer with Inno Setup...")
    inno_setup = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
    if not inno_setup.exists():
        print("ERROR: Inno Setup not found!")
        print("Download from: https://jrsoftware.org/isdl.php")
        sys.exit(1)

    run_command(
        f'"{inno_setup}" "{installer_dir}/PlanningTool.iss"',
        cwd=root_dir
    )

    # Step 4: Move output to dist
    print("\n[4/4] Moving installer to dist...")
    output_file = installer_dir / "Output" / f"PlanningTool_v{APP_VERSION}_Setup.exe"
    if output_file.exists():
        shutil.copy(output_file, dist_dir / output_file.name)
        print(f"\n✓ Installer created: dist/{output_file.name}")
    else:
        print("ERROR: Installer not found!")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Build complete!")
    print(f"Installer: dist/PlanningTool_v{APP_VERSION}_Setup.exe")
    print(f"Size: {(dist_dir / output_file.name).stat().st_size / (1024*1024):.1f} MB")

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python scripts/build_installer.py
```

**Output:**
- `dist/PlanningTool_v0.6.26_Setup.exe` (complete installer)
- `build/` folder (PyInstaller temp files - kan verwijderd worden)

---

## 4. Auto-Update Systeem

### 4.1 Architectuur Overzicht

```
┌─────────────────┐
│  Planning Tool  │
│   Application   │
└────────┬────────┘
         │
         ├─► [1] Check for updates (GitHub API)
         │   GET https://api.github.com/repos/USER/REPO/releases/latest
         │   Interval: 7 dagen (configurable)
         │
         ├─► [2] Compare versions
         │   Current: 0.6.26
         │   Latest: 0.7.0
         │   Using: packaging.version.parse()
         │
         ├─► [3] Show notification dialog
         │   "Nieuwe versie beschikbaar: 0.7.0"
         │   [Download]  [Later]  [Deze Versie Overslaan]
         │
         ├─► [4] Download installer (background thread)
         │   Download: PlanningTool_v0.7.0_Setup.exe
         │   Save to: %TEMP%\planning_tool_update\
         │   Progress: callback met bytes downloaded/total
         │
         └─► [5] Launch installer & exit
             Run: Setup.exe /SILENT /UPDATE
             Exit: current application (QApplication.quit())
```

### 4.2 Update Checker Service

**Bestand:** `services/update_checker.py`

```python
# services/update_checker.py
"""
Auto-update checking service
Uses GitHub Releases API for version checking and download
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from packaging import version
from config import APP_VERSION

class UpdateChecker:
    """Check for application updates via GitHub Releases"""

    # Configuration
    GITHUB_REPO = "yourusername/planning-tool"  # UPDATE THIS
    GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    CHECK_INTERVAL_DAYS = 7  # Check weekly

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.last_check_file = data_dir / "last_update_check.json"
        self.skipped_versions_file = data_dir / "skipped_versions.json"

    def should_check_for_updates(self) -> bool:
        """
        Determine if we should check for updates based on last check time.
        Returns True if check needed, False otherwise.
        """
        if not self.last_check_file.exists():
            return True

        try:
            data = json.loads(self.last_check_file.read_text())
            last_check = datetime.fromisoformat(data.get('last_check', '2000-01-01'))
            days_since = (datetime.now() - last_check).days
            return days_since >= self.CHECK_INTERVAL_DAYS
        except (json.JSONDecodeError, ValueError):
            return True

    def check_for_updates(self) -> Optional[Dict]:
        """
        Check GitHub Releases API for new version.

        Returns:
            Dict with update info if available, None otherwise
            {
                'version': '0.7.0',
                'download_url': 'https://github.com/.../Setup.exe',
                'release_notes': 'Release notes markdown',
                'published_at': '2025-11-10',
                'asset_size': 50000000
            }
        """
        try:
            # Call GitHub API
            headers = {
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            response = requests.get(self.GITHUB_API, headers=headers, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()

            # Extract version from tag_name (e.g., "v0.7.0" → "0.7.0")
            latest_version = data['tag_name'].lstrip('v')

            # Update last check timestamp
            self._save_last_check()

            # Compare versions
            if version.parse(latest_version) <= version.parse(APP_VERSION):
                return None  # No update available

            # Check if user skipped this version
            if self._is_version_skipped(latest_version):
                return None

            # Find installer asset in release
            installer_url = None
            asset_size = 0
            for asset in data.get('assets', []):
                if asset['name'].endswith('_Setup.exe'):
                    installer_url = asset['browser_download_url']
                    asset_size = asset.get('size', 0)
                    break

            if not installer_url:
                return None  # No installer found

            # Return update info
            return {
                'version': latest_version,
                'download_url': installer_url,
                'release_notes': data.get('body', ''),
                'published_at': data.get('published_at', ''),
                'asset_size': asset_size
            }

        except requests.RequestException as e:
            print(f"Update check failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error checking updates: {e}")
            return None

    def download_update(self, download_url: str, progress_callback=None) -> Optional[Path]:
        """
        Download installer to temp directory.

        Args:
            download_url: URL of installer
            progress_callback: Optional function(bytes_downloaded, total_bytes)

        Returns:
            Path to downloaded file, or None on failure
        """
        try:
            import tempfile

            # Create temp directory
            temp_dir = Path(tempfile.gettempdir()) / "planning_tool_update"
            temp_dir.mkdir(exist_ok=True)

            # Determine filename from URL
            filename = download_url.split('/')[-1]
            output_path = temp_dir / filename

            # Download with progress tracking
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return output_path

        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def skip_version(self, version_str: str):
        """Mark a version as skipped by user"""
        skipped = self._load_skipped_versions()
        if version_str not in skipped:
            skipped.append(version_str)
            self._save_skipped_versions(skipped)

    def _save_last_check(self):
        """Save timestamp of last update check"""
        data = {'last_check': datetime.now().isoformat()}
        self.last_check_file.write_text(json.dumps(data))

    def _load_skipped_versions(self) -> list:
        """Load list of user-skipped versions"""
        if not self.skipped_versions_file.exists():
            return []
        try:
            return json.loads(self.skipped_versions_file.read_text())
        except json.JSONDecodeError:
            return []

    def _save_skipped_versions(self, versions: list):
        """Save list of skipped versions"""
        self.skipped_versions_file.write_text(json.dumps(versions))

    def _is_version_skipped(self, version_str: str) -> bool:
        """Check if user skipped this version"""
        return version_str in self._load_skipped_versions()
```

**Dependencies:**
```bash
pip install requests packaging
```

### 4.3 Update Dialog UI

**Bestand:** `gui/dialogs/update_dialog.py`

```python
# gui/dialogs/update_dialog.py
"""
Update notification dialog
Shows available update with release notes and download option
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.styles import Styles, Colors, Fonts, Dimensions
from config import APP_VERSION
from typing import Dict, Optional
from pathlib import Path
import subprocess
import sys

class DownloadThread(QThread):
    """Background thread for downloading installer"""
    progress: pyqtSignal = pyqtSignal(int, int)  # (downloaded, total)
    finished: pyqtSignal = pyqtSignal(Path)  # downloaded file path
    error: pyqtSignal = pyqtSignal(str)  # error message

    def __init__(self, update_checker, download_url: str):
        super().__init__()
        self.update_checker = update_checker
        self.download_url = download_url

    def run(self):
        """Download installer in background"""
        try:
            path = self.update_checker.download_update(
                self.download_url,
                progress_callback=lambda dl, total: self.progress.emit(dl, total)  # type: ignore
            )
            if path:
                self.finished.emit(path)  # type: ignore
            else:
                self.error.emit("Download failed")  # type: ignore
        except Exception as e:
            self.error.emit(str(e))  # type: ignore

class UpdateDialog(QDialog):
    """Dialog showing available update"""

    def __init__(self, update_info: Dict, update_checker, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.update_checker = update_checker
        self.download_thread: Optional[DownloadThread] = None
        self.downloaded_file: Optional[Path] = None

        self.setWindowTitle("Update Beschikbaar")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self.init_ui()

    def init_ui(self):
        """Build dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        header = QLabel(
            f"Planning Tool {self.update_info['version']} is beschikbaar!"
        )
        header.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {Colors.PRIMARY};")
        layout.addWidget(header)

        # Current version info
        current_label = QLabel(f"Huidige versie: {APP_VERSION}")
        current_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(current_label)

        # Release notes
        notes_label = QLabel("Release notities:")
        notes_label.setStyleSheet(f"font-weight: bold; margin-top: 12px;")
        layout.addWidget(notes_label)

        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setPlainText(self.update_info['release_notes'])
        self.notes_text.setMaximumHeight(250)
        self.notes_text.setStyleSheet(Styles.input_field())
        layout.addWidget(self.notes_text)

        # Download progress (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                text-align: center;
                background: {Colors.BG_WHITE};
            }}
            QProgressBar::chunk {{
                background: {Colors.PRIMARY};
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.skip_btn = QPushButton("Deze Versie Overslaan")
        self.skip_btn.setStyleSheet(Styles.button_secondary())
        self.skip_btn.clicked.connect(self.on_skip)  # type: ignore
        button_layout.addWidget(self.skip_btn)

        self.later_btn = QPushButton("Later Herinneren")
        self.later_btn.setStyleSheet(Styles.button_secondary())
        self.later_btn.clicked.connect(self.reject)  # type: ignore
        button_layout.addWidget(self.later_btn)

        self.download_btn = QPushButton("Download Update")
        self.download_btn.setStyleSheet(Styles.button_primary())
        self.download_btn.clicked.connect(self.on_download)  # type: ignore
        button_layout.addWidget(self.download_btn)

        layout.addLayout(button_layout)

    def on_skip(self):
        """User wants to skip this version"""
        self.update_checker.skip_version(self.update_info['version'])
        self.reject()

    def on_download(self):
        """Start downloading update"""
        # Disable buttons
        self.download_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.later_btn.setEnabled(False)

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Downloaden...")

        # Start download thread
        self.download_thread = DownloadThread(
            self.update_checker,
            self.update_info['download_url']
        )
        self.download_thread.progress.connect(self.on_progress)  # type: ignore
        self.download_thread.finished.connect(self.on_download_complete)  # type: ignore
        self.download_thread.error.connect(self.on_download_error)  # type: ignore
        self.download_thread.start()

    def on_progress(self, downloaded: int, total: int):
        """Update progress bar"""
        if total > 0:
            percent = int((downloaded / total) * 100)
            self.progress_bar.setValue(percent)

            # Show MB
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.status_label.setText(
                f"Downloaden... {mb_downloaded:.1f} MB / {mb_total:.1f} MB"
            )

    def on_download_complete(self, file_path: Path):
        """Download finished successfully"""
        self.downloaded_file = file_path
        self.status_label.setText("Download compleet!")
        self.progress_bar.setValue(100)

        # Change button to "Install"
        self.download_btn.setText("Installeren & Afsluiten")
        self.download_btn.setEnabled(True)
        self.download_btn.clicked.disconnect()  # type: ignore
        self.download_btn.clicked.connect(self.on_install)  # type: ignore

    def on_download_error(self, error_msg: str):
        """Download failed"""
        self.status_label.setText(f"Fout: {error_msg}")
        self.progress_bar.setVisible(False)

        # Re-enable buttons
        self.download_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.later_btn.setEnabled(True)

        QMessageBox.critical(
            self,
            "Download Mislukt",
            f"Kan update niet downloaden:\n{error_msg}\n\n"
            f"Probeer later opnieuw of download handmatig van GitHub."
        )

    def on_install(self):
        """Launch installer and exit application"""
        if not self.downloaded_file or not self.downloaded_file.exists():
            return

        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Installatie Bevestigen",
            "De applicatie zal nu afsluiten en de installer starten.\n\n"
            "Uw database en instellingen worden automatisch behouden.\n\n"
            "Doorgaan met installatie?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Launch installer with /UPDATE flag
            subprocess.Popen([str(self.downloaded_file), '/SILENT', '/UPDATE'])

            # Exit application
            sys.exit(0)
```

### 4.4 Integratie in Main Application

**Bestand:** `main.py` (toevoegingen)

```python
# main.py (additions)

from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from services.update_checker import UpdateChecker
from gui.dialogs.update_dialog import UpdateDialog
from pathlib import Path

class PlanningToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... existing initialization ...

        # Check for updates after UI loads (5 second delay)
        QTimer.singleShot(5000, self.check_for_updates)

    def check_for_updates(self):
        """Check for application updates (non-blocking)"""
        try:
            # Get data directory from current database location
            data_dir = Path(__file__).parent / "data"
            update_checker = UpdateChecker(data_dir)

            # Only check if enough time passed
            if not update_checker.should_check_for_updates():
                return

            # Check in background thread
            class CheckThread(QThread):
                result: pyqtSignal = pyqtSignal(object)

                def __init__(self, checker):
                    super().__init__()
                    self.checker = checker

                def run(self):
                    update_info = self.checker.check_for_updates()
                    self.result.emit(update_info)  # type: ignore

            # Start check
            thread = CheckThread(update_checker)
            thread.result.connect(lambda info: self.on_update_check_complete(info, update_checker))  # type: ignore
            thread.start()
            self._update_check_thread = thread  # Keep reference

        except Exception as e:
            print(f"Update check error: {e}")

    def on_update_check_complete(self, update_info, update_checker):
        """Handle update check result"""
        if update_info:
            # Show update dialog
            dialog = UpdateDialog(update_info, update_checker, self)
            dialog.exec()
```

---

## 5. Database Migration Manager

### 5.1 Migration Strategie

**Doel:** Automatisch detecteren van database versie en vereiste migraties uitvoeren bij app start.

**Migration Workflow:**
```
App Start
    ↓
Get DB Version (uit db_metadata tabel)
    ↓
Compare met MIN_DB_VERSION (uit config.py)
    ↓
    ├─► DB Current → Launch app normaal
    ├─► DB Old → Show MigrationDialog → Run migrations → Launch app
    └─► DB Incompatible → Show error → Exit
```

**Bestaande Migration Scripts:**
```
migrations/
├── upgrade_to_v0_6_13.py    # db_metadata tabel
├── upgrade_to_v0_6_14.py    # gebruiker_werkposten
├── upgrade_to_v0_6_21.py    # shift_codes.is_kritisch
├── upgrade_to_v0_6_23.py    # verlof vervaldatum
├── upgrade_to_v0_6_24.py    # week definitie
└── (future scripts...)
```

### 5.2 Migration Manager Implementation

**Bestand:** `services/migration_manager.py`

```python
# services/migration_manager.py
"""
Automatic database migration system
Detects database version and runs required migration scripts
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple
import importlib.util
import shutil
from datetime import datetime
from config import MIN_DB_VERSION, APP_VERSION

class MigrationManager:
    """Manage database migrations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.migrations_dir = Path(__file__).parent.parent / "migrations"
        self.backups_dir = db_path.parent / "backups"
        self.backups_dir.mkdir(exist_ok=True)

    def get_current_db_version(self) -> str:
        """Get database version from db_metadata table"""
        from database.connection import get_db_version
        version = get_db_version()
        return version if version else "0.0.0"

    def needs_migration(self) -> bool:
        """Check if database needs migration"""
        from packaging import version
        current = self.get_current_db_version()
        return version.parse(current) < version.parse(MIN_DB_VERSION)

    def find_required_migrations(self) -> List[Path]:
        """
        Find all migration scripts needed to upgrade database.
        Returns list of migration scripts sorted by version.
        """
        from packaging import version

        current_version = self.get_current_db_version()
        required = []

        # Find all upgrade_to_vX_Y_Z.py scripts
        for script in self.migrations_dir.glob("upgrade_to_v*.py"):
            # Extract version from filename (e.g., "upgrade_to_v0_6_24.py" → "0.6.24")
            version_str = script.stem.replace("upgrade_to_v", "").replace("_", ".")

            # Include if version > current and <= MIN_DB_VERSION
            if (version.parse(version_str) > version.parse(current_version) and
                version.parse(version_str) <= version.parse(MIN_DB_VERSION)):
                required.append((version_str, script))

        # Sort by version
        required.sort(key=lambda x: [int(n) for n in x[0].split('.')])

        return [script for _, script in required]

    def create_backup(self) -> Path:
        """
        Create backup of database before migration.
        Returns path to backup file.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_str = self.get_current_db_version().replace(".", "_")
        backup_name = f"planning_v{version_str}_{timestamp}.db"
        backup_path = self.backups_dir / backup_name

        shutil.copy2(self.db_path, backup_path)
        print(f"✓ Backup created: {backup_path}")

        return backup_path

    def run_migration_script(self, script_path: Path) -> bool:
        """
        Run a single migration script.
        Returns True on success, False on failure.
        """
        try:
            print(f"\nRunning migration: {script_path.name}...")

            # Import migration script dynamically
            spec = importlib.util.spec_from_file_location("migration", script_path)
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load migration: {script_path}")

            migration = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration)

            # Run migration (should have upgrade() or main() function)
            if hasattr(migration, 'upgrade'):
                migration.upgrade()
            elif hasattr(migration, 'main'):
                migration.main()
            else:
                raise AttributeError("Migration script must have upgrade() or main() function")

            print(f"✓ Migration completed: {script_path.name}")
            return True

        except Exception as e:
            print(f"✗ Migration failed: {script_path.name}")
            print(f"  Error: {e}")
            return False

    def run_migrations(self, progress_callback=None) -> Tuple[bool, str]:
        """
        Run all required migrations.

        Args:
            progress_callback: Optional function(step: int, total: int, message: str)

        Returns:
            (success: bool, message: str)
        """
        try:
            # Find migrations
            migrations = self.find_required_migrations()

            if not migrations:
                return (True, "Database is up to date")

            total_steps = len(migrations) + 1  # +1 for backup

            # Step 1: Create backup
            if progress_callback:
                progress_callback(0, total_steps, "Creating backup...")

            backup_path = self.create_backup()

            # Step 2-N: Run migrations
            for i, script in enumerate(migrations):
                if progress_callback:
                    progress_callback(i + 1, total_steps, f"Running {script.name}...")

                success = self.run_migration_script(script)

                if not success:
                    return (False,
                            f"Migration failed: {script.name}\n\n"
                            f"Database backup available at:\n{backup_path}\n\n"
                            f"Contact support for assistance.")

            # All done
            new_version = self.get_current_db_version()
            return (True,
                    f"Database successfully upgraded to v{new_version}\n\n"
                    f"Backup saved to:\n{backup_path}")

        except Exception as e:
            return (False, f"Migration error: {e}")

    def restore_backup(self, backup_path: Path) -> bool:
        """Restore database from backup"""
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup not found: {backup_path}")

            shutil.copy2(backup_path, self.db_path)
            print(f"✓ Database restored from: {backup_path}")
            return True

        except Exception as e:
            print(f"✗ Restore failed: {e}")
            return False
```

### 5.3 Migration Dialog

**Bestand:** `gui/dialogs/migration_dialog.py`

```python
# gui/dialogs/migration_dialog.py
"""
Database migration progress dialog
Shows migration progress with backup info
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.styles import Styles, Colors, Dimensions
from services.migration_manager import MigrationManager

class MigrationThread(QThread):
    """Background thread for running migrations"""
    progress: pyqtSignal = pyqtSignal(int, int, str)  # (step, total, message)
    finished: pyqtSignal = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, migration_manager: MigrationManager):
        super().__init__()
        self.migration_manager = migration_manager

    def run(self):
        """Run migrations in background"""
        def progress_callback(step, total, message):
            self.progress.emit(step, total, message)  # type: ignore

        success, message = self.migration_manager.run_migrations(progress_callback)
        self.finished.emit(success, message)  # type: ignore

class MigrationDialog(QDialog):
    """Dialog showing migration progress"""

    def __init__(self, migration_manager: MigrationManager, parent=None):
        super().__init__(parent)
        self.migration_manager = migration_manager
        self.migration_thread = None
        self.migration_success = False

        self.setWindowTitle("Database Upgrade")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        # Prevent closing during migration
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        self.init_ui()
        self.start_migration()

    def init_ui(self):
        """Build dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimensions.SPACING_MEDIUM)

        # Header
        header = QLabel("Database Upgrade Vereist")
        header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(header)

        # Info text
        info = QLabel(
            "De database moet worden ge-upgrade naar de nieuwste versie.\n"
            "Een backup wordt automatisch aangemaakt."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {Colors.PRIMARY};
            }}
        """)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Voorbereiden...")
        self.status_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.status_label)

        # Log output
        log_label = QLabel("Migratie log:")
        log_label.setStyleSheet("font-weight: bold; margin-top: 12px;")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(Styles.input_field())
        layout.addWidget(self.log_text)

        # Close button (disabled initially)
        self.close_btn = QPushButton("Sluiten")
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet(Styles.button_primary())
        self.close_btn.clicked.connect(self.accept)  # type: ignore
        layout.addWidget(self.close_btn)

    def start_migration(self):
        """Start migration in background thread"""
        self.migration_thread = MigrationThread(self.migration_manager)
        self.migration_thread.progress.connect(self.on_progress)  # type: ignore
        self.migration_thread.finished.connect(self.on_finished)  # type: ignore
        self.migration_thread.start()

    def on_progress(self, step: int, total: int, message: str):
        """Update progress display"""
        percent = int((step / total) * 100)
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        self.log_text.append(f"[{step}/{total}] {message}")

    def on_finished(self, success: bool, message: str):
        """Migration completed"""
        self.migration_success = success
        self.progress_bar.setValue(100 if success else 0)

        if success:
            self.status_label.setText("✓ Migratie succesvol!")
            self.status_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        else:
            self.status_label.setText("✗ Migratie mislukt")
            self.status_label.setStyleSheet(f"color: {Colors.ERROR};")

        self.log_text.append(f"\n{message}")

        # Enable close button
        self.close_btn.setEnabled(True)

        if not success:
            self.close_btn.setText("Afsluiten")
```

### 5.4 Startup Integratie

**Bestand:** `main.py` (toevoegingen)

```python
# main.py (additions to main())

from database.connection import check_db_compatibility
from services.migration_manager import MigrationManager
from gui.dialogs.migration_dialog import MigrationDialog
from PyQt6.QtWidgets import QMessageBox
from pathlib import Path

def main():
    app = QApplication(sys.argv)

    # Step 1: Check database compatibility
    is_compatible, db_version, error_msg = check_db_compatibility()

    if not is_compatible:
        # Database needs migration
        db_path = Path(__file__).parent / "data" / "planning.db"
        migration_manager = MigrationManager(db_path)

        if migration_manager.needs_migration():
            # Show migration dialog
            dialog = MigrationDialog(migration_manager)
            dialog.exec()

            if not dialog.migration_success:
                # Migration failed - show error and exit
                QMessageBox.critical(
                    None,
                    "Database Upgrade Mislukt",
                    "Kan database niet upgraden.\n\n"
                    "Neem contact op met support voor assistentie."
                )
                sys.exit(1)

            # Migration succeeded - continue
        else:
            # Cannot migrate - show error and exit
            QMessageBox.critical(
                None,
                "Database Incompatibel",
                error_msg
            )
            sys.exit(1)

    # Step 2: Launch application
    window = PlanningToolApp()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 6. GitHub Release Workflow

### 6.1 Release Creation Checklist

**Pre-Release Checklist:**
```
[ ] Update APP_VERSION in config.py
[ ] Update MIN_DB_VERSION if DB changed
[ ] Create migration script if needed (upgrade_to_vX_Y_Z.py)
[ ] Update PROJECT_INFO.md with release notes
[ ] Update CLAUDE.md, DEV_NOTES.md, DEVELOPMENT_GUIDE.md version numbers
[ ] Run all tests
[ ] Build installer: python scripts/build_installer.py
[ ] Test installer on clean machine (fresh install)
[ ] Test installer on existing install (upgrade path)
[ ] Verify database migration works (if applicable)
[ ] Test auto-update detection (using previous release)
```

### 6.2 Creating a GitHub Release

**Option 1: Using GitHub CLI (gh)**
```bash
# Tag the release
git tag -a v0.7.0 -m "Release v0.7.0: Feature description"
git push origin v0.7.0

# Create release with installer
gh release create v0.7.0 \
  --title "Planning Tool v0.7.0" \
  --notes-file docs/release_notes/RELEASE_NOTES_v0.7.0.md \
  dist/PlanningTool_v0.7.0_Setup.exe
```

**Option 2: Using GitHub Web UI**
1. Go to repository → Releases → "Draft a new release"
2. Choose tag: `v0.7.0`
3. Release title: `Planning Tool v0.7.0`
4. Description: Copy from PROJECT_INFO.md or create release notes
5. Attach file: `PlanningTool_v0.7.0_Setup.exe`
6. Click "Publish release"

**Verification:**
```bash
# Test API response
curl https://api.github.com/repos/USER/REPO/releases/latest

# Should return JSON with:
# - "tag_name": "v0.7.0"
# - "assets": [{ "name": "PlanningTool_v0.7.0_Setup.exe", "browser_download_url": "..." }]
```

### 6.3 Release Notes Template

**Bestand:** `docs/release_notes/RELEASE_NOTES_v0.X.Y.md`

```markdown
# Planning Tool v0.X.Y

**Release Date:** 2025-XX-XX
**Database Version:** 0.X.Y
**Download:** [PlanningTool_v0.X.Y_Setup.exe](link)

---

## What's New

### Features
- ✅ Feature 1 description
- ✅ Feature 2 description

### Improvements
- 🔧 Improvement 1
- 🔧 Improvement 2

### Bug Fixes
- 🐛 Bug fix 1
- 🐛 Bug fix 2

---

## Upgrade Instructions

### For New Installations
1. Download `PlanningTool_v0.X.Y_Setup.exe`
2. Run installer
3. Follow wizard prompts
4. Default credentials: `admin` / `admin`

### For Existing Users

**⚠️ Important:** Backup your database before upgrading!

1. Close Planning Tool
2. Download `PlanningTool_v0.X.Y_Setup.exe`
3. Run installer (will automatically preserve your data)
4. Database will automatically upgrade on first launch

### Database Migration

This version requires database upgrade from v0.6.X to v0.X.Y:
- **Automatic backup** created before migration
- **Migration changes:** [description of schema changes]
- **Estimated time:** < 1 minute

---

## Known Issues

- Issue 1 description (workaround if available)

---

## Technical Details

- **Application Version:** 0.X.Y
- **Minimum Database Version:** 0.X.Y
- **Python Version:** 3.12
- **PyQt6 Version:** 6.x

---

## Support

- **GitHub Issues:** https://github.com/USER/REPO/issues
- **Email:** support@example.com
- **Documentation:** `Handleiding.html` (included in installation)
```

---

## 7. Implementatie Roadmap

### Phase 1: Installer Setup (4-6 uur)

**Week 1 - Setup & Basic Installer**

**Day 1: Environment Setup (1 uur)**
- [ ] Download en installeer Inno Setup 6
- [ ] Verify installation: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"`
- [ ] Create project folders:
  ```
  mkdir installer
  mkdir installer\Output
  mkdir scripts
  ```
- [ ] Install dependencies: `pip install packaging requests`

**Day 2: Installer Script (2 uur)**
- [ ] Create `installer/PlanningTool.iss` (basis script)
- [ ] Generate unique GUID voor AppId
- [ ] Configure [Setup] sectie (paths, output, compression)
- [ ] Configure [Files] sectie (executable + data folders)
- [ ] Configure [Dirs] sectie (data, exports permissions)
- [ ] Configure [Icons] sectie (Start Menu + Desktop)
- [ ] Configure [Code] sectie (running check, uninstall logic)

**Day 3: Build Automation (1 uur)**
- [ ] Create `scripts/build_installer.py`
- [ ] Test PyInstaller build
- [ ] Test Inno Setup compilation
- [ ] Verify output: `dist/PlanningTool_v0.6.26_Setup.exe`

**Day 4: Testing (2 uur)**
- [ ] Test fresh install op schone machine/VM
- [ ] Verify database created in `data/`
- [ ] Verify Start Menu shortcuts work
- [ ] Test uninstall (keep data)
- [ ] Test uninstall (delete data)
- [ ] Test upgrade scenario (install v0.6.25 → upgrade to v0.6.26)
- [ ] Verify data preserved after upgrade

**Deliverables:**
- ✅ Working installer (`PlanningTool_v0.6.26_Setup.exe`)
- ✅ Build automation script
- ✅ Tested fresh install + upgrade paths

---

### Phase 2: Auto-Update System (6-8 uur)

**Week 2 - Update Checking & Download**

**Day 1: GitHub Setup (2 uur)**
- [ ] Create GitHub repository (private or public)
- [ ] Add `.gitignore` voor Python/PyQt6
- [ ] Push current codebase
- [ ] Create first release:
  - Tag: `v0.6.26`
  - Title: "Planning Tool v0.6.26"
  - Upload: `PlanningTool_v0.6.26_Setup.exe`
- [ ] Test API call: `curl https://api.github.com/repos/USER/REPO/releases/latest`
- [ ] Verify JSON contains correct version + download URL

**Day 2: Update Checker Service (2 uur)**
- [ ] Create `services/update_checker.py`
- [ ] Implement `UpdateChecker` class:
  - [ ] `should_check_for_updates()` - 7 day interval check
  - [ ] `check_for_updates()` - GitHub API call
  - [ ] `download_update()` - Download installer met progress
  - [ ] `skip_version()` - User preference storage
- [ ] Test manually met print statements

**Day 3: Update Dialog UI (2 uur)**
- [ ] Create `gui/dialogs/update_dialog.py`
- [ ] Implement `UpdateDialog` class:
  - [ ] Header met nieuwe versie info
  - [ ] Release notes display (QTextEdit)
  - [ ] Progress bar voor download
  - [ ] Buttons: "Download", "Later", "Skip Version"
- [ ] Implement `DownloadThread` voor background download
- [ ] Test dialog met mock data

**Day 4: Main App Integration (1 uur)**
- [ ] Update `main.py`:
  - [ ] Add `check_for_updates()` method
  - [ ] QTimer.singleShot(5000) voor delayed check
  - [ ] Background thread voor API call
- [ ] Test end-to-end:
  - [ ] Create test release (v0.6.27)
  - [ ] Run app, wait 5 seconds
  - [ ] Verify dialog appears
  - [ ] Test download + install flow

**Day 5: Edge Cases & Polish (1 uur)**
- [ ] Test no internet scenario (graceful failure)
- [ ] Test "skip version" persistence
- [ ] Test "remind later" (check after 7 days)
- [ ] Test already on latest version (no dialog)
- [ ] Add error logging

**Deliverables:**
- ✅ Working auto-update notification
- ✅ One-click download + install
- ✅ GitHub Releases integration
- ✅ User preferences (skip version)

---

### Phase 3: Database Migration System (4-6 uur)

**Week 3 - Automatic Migrations**

**Day 1: Migration Manager (2 uur)**
- [ ] Create `services/migration_manager.py`
- [ ] Implement `MigrationManager` class:
  - [ ] `get_current_db_version()` - Read from db_metadata
  - [ ] `needs_migration()` - Compare current vs MIN_DB_VERSION
  - [ ] `find_required_migrations()` - Discover scripts in migrations/
  - [ ] `create_backup()` - Copy database met timestamp
  - [ ] `run_migration_script()` - Dynamic import + execute
  - [ ] `run_migrations()` - Sequential execution met progress
- [ ] Test manually met v0.6.20 database

**Day 2: Migration Dialog (1 uur)**
- [ ] Create `gui/dialogs/migration_dialog.py`
- [ ] Implement `MigrationDialog` class:
  - [ ] Progress bar + step counter
  - [ ] Log output (QTextEdit)
  - [ ] Success/failure messaging
- [ ] Implement `MigrationThread` voor background execution
- [ ] Test dialog met mock migrations

**Day 3: Startup Integration (1 uur)**
- [ ] Update `main.py`:
  - [ ] Check `check_db_compatibility()` before login
  - [ ] If needs migration → show MigrationDialog
  - [ ] If success → continue to login
  - [ ] If failure → show error + exit
- [ ] Test startup flow

**Day 4: Testing Scenarios (2 uur)**
- [ ] Test fresh install (no migration needed)
- [ ] Test upgrade v0.6.20 → v0.6.26:
  - [ ] Verify all intermediate migrations run (v0.6.21, v0.6.23, v0.6.24)
  - [ ] Verify backup created
  - [ ] Verify db_metadata updated
- [ ] Test migration failure:
  - [ ] Simulate script error
  - [ ] Verify backup not overwritten
  - [ ] Verify error message shown
- [ ] Test rollback procedure (manual)

**Deliverables:**
- ✅ Automatic migration detection
- ✅ Sequential migration execution
- ✅ Automatic backups
- ✅ User-friendly progress display

---

### Phase 4: Documentation & Polish (2 uur)

**Week 4 - Documentation**

**Day 1: User Documentation (1 uur)**
- [ ] Update `Handleiding.html`:
  - [ ] Add "Installatie" sectie
  - [ ] Add "Updates" sectie
  - [ ] Add "Troubleshooting" sectie
- [ ] Create FAQ:
  - Q: Hoe installeer ik Planning Tool?
  - Q: Hoe werk ik de applicatie bij?
  - Q: Wat gebeurt er met mijn data bij update?
  - Q: Hoe herstel ik een backup?

**Day 2: Developer Documentation (1 uur)**
- [ ] Update `DEVELOPMENT_GUIDE.md`:
  - [ ] Add "Building Installer" sectie
  - [ ] Add "Release Workflow" sectie
  - [ ] Add "Migration Best Practices"
- [ ] Update `CLAUDE.md`:
  - [ ] Add installer info to "Running the Application"
  - [ ] Update version management section
- [ ] Create `docs/INSTALLER_IMPLEMENTATION_PLAN.md` (dit document)

**Deliverables:**
- ✅ Complete user guide voor installatie/updates
- ✅ Developer docs voor release process
- ✅ FAQ voor common issues

---

### Summary Timeline

| Phase | Effort | Completion |
|-------|--------|------------|
| Phase 1: Installer | 4-6 uur | Week 1 |
| Phase 2: Auto-Update | 6-8 uur | Week 2 |
| Phase 3: Migrations | 4-6 uur | Week 3 |
| Phase 4: Documentation | 2 uur | Week 4 |
| **TOTAL** | **16-22 uur** | **1 maand** |

**Aanbevolen Planning:**
- Week 1: Installer (direct bruikbaar voor v0.6.27 release)
- Week 2-3: Auto-update + migrations (complete ecosystem)
- Week 4: Documentation + polish

**Milestone Releases:**
- **v0.6.27:** Eerste release met installer (no auto-update yet)
- **v0.7.0:** Complete installer + auto-update + migrations ecosystem

---

## 8. Risico's & Mitigaties

### Technische Risico's

**1. Database Corruption bij Migratie**
- **Risico:** Migration script faalt, database corrupt
- **Impact:** HIGH - Data loss voor gebruikers
- **Mitigatie:**
  - ✅ Automatic backup voor ELKE migratie
  - ✅ Transaction-based migrations waar mogelijk
  - ✅ Test migrations op kopie van productie database
  - ✅ Document manual restoration procedure
  - ✅ Keep previous installer version available

**2. Antivirus False Positives**
- **Risico:** PyInstaller executables worden geflagged door antivirus
- **Impact:** MEDIUM - Gebruikers kunnen niet installeren
- **Mitigatie:**
  - ✅ Code signing certificate (€100/jaar, aanbevolen)
  - ✅ Submit to VirusTotal voor whitelisting
  - ✅ Document in FAQ hoe exception toevoegen
  - ✅ Contact IT afdeling voor centrale whitelist

**3. Permissions Problemen**
- **Risico:** Users zonder admin rechten kunnen niet installeren
- **Impact:** MEDIUM - Blocked installations
- **Mitigatie:**
  - ✅ Installer vereist admin (standard voor Program Files)
  - ✅ IT afdeling pre-install voor alle users
  - ✅ Alternative: "per-user" install mode (no admin, limited features)

**4. Network Drive Performance**
- **Risico:** SQLite op netwerk drive = slow performance
- **Impact:** MEDIUM - Poor user experience
- **Mitigatie:**
  - ✅ Aanbevolen: lokale installatie op C:\
  - ✅ Warning in installer bij netwerk path detectie
  - ✅ Consider SQLite WAL mode voor betere concurrency
  - ✅ Document performance considerations

**5. Update Tijdens Active Use**
- **Risico:** User triggert update terwijl anderen werken
- **Impact:** MEDIUM - Data conflicts, locked files
- **Mitigatie:**
  - ✅ Warn in update dialog: "Sluit op alle machines"
  - ✅ Check for file locks voor migration start
  - ✅ Consider "maintenance window" scheduling
  - ✅ Auto-save functionaliteit in app

**6. GitHub API Rate Limiting**
- **Risico:** Te veel update checks → rate limit hit
- **Impact:** LOW - Update check faalt tijdelijk
- **Mitigatie:**
  - ✅ 7-day check interval (ver onder 60 calls/hour limit)
  - ✅ Graceful failure bij API errors
  - ✅ No retry loop (wait for next scheduled check)

### Healthcare-Specific Risico's

**1. Data Privacy (GDPR/AVG)**
- **Compliance Requirement:** Geen data naar externe servers
- **Mitigatie:**
  - ✅ Update checks: alleen versie nummer uitgewisseld (geen personal data)
  - ✅ Lokale storage: alle data blijft in Program Files (auditable)
  - ✅ No telemetry, no analytics
  - ✅ GitHub: alleen public version info, geen user data

**2. Audit Trail**
- **Requirement:** Traceerbaarheid van changes
- **Mitigatie:**
  - ✅ Migration logs in `data/logs/` directory
  - ✅ db_metadata tabel tracked alle upgrades met timestamps
  - ✅ Backup files timestamped voor forensics
  - ✅ Version info in About dialog

**3. Uptime Requirements**
- **Requirement:** Minimale downtime voor shifts planning
- **Mitigatie:**
  - ✅ Test migration time op large datasets (target: < 1 min)
  - ✅ Document expected downtime per version
  - ✅ Suggest maintenance window (bijv. weekend)
  - ✅ Quick rollback procedure

**4. Multi-Workstation Coordination**
- **Challenge:** Shared database, multiple install points
- **Mitigatie:**
  - ✅ Update instructions: "Install op alle workstations"
  - ✅ Version check waarschuwt als app nieuwer dan DB
  - ✅ Consider centralized update notification
  - ✅ Future: "server" + "client" architecture

### Business Risico's

**1. Support Load**
- **Risk:** 20-50 users × 1-2 support tickets per major update
- **Impact:** MEDIUM - Support time cost
- **Mitigatie:**
  - ✅ Comprehensive documentation (Handleiding.html)
  - ✅ Video tutorial voor installation (optional)
  - ✅ FAQ voor common issues
  - ✅ Beta testing group (5 power users)

**2. Testing Overhead**
- **Risk:** 2-4 hours per release voor testing
- **Impact:** LOW - Manageable time investment
- **Mitigatie:**
  - ✅ Automated test suite (in progress)
  - ✅ Testing checklist (see below)
  - ✅ Staging environment voor pre-release testing

**3. Update Adoption Rate**
- **Risk:** Users don't update, running old versions
- **Impact:** MEDIUM - Fragmented version landscape
- **Mitigatie:**
  - ✅ In-app notifications (implemented)
  - ✅ Email announcement voor major releases
  - ✅ Eventually: minimum version enforcement
  - ✅ Show version in About dialog + login screen

### Testing Checklist

**Voor elke release:**
```
PRE-BUILD:
[ ] Update APP_VERSION in config.py
[ ] Update MIN_DB_VERSION if DB changed
[ ] Create migration script if needed
[ ] Update all documentation (4 files)
[ ] Run unit tests
[ ] Manual smoke test on dev machine

BUILD:
[ ] Run build_installer.py
[ ] Verify no errors in build output
[ ] Check installer size (expected ~50MB)

TESTING - FRESH INSTALL:
[ ] Install on clean Windows 10/11 machine
[ ] Verify database created in data/
[ ] Verify default login works (admin/admin)
[ ] Verify Start Menu shortcut works
[ ] Verify Desktop shortcut works (if enabled)
[ ] Test basic functionality (create user, add shift)
[ ] Check About dialog shows correct version

TESTING - UPGRADE:
[ ] Install previous version first
[ ] Create test data (users, shifts, planning)
[ ] Install new version over existing
[ ] Verify data preserved
[ ] Verify migration runs automatically
[ ] Verify backup created in data/backups/
[ ] Verify db_metadata shows new version
[ ] Test basic functionality still works

TESTING - AUTO-UPDATE:
[ ] Run previous version
[ ] Wait 5 seconds after startup
[ ] Verify update notification appears
[ ] Test "Download" button
[ ] Verify download progress shows
[ ] Test "Install & Exit" workflow

TESTING - EDGE CASES:
[ ] Test uninstall (keep data)
[ ] Test uninstall (delete data)
[ ] Test install with no admin rights (should fail gracefully)
[ ] Test app running during install (should warn)
[ ] Test network drive installation (if applicable)

POST-RELEASE:
[ ] Create GitHub release
[ ] Upload installer as asset
[ ] Verify API returns correct version
[ ] Test auto-update detection from previous version
[ ] Announce to users (email/Slack)
```

---

## 9. Code Examples

### 9.1 Inno Setup - Custom Page Example

**Custom page voor database locatie kiezen (advanced users):**

```pascal
[Code]
var
  DataDirPage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  // Create custom page for data directory
  DataDirPage := CreateInputDirPage(wpSelectDir,
    'Database Locatie',
    'Waar moeten gebruikersgegevens worden opgeslagen?',
    'Standaard locatie is in de installatie map.' + #13#10 +
    'Wijzig dit alleen als u een specifieke locatie nodig heeft (bijv. netwerkschijf).',
    False, '');

  DataDirPage.Add('Database directory:');
  DataDirPage.Values[0] := ExpandConstant('{app}\data');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Save selected data directory for application to read
    SaveStringToFile(ExpandConstant('{app}\data_path.txt'),
                     DataDirPage.Values[0], False);
  end;
end;
```

**Application code om custom path te lezen:**

```python
# config.py (optional enhancement)

def get_data_directory():
    """Get data directory (supports custom installer path)"""
    # Check for installer-configured path
    app_dir = Path(__file__).parent
    data_path_file = app_dir / "data_path.txt"

    if data_path_file.exists():
        custom_path = data_path_file.read_text().strip()
        return Path(custom_path)

    # Default: relative to app directory
    return app_dir / "data"

# Usage in connection.py
from config import get_data_directory
DB_PATH = get_data_directory() / "planning.db"
```

### 9.2 Migration Script Template

**Template voor nieuwe migration scripts:**

```python
#!/usr/bin/env python
"""
Database Migration: v0.6.X to v0.7.0
Description: Add new feature XYZ tables and columns
"""

import sqlite3
from pathlib import Path

def upgrade():
    """Run the migration"""
    # Get database path
    db_path = Path(__file__).parent.parent / "data" / "planning.db"

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    print(f"Starting migration for {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Start transaction
        conn.execute("BEGIN TRANSACTION")

        # Check if migration already applied
        cursor.execute("PRAGMA table_info(your_table)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'new_column' in columns:
            print("Migration already applied, skipping...")
            conn.rollback()
            return

        # === APPLY CHANGES ===

        # 1. Add new column
        print("Adding new_column to your_table...")
        cursor.execute("""
            ALTER TABLE your_table
            ADD COLUMN new_column TEXT DEFAULT 'default_value'
        """)

        # 2. Create new table
        print("Creating new_feature table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS new_feature (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_actief INTEGER DEFAULT 1
            )
        """)

        # 3. Migrate data (if needed)
        print("Migrating existing data...")
        cursor.execute("""
            UPDATE your_table
            SET new_column = 'migrated_value'
            WHERE some_condition = 1
        """)

        # 4. Update database version
        print("Updating database version...")
        cursor.execute("""
            INSERT INTO db_metadata (version_number, migration_description, applied_at)
            VALUES ('0.7.0', 'Add feature XYZ support', CURRENT_TIMESTAMP)
        """)

        # Commit transaction
        conn.commit()
        print("✓ Migration completed successfully!")

    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
```

**Usage:**
```bash
python migrations/upgrade_to_v0_7_0.py
```

### 9.3 GitHub API Testing Script

**Script om update check te testen zonder app te runnen:**

```python
#!/usr/bin/env python
"""
Test script for GitHub Releases API
Verifies API access and response format
"""

import requests
import json
from packaging import version

GITHUB_REPO = "your-username/planning-tool"  # UPDATE THIS
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CURRENT_VERSION = "0.6.26"

def test_update_check():
    """Test update checker logic"""
    print(f"Testing update check for {GITHUB_REPO}...")
    print(f"Current version: {CURRENT_VERSION}")
    print(f"API URL: {API_URL}\n")

    try:
        # Call API
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        response = requests.get(API_URL, headers=headers, timeout=10)

        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print("ERROR: API call failed")
            return

        data = response.json()

        # Extract info
        latest_version = data['tag_name'].lstrip('v')
        release_notes = data.get('body', '')
        published_at = data.get('published_at', '')

        print(f"Latest Version: {latest_version}")
        print(f"Published At: {published_at}")
        print(f"\nRelease Notes:\n{release_notes[:200]}...\n")

        # Find installer asset
        installer_found = False
        for asset in data.get('assets', []):
            if asset['name'].endswith('_Setup.exe'):
                installer_found = True
                print(f"Installer Asset:")
                print(f"  Name: {asset['name']}")
                print(f"  Size: {asset['size'] / (1024*1024):.1f} MB")
                print(f"  Download URL: {asset['browser_download_url']}")
                break

        if not installer_found:
            print("WARNING: No installer found in release assets!")
            return

        # Compare versions
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            print(f"\n✓ Update available: {CURRENT_VERSION} → {latest_version}")
        else:
            print(f"\n✓ Already on latest version")

    except requests.RequestException as e:
        print(f"ERROR: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")

if __name__ == "__main__":
    test_update_check()
```

**Usage:**
```bash
python scripts/test_update_check.py
```

---

## 10. Veelgestelde Vragen (FAQ)

### Voor Gebruikers

**Q: Hoe installeer ik Planning Tool?**
A: Download `PlanningTool_vX.Y.Z_Setup.exe`, dubbelklik, en volg de wizard. De installer vraagt om admin rechten (normaal voor software installatie). Kies een installatie locatie (standaard: `C:\Program Files\Planning Tool`). Na installatie vind je een snelkoppeling in het Start Menu.

**Q: Wat gebeurt er met mijn data bij een update?**
A: Je data (database, exports) blijven volledig behouden. De installer overschrijft alleen de applicatie zelf, niet je gegevens. Daarnaast maakt het systeem automatisch een backup van je database voor elke update.

**Q: Hoe werk ik de applicatie bij?**
A: Planning Tool checkt automatisch op updates (elke 7 dagen). Als een nieuwe versie beschikbaar is, zie je een notificatie. Klik op "Download Update", wacht tot de download klaar is, en klik "Installeren & Afsluiten". De nieuwe versie wordt automatisch geïnstalleerd.

**Q: Kan ik een update overslaan?**
A: Ja, klik op "Deze Versie Overslaan" in de update dialog. Je krijgt dan geen notificatie meer voor die specifieke versie. Voor nieuwere versies krijg je wel weer een notificatie.

**Q: Hoe herstel ik een backup?**
A: Backups staan in `C:\Program Files\Planning Tool\data\backups\`. Sluit Planning Tool, hernoem de huidige `planning.db`, en kopieer de backup naar `planning.db`. Let op: je verliest dan wijzigingen na de backup datum.

**Q: Werkt Planning Tool zonder internet?**
A: Ja! Planning Tool werkt volledig offline. Internet is alleen nodig voor de automatische update check. Als je geen internet hebt, kan je de applicatie gewoon blijven gebruiken.

**Q: Mijn antivirus blokkeert de installer, wat nu?**
A: PyInstaller executables worden soms ten onrechte geblokkeerd. Voeg een exception toe in je antivirus voor `PlanningTool_vX.Y.Z_Setup.exe`. Contact je IT afdeling als je hiermee niet zelf kan. De installer bevat geen virus - dit is een "false positive".

### Voor Developers

**Q: Hoe bouw ik een nieuwe installer?**
A: Run `python scripts/build_installer.py`. Dit script doet alles automatisch: PyInstaller build → Inno Setup compile → Output naar `dist/`. Zorg dat Inno Setup 6 geïnstalleerd is.

**Q: Hoe maak ik een nieuwe release?**
A:
1. Update `APP_VERSION` in `config.py`
2. Create migration script indien nodig
3. Build installer: `python scripts/build_installer.py`
4. Test op schone machine
5. Create GitHub release met tag `vX.Y.Z`
6. Upload installer als asset

**Q: Wanneer moet ik `MIN_DB_VERSION` verhogen?**
A: Alleen bij database schema changes (nieuwe tabel, nieuwe kolom, changed kolom type). Bij GUI-only changes blijft `MIN_DB_VERSION` hetzelfde.

**Q: Hoe test ik een upgrade scenario?**
A:
1. Install vorige versie op test machine
2. Maak test data (users, shifts, planning)
3. Install nieuwe versie (overschrijft oude)
4. Verify data preserved + migration succesvol
5. Test functionaliteit

**Q: Wat als een migration faalt in productie?**
A:
1. Check backup in `data/backups/` folder
2. Hernoem backup naar `planning.db`
3. Run oude app versie (previous installer)
4. Contact developer met error log uit `data/logs/`
5. Fix migration script + re-release

**Q: Hoe debug ik de auto-update checker?**
A: Run `python scripts/test_update_check.py` (zie Code Examples). Dit test de GitHub API zonder de hele app te starten. Check ook `data/last_update_check.json` voor laatste check timestamp.

---

## 11. Conclusie & Next Steps

### Samenvatting

Dit implementatieplan biedt een complete, pragmatische oplossing voor professionele Windows deployment van Planning Tool:

**Technisch:**
- ✅ Inno Setup installer (industry standard, makkelijk te onderhouden)
- ✅ Database in installatiemap (simpel, geen code changes)
- ✅ GitHub Releases voor distributie (gratis, betrouwbaar)
- ✅ Automatische migraties met backups (veilig, user-friendly)

**Business:**
- ✅ Professional user experience (wizard, shortcuts, uninstaller)
- ✅ Lage support overhead (automated processes)
- ✅ Schaalbaar naar 20-50+ gebruikers
- ✅ Healthcare compliant (lokale data, audit trail)

**Effort:**
- ✅ 16-22 uur totaal (medium complexity)
- ✅ Gefaseerde implementatie mogelijk
- ✅ Eerste fase (installer) direct bruikbaar

### Aanbevolen Start

**Begin met Phase 1 (Installer):**
1. Installeer Inno Setup (30 min)
2. Maak basis installer script (2 uur)
3. Test op schone machine (1 uur)
4. Release v0.6.27 met installer ✅

**Voordelen:**
- Direct professionele distributie
- Minimale investering (4-6 uur)
- Feedback van users voor Phase 2/3

**Later uitbreiden:**
- Week 2-3: Auto-update + migrations
- Complete ecosystem release: v0.7.0

### Success Metrics

**Na Phase 1 (Installer):**
- [ ] 90%+ users kunnen zonder support installeren
- [ ] Geen data loss reports bij updates
- [ ] < 5 minuten install time (gemiddeld)

**Na Phase 2-3 (Complete):**
- [ ] 80%+ users updaten binnen 1 week na release
- [ ] < 2 support tickets per release (avg)
- [ ] 100% data preserved bij updates

### Support & Maintenance

**Ongoing Effort:**
- **Per release:** 2-4 uur testing + deployment
- **Per major update:** +2 uur documentatie updates
- **Support:** ~1-2 uur per 50 users per major release

**Maintenance Tasks:**
- Update GitHub releases (quarterly)
- Monitor GitHub API rate limits (yearly review)
- Refresh code signing certificate (yearly, €100)
- Review migration scripts (per release)

---

**Document Versie:** 1.0
**Laatst Bijgewerkt:** 2025-11-05
**Auteur:** Claude Code (Research & Planning)
**Status:** APPROVED FOR IMPLEMENTATION ✅

---

## Appendix A: Useful Resources

### Official Documentation
- **Inno Setup:** https://jrsoftware.org/ishelp/
- **GitHub Releases API:** https://docs.github.com/en/rest/releases
- **PyInstaller:** https://pyinstaller.org/en/stable/
- **SQLite Backup:** https://www.sqlite.org/backup.html

### Community Examples
- **Inno Setup Examples:** https://github.com/jrsoftware/issrc/tree/main/Examples
- **Python Installer Tutorials:** Search "PyInstaller + Inno Setup"
- **Auto-Update Patterns:** Search "electron-updater" (concepts applicable)

### Tools
- **GUID Generator:** https://www.guidgenerator.com/
- **VirusTotal:** https://www.virustotal.com/ (for false positive checks)
- **Code Signing:** Sectigo, DigiCert (€100-200/year)

---

*Einde document - Klaar voor implementatie wanneer je wilt beginnen!*
