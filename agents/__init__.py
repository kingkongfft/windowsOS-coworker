from __future__ import annotations

# ---------------------------------------------------------------------------
# SDK bridge — make the openai-agents SDK symbols available from this package.
#
# The local `agents/` folder shadows the SDK that also installs as `agents`.
# We resolve this by:
#  1. Temporarily swapping sys.modules["agents"] to the SDK copy.
#  2. Collecting all SDK symbols and registered sub-module keys.
#  3. Restoring sys.modules["agents"] to this local package.
#  4. Re-registering the SDK's sub-modules under the `agents.*` namespace.
#  5. Injecting the SDK symbols into this module's globals.
# ---------------------------------------------------------------------------

import importlib.util
import site
import sys
from pathlib import Path

# Locate the SDK's agents/__init__.py in site-packages (not this file).
_this_file = Path(__file__).resolve()
_sdk_init: Path | None = None

for _sp in site.getsitepackages() + [site.getusersitepackages()]:
    _c = Path(_sp) / "agents" / "__init__.py"
    if _c.exists() and _c.resolve() != _this_file:
        _sdk_init = _c
        break

if _sdk_init is None:
    raise ImportError(
        "openai-agents SDK not found in site-packages. "
        "Run: pip install 'openai-agents>=0.0.19'"
    )

_site_pkg = str(_sdk_init.parent.parent)  # the site-packages directory

# Stash a ref to *this* module before we temporarily remove it.
_local_pkg = sys.modules["agents"]

# Remove our local package so the SDK's `agents` can load under that name.
del sys.modules["agents"]

# Insert site-packages first so the SDK's `from agents.X import …` works.
sys.path.insert(0, _site_pkg)
try:
    import agents as _sdk  # noqa: E402  — this loads the SDK

    # Force-load the extensions sub-package (used by orchestrator.py)
    import agents.extensions  # noqa: F401
    import agents.extensions.handoff_prompt  # noqa: F401

    _sdk_symbols = {k: v for k, v in _sdk.__dict__.items() if not k.startswith("_")}
    # Capture all SDK sub-modules that were registered (e.g. agents.extensions, …)
    _sdk_submodules = {k: v for k, v in sys.modules.items() if k.startswith("agents.")}
finally:
    # Restore: remove site-packages prefix and put our package back.
    sys.path.pop(0)
    sys.modules["agents"] = _local_pkg  # restore local package

# Re-register all SDK sub-modules under the `agents.*` namespace so that
# imports like `from agents.extensions.handoff_prompt import …` still work.
sys.modules.update(_sdk_submodules)

# Inject all SDK symbols into this module's globals.
globals().update(_sdk_symbols)
