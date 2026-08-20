from __future__ import annotations

from .db import Base, make_engine, make_session_factory

__all__ = ["Base", "make_engine", "make_session_factory", "check_project"]


def check_project(*args, **kwargs):
    from .fsck import check_project as _check_project
    return _check_project(*args, **kwargs)
