# kidSQL — Go

SQL을 유치원생도 쓸 수 있을 정도로 쉽게 만든 라이브러리

```go
import "github.com/kimwoosol0002-lang/kidsql"

db, err := kidsql.New("")
if err != nil { panic(err) }
defer db.Close()

people := db.Table("people")

// 저장 (추가 또는 수정)
people.Save(map[string]any{"name": "짱구", "age": 5})
people.Save(map[string]any{"id": int64(1), "age": 6})  // id가 있으면 수정

// 조회 (전체 또는 조건)
people.Get(nil)                          // 전체
people.Get(map[string]any{"age": 5})     // WHERE age = 5
people.Get(map[string]any{"age>": 5})    // WHERE age > 5

// 삭제
people.Remove(map[string]any{"name": "짱구"})

// 벌크 저장
people.Save([]map[string]any{
    {"name": "A"},
    {"name": "B"},
})
```

## 기능

- **SQL 몰라도 됨** — `SELECT`, `INSERT`, `CREATE TABLE` 전혀 없음
- **자동 스키마** — 첫 `Save()`가 map 보고 테이블 자동 생성
- **자동 마이그레이션** — 새 필드 추가 시 자동 `ALTER TABLE`
- **3개의 동사**: `Save`, `Get`, `Remove`
- **조건 연산자**: `=`, `>`, `<`, `>=`, `<=`, `!=`, `LIKE`
- **정렬, 페이징**: opts map으로 `order=`, `limit=`, `offset=`
- **보이지 않는 PK**: 자동 증가 `id` 컬럼 내장
- **Pure Go** — CGO 불필요 (`modernc.org/sqlite` 사용)
