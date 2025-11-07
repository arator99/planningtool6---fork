# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file voor Planning Tool v0.6.9

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include documentatie (nodig voor handleiding systeem)
        ('PROJECT_INFO.md', '.'),
        ('HANDLEIDING.md', '.'),

        # Include database (optioneel - kan ook leeg starten)
        # ('data/planning.db', 'data'),

        # Als je een icon wilt (optioneel)
        # ('icon.ico', '.'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',

        # Database
        'sqlite3',

        # Security
        'bcrypt',

        # Alle GUI modules
        'gui.styles',
        'gui.screens.login_screen',
        'gui.screens.dashboard_screen',
        'gui.screens.gebruikersbeheer_screen',
        'gui.screens.feestdagen_screen',
        'gui.screens.shift_codes_screen',
        'gui.screens.typetabel_beheer_screen',
        'gui.screens.planning_editor_screen',
        'gui.screens.verlof_aanvragen_screen',
        'gui.screens.verlof_goedkeuring_screen',
        'gui.screens.mijn_planning_screen',
        'gui.screens.hr_regels_beheer_screen',
        'gui.screens.rode_lijnen_beheer_screen',

        # Dialogs
        'gui.dialogs.about_dialog',
        'gui.dialogs.speciale_code_dialog',
        'gui.dialogs.werkpost_naam_dialog',
        'gui.dialogs.shift_codes_grid_dialog',
        'gui.dialogs.typetabel_dialogs',
        'gui.dialogs.typetabel_editor_dialog',
        'gui.dialogs.handleiding_dialog',
        'gui.dialogs.hr_regel_edit_dialog',
        'gui.dialogs.rode_lijnen_config_dialog',

        # Widgets
        'gui.widgets.grid_kalender_base',
        'gui.widgets.planner_grid_kalender',
        'gui.widgets.teamlid_grid_kalender',
        'gui.widgets.theme_toggle_widget',

        # Database & Services
        'database.connection',
        'services.data_ensure_service',
        'services.term_code_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development/test modules
        'pytest',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PlanningTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Geen console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico'  # Optioneel: voeg icon toe
)