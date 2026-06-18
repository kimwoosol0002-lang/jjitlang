'use strict';

const Database = require('better-sqlite3');

function parseCond(cond) {
  const parts = [];
  const params = [];
  for (const [key, val] of Object.entries(cond)) {
    let col, op;
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

function pyToSql(val) {
  if (val === null || val === undefined) return 'NULL';
  if (typeof val === 'number') return Number.isInteger(val) ? 'INTEGER' : 'REAL';
  if (typeof val === 'string') return 'TEXT';
  if (Buffer.isBuffer(val)) return 'BLOB';
  if (typeof val === 'boolean') return 'INTEGER';
  return 'TEXT';
}

class Table {
  constructor(db, name) {
    this._db = db;
    this._name = name;
    this._exists = null;
  }

  _ensure(sample) {
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

  _columns() {
    const rows = this._db.prepare(`PRAGMA table_info("${this._name}")`).all();
    return new Set(rows.map(r => r.name));
  }

  _create(data) {
    const cols = [];
    for (const [k, v] of Object.entries(data)) {
      if (k === 'id') continue;
      cols.push(`"${k}" ${pyToSql(v)}`);
    }
    this._db.exec(
      `CREATE TABLE "${this._name}" (id INTEGER PRIMARY KEY AUTOINCREMENT, ${cols.join(', ')})`
    );
  }

  _migrate(data) {
    const existing = this._columns();
    for (const [k, v] of Object.entries(data)) {
      if (k === 'id' || existing.has(k)) continue;
      this._db.exec(`ALTER TABLE "${this._name}" ADD COLUMN "${k}" ${pyToSql(v)}`);
    }
  }

  save(data) {
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

  get(cond, opts = {}) {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    let sql = `SELECT ${opts.select || '*'} FROM "${this._name}" ${where}`;
    if (opts.group) sql += ` GROUP BY ${opts.group}`;
    if (opts.order) sql += ` ORDER BY ${opts.order}`;
    if (opts.limit != null) sql += ` LIMIT ${opts.limit}`;
    if (opts.offset != null) sql += ` OFFSET ${opts.offset}`;
    return this._db.prepare(sql).all(...params);
  }

  remove(cond) {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    const info = this._db.prepare(`DELETE FROM "${this._name}" ${where}`).run(...params);
    return info.changes;
  }

  count(cond) {
    const [where, params] = cond ? parseCond(cond) : ['', []];
    return this._db.prepare(`SELECT COUNT(*) as cnt FROM "${this._name}" ${where}`).get(...params).cnt;
  }

  get length() {
    return this.count();
  }
}

class KidSQL {
  constructor(path) {
    const db = new Database(path || ':memory:');
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    this._db = db;
    this._tables = {};

    return new Proxy(this, {
      get(target, prop) {
        if (prop in target || typeof prop === 'symbol' || (typeof prop === 'string' && prop.startsWith('_'))) {
          return target[prop];
        }
        if (!target._tables[prop]) {
          target._tables[prop] = new Table(target._db, prop);
        }
        return target._tables[prop];
      }
    });
  }

  close() {
    this._db.close();
  }

  transaction(fn) {
    const tx = this._db.transaction(fn);
    return tx();
  }
}

module.exports = KidSQL;
module.exports.KidSQL = KidSQL;
