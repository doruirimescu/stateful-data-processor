import unittest
import os
from stateful_data_processor.file_rw import JsonFileRW
from utils import TEST_FILE_JSON_PATH, wait_for_file

class TestJsonFileRW(unittest.TestCase):
    def setUp(self):
        self.file_rw = JsonFileRW(TEST_FILE_JSON_PATH)

    def test_read(self):
        data = self.file_rw.read()
        self.assertEqual(data, {})

    def test_write(self):
        data = {"key": "value"}
        self.file_rw.write(data)
        read_data = self.file_rw.read()
        self.assertEqual(data, read_data)
        wait_for_file(TEST_FILE_JSON_PATH)

    def tearDown(self):
        if os.path.exists(TEST_FILE_JSON_PATH):
            os.remove(TEST_FILE_JSON_PATH)
