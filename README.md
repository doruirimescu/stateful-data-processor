![Python](https://img.shields.io/badge/-Python-05122A?style=flat&logo=python)
[![PyPI-Server](https://img.shields.io/pypi/v/stateful-data-processor.svg)](https://pypi.org/project/stateful-data-processor/)
[![Coverage..](https://coveralls.io/repos/github/doruirimescu/stateful-data-processor/badge.svg?branch=master)](https://coveralls.io/github/doruirimescu/stateful-data-processor?branch=master)
![Pipeline status](https://github.com/doruirimescu/stateful-data-processor/actions/workflows/main.yml/badge.svg?branch=master)
[![Monthly Downloads](https://pepy.tech/badge/stateful-data-processor/month)](https://pepy.tech/project/stateful-data-processor)
[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# stateful-data-processor

**stateful-data-processor** is a utility designed to handle large
amounts of data incrementally. It allows you to process data
step-by-step, saving progress to avoid data loss in case of
interruptions or errors. The processor can be subclassed to implement
custom data processing logic.

## Features

-   Incrementally process large datasets.
-   Save the processing state to a file.
-   Resume the processing state and skip already processed items
    automatically
-   Handle SIGINT and SIGTERM signals for graceful shutdown and state
    saving.
-   Easily subclass to implement custom data processing.
-   Reprocess items that were already stored into a file (explore
    alternative processing on cached data).

### Problem

You have a large amount of data that you want to loop through and
process incrementally. Processing takes time, and in case an error
occurs, you do not want to lose all the progress. You want to save the
data to a file and be able to continue processing from where you left
off. You also want to be able to interrupt the processing with a SIGINT
signal and save the data to the file. You want to be able to subclass
the processor and implement the process_data and process_item methods.
You want to be able to iterate through items and process them one by
one.

### Solution

**StatefulDataProcessor** class to process data incrementally:

-   **Incremental Processing**: Process large amounts of data in a JSON
    file incrementally.
-   **Data Storage**: The data is stored in a dictionary, and the
    processor keeps track of the current step being processed.
-   **Graceful Interruption**: The processor can be interrupted with a
    SIGINT or SIGTERM signal, and the data will be saved to the file.
-   **Subclassing**: The processor is meant to be subclassed, and the
    [process_item]{.title-ref} method should be implemented.
-   **Item Processing**: The [process_item]{.title-ref} is being called
    with all arguments forwarded from [run]{.title-ref}, except for
    [items]{.title-ref}, which is unpacked and iterated item by item.
-   **Unique Labels**: The data is be stored in a dictionary using
    unique labels corresponding to [items]{.title-ref}. Thus, each
    [item]{.title-ref} must be unique.
-   **Customization**: The [process_data]{.title-ref} method can be
    overridden for more customized processing of the items.

## Usage

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
     time.sleep(delay)

# Example usage
file_rw = FileRW('data.json')
processor = MyDataProcessor(file_rw)

items_to_process = [1, 2, 3, 4, 5]
processor.run(items=items_to_process, delay=1.5)
```

The processor will handle SIGINT and SIGTERM signals to save the current
state before exiting. Run your processor, and use Ctrl+C to send a
SIGINT signal. When you run again, the processing will pick up from
where you left off. A logger is automatically created if you do not
inject it into the constructor.

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
