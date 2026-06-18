import sqlite3


PY_TYPE_MAP = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bytes: "BLOB",
    type(None): "NULL",
}


def _py_to_sql(val):
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "INTEGER"
    return PY_TYPE_MAP.get(type(val), "TEXT")


def _parse_cond(cond):
    parts = []
    params = []
    for key, val in cond.items():
        if key.endswith(">="):
            col, op = key[:-2], ">="
        elif key.endswith("<="):
            col, op = key[:-2], "<="
        elif key.endswith("!="):
            col, op = key[:-2], "!="
        elif key.endswith(">"):
            col, op = key[:-1], ">"
        elif key.endswith("<"):
            col, op = key[:-1], "<"
        elif key.endswith("%"):
            col, op = key[:-1], "LIKE"
        else:
            col, op = key, "="
        parts.append(f'"{col}" {op} ?')
        params.append(val)
    return "WHERE " + " AND ".join(parts), params


def _build_insert(name, data):
    keys = [k for k in data if k != "id"]
    cols = ", ".join(f'"{k}"' for k in keys)
    vals = ", ".join("?" for _ in keys)
    return f'INSERT INTO "{name}" ({cols}) VALUES ({vals})', [data[k] for k in keys]


def _build_update(name, data):
    keys = [k for k in data if k != "id"]
    set_clause = ", ".join(f'"{k}" = ?' for k in keys)
    return f'UPDATE "{name}" SET {set_clause} WHERE id = ?', [data[k] for k in keys] + [data["id"]]


class Table:
    def __init__(self, conn, name):
        self._conn = conn
        self._name = name
        self._exists = None

    def _ensure(self, sample=None):
        if self._exists is None:
            cur = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (self._name,),
            )
            if cur.fetchone() is None:
                if sample:
                    self._create(sample)
                else:
                    self._conn.execute(
                        f'CREATE TABLE "{self._name}" (id INTEGER PRIMARY KEY AUTOINCREMENT)'
                    )
                self._exists = True
                return
            self._exists = True
        if sample:
            self._migrate(sample)

    def _columns(self):
        cur = self._conn.execute(f'PRAGMA table_info("{self._name}")')
        return {row[1] for row in cur.fetchall()}

    def _create(self, data):
        cols = []
        for k, v in data.items():
            if k == "id":
                continue
            cols.append(f'"{k}" {_py_to_sql(v)}')
        sql = (
            f'CREATE TABLE "{self._name}" ('
            f"id INTEGER PRIMARY KEY AUTOINCREMENT, "
            f'{", ".join(cols)}'
            f")"
        )
        self._conn.execute(sql)

    def _migrate(self, data):
        existing = self._columns()
        for k, v in data.items():
            if k == "id" or k in existing:
                continue
            self._conn.execute(
                f'ALTER TABLE "{self._name}" ADD COLUMN "{k}" {_py_to_sql(v)}'
            )

    def save(self, data):
        if isinstance(data, list):
            return [self.save(item) for item in data]
        self._ensure(data)
        if "id" in data and data["id"] is not None:
            sql, params = _build_update(self._name, data)
            self._conn.execute(sql, params)
            return data["id"]
        sql, params = _build_insert(self._name, data)
        return self._conn.execute(sql, params).lastrowid

    def get(self, cond=None, order=None, limit=None, offset=None, select=None, group=None):
        where, params = _parse_cond(cond) if cond else ("", [])
        sql = f'SELECT {select or "*"} FROM "{self._name}" {where}'
        if group:
            sql += f" GROUP BY {group}"
        if order:
            sql += f" ORDER BY {order}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset is not None:
            sql += f" OFFSET {offset}"
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def remove(self, cond=None):
        where, params = _parse_cond(cond) if cond else ("", [])
        return self._conn.execute(
            f'DELETE FROM "{self._name}" {where}', params
        ).rowcount

    def count(self, cond=None):
        where, params = _parse_cond(cond) if cond else ("", [])
        return self._conn.execute(
            f'SELECT COUNT(*) FROM "{self._name}" {where}', params
        ).fetchone()[0]

    def __len__(self):
        return self.count()

    def __getitem__(self, idx):
        if isinstance(idx, int):
            r = self.get(limit=1, offset=idx)
            return r[0] if r else None
        raise TypeError("index must be int")
