# Safe-Fuckit JavaScript

**JavaScript를 위한 안전한 에러 처리 라이브러리**

## 개요

Safe-Fuckit JavaScript는 예상치 못한 에러를 우아하게 처리하면서 프로그램의 상태를 안전하게 유지해주는 라이브러리입니다. 기존 Fuckit의 원리를 따르면서 더욱 개선된 기능을 제공합니다.

## 주요 특징

- 🛡️ **안전한 에러 격리**: 에러 발생 시에도 프로그램이 계속 실행됨
- 🔄 **상태 복구**: 전역 변수의 상태를 스냅샷으로 저장하고 복구
- 🎯 **정확한 예외 필터링**: 특정 예외 타입만 처리 가능
- 📝 **상세한 로깅**: 에러 발생 원인 및 위치 추적
- 🌐 **브라우저/Node.js 호환**: 모든 JavaScript 환경에서 작동

## 설치

```bash
npm install safe-fuckit
```

또는

```bash
yarn add safe-fuckit
```

## 빠른 시작

### 기본 사용법

```javascript
const { safeFuckit } = require('safe-fuckit');

// 함수 래핑
const divide = safeFuckit((a, b) => {
    return a / b;
});

const result = divide(10, 0);  // 에러가 발생해도 안전함
console.log(result);  // undefined
```

### 컨텍스트 매니저 사용

```javascript
const { SafeFuckIt } = require('safe-fuckit');

const sf = new SafeFuckIt();
sf.enter();

try {
    // 위험한 코드
    risky_operation();
} finally {
    sf.exit();
}
```

### 특정 예외만 처리

```javascript
const { safeFuckit } = require('safe-fuckit');

const divide = safeFuckit(
    (a, b) => a / b,
    { exTypes: [RangeError, TypeError] }
);

divide(10, 0);  // ZeroDivisionError는 처리되지 않음
```

### 전역 변수 보호

```javascript
const { SafeFuckIt } = require('safe-fuckit');

// 전역 객체 지정
const sf = new SafeFuckIt({ targetGlobals: global });

const wrappedFn = sf.wrap(riskFunction);
wrappedFn();  // 실행 후 전역 변수가 원래 상태로 복구됨
```

## API 문서

### `safeFuckit(fn, options)`

함수를 래핑하여 안전하게 만듭니다.

**매개변수:**
- `fn` (function): 래핑할 함수
- `options` (object, optional):
  - `exTypes` (array): 처리할 예외 타입들 (기본값: [Error])
  - `targetGlobals` (object): 보호할 전역 객체 (기본값: null)

**반환값:**
- 래핑된 함수

### `SafeFuckIt` 클래스

**생성자:**
```javascript
const sf = new SafeFuckIt({
    exTypes: [Error],        // 처리할 예외 타입
    targetGlobals: null      // 보호할 전역 객체
});
```

**메서드:**

#### `wrap(fn)`
함수를 래핑합니다.

```javascript
const safeFn = sf.wrap(riskFunction);
```

#### `enter()`
스냅샷을 시작합니다.

```javascript
sf.enter();
```

#### `exit()`
스냅샷을 종료합니다.

```javascript
sf.exit();
```

## 실전 예제

### 비동기 함수 처리

```javascript
const { safeFuckit } = require('safe-fuckit');

const fetchData = safeFuckit(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Network error');
    return response.json();
});

(async () => {
    const data = await fetchData('https://invalid-url.com');
    console.log(data);  // undefined (에러가 격리됨)
})();
```

### JSON 파싱

```javascript
const { safeFuckit } = require('safe-fuckit');

const parseJSON = safeFuckit((str) => {
    return JSON.parse(str);
});

const config = parseJSON(invalidJsonString);
console.log(config);  // undefined (에러가 격리됨)
```

### API 호출

```javascript
const { safeFuckit } = require('safe-fuckit');

const getUser = safeFuckit((userId) => {
    const response = fetch(`/api/users/${userId}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
});

const user = getUser(123);
console.log(user);  // 에러 발생 시 undefined
```

### 데이터 처리

```javascript
const { safeFuckit } = require('safe-fuckit');

const processData = safeFuckit((data) => {
    // 복잡한 데이터 처리
    const transformed = complexTransform(data);
    updateGlobalState(transformed);
    return transformed;
}, {
    exTypes: [SyntaxError, TypeError],
    targetGlobals: global
});

const result = processData(rawData);
```

## 에러 출력 예제

에러 발생 시 다음과 같이 상세한 정보가 출력됩니다:

```
[safe_fuckit] Exception isolated successfully!
   - Reason  : TypeError: Cannot read property 'x' of undefined
   - Location: at Object.<anonymous> (/path/to/file.js:10:5)
[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.
```

## 동기 vs 비동기

SafeFuckIt는 함수가 비동기인지 동기인지 자동으로 감지합니다:

```javascript
const { safeFuckit } = require('safe-fuckit');

// 동기 함수
const syncFn = safeFuckit(() => 1 / 0);
console.log(syncFn());  // undefined

// 비동기 함수
const asyncFn = safeFuckit(async () => {
    await delay(100);
    return 1 / 0;
});

asyncFn().then(result => console.log(result));  // undefined
```

## 타입 정의

TypeScript를 사용하는 경우, `index.d.ts` 파일에서 완벽한 타입 정의를 제공합니다:

```typescript
import { safeFuckit, SafeFuckIt } from 'safe-fuckit';

const divide: (a: number, b: number) => number | undefined = safeFuckit(
    (a: number, b: number) => a / b
);
```

## 주의사항

- 모든 예외를 무시하지 않으며, `exTypes`에 지정된 타입만 처리합니다
- 전역 변수 복구는 구조화 가능한 객체에만 작동합니다
- 프로덕션 환경에서는 예외의 근본 원인을 파악하고 해결하는 것이 좋습니다

## 성능

- 함수 호출 오버헤드: ~1-2% (스냅샷 비용 포함)
- 예외 처리: 빠른 예외 격리
- 메모리: 최소한의 스냅샷 메모리 사용

## 실행 흐름

```
함수 호출
    ↓
스냅샷 생성
    ↓
함수 실행 시도
    ↓
예외 발생?
    ├─ 아니오 → 결과 반환
    └─ 예
        ↓
    exTypes 확인
        ├─ 일치 → 에러 처리 및 상태 복구
        └─ 불일치 → 예외 던지기
```

## 예제: 안전한 데이터 파이프라인

```javascript
const { safeFuckit } = require('safe-fuckit');

// 데이터 파이프라인 구성
const pipeline = [
    safeFuckit(parseJSON),
    safeFuckit(validateSchema),
    safeFuckit(transformData),
    safeFuckit(saveToDatabase)
];

// 각 단계를 안전하게 실행
let data = rawInput;
for (const processor of pipeline) {
    data = processor(data);
    if (!data) {
        console.log('Pipeline 중단 - 안전하게 실패');
        break;
    }
}
```

## 라이선스

AGPL-3.0

## 기여

풀 리퀘스트와 이슈는 언제나 환영합니다!
