import logging
import multiprocessing
import os
import time
import unittest
from typing import Any, List
from unittest.mock import MagicMock, call

from stateful_data_processor.file_rw import JsonFileRW
from stateful_data_processor.processor import StatefulDataProcessor
from utils import TEST_FILE_JSON_PATH, wait_for_file


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


class SymbolProcessor(StatefulDataProcessor):
    """
    This class processes a list of symbols.
    """

    def process_item(
        self, item: str, iteration_index: int, delay=0.0, *args: Any, **kwargs: Any
    ) -> None:
        processed = item + "!"
        self.data[item] = processed
        time.sleep(delay)


class NumberProcessor(StatefulDataProcessor):
    LOOKUP = ["a", "b", "c", "d"]

    def process_item(
        self, item: int, iteration_index: int, delay=0.0, *args: Any, **kwargs: Any
    ) -> None:
        '''
            Process an item by squaring it and adding the corresponding letter from the lookup.
        Note: the item and iteration_index are coming from the process_data method.
        delay is an argument that must be supplied by the user through the run method.
        '''
        processed = NumberProcessor.LOOKUP[iteration_index] + str(item ** 2)
        self.data[item] = processed
        time.sleep(delay)


class TestStatefulDataProcessor(unittest.TestCase):
    def setUp(self):
        self.file_rw = JsonFileRW(TEST_FILE_JSON_PATH)
        self.mock_logger = MagicMock()

    def tearDown(self) -> None:
        self.mock_logger.reset_mock()
        if os.path.exists(TEST_FILE_JSON_PATH):
            os.remove(TEST_FILE_JSON_PATH)
        del self.file_rw

    def test_items_must_be_unique(self):
        processor = SymbolProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger
        )
        processor.run(items=["a", "a", "b"], delay=0)
        calls = [
            call("Items must be unique."),
        ]
        self.mock_logger.error.assert_has_calls(calls, any_order=True)

    def test_process_data(self):
        processor = SymbolProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger
        )
        processor.run(items=["a", "b", "c"], delay=0)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        calls = [
            call("Processed item a 1 / 3"),
            call("Processed item b 2 / 3"),
            call("Processed item c 3 / 3"),
            call("Finished processing all items. 3 / 3 items processed."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
        wait_for_file(TEST_FILE_JSON_PATH)

    def test_processes_data_and_retrieves_completed_state_after_deletion(self):
        processor = SymbolProcessor(self.file_rw, should_read=False)
        processor.run(items=["a", "b", "c"], delay=0)

        wait_for_file(TEST_FILE_JSON_PATH)
        del processor

        processor = SymbolProcessor(
            self.file_rw, should_read=True, logger=self.mock_logger
        )
        calls = [call(f"Read from file: {TEST_FILE_JSON_PATH} data of len 3")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        # also test that the files contains the right data
        data = self.file_rw.read()
        self.assertEqual(data, {"a": "a!", "b": "b!", "c": "c!"})

    def test_skip_already_processed_items(self):
        processor = SymbolProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger
        )
        processor.run(items=["a", "b", "c"], delay=0)
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        processor.run(items=["a", "b", "c"], delay=0)
        calls = [call("All items already processed, skipping...")]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)

    def test_resumes_after_termination_with_saved_state(self):
        log_queue = multiprocessing.Queue()

        # Create a logger
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.INFO)
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        symbol_processor = SymbolProcessor(
            self.file_rw, should_read=False, logger=logger
        )

        # Add a large enough delay to ensure the process is terminated before it processes another item

        p = multiprocessing.Process(
            target=symbol_processor.run, kwargs={"items": ["a", "b", "c"], "delay": 5}
        )
        p.start()

        # wait for process to start and process one item
        time.sleep(0.5)
        p.terminate()

        wait_for_file(TEST_FILE_JSON_PATH)

        self.assertEqual(self.file_rw.read(), {"a": "a!"})

        # Process log messages from the queue
        while not log_queue.empty():
            log_message = log_queue.get()
            self.mock_logger.info(log_message)
        calls = [
            call("Interrupt signal received, saving data..."),
            call("Data saved, exiting."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)

        processor = SymbolProcessor(
            self.file_rw, should_read=True, logger=self.mock_logger
        )
        processor.run(items=["a", "b", "c"], delay=0)
        calls = [
            call("Item a already processed, skipping..."),
            call("Processed item b 2 / 3"),
            call("Processed item c 3 / 3"),
            call("Finished processing all items. 3 / 3 items processed."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)

    def test_number_processor_print_interval(self):
        processor = NumberProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger, print_interval=2
        )
        processor.run(items=[1, 2, 3, 4], delay=0)
        self.assertEqual(processor.data, {1: "a1", 2: "b4", 3: "c9", 4: "d16"})

        calls = [
            call("Processed item 1 1 / 4"),
            call("Processed item 3 3 / 4"),
            call("Finished processing all items. 4 / 4 items processed."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)

    def test_number_processor_skip_list(self):
        skip_list = [2, 4, 7]
        processor = NumberProcessor(
            self.file_rw, should_read=False, logger=self.mock_logger, skip_list=skip_list
        )
        processor.run(items=[1, 2, 3, 4, 7], delay=0)
        self.assertEqual(processor.data, {1: "a1", 3: "c9"})

        calls = [
            call("Processed item 1 1 / 5"),
            call("Item 2 in skip list, skipping..."),
            call("Processed item 3 3 / 5"),
            call("Item 4 in skip list, skipping..."),
            call("Item 7 in skip list, skipping..."),
            call("Finished processing all items. 2 / 5 items processed."),
        ]
        self.mock_logger.info.assert_has_calls(calls, any_order=True)
