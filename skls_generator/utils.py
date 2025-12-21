import os
from pathlib import Path
import time
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor
from pyparsing import wraps
from tqdm import tqdm


def measure_time(logger, precision=6, prefix=""):
    """
    Decorator factory that accepts arguments.
    Usage: @measure_time(logger, precision=3, prefix="Processing: ")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            logger.info(f"{prefix}{func.__name__} took {end - start:.{precision}f} seconds")
            return result
        return wrapper
    return decorator


def apply_to_all_files(
    folder_path: str,
    func: Callable[[str], Any],
    max_workers: int = 5,
    chunksize: int = 1,
) -> None:
    """
    Recursively apply a function to every file in a directory, in parallel using threads, with a progress bar.

    Args:
        folder_path (str): Path to the root folder.
        func (Callable[[str], Any]): Function to apply. It will be called as func(file_path).
        max_workers (int, optional): Number of worker threads. If None, uses os.cpu_count().
        chunksize (int): This parameter is kept for API compatibility but not used in threading.
    """
    root = Path(folder_path)
    if not root.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Collect all file paths first
    file_paths = [str(p) for p in root.rglob("*") if p.is_file()]

    if not file_paths:
        print(f"No files found in '{folder_path}'.")
        return

    # Use ThreadPoolExecutor with tqdm for progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(func, file_path) for file_path in file_paths]

        # Use tqdm to show progress as tasks complete
        for _ in tqdm(futures, total=len(file_paths), desc="Processing files", unit="file"):
            pass  # We just need to wait for all futures to complete

        # If you need to collect results, you can get them like this:
        # results = [future.result() for future in futures]
