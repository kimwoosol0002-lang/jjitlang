# safe_fuckit

`safe_fuckit` is an enterprise-grade exception isolation and automatic state recovery (rollback) utility for Python. Inspired by the unapologetic philosophy of the original `fuckit` library—which forces code to run despite errors—`safe_fuckit` is completely re-engineered from scratch to be safe, highly optimized, and robust enough for production and concurrent environments.

It completely solves the two fatal flaws of the original library: **Unhandlable Obscurity (Inability to debug)** and **Data Corruption (State pollution)**. With `safe_fuckit`, your application can gracefully bypass unexpected execution-time failures without crashing or leaving half-mutated data in memory.

---

## 🆚 Comparison: Original `fuckit` vs. `safe_fuckit`

| Feature / Metric | Original `fuckit` | **safe_fuckit (This Project)** |
| :--- | :--- | :--- |
| **Bypass Mechanism** | Modifies AST / slices source code to delete failing lines | Clean Context/Decorator-based execution sandboxing |
| **Data Integrity** | Continues with partially corrupted data states | **`Deep-Copy` based atomic rollback** to pre-entry states |
| **Debugging Visibility** | Exceptions vanish silently; impossible to trace | Explicit text-based logging of `Location` and `Reason` |
| **Asynchronous Support** | No support for `async / await` paradigms | **Full native support** for asynchronous coroutines |
| **Context Monitoring** | Requires manual scope registration via `with` | **Automatic caller scope discovery** via frame inspection |
| **Concurrency Safety** | Thread-unsafe; prone to severe race conditions | **Thread-safe isolation** utilizing `threading.local` |
| **Exception Filtering** | Blanket suppression of all errors indiscriminately | **Whitelist filtering** via customizable `ex_types` |
| **Performance Overhead** | Minimal but destroys structural code predictability | Optimized via structural data filtering to bypass heavy objects |

---

## 🚀 Key Features

* **Atomic State Rollback (Deep-Copy Based)**: If a mutable data structure (such as a nested `list` or `dict`) is partially modified or corrupted mid-execution before an error triggers, `safe_fuckit` instantly reverts the entire in-scope memory state back to its clean, pre-entry snapshot.
* **Automatic Scope Resolution**: Powered by Python's frame inspection (`sys._getframe`), the utility dynamically traces back to find the caller's global namespace. This allows developers to use `@safe_fuckit` cleanly without passing repetitive parameters.
* **Dual Sync/Async Runtime Interception**: Seamlessly operates as a decorator across both standard blocking functions (`def`) and asynchronous coroutines (`async def`), dynamically switching execution wrappers at runtime based on inspection.
* **Granular Whitelist Filtering**: Offers the flexibility to catch specific exception subsets (e.g., `ex_types=(ValueError, KeyError)`) while allowing critical or system-level crashes (like `SystemExit`, `KeyboardInterrupt`, or `MemoryError`) to propagate normally.
* **Snapshot Memory Optimization**: To resolve performance bottlenecks common with deep-copying, the engine scans the namespace and intentionally filters out heavy dependencies—such as imported modules, classes, functions, and dunder (`__`) variables—copying only pure user data variables.
* **Thread-Safe Memory Isolation**: Implements `threading.local()` to store individual execution snapshots, guaranteeing zero data leakage or race conditions even when handled across dense multithreaded environments.
* **Clean Text-Only Logging**: Formatted using clean, standard text outputs designed to integrate flawlessly into command-line interfaces and headless CI/CD pipelines without relying on terminal-breaking emojis.

---

## 🛠️ Installation

Clone the repository locally and install it in editable mode via your project's root directory:

```bash
pip install -e .

## 💻 Usage

1. Decorator Syntax
Simply attach @safe_fuckit over any standard or asynchronous function. It automatically captures the enclosing state and ensures seamless fallback continuity.

Python
import asyncio
from safe_fuckit import safe_fuckit

# Synchronous Function Example
@safe_fuckit
def sync_task():
    data_pool = ["item_1", "item_2"]
    data_pool.append("corrupted_mutation")
    raise ValueError("Unexpected payload error")  # Isolated instantly; data_pool rolls back seamlessly

# Asynchronous Coroutine Example
@safe_fuckit
async def async_task():
    await asyncio.sleep(0.1)
    raise RuntimeError("Async non-blocking connection dropped")  # Intercepted cleanly

2. Context Manager Syntax
Isolate precise code blocks inline inside functions using standard with statements.

Python
from safe_fuckit import safe_fuckit

app_config = {"status": "INITIALIZED"}

with safe_fuckit():
    app_config["status"] = "PROCESSING_UNSTABLE_STREAM"
    raise KeyError("Missing stream metadata packet")  # Triggers rollback to "INITIALIZED"

print(f"Current Runtime Status: {app_config['status']}")  # Output: INITIALIZED

3. Target Specific Exception Classes
Configure the guard to filter only specialized error classes while allowing critical core failures to halt execution.

Python
from safe_fuckit import safe_fuckit

# Only capture and suppress ValueError instances
@safe_fuckit(ex_types=(ValueError,))
def dynamic_safety_gate(is_fatal: bool):
    if is_fatal:
        raise ZeroDivisionError("Core system collapse")  # Out of scope: Crashes program normally
    raise ValueError("Minor processing abnormality")  # Whitelisted: Logged and bypassed safely

📋 Console Output Example
When safe_fuckit successfully captures an exception and enforces state restoration, it prints structured diagnostics via standard error logs:

Plaintext
[2026-06-11 15:52:10,401] ERROR: [safe_fuckit] Exception isolated successfully!
[2026-06-11 15:52:10,401] ERROR:   - Location: Line 15 -> `raise ValueError("sync task failed")`
[2026-06-11 15:52:10,402] ERROR:   - Reason  : ValueError: sync task failed
[2026-06-11 15:52:10,402] WARNING: [safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.
📐 Architecture & Engineering Highlights
safe_fuckit avoids clumsy global try-except chains by establishing a multi-layered lifecycle hook around execution scopes:

Intelligent Deep-Copy Pruning: When fetching the runtime scope dictionary, copying third-party modules (like pandas, numpy, or sys) causes extreme performance degradation. safe_fuckit dynamically interrogates object types using types.ModuleType, types.FunctionType, and type, skipping them to evaluate and capture only pure data variables.

Concurrent Storage Encapsulation: To handle intensive asynchronous frameworks (like FastAPI) or concurrent workers (like Celery), instance state histories are assigned to thread-local contexts. This prevents overlapping execution routines from rewriting each other’s history maps.

Asynchronous Coroutine Interception: During decorator binding, the utility checks the function footprint via inspect.iscoroutinefunction. If true, it dynamically yields a custom asynchronous closure, injecting runtime handlers into the event loop stack to accurately catch exceptions thrown down the line.
