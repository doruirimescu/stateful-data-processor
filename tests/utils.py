import os
import time
from pathlib import Path

__CURRENT_FILE_PATH = Path(__file__).parent
TEST_FILE_JSON_PATH = __CURRENT_FILE_PATH / "test.json"

def wait_for_file(file_path: str):
    n_retries = 10
    for _ in range(n_retries):
        if os.path.exists(file_path):
            break
        time.sleep(0.25)
    else:
        raise Exception(f"File {file_path} does not exist.")
