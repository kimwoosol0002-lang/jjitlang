import sqlite3

from .core import Table


class Database:
    def __init__(self, path=None):
        self._conn = sqlite3.connect(path or ":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._tables = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._tables:
            self._tables[name] = Table(self._conn, name)
        return self._tables[name]

    def close(self):
        self._conn.close()

    def __enter__(self):
        self._conn.execute("BEGIN")
        return self

    def __exit__(self, typ, val, tb):
        if typ:
            self._conn.rollback()
        else:
            self._conn.commit()
