import os
import time
import unittest
from typing import Any
from unittest.mock import MagicMock, call

from stateful_data_processor.file_rw import JsonFileRW
from stateful_data_processor.parallel_processor import ParallelStatefulDataProcessor
from utils import TEST_FILE_JSON_PATH, wait_for_file


class SlowProcessor(ParallelStatefulDataProcessor):
    def process_item(self, item: str, iteration_index: int, delay: float = 0.0, **kwargs) -> None:
        time.sleep(delay)
        self.data[item] = item + "!"


class TestParallelStatefulDataProcessor(unittest.TestCase):
    def setUp(self):
        self.file_rw = JsonFileRW(TEST_FILE_JSON_PATH)
        self.mock_logger = MagicMock()

    def tearDown(self):
        self.mock_logger.reset_mock()
        if os.path.exists(TEST_FILE_JSON_PATH):
            os.remove(TEST_FILE_JSON_PATH)

    def test_processes_all_items(self):
        processor = SlowProcessor(self.file_rw, n_workers=4, should_read=False, logger=self.mock_logger)
        processor.run(items=["a", "b", "c", "d", "e"])
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!", "d": "d!", "e": "e!"})
        wait_for_file(TEST_FILE_JSON_PATH)

    def test_parallel_is_faster_than_sequential(self):
        items = [str(i) for i in range(8)]
        delay = 0.1

        start = time.time()
        processor = SlowProcessor(self.file_rw, n_workers=4, should_read=False)
        processor.run(items=items, delay=delay)
        parallel_duration = time.time() - start

        # Sequential would take 8 * 0.1 = 0.8s; parallel with 4 workers should be ~0.2s
        self.assertLess(parallel_duration, 0.5)

    def test_skips_already_processed_items(self):
        processor = SlowProcessor(self.file_rw, n_workers=2, should_read=False, logger=self.mock_logger)
        processor.run(items=["a", "b", "c"])
        self.assertEqual(processor.data, {"a": "a!", "b": "b!", "c": "c!"})

        processor2 = SlowProcessor(self.file_rw, n_workers=2, should_read=True, logger=self.mock_logger)
        processor2.run(items=["a", "b", "c", "d"])
        self.assertEqual(processor2.data, {"a": "a!", "b": "b!", "c": "c!", "d": "d!"})
        self.mock_logger.info.assert_any_call("Skipped 3 already processed items.")

    def test_verbose_skip(self):
        processor = SlowProcessor(self.file_rw, n_workers=2, should_read=False, logger=self.mock_logger)
        processor.run(items=["a", "b"])

        processor2 = SlowProcessor(
            self.file_rw, n_workers=2, should_read=True,
            logger=self.mock_logger, verbose_skip=True
        )
        processor2.run(items=["a", "b", "c"])
        self.mock_logger.info.assert_any_call("Item a already processed, skipping...")
        self.mock_logger.info.assert_any_call("Item b already processed, skipping...")

    def test_skip_list(self):
        processor = SlowProcessor(
            self.file_rw, n_workers=2, should_read=False,
            logger=self.mock_logger, skip_list=["b", "d"]
        )
        processor.run(items=["a", "b", "c", "d", "e"])
        self.assertEqual(processor.data, {"a": "a!", "c": "c!", "e": "e!"})
        self.mock_logger.info.assert_any_call("Item b in skip list, skipping...")
        self.mock_logger.info.assert_any_call("Item d in skip list, skipping...")

    def test_all_items_already_processed(self):
        processor = SlowProcessor(self.file_rw, n_workers=2, should_read=False, logger=self.mock_logger)
        processor.run(items=["a", "b", "c"])

        processor2 = SlowProcessor(self.file_rw, n_workers=2, should_read=True, logger=self.mock_logger)
        processor2.run(items=["a", "b", "c"])
        self.mock_logger.info.assert_any_call("All items already processed, skipping...")

    def test_exception_saves_partial_state(self):
        class FlakyProcessor(ParallelStatefulDataProcessor):
            def process_item(self, item, iteration_index, **kwargs):
                if item == "c":
                    raise ValueError("boom")
                self.data[item] = item + "!"

        processor = FlakyProcessor(self.file_rw, n_workers=2, should_read=False)
        with self.assertRaises(ValueError):
            processor.run(items=["a", "b", "c", "d", "e"])

        saved = self.file_rw.read()
        self.assertNotIn("c", saved)
        self.assertTrue(len(saved) > 0)
