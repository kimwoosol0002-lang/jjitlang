package kidsql

import (
	"testing"
)

func TestSaveGetRemove(t *testing.T) {
	db, err := New("")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()

	people := db.Table("people")

	id1, err := people.Save(map[string]interface{}{"name": "짱구", "age": 5})
	if err != nil {
		t.Fatal(err)
	}
	if id1.(int64) != 1 {
		t.Fatalf("expected id 1, got %v", id1)
	}

	id2, err := people.Save(map[string]interface{}{"name": "철수", "age": 6})
	if err != nil {
		t.Fatal(err)
	}
	if id2.(int64) != 2 {
		t.Fatalf("expected id 2, got %v", id2)
	}

	// save update
	_, err = people.Save(map[string]interface{}{"id": int64(1), "name": "짱구", "age": 6})
	if err != nil {
		t.Fatal(err)
	}

	rows, err := people.Get(map[string]interface{}{"id": int64(1)})
	if err != nil {
		t.Fatal(err)
	}
	if rows[0]["age"].(int64) != 6 {
		t.Fatalf("expected age 6, got %v", rows[0]["age"])
	}

	// auto migrate
	_, err = people.Save(map[string]interface{}{"name": "유리", "age": 5, "pet": "강아지"})
	if err != nil {
		t.Fatal(err)
	}

	cols, err := db.db.Query(`PRAGMA table_info("people")`)
	if err != nil {
		t.Fatal(err)
	}
	hasPet := false
	for cols.Next() {
		var cid int
		var name, ctype string
		var notNull, pk int
		var dfltValue *string
		if err := cols.Scan(&cid, &name, &ctype, &notNull, &dfltValue, &pk); err != nil {
			t.Fatal(err)
		}
		if name == "pet" {
			hasPet = true
		}
	}
	cols.Close()
	if !hasPet {
		t.Fatal("expected 'pet' column in table")
	}

	// get all
	all, err := people.Get(nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(all) != 3 {
		t.Fatalf("expected 3 rows, got %d", len(all))
	}

	// get cond
	filtered, err := people.Get(map[string]interface{}{"age": 5})
	if err != nil {
		t.Fatal(err)
	}
	if len(filtered) != 1 {
		t.Fatalf("expected 1 row with age=5, got %d", len(filtered))
	}

	// get operators
	gt, err := people.Get(map[string]interface{}{"age>": 5})
	if err != nil {
		t.Fatal(err)
	}
	if len(gt) != 2 {
		t.Fatalf("expected 2 rows with age>5, got %d", len(gt))
	}

	lt, err := people.Get(map[string]interface{}{"age<": 6})
	if err != nil {
		t.Fatal(err)
	}
	if len(lt) != 1 {
		t.Fatalf("expected 1 row with age<6, got %d", len(lt))
	}

	like, err := people.Get(map[string]interface{}{"name%": "짱%"})
	if err != nil {
		t.Fatal(err)
	}
	if len(like) != 1 {
		t.Fatalf("expected 1 row with name like pattern, got %d", len(like))
	}

	// count
	cnt, err := people.Count(nil)
	if err != nil {
		t.Fatal(err)
	}
	if cnt != 3 {
		t.Fatalf("expected count 3, got %d", cnt)
	}

	// bulk
	_, err = people.Save([]map[string]interface{}{
		{"name": "A"},
		{"name": "B"},
	})
	if err != nil {
		t.Fatal(err)
	}
	cnt, err = people.Count(nil)
	if err != nil {
		t.Fatal(err)
	}
	if cnt != 5 {
		t.Fatalf("expected count 5 after bulk, got %d", cnt)
	}

	// remove
	n, err := people.Remove(map[string]interface{}{"name": "유리"})
	if err != nil {
		t.Fatal(err)
	}
	if n != 1 {
		t.Fatalf("expected 1 row removed, got %d", n)
	}
	cnt, err = people.Count(nil)
	if err != nil {
		t.Fatal(err)
	}
	if cnt != 4 {
		t.Fatalf("expected count 4 after remove, got %d", cnt)
	}
}
