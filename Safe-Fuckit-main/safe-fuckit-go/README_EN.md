# Safe-Fuckit Go

**Safe error handling library for Go**

## Overview

Safe-Fuckit Go provides safe and elegant error handling in Go programs. It maintains Go's error handling philosophy while making panic recovery and state rollback more convenient to use.

## Key Features

- 🏃 **High Performance**: Maintains Go's native speed
- 🛡️ **Type Safe**: Leverages Go's type system
- 📊 **Fine-Grained Control**: Recovery and logging options
- 🧹 **Clean Code**: Simplified error handling
- 🔄 **State Recovery**: Snapshots and restores state on panic
- 📝 **Detailed Logging**: Track panic causes and locations

## Installation

```bash
go get github.com/user/safe-fuckit
```

## Quick Start

### Basic Usage

```go
package main

import (
    "fmt"
    safefuckit "github.com/user/safe-fuckit"
)

func main() {
    state := map[string]interface{}{
        "count": 0,
    }

    guard := safefuckit.New(state)
    err := guard.Do(func() {
        state["count"] = 1
        panic("Something went wrong")
    })

    if err != nil {
        fmt.Println("Panic caught:", err)
    }
    fmt.Println("Count:", state["count"])  // 0 (rolled back)
}
```

### Context Manager Pattern

```go
state := map[string]interface{}{
    "value": "original",
}

guard := safefuckit.New(state)
guard.Enter()

// Protected code
state["value"] = "changed"

guard.Exit()
```

### Specify Exception Types

```go
guard := safefuckit.New(state, safefuckit.WithExTypes(
    (*MyCustomError)(nil),
))
```

## API Documentation

### `New(target, options...)`

Creates a new SafeFuckIt guard.

**Parameters:**
- `target` (map[string]interface{}): State to protect
- `options` ([]Option): Configuration options

**Returns:**
- *SafeFuckIt: Guard instance

```go
state := make(map[string]interface{})
guard := safefuckit.New(state)
```

### `Do(fn func())`

Executes a function with panic recovery.

**Parameters:**
- `fn` (func()): Function to execute

**Returns:**
- error: Non-nil if panic occurred

```go
err := guard.Do(func() {
    // Protected code
})
```

### `Enter()`

Enters snapshot mode.

**Returns:**
- *SafeFuckIt: Guard instance (for chaining)

```go
guard.Enter()
```

### `Exit()`

Exits snapshot mode.

```go
guard.Exit()
```

### `WithExTypes(...interface{})`

Option to specify exception types.

```go
opt := safefuckit.WithExTypes(
    (*os.PathError)(nil),
    (*json.SyntaxError)(nil),
)
guard := safefuckit.New(state, opt)
```

## Real-World Examples

### Data Processing with Rollback

```go
package main

import (
    "fmt"
    safefuckit "github.com/user/safe-fuckit"
)

func processData(data map[string]interface{}) error {
    guard := safefuckit.New(data)
    return guard.Do(func() {
        // Complex data transformation
        data["status"] = "processing"
        data["count"] = data["count"].(int) + 1
        
        // Simulate error
        if data["count"].(int) > 10 {
            panic("Count exceeded limit")
        }
        
        data["status"] = "complete"
    })
}

func main() {
    data := map[string]interface{}{
        "status": "initial",
        "count":  5,
    }

    err := processData(data)
    if err != nil {
        fmt.Println("Error:", err)
        fmt.Println("Data rolled back:", data)
        // Output: status: initial, count: 5
    }
}
```

### Safe Concurrent Operations

```go
package main

import (
    "fmt"
    "sync"
    safefuckit "github.com/user/safe-fuckit"
)

func safeIncrement(state map[string]interface{}, wg *sync.WaitGroup) {
    defer wg.Done()

    guard := safefuckit.New(state)
    guard.Do(func() {
        count := state["counter"].(int)
        // Simulate risky operation
        if count%10 == 0 {
            panic("Failed to increment")
        }
        state["counter"] = count + 1
    })
}

func main() {
    state := map[string]interface{}{
        "counter": 0,
    }

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go safeIncrement(state, &wg)
    }
    wg.Wait()

    fmt.Println("Final counter:", state["counter"])
}
```

### Configuration-Based Processing

```go
package main

import (
    "encoding/json"
    "fmt"
    safefuckit "github.com/user/safe-fuckit"
)

type Config struct {
    Database string
    Port     int
    Debug    bool
}

func loadConfig(configData map[string]interface{}) error {
    guard := safefuckit.New(configData)
    return guard.Do(func() {
        // Parse and validate config
        var config Config
        jsonData := configData["json"].(string)
        
        if err := json.Unmarshal([]byte(jsonData), &config); err != nil {
            panic(err)
        }
        
        if config.Port < 0 || config.Port > 65535 {
            panic("Invalid port number")
        }
        
        configData["database"] = config.Database
        configData["port"] = config.Port
        configData["debug"] = config.Debug
    })
}

func main() {
    configData := map[string]interface{}{
        "json": `{"database":"localhost","port":5432,"debug":true}`,
    }

    err := loadConfig(configData)
    if err != nil {
        fmt.Println("Failed to load config:", err)
    } else {
        fmt.Println("Config loaded:", configData)
    }
}
```

### Multi-Stage Pipeline

```go
package main

import (
    "fmt"
    safefuckit "github.com/user/safe-fuckit"
)

func validateAndProcess(state map[string]interface{}) []error {
    var errors []error

    stages := []struct {
        name string
        fn   func()
    }{
        {
            name: "validation",
            fn: func() {
                if state["input"] == nil {
                    panic("Input is nil")
                }
            },
        },
        {
            name: "processing",
            fn: func() {
                state["processed"] = true
            },
        },
        {
            name: "finalization",
            fn: func() {
                state["complete"] = true
            },
        },
    }

    for _, stage := range stages {
        guard := safefuckit.New(state)
        if err := guard.Do(stage.fn); err != nil {
            errors = append(errors, fmt.Errorf("%s failed: %v", stage.name, err))
            // Rollback occurred automatically
            break
        }
    }

    return errors
}

func main() {
    state := map[string]interface{}{
        "input": "test data",
    }

    if errs := validateAndProcess(state); len(errs) > 0 {
        fmt.Println("Pipeline failed:")
        for _, err := range errs {
            fmt.Println("-", err)
        }
    } else {
        fmt.Println("Pipeline completed:", state)
    }
}
```

## How It Works

### State Snapshot Process

```
1. Enter Protected Block
   ↓
2. Take Snapshot of State
   ↓
3. Execute Function
   ↓
4. Panic Occurs?
   ├─ No → Return success
   └─ Yes → Handle Exception
            ↓
            Check Exception Type
            ├─ Match → Rollback State
            └─ No Match → Re-panic
```

## Error Output Example

When a panic is caught:

```
2026/06/11 07:00:00 [safe_fuckit] Exception isolated successfully!
2026/06/11 07:00:00    - Reason  : string: Something went wrong
2026/06/11 07:00:00    - Location: main.main (/path/to/file.go:15)
2026/06/11 07:00:00 [safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.
```

## Important Notes

- Only recovers from panics, not regular errors
- State rollback works with maps; deep copies are made
- Use caution in concurrent scenarios
- Prefer explicit error handling when possible
- Snapshots incur a small performance cost

## Performance Considerations

- Snapshot creation: O(n) where n = number of state keys
- Panic recovery: Minimal overhead
- Deep copy: Handles slices and maps efficiently
- No allocation if no panic occurs

## Testing

Run tests with:

```bash
go test ./...
```

Existing tests cover:
- Basic panic protection and rollback
- Normal execution without panic
- Enter/Exit snapshot mode

## License

AGPL-3.0

## Contributing

Pull requests and issues are always welcome!
