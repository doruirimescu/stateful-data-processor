from abc import abstractmethod
from logging import Logger, getLogger
import signal
from stateful_data_processor.file_rw import FileRW
from typing import Optional, Any, Collection


"""
Problem: let's say you have a large amount of data, that you want to loop through and process incrementally.
Processing takes time, and in case an error occurs, you do not want to lose all the progress.
You want to save the data to a file and be able to continue processing from where you left off.
You also want to be able to interrupt the processing with a SIGINT signal and save the data to the file.
You want to be able to subclass the processor and implement the process_data and process_item methods.
You want to be able to iterate through items and process them one by one.

StatefulDataProcessor class to process data incrementally.
    Process large amounts of data in a JSON file incrementally.
    The data is stored in a dictionary and the processor keeps track of the current step being processed.
    The processor can be interrupted with a SIGINT or SIGTERM signal and the data will be saved to the file.
    The processor is meant to be subclassed and the process_data method should be implemented.
    The process_item method should be implemented to process a single item, if _iterate_items is used.
"""


class StatefulDataProcessor:
    def __init__(
        self,
        file_rw: FileRW,
        logger: Optional[Logger] = None,
        should_read: Optional[bool] = True,
        print_interval: Optional[int] = 1,
        skip_list: Optional[Collection[Any]] = None,
    ):
        self.file_rw = file_rw
        self.print_interval = print_interval
        self.skip_list = skip_list
        if logger is None:
            self.logger = getLogger("StatefulDataProcessor")
        else:
            self.logger = logger

        if should_read:
            try:
                self.data = file_rw.read()
                self.logger.info(
                    f"Read from file: {self.file_rw.file_name} data of len {len(self.data)}"
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to read from file: {self.file_rw.file_name}, starting with empty data."
                )
                self.data = {}
        else:
            self.data = {}

        # Setup the signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    @abstractmethod
    def process_data(self, items: Collection[Any], *args, **kwargs):
        """Template method for processing data. Get data, and call _iterate_items.
        Arguments are forwarded to _iterate_items. You can override this method to implement
        more custom processing."""
        self._iterate_items(items, *args, **kwargs)

    def _iterate_items(self, items: Collection[Any], *args, **kwargs):
        """General iteration method for processing items. This should be called from process_data.
        This method will iterate through the items and call process_item for each item.
        If an item is already processed, it will skip it.
        Arguments are forwarded to process_item."""

        items_len = len(items)
        if len(self.data) == items_len:
            self.logger.info("All items already processed, skipping...")
            return

        for iteration_index, item in enumerate(items):
            if item in self.data:
                self.logger.info(f"Item {item} already processed, skipping...")
                continue

            if self.skip_list and item in self.skip_list:
                self.logger.info(f"Item {item} in skip list, skipping...")
                continue

            self.process_item(item, iteration_index, *args, **kwargs)
            if (iteration_index) % self.print_interval == 0:
                self.logger.info(f"Processed item {item} {iteration_index + 1} / {items_len}")
        self.logger.info(f"Finished processing all items. {len(self.data)} / {items_len} items processed.")

    @abstractmethod
    def process_item(
        self, item: Any, iteration_index: int, *args: Any, **kwargs: Any
    ) -> Any:
        """Process a single item."""
        pass

    def _signal_handler(self, signum, frame):
        """Handles the SIGINT signal."""
        self.logger.info("Interrupt signal received, saving data...")
        self.file_rw.write(self.data)
        self.logger.info("Data saved, exiting.")
        exit(0)

    def run(self, items: Collection[Any], *args, **kwargs):
        """Main method to run the processor."""
        if not items:
            self.logger.error("No items to process.")
            return

        if len(list(set(items))) != len(list(items)):
            self.logger.error("Items must be unique.")
            return

        try:
            self.process_data(items, *args, **kwargs)
        except Exception as e:
            raise e
        self.file_rw.write(self.data)
