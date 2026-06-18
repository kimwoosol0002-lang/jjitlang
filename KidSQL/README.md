# KidSQL

**SQL made so easy a kindergartner can use it.**

KidSQL is a multi-language library that lets you use SQLite without writing a single SQL keyword. Just 3 verbs: `save`, `get`, `remove`.

## Languages

| Language | Directory | Status |
|----------|-----------|--------|
| Python | [`py/`](py/) | ✅ v0.1 |
| JavaScript | [`js/`](js/) | ✅ v0.1 |
| TypeScript | [`ts/`](ts/) | ✅ v0.1 |
| Go | [`go/`](go/) | ✅ v0.1 |

## What makes KidSQL different?

```python
# No SQL. No schema. Just 3 verbs.
from kidsql import Database
db = Database()
db.people.save({"name": "짱구", "age": 5})
db.people.get({"age>": 5})
db.people.remove({"name": "짱구"})
```

- **Zero SQL** — no `SELECT`, `INSERT`, `CREATE TABLE` ever
- **Auto schema** — first `save()` creates the table from your data
- **Auto migration** — new fields auto-add with `ALTER TABLE`
- **3 verbs**: `save`, `get`, `remove` — same across all languages
- **Invisible PK**: auto-increment `id` column managed internally
