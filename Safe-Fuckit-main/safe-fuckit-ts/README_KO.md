# Safe-Fuckit TypeScript

**TypeScript를 위한 타입-안전한 에러 처리 라이브러리**

## 개요

Safe-Fuckit TypeScript는 TypeScript의 강력한 타입 시스템을 활용하여 안전하고 우아한 에러 처리를 제공합니다. SafeFuckIt의 원리를 따르면서 완벽한 타입 안정성을 보장합니다.

## 주요 특징

- 🎯 **완벽한 타입 안전성**: TypeScript의 모든 타입 기능 지원
- 🔍 **제너릭 지원**: 모든 함수 시그니처에 대한 타입 추론
- 📦 **경량**: 의존성 최소화
- 🚀 **비동기 완벽 지원**: Promise와 async/await 완벽 호환
- 🛡️ **런타임 안전**: 런타임에서의 예외 처리 보장
- 🔄 **상태 복구**: 전역 변수의 스냅샷 저장 및 복구

## 설치

```bash
npm install safe-fuckit
```

또는

```bash
yarn add safe-fuckit
```

## 빠른 시작

### 기본 사용

```typescript
import { safeFuckit } from 'safe-fuckit';

const divide = safeFuckit((a: number, b: number): number => {
    return a / b;
});

const result = divide(10, 0);  // undefined
console.log(result);
```

### 기본값 설정

```typescript
import { safeFuckit } from 'safe-fuckit';

const divide = safeFuckit(
    (a: number, b: number): number => a / b,
    { default: 0 }
);

const result = divide(10, 0);
console.log(result);  // 0
```

### 제너릭 사용

```typescript
import { safeFuckit } from 'safe-fuckit';

interface User {
    id: number;
    name: string;
}

const getUser = safeFuckit(async (userId: number): Promise<User> => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
});

const user = await getUser(1);  // User | undefined
```

### 비동기 함수 처리

```typescript
import { safeFuckit } from 'safe-fuckit';

const fetchData = safeFuckit(async (url: string) => {
    const response = await fetch(url);
    return response.json();
});

const data = await fetchData('https://invalid-url.com');
console.log(data);  // undefined
```

### 특정 예외만 처리

```typescript
import { safeFuckit } from 'safe-fuckit';

const divide = safeFuckit(
    (a: number, b: number): number => a / b,
    { exTypes: [RangeError, TypeError] }
);

divide(10, 0);  // ZeroDivisionError는 처리되지 않음
```

### 전역 변수 보호

```typescript
import { safeFuckit } from 'safe-fuckit';

const processData = safeFuckit(
    (data: any) => complexOperation(data),
    { targetGlobals: global }
);

const result = processData(someData);
// 실행 후 전역 변수가 원래 상태로 복구됨
```

## API 문서

### `safeFuckit<T>`

함수를 안전하게 래핑합니다.

**매개변수:**
- `fn` (function): 래핑할 함수
- `options` (object, optional):
  - `exTypes` (array): 처리할 예외 타입들 (기본값: [Error])
  - `targetGlobals` (object): 보호할 전역 객체 (기본값: null)

**반환값:**
- 래핑된 함수

### `SafeFuckIt` 클래스

**생성자:**
```typescript
const sf = new SafeFuckIt({
    exTypes: [Error],        // 처리할 예외 타입
    targetGlobals: null      // 보호할 전역 객체
});
```

**메서드:**

#### `wrap<T>(fn: T): T`
함수를 래핑합니다.

```typescript
const safeFn = sf.wrap(riskFunction);
```

#### `enter(): this`
스냅샷을 시작합니다.

```typescript
sf.enter();
```

#### `exit(): void`
스냅샷을 종료합니다.

```typescript
sf.exit();
```

## 실전 예제

### API 호출 안전화

```typescript
import { safeFuckit } from 'safe-fuckit';

interface ApiResponse<T> {
    data: T;
    status: number;
}

interface User {
    id: number;
    name: string;
}

const fetchJson = safeFuckit(
    async <T>(url: string): Promise<T> => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    }
);

const users = await fetchJson<User[]>('/api/users');
```

### JSON 파싱

```typescript
import { safeFuckit } from 'safe-fuckit';

interface Config {
    port: number;
    host: string;
}

const parseJSON = safeFuckit(
    <T = unknown>(str: string): T => JSON.parse(str)
);

const config = parseJSON<Config>(jsonString);
```

### 재시도 로직

```typescript
import { safeFuckit } from 'safe-fuckit';

const retry = (fn: () => any, times: number = 3) => {
    for (let i = 0; i < times; i++) {
        const result = safeFuckit(fn)();
        if (result !== undefined) return result;
    }
    return null;
};
```

### 데이터 처리

```typescript
import { safeFuckit } from 'safe-fuckit';

interface ProcessedData {
    items: any[];
    count: number;
}

const processData = safeFuckit(
    (data: unknown): ProcessedData => {
        // 복잡한 데이터 처리
        const transformed = complexTransform(data);
        updateGlobalState(transformed);
        return transformed;
    },
    {
        exTypes: [SyntaxError, TypeError],
        targetGlobals: global
    }
);

const result = processData(rawData);
```

### 타입 안전 데이터 검증

```typescript
import { safeFuckit } from 'safe-fuckit';

interface ValidationResult {
    valid: boolean;
    errors: string[];
}

const validateUser = safeFuckit(
    (data: unknown): ValidationResult => {
        const user = data as any;
        const errors: string[] = [];
        
        if (!user.email || typeof user.email !== 'string') {
            errors.push('Invalid email');
        }
        if (!user.age || typeof user.age !== 'number' || user.age < 0) {
            errors.push('Invalid age');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    },
    { default: { valid: false, errors: ['Unknown error'] } }
);

const result = validateUser(someData);
```

## 타입 안전성

Safe-Fuckit TypeScript는 완벽한 타입 추론을 제공합니다:

```typescript
// 타입이 자동으로 추론됩니다
const fn = (x: number) => x * 2;
const safeFn = safeFuckit(fn);

const result = safeFn(5);  // number | undefined
```

## 동기 vs 비동기

함수가 비동기인지 동기인지 자동으로 감지합니다:

```typescript
import { safeFuckit } from 'safe-fuckit';

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

## 유니언 타입 처리

```typescript
import { safeFuckit } from 'safe-fuckit';

type Result = Success | Failure;

interface Success {
    ok: true;
    data: any;
}

interface Failure {
    ok: false;
    error: string;
}

const processWithFallback = safeFuckit(
    (input: unknown): Result => {
        const processed = complexProcess(input);
        return { ok: true, data: processed };
    },
    { default: { ok: false, error: 'Processing failed' } }
);
```

## 주의사항

- 모든 예외를 무시하지 않으며, `exTypes`에 지정된 타입만 처리합니다
- 전역 변수 복구는 구조화 가능한 객체에만 작동합니다
- 프로덕션 환경에서는 예외의 근본 원인을 파악하고 해결하는 것이 좋습니다
- TypeScript의 strict 모드에서 완벽하게 작동합니다

## 성능

- Zero-cost abstraction에 가까운 성능
- 컴파일 타임에 최적화됨
- 런타임 타입 체크 없음
- 최소한의 메모리 오버헤드

## 실행 흐름도

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
        ├─ 일치 → 상태 복구 및 undefined 반환
        └─ 불일치 → 예외 던지기
```

## 라이선스

AGPL-3.0

## 기여

풀 리퀘스트와 이슈는 언제나 환영합니다!
