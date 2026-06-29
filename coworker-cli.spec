# coworker-cli.spec  —  PyInstaller build spec for the CLI entry point.
# Build with:  pyinstaller coworker-cli.spec
#
# Output: dist/coworker-cli/coworker-cli.exe  (one-folder, console window)

from __future__ import annotations

from pathlib import Path

ROOT = Path(SPECPATH)  # repo root

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # OpenAI Agents SDK
        "agents",
        "agents.orchestrator",
        # Rich console
        "rich",
        "rich.console",
        "rich.markdown",
        "rich.panel",
        "rich.table",
        "rich.text",
        # Project core
        "config",
        "core.risk",
        "core.audit_log",
        "core.approval",
        "core.exceptions",
        "core.memory_store",
        "core.powershell",
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
        # GUI deps not needed for CLI
        "PyQt6",
        "qasync",
        # Test infrastructure
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
    name="coworker-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,            # console window — CLI app
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
    name="coworker-cli",
)
