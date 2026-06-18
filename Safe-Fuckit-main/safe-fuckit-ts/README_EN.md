# Safe-Fuckit TypeScript

**Type-safe error handling library for TypeScript**

## Overview

Safe-Fuckit TypeScript provides safe and elegant error handling by leveraging TypeScript's powerful type system.

## Features

- 🎯 **Perfect Type Safety**: Full TypeScript type system support
- 🔍 **Generic Support**: Type inference for all function signatures
- 📦 **Lightweight**: Minimal dependencies
- 🚀 **Perfect Async Support**: Full compatibility with Promise and async/await
- 🛡️ **Runtime Safety**: Exception handling guarantee at runtime

## Installation

```bash
npm install safe-fuckit-ts
```

or

```bash
yarn add safe-fuckit-ts
```

## Usage Examples

### Basic Usage

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';

const divide = ignoreErrors((a: number, b: number): number => {
    return a / b;
});

const result = divide(10, 0);  // undefined
console.log(result);
```

### Default Value

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';

const divide = ignoreErrors(
    (a: number, b: number): number => a / b,
    { default: 0 }
);

const result = divide(10, 0);
console.log(result);  // 0
```

### Generic Usage

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';

interface User {
    id: number;
    name: string;
}

const getUser = ignoreErrors(async (userId: number): Promise<User> => {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
}, { default: null });

const user = await getUser(1);  // User | null
```

### Promise Handling

```typescript
import { ignoreErrorsAsync } from 'safe-fuckit-ts';

const fetchData = ignoreErrorsAsync(async (url: string) => {
    const response = await fetch(url);
    return response.json();
}, { default: {} });

const data = await fetchData('https://invalid-url.com');
console.log(data);  // {}
```

### Enable Logging

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';
import type { Logger } from 'safe-fuckit-ts';

const logger: Logger = {
    error: (message: string, error: any) => console.error(message, error)
};

const riskyFunc = ignoreErrors(
    () => { throw new Error('Test'); },
    { 
        logErrors: true,
        logger: logger
    }
);
```

## API Documentation

### `ignoreErrors<T, R>`

Safely wraps synchronous functions.

```typescript
function ignoreErrors<T extends (...args: any[]) => any>(
    fn: T,
    options?: IgnoreErrorsOptions<ReturnType<T>>
): T
```

### `ignoreErrorsAsync<T>`

Safely wraps asynchronous functions.

```typescript
function ignoreErrorsAsync<T extends (...args: any[]) => Promise<any>>(
    fn: T,
    options?: AsyncIgnoreErrorsOptions<Awaited<ReturnType<T>>>
): T
```

### Options Interfaces

```typescript
interface IgnoreErrorsOptions<R> {
    default?: R;
    exceptions?: (new (...args: any[]) => Error)[];
    logErrors?: boolean;
    logger?: Logger;
}

interface AsyncIgnoreErrorsOptions<R> extends IgnoreErrorsOptions<R> {
    timeout?: number;
}

interface Logger {
    error(message: string, error: any): void;
}
```

## Real-World Examples

### Safe API Calls

```typescript
import { ignoreErrorsAsync } from 'safe-fuckit-ts';

interface ApiResponse<T> {
    data: T;
    status: number;
}

const fetchJson = ignoreErrorsAsync(
    async <T>(url: string): Promise<T> => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    },
    { default: null }
);

const users = await fetchJson<User[]>('/api/users');
```

### JSON Parsing

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';

const parseJSON = ignoreErrors(
    <T = unknown>(str: string): T => JSON.parse(str),
    { default: {} }
);

const config = parseJSON<Config>(jsonString);
```

### Retry Logic

```typescript
import { ignoreErrors } from 'safe-fuckit-ts';

const retry = (fn: () => any, times: number = 3) => {
    for (let i = 0; i < times; i++) {
        const result = ignoreErrors(fn)();
        if (result !== undefined) return result;
    }
    return null;
};
```

## Type Safety

Safe-Fuckit TypeScript provides perfect type inference:

```typescript
// Types are automatically inferred
const fn = (x: number) => x * 2;
const safeFn = ignoreErrors(fn);

const result = safeFn(5);  // number | undefined
```

## Performance

- Near zero-cost abstraction
- Optimized at compile time
- No runtime type checks

## License

AGPL-3.0

## Contributing

Pull requests and issues are always welcome!
