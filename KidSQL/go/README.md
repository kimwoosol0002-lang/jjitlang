# kidSQL — Go

SQL made so easy a kindergartner can use it.

```go
import "github.com/kimwoosol0002-lang/kidsql"

db, err := kidsql.New("")
if err != nil { panic(err) }
defer db.Close()

people := db.Table("people")

// Save (insert or update)
people.Save(map[string]any{"name": "짱구", "age": 5})
people.Save(map[string]any{"id": int64(1), "age": 6})  // update

// Get (all or filtered)
people.Get(nil)                          // all rows
people.Get(map[string]any{"age": 5})     // WHERE age = 5
people.Get(map[string]any{"age>": 5})    // WHERE age > 5

// Remove
people.Remove(map[string]any{"name": "짱구"})

// Bulk
people.Save([]map[string]any{
    {"name": "A"},
    {"name": "B"},
})
```

## Features

- **Zero SQL** — no `SELECT`, `INSERT`, `CREATE TABLE` needed
- **Auto schema** — first `Save()` creates the table from your map
- **Auto migration** — new fields are added via `ALTER TABLE` automatically
- **3 verbs**: `Save`, `Get`, `Remove`
- **Condition operators**: `=`, `>`, `<`, `>=`, `<=`, `!=`, `LIKE`
- **Sorting, pagination**: `order=`, `limit=`, `offset=` (via opts map)
- **Invisible PK**: auto-increment `id` column
- **Pure Go** — no CGO required (uses `modernc.org/sqlite`)
