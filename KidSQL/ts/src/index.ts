import Database from 'better-sqlite3';

type Cond = Record<string, unknown>;
type Opts = {
  order?: string;
  limit?: number;
  offset?: number;
  select?: string;
  group?: string;
};

function parseCond(cond: Cond): [string, unknown[]] {
  const parts: string[] = [];
  const params: unknown[] = [];
  for (const [key, val] of Object.entries(cond)) {
    let col: string, op: string;
    if (key.endsWith('>=')) { col = key.slice(0, -2); op = '>='; }
    else if (key.endsWith('<=')) { col = key.slice(0, -2); op = '<='; }
    else if (key.endsWith('!=')) { col = key.slice(0, -2); op = '!='; }
    else if (key.endsWith('>')) { col = key.slice(0, -1); op = '>'; }
    else if (key.endsWith('<')) { col = key.slice(0, -1); op = '<'; }
    else if (key.endsWith('%')) { col = key.slice(0, -1); op = 'LIKE'; }
    else { col = key; op = '='; }
    parts.push(`"${col}" ${op} ?`);
    params.push(val);
  }
  return [parts.length ? 'WHERE ' + parts.join(' AND ') : '', params];
}

function pyToSql(val: unknown): string {
  if (val === null || val === undefined) return 'NULL';
  if (typeof val === 'number') return Number.isInteger(val) ? 'INTEGER' : 'REAL';
  if (typeof val === 'string') return 'TEXT';
  if (Buffer.isBuffer(val)) return 'BLOB';
  if (typeof val === 'boolean') return 'INTEGER';
  return 'TEXT';
}

class Table {
  private _db: Database.Database;
  private _name: string;
  private _exists: boolean | null = null;

  constructor(db: Database.Database, name: string) {
    this._db = db;
    this._name = name;
  }

  private _ensure(sample?: Record<string, unknown>): void {
    if (this._exists === null) {
      const row = this._db.prepare(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
      ).get(this._name);
      if (!row) {
        if (sample) {
          this._create(sample);
        } else {
          this._db.exec(`CREATE TABLE "${this._name}" (id INTEGER PRIMARY KEY AUTOINCREMENT)`);
        }
        this._exists = true;
        return;
      }
      this._exists = true;
    }
    if (sample) this._migrate(sample);
  }

  private _columns(): Set<string> {
    const rows = this._db.prepare(`PRAGMA table_info("${this._name}")`).all() as Array<Record<string, unknown>>;
    return new Set(rows.map(r => r.name as string));
  }

  private _create(data: Record<string, unknown>): void {
    const cols: string[] = [];
    for (const [k, v] of Object.entries(data)) {
      if (k === 'id') continue;
      cols.push(`"${k}" ${pyToSql(v)}`);
    }
    this._db.exec(
      `CREATE TABLE "${this._name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, ${cols.join(', ')})`
    );
  }

  private _migrate(data: Record<string, unknown>): void {
    const existing = this._columns();
    for (const [k, v] of Object.entries(data)) {
      if (k === 'id' || existing.has(k)) continue;
      this._db.exec(`ALTER TABLE "${this._name}" ADD COLUMN "${k}" ${pyToSql(v)}`);
    }
  }

  save(data: Record<string, unknown>): unknown;
  save(data: Record<string, unknown>[]): unknown[];
  save(data: Record<string, unknown> | Record<string, unknown>[]): unknown {
    if (Array.isArray(data)) return data.map(d => this.save(d));
    this._ensure(data);
    if (data.id != null) {
      const keys = Object.keys(data).filter(k => k !== 'id');
      const setClause = keys.map(k => `"${k}" = ?`).join(', ');
      const params = keys.map(k => data[k]);
      params.push(data.id);
      this._db.prepare(`UPDATE "${this._name}" SET ${setClause} WHERE id = ?`).run(...params);
      return data.id;
    }
    const keys = Object.keys(data).filter(k => k !== 'id');
    const cols = keys.map(k => `"${k}"`).join(', ');
    const placeholders = keys.map(() => '?').join(', ');
    const params = keys.map(k => data[k]);
    const info = this._db.prepare(
      `INSERT INTO "${this._name}" (${cols}) VALUES (${placeholders})`
    ).run(...params);
    return Number(info.lastInsertRowid);
  }

  get(cond?: Cond | null, opts?: Opts): Record<string, unknown>[] {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    let sql = `SELECT ${opts?.select || '*'} FROM "${this._name}" ${where}`;
    if (opts?.group) sql += ` GROUP BY ${opts.group}`;
    if (opts?.order) sql += ` ORDER BY ${opts.order}`;
    if (opts?.limit != null) sql += ` LIMIT ${opts.limit}`;
    if (opts?.offset != null) sql += ` OFFSET ${opts.offset}`;
    return this._db.prepare(sql).all(...params) as Record<string, unknown>[];
  }

  remove(cond?: Cond): number {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    const info = this._db.prepare(`DELETE FROM "${this._name}" ${where}`).run(...params);
    return info.changes;
  }

  count(cond?: Cond): number {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    return (this._db.prepare(
      `SELECT COUNT(*) as cnt FROM "${this._name}" ${where}`
    ).get(...params) as Record<string, number>).cnt;
  }

  get length(): number {
    return this.count();
  }
}

class KidSQL {
  _db: Database.Database;
  private _tables: Record<string, Table> = {};

  constructor(path?: string) {
    const db = new Database(path || ':memory:');
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    this._db = db;

    return new Proxy(this, {
      get(target: KidSQL, prop: string | symbol) {
        if (prop in target || typeof prop === 'symbol' || (typeof prop === 'string' && prop.startsWith('_'))) {
          return (target as unknown as Record<string | symbol, unknown>)[prop];
        }
        if (!target._tables[prop as string]) {
          target._tables[prop as string] = new Table(target._db, prop as string);
        }
        return target._tables[prop as string];
      }
    }) as unknown as KidSQL;
  }

  close(): void {
    this._db.close();
  }

  transaction<T>(fn: () => T): T {
    const tx = this._db.transaction(fn);
    return tx();
  }
}

export { KidSQL, Table };
export type { Cond, Opts };
