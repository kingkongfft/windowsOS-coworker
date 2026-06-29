# coworker-gui.spec  —  PyInstaller build spec for the GUI entry point.
# Build with:  pyinstaller coworker-gui.spec
#
# Output: dist/coworker-gui/coworker-gui.exe  (one-folder, no console window)

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(SPECPATH)  # repo root

# ---------------------------------------------------------------------------
# Collect the QSS stylesheet and any other data files the app needs at runtime
# ---------------------------------------------------------------------------
added_files = [
    # Qt stylesheet  (src_path, dest_folder_inside_dist)
    (str(ROOT / "ui" / "styles" / "main.qss"), "ui/styles"),
]

a = Analysis(
    [str(ROOT / "gui.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # OpenAI Agents SDK dynamic imports
        "agents",
        "agents.orchestrator",
        # PyQt6 – ensure platform plugin is bundled
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.sip",
        # qasync event loop
        "qasync",
        # Pygments lexers/formatters used for code highlighting
        "pygments.lexers",
        "pygments.lexers._mapping",
        "pygments.formatters",
        "pygments.formatters.html",
        "pygments.styles",
        # Project modules
        "config",
        "core.risk",
        "core.audit_log",
        "core.approval",
        "core.exceptions",
        "core.memory_store",
        "core.powershell",
        "ui.app",
        "ui.bridge",
        "ui.main_window",
        "ui.worker",
        "ui.widgets.chat_area",
        "ui.widgets.message_bubble",
        "ui.widgets.input_bar",
        "ui.widgets.sidebar",
        "ui.widgets.approval_dialog",
        "ui.widgets.thinking_indicator",
        "ui.styles.theme",
        # All skill modules
        "skills.disk.tools",
        "skills.memory.tools",
        "skills.cpu.tools",
        "skills.process.tools",
        "skills.service.tools",
        "skills.network.tools",
        "skills.app.tools",
        "skills.patch.tools",
        "skills.eventlog.tools",
        "skills.registry.tools",
        "skills.taskscheduler.tools",
        "skills.diagnostics.tools",
        "skills.envconfig.tools",
        "skills.security.tools",
        "skills.user.tools",
        # All agent modules
        "agents.disk_skill_agent",
        "agents.memory_skill_agent",
        "agents.cpu_skill_agent",
        "agents.process_skill_agent",
        "agents.service_skill_agent",
        "agents.network_skill_agent",
        "agents.app_skill_agent",
        "agents.patch_skill_agent",
        "agents.eventlog_skill_agent",
        "agents.registry_skill_agent",
        "agents.taskscheduler_skill_agent",
        "agents.diagnostics_skill_agent",
        "agents.envconfig_skill_agent",
        "agents.security_skill_agent",
        "agents.user_skill_agent",
        # Windows-specific
        "win32api",
        "win32con",
        "win32security",
        "pywintypes",
        "wmi",
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test infrastructure — not needed at runtime
        "pytest",
        "pytest_cov",
        "pytest_mock",
        "ruff",
        "mypy",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # one-folder mode
    name="coworker-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # no console window — GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="ui/styles/icon.ico",  # uncomment and add icon.ico if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="coworker-gui",
)
