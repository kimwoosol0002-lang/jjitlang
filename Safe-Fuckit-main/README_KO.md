# safe_fuckit (안전한 에러 격리 및 상태 복구 유틸리티)

`safe_fuckit`은 파이썬을 위한 엔터프라이즈급 예외 격리 및 자동 상태 복구(롤백) 유틸리티입니다. 기존의 `fuckit` 라이브러리의 철학에서 영감을 받았으며, 그 치명적인 결함을 완전히 해결합니다.

기존 `fuckit` 라이브러리의 두 가지 치명적 문제점을 완벽히 해결했습니다: **디버깅 불가능한 불명확성** 및 **상태 오염으로 인한 데이터 손상**. `safe_fuckit`과 함께라면 애플리케이션이 안전하게 예외를 격리하고 이전 상태로 자동 복구할 수 있습니다.

---

## 🆚 비교: 기존 `fuckit` vs. `safe_fuckit`

| 기능 / 지표 | 기존 `fuckit` | **safe_fuckit (본 프로젝트)** |
| :--- | :--- | :--- |
| **바이패스 메커니즘** | AST 수정 / 소스 코드 슬라이싱으로 실패한 줄 삭제 | 깔끔한 Context/Decorator 기반 실행 샌드박싱 |
| **데이터 무결성** | 부분적으로 손상된 데이터 상태로 계속 실행 | **Deep-Copy 기반 원자적 롤백**으로 진입 전 상태로 복구 |
| **디버깅 가시성** | 예외가 무음으로 사라짐; 추적 불가능 | 명확한 텍스트 기반 `위치`와 `원인` 로깅 |
| **비동기 지원** | `async / await` 미지원 | **완전한 비동기 코루틴 네이티브 지원** |
| **Context 모니터링** | `with` 문을 통한 수동 범위 등록 필요 | **프레임 검사를 통한 자동 호출자 범위 검색** |
| **동시성 안전성** | 스레드 안전하지 않음; 심각한 경쟁 조건 위험 | **threading.local 활용한 스레드 안전 격리** |
| **예외 필터링** | 모든 에러를 무분별하게 억제 | **커스터마이징 가능한 `ex_types`를 통한 화이트리스트 필터링** |
| **성능 오버헤드** | 최소 하지만 코드 예측 가능성 파괴 | 구조적 데이터 필터링으로 최적화되어 무거운 객체 우회 |

---

## 🚀 주요 기능

* **원자적 상태 롤백 (Deep-Copy 기반)**: 실행 중 중첩된 `list`나 `dict` 같은 변경 가능한 데이터 구조가 부분적으로 수정되거나 손상되기 전 상태로 자동 복구됩니다.

* **자동 범위 해석**: 파이썬의 프레임 검사(`sys._getframe`)를 활용하여 동적으로 호출자의 전역 네임스페이스를 추적합니다. 개발자는 번거로운 설정 없이 데코레이터를 사용할 수 있습니다.

* **동기/비동기 이중 런타임 인터셉션**: 표준 함수(`def`)와 비동기 코루틴(`async def`) 모두에서 데코레이터로 seamlessly 작동하며, 동적으로 실행 모드를 전환합니다.

* **세밀한 화이트리스트 필터링**: 특정 예외 부분집합(예: `ValueError`, `KeyError`)만 캐치하면서 시스템 크래시(예: `SystemExit`)는 차단합니다.

* **스냅샷 메모리 최적화**: Deep-copy의 성능 병목을 해결하기 위해 네임스페이스를 스캔하고 pandas, numpy, sys 같은 무거운 의존성을 의도적으로 필터링합니다.

* **스레드 안전 메모리 격리**: `threading.local()`을 사용하여 개별 실행 스냅샷을 저장하고, 짙은 멀티스레드 환경에서도 데이터 누수나 경쟁 조건이 없음을 보장합니다.

* **깔끔한 텍스트 로깅**: 명령행 인터페이스와 헤드리스 CI/CD 파이프라인에 seamlessly 통합되도록 설계된 표준 텍스트 출력 형식입니다.

---

## 🛠️ 설치

저장소를 로컬로 클론하고 프로젝트 루트 디렉토리에서 editable 모드로 설치하세요:

```bash
pip install -e .
```

---

## 💻 사용법

### 1. 데코레이터 문법

표준 또는 비동기 함수 위에 `@safe_fuckit`을 붙이기만 하면 됩니다. 자동으로 주변 상태를 캡처하고 seamless한 폴백 연속성을 보장합니다.

```python
import asyncio
from safe_fuckit import safe_fuckit

# 동기 함수 예제
@safe_fuckit
def sync_task():
    data_pool = ["item_1", "item_2"]
    data_pool.append("corrupted_mutation")
    raise ValueError("Unexpected payload error")  # 격리됨; data_pool이 seamlessly 롤백됨

# 비동기 코루틴 예제
@safe_fuckit
async def async_task():
    await asyncio.sleep(0.1)
    raise RuntimeError("Async non-blocking connection dropped")  # 깔끔히 인터셉트됨
```

### 2. Context Manager 문법

함수 내부의 정확한 코드 블록을 표준 `with` 문으로 격리하세요.

```python
from safe_fuckit import safe_fuckit

app_config = {"status": "INITIALIZED"}

with safe_fuckit():
    app_config["status"] = "PROCESSING_UNSTABLE_STREAM"
    raise KeyError("Missing stream metadata packet")  # "INITIALIZED"로 롤백 트리거

print(f"Current Runtime Status: {app_config['status']}")  # 출력: INITIALIZED
```

### 3. 특정 예외 클래스 대상 설정

중요한 핵심 실패는 중단시키면서 특정 에러 클래스만 필터링하도록 가드를 설정하세요.

```python
from safe_fuckit import safe_fuckit

# ValueError 인스턴스만 캐치 및 억제
@safe_fuckit(ex_types=(ValueError,))
def dynamic_safety_gate(is_fatal: bool):
    if is_fatal:
        raise ZeroDivisionError("Core system collapse")  # 범위 밖: 프로그램 정상 크래시
    raise ValueError("Minor processing abnormality")  # 화이트리스트: 안전하게 로깅 및 우회
```

---

## 📋 콘솔 출력 예제

`safe_fuckit`이 성공적으로 예외를 캡처하고 상태 복구를 적용할 때 구조화된 진단을 표준 에러 로그에 출력합니다:

```
[2026-06-11 15:52:10,401] ERROR: [safe_fuckit] Exception isolated successfully!
[2026-06-11 15:52:10,401] ERROR:   - Location: Line 15 -> `raise ValueError("sync task failed")`
[2026-06-11 15:52:10,402] ERROR:   - Reason  : ValueError: sync task failed
[2026-06-11 15:52:10,402] WARNING: [safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.
```

---

## 📐 아키텍처 및 엔지니어링 하이라이트

`safe_fuckit`은 투박한 글로벌 try-except 체인을 피하고 실행 범위 주변에 다층 생명주기 훅을 설정합니다:

**지능형 Deep-Copy 가지치기**: 런타임 범위 딕셔너리를 가져올 때, pandas, numpy, sys 같은 써드파티 모듈을 복사하면 극도의 성능 저하가 발생합니다. `safe_fuckit`은 동적으로 이들 의존성을 필터링합니다.

**동시 실행 저장소 캡슐화**: FastAPI 같은 집약적인 비동기 프레임워크나 Celery 같은 동시 작업자를 처리하기 위해 인스턴스 상태 이력을 스레드로컬 컨텍스트에 할당합니다.

**비동기 코루틴 인터셉션**: 데코레이터 바인딩 중에 `inspect.iscoroutinefunction`을 통해 함수 발자국을 확인합니다. 비동기인 경우 동적으로 커스텀 비동기 클로저를 생성합니다.

---

## 📝 라이선스

이 프로젝트의 라이선스 정보를 확인하려면 LICENSE 파일을 참고하세요.

## 🤝 기여

버그 리포트, 기능 요청, 개선 제안은 언제든 환영합니다!

---

**Safe-Fuckit으로 안전하고 예측 가능한 예외 처리를 경험하세요! 🚀**
