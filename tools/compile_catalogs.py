#!/usr/bin/env python3
"""Recompile shipped GPL nano catalogs with msgfmt (no pinned checkout needed)."""
from pathlib import Path
import subprocess
root=Path(__file__).resolve().parents[1]/'assets'
for po in sorted((root/'po').glob('*.po')):
 target=root/'locale'/po.stem/'LC_MESSAGES/nano.mo';target.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run(['msgfmt','--check','-o',str(target),str(po)],check=True)
