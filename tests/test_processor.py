import unittest
from typing import List, Any
import os
import multiprocessing
from pathlib import Path
import time
from stateful_data_processor.processor import StatefulDataProcessor
from stateful_data_processor.file_rw import JsonFileRW
from unittest.mock import MagicMock, call

import logging
class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends log messages to a multiprocessing queue.
    """
    def __init__(self, log_queue: multiprocessing.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            self.log_queue.put(self.format(record))
        except Exception:
            self.handleError(record)


CURRENT_FILE_PATH = Path(__file__).parent
FILE_JSON_PATH = CURRENT_FILE_PATH / "test.json"

def wait_for_file(file_path: str):
    n_retries = 10
    for _ in range(n_retries):
        if os.path.exists(file_path):
            break
        time.sleep(0.25)
    else:
        raise Exception(f"File {file_path} does not exist.")

class SymbolGetter:
    """
    This class could be a complex class that gets a list of data from a database or API.
    """

    def get_symbols(self) -> List[str]:
        return ["a", "b", "c"]


class SymbolProcessor(StatefulDataProcessor):
    """
    This class processes a list of symbols.
    """
    def process_data(self, symbol_getter: SymbolGetter, delay: float = 0.0):
        symbols = symbol_getter.get_symbols()
        self.iterate_items(symbols, delay)

    def process_item(self, item: str, delay=0.0, *args: Any, **kwargs: Any) -> None:
        processed = item + "!"
        self.data[item] = processed
        time.sleep(delay)


class TestStatefulDataProcessor(unittest.TestCase):
    def setUp(self):
        self.file_rw = JsonFileRW(FILE_JSON_PATH)
        self.mock_logger = MagicMock()

    def tearDown(self) -> None:
        self.mock_logger.reset_mock()
        if os.path.exists(FILE_JSON_PATH):
            os.remove(FILE_JSON_PATH)
        del self.file_rw

    def test_process_data(self):
        processor = SymbolProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger
        )
        processor.run(symbol_getter=SymbolGetter(), delay=0)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        calls = [
            call("Processed item a 1 / 3"),
            call("Processed item b 2 / 3"),
            call("Processed item c 3 / 3"),
            call("Finished processing all items."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
        wait_for_file(FILE_JSON_PATH)

    def test_processes_data_and_retrieves_completed_state_after_deletion(self):
        processor = SymbolProcessor(
            self.file_rw, should_read=False
        )
        processor.run(symbol_getter=SymbolGetter(), delay=0)

        wait_for_file(FILE_JSON_PATH)
        del processor

        processor = SymbolProcessor(self.file_rw, should_read=True, logger=self.mock_logger)
        calls = [call(f"Read from file: {FILE_JSON_PATH} data of len 3")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        # also test that the files contains the right data
        data = self.file_rw.read()
        self.assertEqual(data, {"a": "a!", "b": "b!", "c": "c!"})

    def test_skip_already_processed_items(self):
        processor = SymbolProcessor(self.file_rw, should_read=False, logger=self.mock_logger)
        processor.run(symbol_getter=SymbolGetter(), delay=0)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        processor.run(symbol_getter=SymbolGetter(), delay=0)
        calls = [call("All items already processed, skipping...")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)


    def test_resumes_after_termination_with_saved_state(self):
        log_queue = multiprocessing.Queue()

        # Create a logger
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        symbol_processor = SymbolProcessor(self.file_rw, should_read=False, logger=logger)

        # Add a large enough delay to ensure the process is terminated before it processes another item

        p = multiprocessing.Process(target=symbol_processor.run, kwargs={"symbol_getter": SymbolGetter(), "delay": 5})
        p.start()

        # wait for process to start and process one item
        time.sleep(0.5)
        p.terminate()

        wait_for_file(FILE_JSON_PATH)

        self.assertEqual(self.file_rw.read(), {"a": "a!"})

        # Process log messages from the queue
        while not log_queue.empty():
            log_message = log_queue.get()
            self.mock_logger.info(log_message)
        calls=[call("Interrupt signal received, saving data..."),
               call("Data saved, exiting.")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)

        processor = SymbolProcessor(self.file_rw, should_read=True, logger=self.mock_logger)
        processor.run(symbol_getter=SymbolGetter(), delay=0)
        calls = [call("Item a already processed, skipping..."),
                 call("Processed item b 2 / 3"),
                 call("Processed item c 3 / 3"),
                 call("Finished processing all items.")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
