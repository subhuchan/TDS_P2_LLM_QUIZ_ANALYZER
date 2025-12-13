# Design Document

## Overview

This design addresses 34 failing unit tests by fixing test-implementation mismatches, adding missing methods, and correcting edge case handling. The approach prioritizes minimal changes to preserve existing functionality while ensuring test compatibility.

## Architecture

### Component Structure

```
tests/
├── test_web_scraper.py      → Fix mocking strategy (httpx → aiohttp)
├── test_data_processor.py   → Fix mocks, add missing methods
└── test_analysis_engine.py  → Fix method signatures, edge cases

src/
├── web_scraper.py           → No changes needed (already uses aiohttp)
├── data_processor.py        → Add missing methods, update signatures
└── analysis_engine.py       → Add missing methods, fix edge cases
```

### Design Principles

1. **Test-First Alignment**: Modify implementations to match test expectations
2. **Backward Compatibility**: Preserve existing method behavior
3. **Minimal Changes**: Only fix what's broken
4. **Edge Case Handling**: Add proper validation for single-row and uniform datasets

## Components and Interfaces

### 1. WebScraper Test Fixes

**Problem**: Tests mock `httpx` but implementation uses `aiohttp`

**Solution**: Update test mocks to use `aiohttp.ClientSession`

**Changes Required**:
- Replace `httpx.AsyncClient` mocks with `aiohttp.ClientSession` mocks
- Update exception types from `httpx.*` to `aiohttp.*`
- Mock `aiohttp` response objects with proper `content`, `text`, and `status` attributes
- Ensure context manager protocol is properly mocked

**Mock Structure**:
```python
# Old (httpx)
with patch.object(httpx.AsyncClient, 'get', return_value=mock_response):

# New (aiohttp)
with patch('aiohttp.ClientSession') as mock_session:
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
```

### 2. DataProcessor Method Additions

**Problem**: Missing methods and incorrect method signatures

**Solution**: Add missing methods and update `clean_data` signature

#### 2.1 Update `clean_data` Method

**Current Signature**:
```python
def clean_data(df, drop_na=False, strip_strings=True, convert_numeric=True)
```

**New Signature**:
```python
def clean_data(df, drop_na=False, strip_strings=True, convert_numeric=True,
               remove_nulls=None, fill_value=None, remove_duplicates=False,
               strip_whitespace=None)
```

**Logic**:
- `remove_nulls` → maps to `drop_na` (for backward compatibility)
- `strip_whitespace` → maps to `strip_strings` (for backward compatibility)
- `fill_value` → fills NA values with specified value
- `remove_duplicates` → drops duplicate rows

#### 2.2 Add `extract_pdf_text` Method

```python
def extract_pdf_text(pdf_bytes: bytes, page: Optional[int] = None) -> str
```

**Implementation**: Wrapper around existing `extract_text_from_pdf` method

#### 2.3 Add `convert_types` Method

```python
def convert_types(df: pd.DataFrame, type_map: Dict[str, type]) -> pd.DataFrame
```

**Implementation**: Apply `astype()` for each column in type_map

#### 2.4 Add `filter_data` Method

```python
def filter_data(df: pd.DataFrame, column: str, operator: str, value: Any) -> pd.DataFrame
```

**Implementation**: Apply pandas boolean indexing based on operator

#### 2.5 Add `aggregate_data` Method

```python
def aggregate_data(df: pd.DataFrame, group_by: str, agg_func: str, agg_column: str) -> pd.DataFrame
```

**Implementation**: Use `groupby().agg()` and reset index

#### 2.6 Fix `parse_csv` Error Handling

**Current**: Catches exceptions but doesn't re-raise properly
**Fix**: Ensure invalid CSV raises Exception (not just logs)

#### 2.7 Fix `parse_json` Object Handling

**Current**: Returns dict for JSON objects
**Fix**: Convert single JSON object to single-row DataFrame

#### 2.8 Fix `extract_pdf_table` Mock Compatibility

**Current**: Mock doesn't support context manager protocol
**Fix**: Update test to use `MagicMock` with proper `__enter__` and `__exit__`

### 3. AnalysisEngine Method Additions and Fixes

**Problem**: Missing methods, incorrect signatures, edge case errors

#### 3.1 Update `calculate_statistics` Signature

**Current**:
```python
def calculate_statistics(df, columns=None, stats=None)
```

**New**: Add support for singular `column` parameter
```python
def calculate_statistics(df, columns=None, column=None, stats=None)
```

**Logic**: If `column` provided, convert to `columns=[column]`

#### 3.2 Fix `calculate_statistics` Edge Cases

**Problem**: `pd.DataFrame(results)` fails when results is dict of scalars

**Solution**: Provide index parameter
```python
result_df = pd.DataFrame(results, index=[0])
```

#### 3.3 Add `calculate_correlation` Method

```python
def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> float
```

**Implementation**: Return `df[col1].corr(df[col2])`

#### 3.4 Add `calculate_percentile` Method

```python
def calculate_percentile(df: pd.DataFrame, column: str, percentile: float) -> float
```

**Implementation**: Return `df[column].quantile(percentile / 100)`

#### 3.5 Update `rank_data` Signature

**Current**:
```python
def rank_data(df, column, method='average', ascending=True)
```

**New**: Support `by` parameter
```python
def rank_data(df, column=None, by=None, method='average', ascending=True)
```

**Logic**: If `by` provided, use it as `column`

#### 3.6 Fix `rank_data` Return Value

**Current**: Returns Series
**New**: Return DataFrame with 'rank' column added

```python
df_ranked = df.copy()
df_ranked['rank'] = ranks
return df_ranked
```

#### 3.7 Add `normalize_data` Method

```python
def normalize_data(df: pd.DataFrame, column: str) -> pd.DataFrame
```

**Implementation**: Min-max normalization
```python
df_normalized = df.copy()
col_min = df[column].min()
col_max = df[column].max()
if col_max != col_min:
    df_normalized[column] = (df[column] - col_min) / (col_max - col_min)
else:
    df_normalized[column] = 0
return df_normalized
```

#### 3.8 Fix `filter_data` Comparison Logic

**Problem**: Greater than includes equal values, less than includes equal values

**Current Behavior**: Tests expect strict inequality
**Fix**: Already correct in implementation, but verify test expectations

**Analysis**: 
- Test expects `age > 28` to return 2 rows (30, 35) - excludes 28 ✓
- Test expects `salary < 60000` to return 2 rows (50000, 55000) - excludes 60000 ✓
- Implementation is correct, but need to verify null handling

#### 3.9 Fix Null Handling in Filters

**Problem**: Null values may cause unexpected results in comparisons

**Solution**: Pandas comparison operators already handle nulls correctly (return False), but ensure dropna() is applied where needed

## Data Models

### Test Mock Structures

#### WebScraper Mock Response (aiohttp)
```python
mock_response = AsyncMock()
mock_response.content = AsyncMock()
mock_response.content.iter_chunked = AsyncMock(return_value=[b"chunk1", b"chunk2"])
mock_response.status = 200
mock_response.headers = {'Content-Type': 'application/pdf'}
mock_response.raise_for_status = Mock()
```

#### DataProcessor PDF Mock
```python
mock_pdf = MagicMock()
mock_pdf.__enter__.return_value = mock_pdf
mock_pdf.__exit__.return_value = None
mock_page = Mock()
mock_page.extract_text.return_value = "text"
mock_pdf.pages = [mock_page]
```

## Error Handling

### WebScraper Tests
- Timeout errors: Raise `asyncio.TimeoutError`
- HTTP errors: Raise `aiohttp.ClientResponseError`
- Connection errors: Raise `aiohttp.ClientConnectorError`

### DataProcessor
- Invalid CSV: Raise `Exception` (or `ValueError`)
- Invalid JSON: Raise `Exception` (or `ValueError`)
- Missing PDF methods: Add methods to avoid `AttributeError`

### AnalysisEngine
- Edge cases: Handle single-row and uniform-value DataFrames
- Missing columns: Validate column existence
- Invalid operators: Log warning and skip

## Testing Strategy

### Approach
1. Fix one module at a time: WebScraper → DataProcessor → AnalysisEngine
2. Run tests after each fix to verify progress
3. Ensure no regression in passing tests

### Validation
- Run full test suite after all fixes
- Verify 49 tests pass (currently 15 pass, 34 fail)
- Check for any new failures in other test files

### Test Execution Order
1. Fix `test_web_scraper.py` (11 failures)
2. Fix `test_data_processor.py` (12 failures)
3. Fix `test_analysis_engine.py` (11 failures)

## Implementation Notes

### WebScraper
- **No source code changes needed** - only test file updates
- Tests need complete rewrite of mocking strategy

### DataProcessor
- Add 5 new methods
- Update 1 method signature (clean_data)
- Fix 2 parsing behaviors (CSV error, JSON object)

### AnalysisEngine
- Add 3 new methods
- Update 2 method signatures
- Fix 1 return type (rank_data)
- Fix 1 edge case (calculate_statistics)

### Risk Assessment
- **Low Risk**: WebScraper (test-only changes)
- **Medium Risk**: DataProcessor (new methods, signature changes)
- **Medium Risk**: AnalysisEngine (new methods, behavior changes)

### Backward Compatibility
- Use parameter aliasing (e.g., `remove_nulls` → `drop_na`)
- Preserve existing method behavior
- Add new parameters as optional with defaults
