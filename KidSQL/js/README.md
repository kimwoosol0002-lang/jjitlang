# kidSQL — JavaScript

SQL made so easy a kindergartner can use it.

```javascript
const KidSQL = require('kidsql');
const db = new KidSQL();

// Save (insert or update)
db.people.save({ name: '짱구', age: 5 });
db.people.save({ id: 1, age: 6 });           // update (has id)

// Get (all or filtered)
db.people.get();                               // all rows
db.people.get({ age: 5 });                    // WHERE age = 5
db.people.get({ 'age>': 5 });                 // WHERE age > 5
db.people.get({ 'name%': '짱%' });            // LIKE '짱%'
db.people.get(null, { order: 'age desc', limit: 10 });

// Remove
db.people.remove({ name: '짱구' });

// Transactions
db.transaction(() => {
    db.people.save({ name: '짱구' });
    db.scores.save({ person_id: 1, score: 100 });
});

// Bulk
db.people.save([{ name: 'A' }, { name: 'B' }]);
```

## Features

- **Zero SQL** — no `SELECT`, `INSERT`, `CREATE TABLE` needed
- **Auto schema** — first `save()` creates the table from your object
- **Auto migration** — new fields are added via `ALTER TABLE` automatically
- **3 verbs**: `save`, `get`, `remove`
- **Condition operators**: `=`, `>`, `<`, `>=`, `<=`, `!=`, `LIKE`
- **Sorting, pagination**: `order=`, `limit=`, `offset=`
- **Transactions**: `db.transaction()`
- **Invisible PK**: auto-increment `id` column
- **Sync API** — powered by `better-sqlite3`
