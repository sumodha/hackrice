
"""Simple CSV-backed DataFrame loader.

This module treats a single CSV file as the canonical dataset (a small local
"database") and loads it into a pandas DataFrame for easy querying.

Features:
- Load a CSV into memory as a single DataFrame.
- Optional schema coercion for common types.
- Optional cache to a Parquet file for faster reloads.
- Simple DataFrameDB class to manage a reloadable, in-memory DataFrame.

When to use this approach:
- Good for development, small-to-medium datasets that fit in memory,
  and when you primarily need fast in-memory queries.
- If you need concurrent writes, high-volume writes, or multi-process
  transactional access, consider using a proper DB (SQLite/Postgres).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class DataFrameDB:
    """Manage a CSV-backed DataFrame with optional Parquet caching.

    Typical usage:
        db = DataFrameDB(csv_path='data/programs.csv', cache_dir='data/cache')
        df = db.get_df()  # loads (from parquet cache if available)
        db.refresh()      # force reload from CSV
    """

    def __init__(self, csv_path: str | Path, *, cache_dir: Optional[str | Path] = None):
        self.csv_path = Path(csv_path)
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = self.csv_path.parent / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_path = self.cache_dir / (self.csv_path.stem + '.parquet')
        self._df: Optional[pd.DataFrame] = None

    def _default_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply light, safe cleaning to the DataFrame."""
        # Trim whitespace on string columns and convert empty strings to NA
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].astype(str).str.strip().replace({'': pd.NA, 'nan': pd.NA})
        return df

    def load_csv(self, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None) -> pd.DataFrame:
        """Load data from CSV, coerce according to dtype_map, clean, and cache to parquet.

        dtype_map: mapping column -> simple type string: 'int', 'float', 'str', 'bool', 'datetime', 'category'
        """
        if not self.csv_path.exists():
            raise FileNotFoundError(f'CSV not found: {self.csv_path}')

        # Read CSV (let pandas infer dtypes, safer than forcing to str always here)
        df = pd.read_csv(self.csv_path, parse_dates=parse_dates)

        df = self._default_clean(df)

        # Coerce types per dtype_map
        if dtype_map:
            for col, typ in dtype_map.items():
                if col not in df.columns:
                    logger.warning('Column %s not present in CSV; skipping coercion', col)
                    continue
                try:
                    if typ in ('int', 'integer'):
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
                    elif typ in ('float', 'double'):
                        df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
                    elif typ in ('bool', 'boolean'):
                        df[col] = df[col].astype(str).str.lower().map({'true': True, 'false': False, 'yes': True, 'no': False, '1': True, '0': False})
                        df[col] = df[col].astype('boolean')
                    elif typ in ('datetime', 'date'):
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    elif typ == 'category':
                        df[col] = df[col].astype('category')
                    else:
                        df[col] = df[col].astype('string')
                except Exception:
                    logger.exception('Failed to coerce column %s to %s; leaving as string', col, typ)
                    df[col] = df[col].astype('string')

        # Cache to parquet for faster subsequent loads
        try:
            df.to_parquet(self.parquet_path, index=False)
        except Exception:
            logger.exception('Failed to write parquet cache to %s', self.parquet_path)

        self._df = df
        return df

    def load_parquet(self) -> pd.DataFrame:
        """Load DataFrame from parquet cache. Raises if cache missing."""
        if not self.parquet_path.exists():
            raise FileNotFoundError(f'Parquet cache not found: {self.parquet_path}')
        df = pd.read_parquet(self.parquet_path)
        self._df = df
        return df

    def get_df(self, *, prefer_cache: bool = True, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None, copy: bool = True) -> pd.DataFrame:
        """Return the loaded DataFrame. If not loaded, try parquet cache then CSV.

        prefer_cache: if True load parquet cache when present for speed.
        dtype_map/parse_dates are forwarded to CSV loader if cache absent.
        copy: if True return a deep copy so callers cannot mutate internal state.
        """
        if self._df is not None:
            return self._get_df_copy() if copy else self._df

        # Try cache first
        if prefer_cache and self.parquet_path.exists():
            try:
                df = self.load_parquet()
                return df.copy(deep=True) if copy else df
            except Exception:
                logger.exception('Failed to load parquet cache; falling back to CSV')

        df = self.load_csv(dtype_map=dtype_map, parse_dates=parse_dates)
        return df.copy(deep=True) if copy else df

    def refresh(self, *, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None) -> pd.DataFrame:
        """Force reload from CSV and update cache and in-memory DataFrame."""
        return self.load_csv(dtype_map=dtype_map, parse_dates=parse_dates)

    # Note: This DataFrameDB is intentionally read-only with respect to the
    # canonical CSV file. We do NOT provide methods that write back to the CSV
    # to avoid accidental mutation of the source data. The only persistent
    # artifact we create is a local Parquet cache for faster reads; this cache
    # is considered a derived artifact and not the source-of-truth.

    def _get_df_copy(self) -> pd.DataFrame:
        """Return a defensive copy of the loaded DataFrame to prevent callers
        from accidentally modifying the internal cached DataFrame or the
        canonical CSV source."""
        if self._df is None:
            raise RuntimeError('No DataFrame loaded; call get_df() first')
        return self._df.copy(deep=True)


# Top-level convenience constructor
def make_db(csv_path: str | Path, cache_dir: Optional[str | Path] = None) -> DataFrameDB:
    """Convenience constructor for creating a DataFrameDB."""
    return DataFrameDB(csv_path, cache_dir=cache_dir)


