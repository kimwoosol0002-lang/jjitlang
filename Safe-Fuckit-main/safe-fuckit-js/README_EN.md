# Safe-Fuckit JavaScript

**Safe error handling library for JavaScript**

## Overview

Safe-Fuckit JavaScript gracefully handles unexpected errors while maintaining program state safely. It follows the principles of the original Fuckit while providing enhanced functionality.

## Key Features

- 🛡️ **Safe Error Isolation**: Program continues running even when errors occur
- 🔄 **State Recovery**: Snapshots and restores global variable state
- 🎯 **Precise Exception Filtering**: Handle only specific exception types
- 📝 **Detailed Logging**: Track error causes and locations
- 🌐 **Browser/Node.js Compatible**: Works in all JavaScript environments

## Installation

```bash
npm install safe-fuckit
```

or

```bash
yarn add safe-fuckit
```

## Quick Start

### Basic Usage

```javascript
const { safeFuckit } = require('safe-fuckit');

// Wrap a function
const divide = safeFuckit((a, b) => {
    return a / b;
});

const result = divide(10, 0);  // Safe even with error
console.log(result);  // undefined
```

### Context Manager Usage

```javascript
const { SafeFuckIt } = require('safe-fuckit');

const sf = new SafeFuckIt();
sf.enter();

try {
    // Risky code
    risky_operation();
} finally {
    sf.exit();
}
```

### Handle Specific Exceptions

```javascript
const { safeFuckit } = require('safe-fuckit');

const divide = safeFuckit(
    (a, b) => a / b,
    { exTypes: [RangeError, TypeError] }
);

divide(10, 0);  // ZeroDivisionError not handled
```

### Protect Global Variables

```javascript
const { SafeFuckIt } = require('safe-fuckit');

// Specify global object to protect
const sf = new SafeFuckIt({ targetGlobals: global });

const wrappedFn = sf.wrap(riskFunction);
wrappedFn();  // Global variables restored after execution
```

## API Documentation

### `safeFuckit(fn, options)`

Wraps a function to make it safe.

**Parameters:**
- `fn` (function): Function to wrap
- `options` (object, optional):
  - `exTypes` (array): Exception types to handle (default: [Error])
  - `targetGlobals` (object): Global object to protect (default: null)

**Returns:**
- Wrapped function

### `SafeFuckIt` Class

**Constructor:**
```javascript
const sf = new SafeFuckIt({
    exTypes: [Error],        // Exception types to handle
    targetGlobals: null      // Global object to protect
});
```

**Methods:**

#### `wrap(fn)`
Wraps a function.

```javascript
const safeFn = sf.wrap(riskFunction);
```

#### `enter()`
Starts snapshot.

```javascript
sf.enter();
```

#### `exit()`
Ends snapshot.

```javascript
sf.exit();
```

## Real-World Examples

### Async Function Handling

```javascript
const { safeFuckit } = require('safe-fuckit');

const fetchData = safeFuckit(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error('Network error');
    return response.json();
});

(async () => {
    const data = await fetchData('https://invalid-url.com');
    console.log(data);  // undefined (error isolated)
})();
```

### JSON Parsing

```javascript
const { safeFuckit } = require('safe-fuckit');

const parseJSON = safeFuckit((str) => {
    return JSON.parse(str);
});

const config = parseJSON(invalidJsonString);
console.log(config);  // undefined (error isolated)
```

### API Calls

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
console.log(user);  // undefined on error
```

### Data Processing

```javascript
const { safeFuckit } = require('safe-fuckit');

const processData = safeFuckit((data) => {
    // Complex data processing
    const transformed = complexTransform(data);
    updateGlobalState(transformed);
    return transformed;
}, {
    exTypes: [SyntaxError, TypeError],
    targetGlobals: global
});

const result = processData(rawData);
```

## Error Output Example

When an error occurs, detailed information is logged:

```
[safe_fuckit] Exception isolated successfully!
   - Reason  : TypeError: Cannot read property 'x' of undefined
   - Location: at Object.<anonymous> (/path/to/file.js:10:5)
[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.
```

## Sync vs Async

SafeFuckIt automatically detects if a function is async or sync:

```javascript
const { safeFuckit } = require('safe-fuckit');

// Sync function
const syncFn = safeFuckit(() => 1 / 0);
console.log(syncFn());  // undefined

// Async function
const asyncFn = safeFuckit(async () => {
    await delay(100);
    return 1 / 0;
});

asyncFn().then(result => console.log(result));  // undefined
```

## Important Notes

- Does not ignore all exceptions; only processes types in `exTypes`
- Global variable recovery only works with structurable objects
- In production, it's better to identify and resolve root causes

## Performance

- Function call overhead: ~1-2% (including snapshot cost)
- Exception handling: Fast exception isolation
- Memory: Minimal snapshot memory usage

## License

AGPL-3.0

## Contributing

Pull requests and issues are always welcome!
