![Python](https://img.shields.io/badge/-Python-05122A?style=flat&logo=python)
[![PyPI-Server](https://img.shields.io/pypi/v/stateful-data-processor.svg)](https://pypi.org/project/stateful-data-processor/)
[![Coverage..](https://coveralls.io/repos/github/doruirimescu/stateful-data-processor/badge.svg?branch=master)](https://coveralls.io/github/doruirimescu/stateful-data-processor?branch=master)
![Pipeline status](https://github.com/doruirimescu/stateful-data-processor/actions/workflows/main.yml/badge.svg?branch=master)
[![Monthly Downloads](https://pepy.tech/badge/stateful-data-processor/month)](https://pepy.tech/project/stateful-data-processor)
[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# stateful-data-processor

**Resumable, checkpointed item processing with graceful interrupts — subclass and go.**

A tiny utility for long-running, restart-safe loops: process items, persist state, resume exactly where you stopped or when an exception is raised, and handle SIGINT/SIGTERM cleanly.

- **Install:** `pip install stateful-data-processor`
- **Why:** Skip rework after crashes/interrupts; keep logic in a single subclass.
- **Good for:** Batch jobs, ETL steps, scraping, “process a big list with restarts”.

## Quick start (60 seconds)

``` python
import time
from stateful_data_processor.file_rw import FileRW
from stateful_data_processor.processor import StatefulDataProcessor

class MyDataProcessor(StatefulDataProcessor):

 def process_item(self, item, iteration_index: int, delay: float):
     ''' item and iteration_index are automatically supplied by the framework.
      iteration_index may or may not be used.
     '''
     self.data[item] = item ** 2  # Example processing: square the item
     time.sleep(delay) # Simulate long processing time

# Example usage
file_rw = FileRW('data.json')
processor = MyDataProcessor(file_rw)

items_to_process = [1, 2, 3, 4, 5]
processor.run(items=items_to_process, delay=1.5) # Ctrl+C anytime; rerun to resume.
```

---

**stateful-data-processor** is a utility designed to handle large
amounts of data incrementally. It allows you to process data
step-by-step, saving progress to avoid data loss in case of
interruptions or errors. The processor can be subclassed to implement
custom data processing logic.

### Features

* **Incremental & resumable** — process large datasets in chunks and pick up exactly where you left off.
* **State persisted to disk** — saves progress to a file so restarts are fast and reliable.
* **Graceful shutdown** — handles `SIGINT`/`SIGTERM` (e.g., Ctrl+C) and saves state before exiting.
* **Crash-safe** — catches exceptions, saves current progress, and lets you restart without losing work.
* **Automatic logging** — a logger is created for you if you don’t inject one.
* **Skip completed work** — automatically avoids already processed items on restart.
* **Easy to extend** — subclass to implement custom processing logic.
* **Reprocess cached items** — optionally revisit items already stored to explore alternative processing strategies.


### Problem

Processing massive datasets is slow, brittle, and easy to interrupt. You need a way to:

* Iterate through items one-by-one and **save progress to disk** as you go.
* **Resume exactly where you left off** after crashes, timeouts, restarts, or upgrades.
* **Gracefully interrupt** with `SIGINT`/`SIGTERM` (e.g., Ctrl+C) and persist state before exiting.
* **Subclass cleanly** to provide your own `process_data` and `process_item` logic.
* **Avoid rework** by skipping already-processed items—or intentionally **reprocess cached items** to explore alternatives.

In short: incremental processing with safety, resumability, and extensibility built in.

### Solution

**`StatefulDataProcessor`** provides a resilient, incremental pipeline for large datasets:

* **Incremental processing:** Iterate through big inputs in manageable chunks (e.g., from a JSON source) without starting over.
* **Persistent state:** Progress and results are stored in a dictionary on disk; the processor tracks the current position.
* **Graceful interruption:** Handles `SIGINT`/`SIGTERM` (e.g., Ctrl+C) and saves state before exiting.
* **Subclass-first design:** Implement your own logic by overriding `process_item` (required) and `process_data` (optional).
* **Per-item execution:** `run(**kwargs)` forwards all arguments to `process_item`, iterating over `items` and processing one at a time.
* **Unique keys:** Results are keyed by each item’s unique label, so items must be unique.
* **Customizable workflow:** Override `process_data` to pre/post-process items, filter, batch, or enrich as needed.


## Usage
**Example usage in a large project:**

[alphaspread analysis of nasdaq
symbols](https://github.com/doruirimescu/python-trading/blob/65a558fcb3a5e80a1686c58cbf35722e045c8f1e/Trading/stock/analyze_nasdaq.py#L22)

[filter ranging
stocks](https://github.com/doruirimescu/python-trading/blob/master/Trading/live/range/filter_ranging_stocks.py)

[xtb to yfinance symbol
conversion](https://github.com/doruirimescu/python-trading/blob/941055693ad64bfe8c843fed79429b6db2a4317d/Trading/symbols/yfinance/xtb_to_yfinance.py#L21)

### Example: Passing extra arguments via a subclass

File: `processors.py`

```python3
from typing import Any, Optional
from stateful_data_processor.processor import StatefulDataProcessor

class GenericAnalyzer(StatefulDataProcessor):
    """
    Parent processor that expects an extra kwarg: `payload`.
    In a real project this could be HTML, JSON, text, bytes, etc.
    """

    def process_item(self, item: str, payload: Optional[Any], iteration_index: int):
        # Use the extra arg however you like
        self.logger.info(f"[{iteration_index}] Processing {item}; has_payload={payload is not None}")

        # Do minimal "work" for the README: store something derived from the payload
        result = {
            "item": item,
            "payload_preview": str(payload)[:40],  # keep it tiny for docs
            "payload_length": len(str(payload)) if payload is not None else 0,
        }

        # Persist per-item result; the base class handles saving/resuming
        self.data[item] = result
```

File: `run_example.py`

```python3
# run_example.py
from datetime import date
from typing import Any, List

from stateful_data_processor.file_rw import JsonFileRW
from processors import GenericAnalyzer

def build_payload(item: str) -> Any:
    """
    Stand-in for I/O or computation (e.g., HTTP GET, DB read, cache lookup).
    Keep it simple for the README.
    """
    return f"payload for {item}"

class UrlAnalyzer(GenericAnalyzer):
    """
    Child processor that *adds* the extra argument (`payload`)
    and forwards it to the parent via super().
    """
    def process_item(self, item: str, iteration_index: int):
        payload = build_payload(item)
        # Forward both the original item and the extra kwarg to the parent
        super().process_item(item=item, payload=payload, iteration_index=iteration_index)

if __name__ == "__main__":
    items: List[str] = ["AAPL", "MSFT", "GOOGL", "NVDA"]

    # Results are saved incrementally; reruns resume from where you stopped.
    out_file = JsonFileRW(f"./demo-analysis-{date.today()}.json")

    analyzer = UrlAnalyzer(json_file_writer=out_file)
    analyzer.run(items=items)

    # Access in-memory results if needed
    data = analyzer.data
    print(f"Processed {len(data)} items. Output file: {out_file.path}")
```


---

### Example: Passing extra arguments via a subclass

Sometimes your per-item logic needs more than just the item itself (e.g., a pre-fetched blob, metadata, cached JSON). You can add **any keyword args you want** to your processor’s `process_item` signature, and then supply them from a subclass.

#### `processors.py`

```python
# processors.py
from typing import Any, Optional
from stateful_data_processor.processor import StatefulDataProcessor

class GenericAnalyzer(StatefulDataProcessor):
    """
    Parent processor that expects an extra kwarg: `payload`.
    In a real project this could be HTML, JSON, text, bytes, etc.
    """

    def process_item(self, item: str, payload: Optional[Any], iteration_index: int):
        # Use the extra arg however you like
        self.logger.info(f"[{iteration_index}] Processing {item}; has_payload={payload is not None}")

        # Do minimal "work" for demonstrational purpose: store something derived from the payload
        result = {
            "item": item,
            "payload_preview": str(payload)[:40],  # keep it tiny for docs
            "payload_length": len(str(payload)) if payload is not None else 0,
        }

        # Persist per-item result; the base class handles saving/resuming
        self.data[item] = result
```

#### `run_example.py`

```python
# run_example.py
from datetime import date
from typing import Any, List

from stateful_data_processor.file_rw import JsonFileRW
from processors import GenericAnalyzer

def build_payload(item: str) -> Any:
    """
    Stand-in for I/O or computation (e.g., HTTP GET, DB read, cache lookup).
    Keep it simple for the README.
    """
    return f"payload for {item}"

class UrlAnalyzer(GenericAnalyzer):
    """
    Child processor that *adds* the extra argument (`payload`)
    and forwards it to the parent via super().
    """
    def process_item(self, item: str, iteration_index: int):
        payload = build_payload(item)
        # Forward both the original item and the extra kwarg to the parent
        super().process_item(item=item, payload=payload, iteration_index=iteration_index)

if __name__ == "__main__":
    items: List[str] = ["AAPL", "MSFT", "GOOGL", "NVDA"]

    # Results are saved incrementally; reruns resume from where you stopped.
    out_file = JsonFileRW(f"./demo-analysis-{date.today()}.json")

    analyzer = UrlAnalyzer(json_file_writer=out_file)
    analyzer.run(items=items)

    # Access in-memory results if needed
    data = analyzer.data
    print(f"Processed {len(data)} items. Output file: {out_file.path}")
```

#### What this demonstrates

* The **parent** class `GenericAnalyzer` defines `process_item(self, item, payload, iteration_index)` — here, `payload` is an *extra* kwarg (analogous to the `soup` argument in your original `GurufocusAnalyzer`).
* The **child** class `UrlAnalyzer` overrides `process_item(self, item, iteration_index)`, computes the extra data (`payload = build_payload(item)`), and then **forwards** it with:

  ```python
  super().process_item(item=item, payload=payload, iteration_index=iteration_index)
  ```
* You can add **any keyword arguments** you need to the parent’s `process_item` (e.g., `html`, `row`, `features`, `raw_bytes`, `context`, etc.), and supply them from subclasses that know how to build/fetch them.
* All the usual benefits still apply: incremental processing, state persisted to disk, resumability after crashes or Ctrl+C, and a simple subclassing model.



## Releasing

``` bash
git tag x.y
tox
tox -e docs
tox -e build
tox -e publish -- --repository pypi --verbose
```

### Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see <https://pyscaffold.org/>.
