from __future__ import annotations

from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import pandas as pd

from src.models.welfare_program import WelfareProgram

logger = logging.getLogger(__name__)


_DEFAULT_COLUMN_ALIASES: Dict[str, List[str]] = {
    'name': ['name', 'program_name', 'title'],
    'description': ['description', 'desc', 'summary'],
    'min_age': ['min_age', 'minimum_age'],
    'max_age': ['max_age', 'maximum_age'],
    'citizenship': ['citizenship', 'is_citizen', 'citizen'],
    'address': ['address', 'has_address', 'stable_address'],
    'household_size': ['household_size', 'household'],
    'max_monthly_income': ['max_monthly_income', 'income_limit', 'monthly_income_limit'],
    'employment_required': ['employment_required', 'requires_employment', 'employment'],
    'disability_status': ['disability_status', 'disabled'],
    'veteran': ['veteran', 'is_veteran'],
    'criminal_record': ['criminal_record', 'has_criminal_record'],
    'child': ['child', 'has_child', 'children'],
    'refugee': ['refugee', 'is_refugee']
}


def _normalize(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    return str(s).strip().lower()


def _to_bool(val: Any) -> Optional[bool]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, bool):
        return val
    sval = str(val).strip().lower()
    if sval in ('true', 'yes', '1', 'y', 't'):
        return True
    if sval in ('false', 'no', '0', 'n', 'f'):
        return False
    return None


def _to_int(val: Any) -> Optional[int]:
    try:
        if val is None:
            return None
        if isinstance(val, (int,)):
            return int(val)
        if isinstance(val, float) and pd.isna(val):
            return None
        return int(float(str(val).strip()))
    except Exception:
        return None


class WelfareService:
    """Service that maps program names to WelfareProgram model instances.

    Usage:
        svc = WelfareService(csv_path='data/welfare_programs.csv')
        programs = svc.get_programs_by_name(['SNAP', 'Medicaid'])
    """

    def __init__(self, csv_path: Optional[str | Path] = None, *, df: Optional[pd.DataFrame] = None, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None):
        """Construct a WelfareService.

        You can provide either a pre-loaded DataFrame via `df` (useful for tests),
        or a `csv_path` to load directly. `dtype_map` and `parse_dates` are
        forwarded to the CSV loader for optional coercion.
        """
        self._dtype_map = dtype_map
        self._parse_dates = parse_dates
        if df is not None:
            # accept an injected DataFrame (copy to avoid caller mutations)
            self._df = df.copy(deep=True)
        else:
            if not csv_path:
                raise ValueError('csv_path is required when df is not provided')
            self._csv_path = Path(csv_path)
            self._df = self._load_csv(self._csv_path, dtype_map=dtype_map, parse_dates=parse_dates)

    def _find_column(self, df: pd.DataFrame, logical_name: str) -> Optional[str]:
        """Find best matching column name in df for a logical field name."""
        aliases = _DEFAULT_COLUMN_ALIASES.get(logical_name, [logical_name])
        df_cols = {c.lower(): c for c in df.columns}
        for a in aliases:
            if a.lower() in df_cols:
                return df_cols[a.lower()]
        return None

    def _default_clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Light cleaning similar to DataFrameDB._default_clean: trim strings and normalize empty to NA."""
        for col in df.select_dtypes(include=['object', 'string']).columns:
            df[col] = df[col].astype(str).str.strip().replace({'': pd.NA, 'nan': pd.NA})
        return df

    def _load_csv(self, csv_path: Path, *, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None) -> pd.DataFrame:
        if not csv_path.exists():
            raise FileNotFoundError(f'CSV not found: {csv_path}')

        df = pd.read_csv(csv_path, parse_dates=parse_dates)
        df = self._default_clean(df)

        # minimal coercion: mirror essential behaviors from DataFrameDB for ints/floats/bools/datetime
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

        return df

    def _row_to_model(self, row: pd.Series) -> WelfareProgram:
        # Build kwargs mapping for the WelfareProgram model
        df = row
        kwargs: Dict[str, Any] = {}

        # name & description
        kwargs['name'] = row.get(self._find_column(row.to_frame().T, 'name')) or row.get('name') or ''
        kwargs['description'] = row.get(self._find_column(row.to_frame().T, 'description')) or ''

        # numeric / optional fields
        kwargs['min_age'] = _to_int(row.get(self._find_column(row.to_frame().T, 'min_age')))
        kwargs['max_age'] = _to_int(row.get(self._find_column(row.to_frame().T, 'max_age')))
        # booleans
        # Citizenship: parse as Optional[bool]
        cit_col = self._find_column(row.to_frame().T, 'citizenship')
        cit_val = row.get(cit_col) if cit_col else None
        kwargs['citizenship'] = _to_bool(cit_val)

        kwargs['address'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'address')))
        # household_size in model is Optional[bool]; parse as boolean-like value
        hs = row.get(self._find_column(row.to_frame().T, 'household_size'))
        kwargs['household_size'] = _to_bool(hs)

        # refugee flag (new in model)
        kwargs['refugee'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'refugee')))

        kwargs['max_monthly_income'] = _to_int(row.get(self._find_column(row.to_frame().T, 'max_monthly_income')))
        kwargs['employment_required'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'employment_required')))
        kwargs['disability_status'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'disability_status')))
        kwargs['veteran'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'veteran')))
        kwargs['criminal_record'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'criminal_record')))
        kwargs['child'] = _to_bool(row.get(self._find_column(row.to_frame().T, 'child')))

        # Ensure required types align with Pydantic model expectations
        return WelfareProgram(**kwargs)

    def get_programs_by_name(self, names: List[str], *, include_missing: bool = False) -> List[WelfareProgram]:
        """Return list of WelfareProgram instances matching any of the provided names.

        Args:
            names: list of program names to look up (case-insensitive)
            include_missing: if True, returns placeholder WelfareProgram objects for names not found
        """
        if not names:
            return []

        df = self._df.copy(deep=True)

        # prepare normalized map of df names to rows
        name_col = self._find_column(df, 'name') or 'name'
        if name_col not in df.columns:
            raise RuntimeError(f'Name column not found in CSV (looked for {name_col})')

        # build lookup: normalized name -> first matching row index
        lookup: Dict[str, int] = {}
        for idx, val in df[name_col].items():
            if pd.isna(val):
                continue
            lookup[_normalize(val)] = idx

        out: List[WelfareProgram] = []
        for q in names:
            qnorm = _normalize(q) or ''
            if qnorm in lookup:
                row = df.loc[lookup[qnorm]]
                try:
                    out.append(self._row_to_model(row))
                except Exception:
                    logger.exception('Failed to convert row for program %s', q)
            else:
                logger.debug('Program not found: %s', q)
                if include_missing:
                    out.append(WelfareProgram(name=q, description=''))

        return out

    def get_programs_by_name_dicts(self, names: List[str], *, include_missing: bool = False) -> List[Dict[str, Any]]:
        """Return list of programs as plain dictionaries with the same fields as WelfareProgram.

        This method preserves the exact content that would be present on the Pydantic
        `WelfareProgram` instances but returns plain dicts (useful for JSON serialization
        or APIs that expect raw dicts).
        """
        progs = self.get_programs_by_name(names, include_missing=include_missing)
        # Use Pydantic's .dict() to produce the same field set and types
        return [p.dict() for p in progs]


def make_service(csv_path: Optional[str | Path] = None, *, df: Optional[pd.DataFrame] = None, dtype_map: Optional[Dict[str, str]] = None, parse_dates: Optional[list[str]] = None) -> WelfareService:
    return WelfareService(csv_path=csv_path, df=df, dtype_map=dtype_map, parse_dates=parse_dates)
