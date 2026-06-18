# kidSQL — TypeScript

SQL을 유치원생도 쓸 수 있을 정도로 쉽게 만든 라이브러리

```typescript
import { KidSQL } from 'kidsql';

const db = new KidSQL();

// 저장 (추가 또는 수정)
db.people.save({ name: '짱구', age: 5 });
db.people.save({ id: 1, age: 6 });           // id가 있으면 수정

// 조회 (전체 또는 조건)
db.people.get();                               // 전체
db.people.get({ age: 5 });                    // WHERE age = 5
db.people.get({ 'age>': 5 });                 // WHERE age > 5
db.people.get({ 'name%': '짱%' });            // LIKE '짱%'
db.people.get(null, { order: 'age desc', limit: 10 });

// 삭제
db.people.remove({ name: '짱구' });

// 트랜잭션
db.transaction(() => {
    db.people.save({ name: '짱구' });
    db.scores.save({ person_id: 1, score: 100 });
});

// 벌크 저장
db.people.save([{ name: 'A' }, { name: 'B' }]);
```

## 기능

- **SQL 몰라도 됨** — `SELECT`, `INSERT`, `CREATE TABLE` 전혀 없음
- **자동 스키마** — 첫 `save()`가 객체 보고 테이블 자동 생성
- **자동 마이그레이션** — 새 필드 추가 시 자동 `ALTER TABLE`
- **3개의 동사**: `save`, `get`, `remove`
- **조건 연산자**: `=`, `>`, `<`, `>=`, `<=`, `!=`, `LIKE`
- **정렬, 페이징**: `order=`, `limit=`, `offset=`
- **트랜잭션**: `db.transaction()`
- **보이지 않는 PK**: 자동 증가 `id` 컬럼 내장
- **TypeScript 타입** 내장
