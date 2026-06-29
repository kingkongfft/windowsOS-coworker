# How to Run with venv

## Option 1 — One-off (no activation needed)

```powershell
.\venv\Scripts\python.exe gui.py
```

## Option 2 — Activate venv first, then use `python` normally

```powershell
.\venv\Scripts\Activate.ps1
python gui.py
```

After activation you'll see `(venv)` in your prompt.  
All `python` / `pip` commands use the venv until you close the terminal or run `deactivate`.

---

## Why this is needed

PyQt6 (and other GUI deps) are installed **inside `venv/`**, not in the system Python.  
Running bare `python gui.py` picks up the Windows Store Python at  
`C:\Users\...\AppData\Local\Microsoft\WindowsApps\python.exe`, which has no PyQt6.

---

## Quick reference

| Goal | Command |
|---|---|
| Launch GUI | `.\venv\Scripts\python.exe gui.py` |
| Launch CLI | `.\venv\Scripts\python.exe main.py` |
| Run tests | `.\venv\Scripts\pytest.exe -m "not integration"` |
| Activate venv | `.\venv\Scripts\Activate.ps1` |
| Deactivate venv | `deactivate` |
| Install deps | `.\venv\Scripts\pip.exe install -r requirements.txt` |
