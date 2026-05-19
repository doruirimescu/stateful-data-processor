from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger
from typing import Any, Collection, Optional

from stateful_data_processor.file_rw import FileRW
from stateful_data_processor.processor import StatefulDataProcessor


class ParallelStatefulDataProcessor(StatefulDataProcessor):
    """
    Processes items in parallel using a thread pool.

    Items not yet processed are distributed across n_workers threads. Results
    accumulate in self.data as workers finish; the file is written once by the
    base run() method after all workers complete (or on interrupt/exception).

    CPython note: self.data[item] = value inside process_item is safe across
    threads because GIL-protected dict assignments on distinct keys do not race.
    """

    def __init__(
        self,
        file_rw: FileRW,
        n_workers: int = 4,
        logger: Optional[Logger] = None,
        should_read: Optional[bool] = True,
        print_interval: Optional[int] = 1,
        skip_list: Optional[Collection[Any]] = None,
        should_reprocess: Optional[bool] = False,
        verbose_skip: bool = False,
    ):
        super().__init__(
            file_rw=file_rw,
            logger=logger,
            should_read=should_read,
            print_interval=print_interval,
            skip_list=skip_list,
            should_reprocess=should_reprocess,
            verbose_skip=verbose_skip,
        )
        self.n_workers = n_workers

    def process_data(self, items: Collection[Any], *args, **kwargs):
        items_list = list(items)
        items_len = len(items_list)

        pending, already_processed, skip_listed = [], [], []
        for item in items_list:
            if self.skip_list and item in self.skip_list:
                skip_listed.append(item)
            elif item in self.data and not self.should_reprocess:
                already_processed.append(item)
            else:
                pending.append(item)

        if not pending and not skip_listed:
            self.logger.info("All items already processed, skipping...")
            return

        for item in skip_listed:
            self.logger.info(f"Item {item} in skip list, skipping...")

        if already_processed:
            if self.verbose_skip:
                for item in already_processed:
                    self.logger.info(f"Item {item} already processed, skipping...")
            else:
                self.logger.info(f"Skipped {len(already_processed)} already processed items.")

        if pending:
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                futures = {
                    executor.submit(self._process_one, item, idx, *args, **kwargs): item
                    for idx, item in enumerate(pending)
                }
                for future in as_completed(futures):
                    future.result()

        self.logger.info(
            f"Finished processing all items. {len(self.data)} / {items_len} items processed."
        )

    def _process_one(self, item: Any, idx: int, *args: Any, **kwargs: Any):
        if self.should_reprocess and item in self.data:
            self.reprocess_item(item, idx, *args, **kwargs)
        else:
            self.process_item(item, idx, *args, **kwargs)
        self.logger.info(f"Processed item {item}")
