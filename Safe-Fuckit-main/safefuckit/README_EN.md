# Safe-Fuckit

**Python Package: Safe error handling library**

## Overview

safefuckit is a Python package that gracefully handles unexpected errors while maintaining program stability.

## Features

- ✨ **Decorator-based**: Simple function application
- 🔒 **Type Safety**: Type hints support
- 📝 **Logging**: Optional error logging
- 🎯 **Precise Control**: Handle specific exceptions only
- 🚀 **Easy Installation**: Simple pip installation

## Package Structure

```
safefuckit/
├── __init__.py           # Package initialization
├── core.py              # Core implementation
├── decorators.py        # Decorators
└── utils.py             # Utilities
```

## Installation

```bash
pip install safe-fuckit
```

## Quick Start

### Basic Usage

```python
from safefuckit import ignore_errors

@ignore_errors
def divide(a, b):
    return a / b

result = divide(10, 0)  # No error raised
print(result)  # None
```

### Default Value

```python
from safefuckit import ignore_errors

@ignore_errors(default=0)
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)  # 0
```

### Handle Specific Exceptions

```python
from safefuckit import ignore_errors

@ignore_errors(exceptions=(ZeroDivisionError, ValueError))
def risky_operation():
    # Only ZeroDivisionError and ValueError are handled
    pass
```

### Enable Logging

```python
from safefuckit import ignore_errors
import logging

logger = logging.getLogger(__name__)

@ignore_errors(log_errors=True, logger=logger)
def sensitive_operation():
    pass
```

## Advanced Usage

### Apply to Class Methods

```python
from safefuckit import ignore_errors

class DataProcessor:
    @ignore_errors(default=None)
    def process(self, data):
        return parse_complex_data(data)
```

### Context Manager

```python
from safefuckit import safe_execution

with safe_execution(default=None):
    result = risky_operation()
```

### Combine Multiple Decorators

```python
from safefuckit import ignore_errors
import functools

def retry(times=3):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for i in range(times):
                result = fn(*args, **kwargs)
                if result is not None:
                    return result
            return None
        return wrapper
    return decorator

@retry(times=3)
@ignore_errors(default=None)
def risky_api_call():
    pass
```

## API Documentation

### `ignore_errors` Decorator

**Parameters:**
- `default` (any, optional): Default value to return on error (default: None)
- `exceptions` (tuple, optional): Specific exceptions to handle (default: Exception)
- `log_errors` (bool, optional): Whether to log errors (default: False)
- `logger` (logging.Logger, optional): Logger to use

**Returns:**
- Decorated function

### `safe_execution` Context Manager

```python
with safe_execution(default=None, logger=logger):
    # Code that will be executed safely
    pass
```

## Real-World Examples

### Data Processing

```python
from safefuckit import ignore_errors
import json

@ignore_errors(default={})
def parse_json_config(config_str):
    return json.loads(config_str)

config = parse_json_config(invalid_json)
```

### Database Connection

```python
from safefuckit import ignore_errors

@ignore_errors(default=None, exceptions=(ConnectionError, TimeoutError))
def connect_to_db(connection_string):
    return Database.connect(connection_string)
```

### API Requests

```python
from safefuckit import ignore_errors
import requests

@ignore_errors(default=None)
def fetch_user_data(user_id):
    response = requests.get(f'https://api.example.com/users/{user_id}')
    response.raise_for_status()
    return response.json()
```

## Troubleshooting

### Errors are not being logged
Make sure to pass the logger explicitly and check the logging level.

```python
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@ignore_errors(log_errors=True, logger=logger)
def my_function():
    pass
```

### Only handling specific exceptions
Specify exception types in the `exceptions` parameter.

```python
@ignore_errors(exceptions=(ValueError, KeyError))
def my_function():
    pass
```

## Performance Considerations

- Decorator overhead is minimized.
- Additional performance cost only occurs when exceptions are raised.
- Safe to use in production environments.

## License

AGPL-3.0

## Contributing

Pull requests and issues are always welcome!
