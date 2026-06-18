# Safe-Fuckit Go

**Go를 위한 안전한 에러 처리 라이브러리**

## 개요

Safe-Fuckit Go는 Go 프로그램에서 안전하고 우아한 에러 처리를 제공합니다. Go의 에러 처리 철학을 유지하면서도 더욱 간편하게 사용할 수 있습니다.

## 특징

- 🏃 **고성능**: Go의 네이티브 속도 유지
- 🛡️ **타입 안전**: 제너릭 지원 (Go 1.18+)
- 📊 **세밀한 제어**: 복구 및 로깅 옵션
- 🧹 **클린 코드**: 에러 처리 간소화

## 설치

```bash
go get github.com/user/safe-fuckit
```

## 사용 예제

### 기본 사용

```go
package main

import (
    "fmt"
    safefuckit "github.com/user/safe-fuckit"
)

func main() {
    result := safefuckit.IgnoreErrors(func() interface{} {
        return 1 / 0  // 패닉 발생
    })
    fmt.Println(result)  // nil
}
```

### 기본값 설정

```go
result := safefuckit.IgnoreErrorsWithDefault(func() interface{} {
    return 1 / 0
}, 0)
fmt.Println(result)  // 0
```

### 로깅 활성화

```go
import "log"

logger := log.New(os.Stdout, "[ERROR] ", log.LstdFlags)
result := safefuckit.IgnoreErrorsWithLogger(func() interface{} {
    panic("Something went wrong")
}, logger)
```

### 함수 래핑

```go
divide := func(a, b int) int {
    return a / b
}

safeDivide := safefuckit.Wrap(divide)
result := safeDivide(10, 0)  // 패닉이 복구됨
```

## API 문서

### `IgnoreErrors`

패닉을 복구하고 nil을 반환합니다.

```go
func IgnoreErrors(fn func() interface{}) interface{}
```

### `IgnoreErrorsWithDefault`

패닉을 복구하고 기본값을 반환합니다.

```go
func IgnoreErrorsWithDefault(fn func() interface{}, defaultVal interface{}) interface{}
```

### `IgnoreErrorsWithLogger`

패닉을 복구하고 로깅한 후 nil을 반환합니다.

```go
func IgnoreErrorsWithLogger(fn func() interface{}, logger *log.Logger) interface{}
```

### `IgnoreErrorsWithLoggerAndDefault`

패닉을 복구하고 로깅한 후 기본값을 반환합니다.

```go
func IgnoreErrorsWithLoggerAndDefault(fn func() interface{}, logger *log.Logger, defaultVal interface{}) interface{}
```

## 고급 사용법

### 에러 정보 캡처

```go
type ErrorResult struct {
    Value interface{}
    Error string
}

result := safefuckit.CaptureError(func() interface{} {
    return 1 / 0
})
if result.Error != "" {
    fmt.Println("Error occurred:", result.Error)
} else {
    fmt.Println("Result:", result.Value)
}
```

### 조건부 복구

```go
result := safefuckit.IgnoreErrorsIf(func() interface{} {
    return someRiskyOperation()
}, func(err interface{}) bool {
    // 특정 에러만 무시
    return true
})
```

## 주의사항

- 패닉만 복구합니다. 일반적인 에러는 처리하지 않습니다.
- 프로덕션 코드에서는 신중하게 사용하세요.
- 가능하면 명시적인 에러 처리를 권장합니다.

## 성능 고려사항

Safe-Fuckit Go는 매우 효율적이며 최소한의 오버헤드를 추가합니다:
- 패닉이 발생하지 않는 경우: 거의 오버헤드 없음
- 패닉 복구: 약간의 성능 비용 발생

## 라이선스

AGPL-3.0

## 기여

풀 리퀘스트와 이슈는 언제나 환영합니다!
