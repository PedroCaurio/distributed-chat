"""Executar: PYTHONPATH=<raiz>;<raiz>/legacy python -m client (a partir de legacy/)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_LEGACY = Path(__file__).resolve().parent.parent
for p in (_ROOT, _LEGACY):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

from client.main import main

if __name__ == "__main__":
    main()
