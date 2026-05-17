"""
stack.py — Atalho na raiz do repositório
========================================
Equivale a ``python -m chatnet``. Mantido para compatibilidade com scripts
e deploy que chamam ``python stack.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Garante que ``src`` está no path ao rodar da raiz sem PYTHONPATH
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from chatnet.stack import main  # noqa: E402

if __name__ == "__main__":
    main()
