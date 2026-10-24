"""The deployed configuration as a linked assembly.  See nose_linked.py."""

from __future__ import annotations

import nose_linked
from nose_assembly_open import OPEN_DEG


def gen_step():
    return {"children": nose_linked.children(OPEN_DEG, released=True)}
