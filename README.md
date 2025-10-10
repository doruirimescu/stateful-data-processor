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

## Installation

You can install **stateful-data-processor** using pip:

``` bash
pip install stateful-data-processor
```

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
