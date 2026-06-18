package kidsql

import (
	"database/sql"
	"fmt"
	"strings"

	_ "modernc.org/sqlite"
)

func pyToSql(v interface{}) string {
	if v == nil {
		return "NULL"
	}
	switch v.(type) {
	case int, int8, int16, int32, int64, uint, uint8, uint16, uint32, uint64, bool:
		return "INTEGER"
	case float32, float64:
		return "REAL"
	case string:
		return "TEXT"
	case []byte:
		return "BLOB"
	default:
		return "TEXT"
	}
}

func parseCond(cond map[string]interface{}) (string, []interface{}) {
	if len(cond) == 0 {
		return "", nil
	}
	var parts []string
	var params []interface{}
	for key, val := range cond {
		var col, op string
		switch {
		case strings.HasSuffix(key, ">="):
			col = strings.TrimSuffix(key, ">=")
			op = ">="
		case strings.HasSuffix(key, "<="):
			col = strings.TrimSuffix(key, "<=")
			op = "<="
		case strings.HasSuffix(key, "!="):
			col = strings.TrimSuffix(key, "!=")
			op = "!="
		case strings.HasSuffix(key, ">"):
			col = strings.TrimSuffix(key, ">")
			op = ">"
		case strings.HasSuffix(key, "<"):
			col = strings.TrimSuffix(key, "<")
			op = "<"
		case strings.HasSuffix(key, "%"):
			col = strings.TrimSuffix(key, "%")
			op = "LIKE"
		default:
			col = key
			op = "="
		}
		parts = append(parts, fmt.Sprintf(`"%s" %s ?`, col, op))
		params = append(params, val)
	}
	return "WHERE " + strings.Join(parts, " AND "), params
}

type Table struct {
	db   *sql.DB
	name string
}

func (t *Table) ensure(sample map[string]interface{}) error {
	var name string
	err := t.db.QueryRow(
		"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
		t.name,
	).Scan(&name)

	if err == sql.ErrNoRows {
		if sample != nil {
			return t.create(sample)
		}
		_, err = t.db.Exec(fmt.Sprintf(
			`CREATE TABLE "%s" (id INTEGER PRIMARY KEY AUTOINCREMENT)`, t.name,
		))
		return err
	}
	if err != nil {
		return err
	}
	if sample != nil {
		return t.migrate(sample)
	}
	return nil
}

func (t *Table) columns() (map[string]bool, error) {
	rows, err := t.db.Query(fmt.Sprintf(`PRAGMA table_info("%s")`, t.name))
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	cols := make(map[string]bool)
	for rows.Next() {
		var cid int
		var name, colType string
		var notNull, pk int
		var dfltValue *string
		if err := rows.Scan(&cid, &name, &colType, &notNull, &dfltValue, &pk); err != nil {
			return nil, err
		}
		cols[name] = true
	}
	return cols, nil
}

func (t *Table) create(data map[string]interface{}) error {
	var cols []string
	for k, v := range data {
		if k == "id" {
			continue
		}
		cols = append(cols, fmt.Sprintf(`"%s" %s`, k, pyToSql(v)))
	}
	_, err := t.db.Exec(fmt.Sprintf(
		`CREATE TABLE "%s" (id INTEGER PRIMARY KEY AUTOINCREMENT, %s)`,
		t.name, strings.Join(cols, ", "),
	))
	return err
}

func (t *Table) migrate(data map[string]interface{}) error {
	existing, err := t.columns()
	if err != nil {
		return err
	}
	for k, v := range data {
		if k == "id" || existing[k] {
			continue
		}
		_, err := t.db.Exec(fmt.Sprintf(
			`ALTER TABLE "%s" ADD COLUMN "%s" %s`, t.name, k, pyToSql(v),
		))
		if err != nil {
			return err
		}
	}
	return nil
}

func (t *Table) Save(data interface{}) (interface{}, error) {
	switch d := data.(type) {
	case map[string]interface{}:
		return t.saveOne(d)
	case []map[string]interface{}:
		var ids []interface{}
		for _, item := range d {
			id, err := t.saveOne(item)
			if err != nil {
				return nil, err
			}
			ids = append(ids, id)
		}
		return ids, nil
	default:
		return nil, fmt.Errorf("kidsql: Save requires map or []map")
	}
}

func (t *Table) saveOne(data map[string]interface{}) (interface{}, error) {
	if err := t.ensure(data); err != nil {
		return nil, err
	}

	if id, ok := data["id"]; ok && id != nil {
		var keys []string
		var vals []interface{}
		for k, v := range data {
			if k == "id" {
				continue
			}
			keys = append(keys, fmt.Sprintf(`"%s" = ?`, k))
			vals = append(vals, v)
		}
		vals = append(vals, id)
		_, err := t.db.Exec(
			fmt.Sprintf(`UPDATE "%s" SET %s WHERE id = ?`, t.name, strings.Join(keys, ", ")),
			vals...,
		)
		return id, err
	}

	var keys []string
	var vals []interface{}
	for k, v := range data {
		if k == "id" {
			continue
		}
		keys = append(keys, fmt.Sprintf(`"%s"`, k))
		vals = append(vals, v)
	}
	placeholders := make([]string, len(keys))
	for i := range placeholders {
		placeholders[i] = "?"
	}

	res, err := t.db.Exec(
		fmt.Sprintf(
			`INSERT INTO "%s" (%s) VALUES (%s)`,
			t.name, strings.Join(keys, ", "), strings.Join(placeholders, ", "),
		),
		vals...,
	)
	if err != nil {
		return nil, err
	}
	return res.LastInsertId()
}

func (t *Table) Get(cond map[string]interface{}, opts ...map[string]interface{}) ([]map[string]interface{}, error) {
	where, params := parseCond(cond)
	sql := fmt.Sprintf(`SELECT * FROM "%s" %s`, t.name, where)

	if len(opts) > 0 {
		o := opts[0]
		if group, ok := o["group"].(string); ok && group != "" {
			sql += " GROUP BY " + group
		}
		if order, ok := o["order"].(string); ok && order != "" {
			sql += " ORDER BY " + order
		}
		if limit, ok := o["limit"]; ok {
			sql += fmt.Sprintf(" LIMIT %d", limit)
		}
		if offset, ok := o["offset"]; ok {
			sql += fmt.Sprintf(" OFFSET %d", offset)
		}
	}

	rows, err := t.db.Query(sql, params...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	return rowsToMaps(rows)
}

func rowsToMaps(rows *sql.Rows) ([]map[string]interface{}, error) {
	cols, err := rows.Columns()
	if err != nil {
		return nil, err
	}

	var results []map[string]interface{}
	for rows.Next() {
		vals := make([]interface{}, len(cols))
		valPtrs := make([]interface{}, len(cols))
		for i := range vals {
			valPtrs[i] = &vals[i]
		}

		if err := rows.Scan(valPtrs...); err != nil {
			return nil, err
		}

		row := make(map[string]interface{})
		for i, col := range cols {
			row[col] = vals[i]
		}
		results = append(results, row)
	}
	return results, nil
}

func (t *Table) Remove(cond map[string]interface{}) (int64, error) {
	where, params := parseCond(cond)
	res, err := t.db.Exec(
		fmt.Sprintf(`DELETE FROM "%s" %s`, t.name, where), params...,
	)
	if err != nil {
		return 0, err
	}
	return res.RowsAffected()
}

func (t *Table) Count(cond map[string]interface{}) (int, error) {
	where, params := parseCond(cond)
	var count int
	err := t.db.QueryRow(
		fmt.Sprintf(`SELECT COUNT(*) FROM "%s" %s`, t.name, where), params...,
	).Scan(&count)
	return count, err
}

type KidSQL struct {
	db *sql.DB
}

func New(path string) (*KidSQL, error) {
	if path == "" {
		path = ":memory:"
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	db.Exec("PRAGMA journal_mode=WAL")
	db.Exec("PRAGMA foreign_keys=ON")
	return &KidSQL{db: db}, nil
}

func (k *KidSQL) Close() error {
	return k.db.Close()
}

func (k *KidSQL) Table(name string) *Table {
	return &Table{db: k.db, name: name}
}
