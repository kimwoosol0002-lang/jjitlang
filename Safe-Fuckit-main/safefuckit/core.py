import copy
import inspect
import logging
import sys
import threading
import traceback
import types
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar, Union, overload

F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger("SafeFuckIt")


class SafeFuckIt:
    def __init__(
        self,
        target_globals: Optional[Dict[str, Any]] = None,
        ex_types: Tuple[Type[BaseException], ...] = (Exception,),
    ) -> None:
        """
        Catch selected exceptions and roll back simple global state mutations.

        Args:
            target_globals: Globals dictionary to snapshot. If omitted, the caller's
                global scope is detected automatically.
            ex_types: Exception classes to suppress.
        """
        self._explicit_globals = target_globals
        self._ex_types = ex_types
        self._local_storage = threading.local()

    def _get_effective_globals(self) -> Dict[str, Any]:
        if self._explicit_globals is not None:
            return self._explicit_globals

        try:
            frame = sys._getframe(2)
            while frame.f_code.co_name in {
                "_take_snapshot",
                "_handle_exception",
                "__enter__",
                "__exit__",
                "sync_wrapper",
                "async_wrapper",
            }:
                frame = frame.f_back
                if frame is None:
                    return {}
            return frame.f_globals
        except ValueError:
            return {}

    def _take_snapshot(self) -> None:
        target = self._get_effective_globals()
        clean_state: Dict[str, Any] = {}

        for key, value in target.items():
            if (
                key.startswith("__")
                or isinstance(value, types.ModuleType)
                or isinstance(
                    value,
                    (
                        types.FunctionType,
                        types.MethodType,
                        types.BuiltinFunctionType,
                    ),
                )
                or isinstance(value, type)
            ):
                continue
            clean_state[key] = value

        try:
            self._local_storage.snapshot = copy.deepcopy(clean_state)
        except Exception:
            self._local_storage.snapshot = copy.copy(clean_state)

    def _handle_exception(self, exc_type, exc_val, exc_tb) -> None:
        tb_lines = traceback.extract_tb(exc_tb)
        last_trace = tb_lines[-1] if tb_lines else None

        line_no = last_trace.lineno if last_trace else "UNKNOWN"
        code_str = last_trace.line if last_trace else "UNKNOWN"

        logger.error("[safe_fuckit] Exception isolated successfully!")
        logger.error("   - Location: Line %s -> `%s`", line_no, code_str)
        logger.error("   - Reason  : %s: %s", exc_type.__name__, exc_val)

        target = self._get_effective_globals()
        snapshot = getattr(self._local_storage, "snapshot", None)

        if target and snapshot is not None:
            logger.warning(
                "[safe_fuckit] Data pollution risk detected. "
                "Rolling back variables to safe state."
            )
            for key in list(target.keys()):
                if (
                    not key.startswith("__")
                    and key not in snapshot
                    and not isinstance(
                        target[key], (types.ModuleType, types.FunctionType, type)
                    )
                ):
                    del target[key]

            for key, value in snapshot.items():
                target[key] = value

    def __enter__(self) -> "SafeFuckIt":
        self._take_snapshot()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None and issubclass(exc_type, self._ex_types):
            self._handle_exception(exc_type, exc_val, exc_tb)
            return True
        return False

    def __call__(self, func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                self._take_snapshot()
                try:
                    return await func(*args, **kwargs)
                except self._ex_types:
                    exc_type, exc_val, exc_tb = sys.exc_info()
                    self._handle_exception(exc_type, exc_val, exc_tb)
                    return None

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            self._take_snapshot()
            try:
                return func(*args, **kwargs)
            except self._ex_types:
                exc_type, exc_val, exc_tb = sys.exc_info()
                self._handle_exception(exc_type, exc_val, exc_tb)
                return None

        return sync_wrapper  # type: ignore[return-value]


@overload
def safe_fuckit(func: F) -> F:
    ...


@overload
def safe_fuckit(
    func: None = None,
    *,
    target_globals: Optional[Dict[str, Any]] = None,
    ex_types: Tuple[Type[BaseException], ...] = (Exception,),
) -> SafeFuckIt:
    ...


def safe_fuckit(
    func: Optional[F] = None,
    *,
    target_globals: Optional[Dict[str, Any]] = None,
    ex_types: Tuple[Type[BaseException], ...] = (Exception,),
) -> Union[F, SafeFuckIt]:
    """
    Create a SafeFuckIt guard, or decorate a function directly.

    Examples:
        @safe_fuckit
        def task(): ...

        @safe_fuckit(ex_types=(ValueError,))
        def task(): ...

        with safe_fuckit():
            ...
    """
    guard = SafeFuckIt(target_globals=target_globals, ex_types=ex_types)
    if func is None:
        return guard
    return guard(func)
