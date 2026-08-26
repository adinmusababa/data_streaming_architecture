"""
CSV Reader — reads CSV files in batches asynchronously.

Maps each row to a dict and hands them up to the streaming orchestrator
for conversion into the standard StreamMessage payload.
"""

from __future__ import annotations

import asyncio
import csv
import io
from pathlib import Path
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor

from shared_sdk.logger import get_logger

logger = get_logger("csv_reader")


class CsvReader:
    """Reads a CSV file in batches, yielding rows as dicts.

    Usage::

        reader = CsvReader("sample_data/sample.csv")
        reader.open()
        for batch in reader.read_batch(10):
            ...  # list[dict]
        reader.close()
    """

    def __init__(self, file_path: str | Path) -> None:
        self._path = Path(file_path).resolve()
        self._file: io.TextIOWrapper | None = None
        self._reader: csv.DictReader | None = None
        self._total_rows: int = 0
        self._read_so_far: int = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="csv")
        self._columns: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def file_path(self) -> Path:
        """Resolved path to the CSV file."""
        return self._path

    @property
    def columns(self) -> list[str]:
        """Column names from the CSV header."""
        return list(self._columns)

    @property
    def row_count(self) -> int:
        """Number of rows already read (cumulative)."""
        return self._read_so_far

    @property
    def total_estimated(self) -> int:
        """Total rows in the file (best-effort count at open time)."""
        return self._total_rows

    def open(self) -> None:
        """Open the CSV file and read the header."""
        if not self._path.exists():
            raise FileNotFoundError(f"CSV not found: {self._path}")

        self._file = self._path.open("r", encoding="utf-8-sig", newline="")
        self._reader = csv.DictReader(self._file)
        self._columns = self._reader.fieldnames or []
        logger.info(
            "CSV file opened",
            file=str(self._path),
            columns=self._columns,
        )

        # Quick first pass — count total rows for progress reporting
        # (runs in executor so it doesn't block the event loop)
        self._total_rows = self._count_lines()

    async def read_batch(self, batch_size: int = 100) -> list[dict[str, Any]]:
        """Read up to *batch_size* rows as dicts.

        Runs the actual CSV iteration in a thread-pool executor so the
        event loop stays responsive.
        """
        if self._reader is None:
            raise RuntimeError("Reader not opened — call .open() first")

        loop = asyncio.get_running_loop()
        rows: list[dict[str, Any]] = await loop.run_in_executor(
            self._executor,
            self._read_batch_sync,
            batch_size,
        )
        self._read_so_far += len(rows)
        return rows

    def close(self) -> None:
        """Close the CSV file and shut down the executor."""
        self._executor.shutdown(wait=False)
        if self._file and not self._file.closed:
            self._file.close()
            self._file = None
            self._reader = None
            logger.info("CSV file closed", file=str(self._path))

    def __enter__(self) -> "CsvReader":
        self.open()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_batch_sync(self, batch_size: int) -> list[dict[str, Any]]:
        """Synchronous batch-read (runs in executor thread)."""
        rows: list[dict[str, Any]] = []
        for _ in range(batch_size):
            try:
                row = next(self._reader)  # type: ignore[arg-type]
            except StopIteration:
                break
            rows.append(dict(row))
        return rows

    def _count_lines(self) -> int:
        """Count rows in the file (minus header). Quick estimate."""
        try:
            with self._path.open("r", encoding="utf-8-sig") as f:
                return sum(1 for _ in f) - 1
        except Exception:
            return 0


