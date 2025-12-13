# Implementation Plan

- [x] 1. Fix WebScraper test mocking strategy
  - Update all test mocks from httpx to aiohttp
  - Replace httpx.AsyncClient mocks with aiohttp.ClientSession mocks
  - Update exception types from httpx to aiohttp exceptions
  - Ensure async context manager protocol is properly mocked for aiohttp responses
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Add missing DataProcessor methods
- [x] 2.1 Add extract_pdf_text method
  - Create extract_pdf_text method as wrapper around extract_text_from_pdf
  - Accept pdf_bytes and optional page parameter
  - Return extracted text string
  - _Requirements: 2.1, 2.3_

- [x] 2.2 Add convert_types method
  - Create convert_types method accepting DataFrame and type_map dictionary
  - Apply astype() conversion for each column in type_map
  - Return converted DataFrame
  - _Requirements: 2.6_

- [x] 2.3 Add filter_data method
  - Create filter_data method accepting DataFrame, column, operator, and value
  - Implement pandas boolean indexing for operators: '>', '<', '>=', '<=', '==', '!='
  - Return filtered DataFrame
  - _Requirements: 2.7_

- [x] 2.4 Add aggregate_data method
  - Create aggregate_data method accepting DataFrame, group_by, agg_func, and agg_column
  - Use groupby().agg() pattern and reset index
  - Return aggregated DataFrame
  - _Requirements: 2.8_

- [x] 3. Update DataProcessor clean_data method signature
  - Add remove_nulls parameter (maps to drop_na for backward compatibility)
  - Add fill_value parameter to fill NA values with specified value
  - Add remove_duplicates parameter to drop duplicate rows
  - Add strip_whitespace parameter (maps to strip_strings for backward compatibility)
  - Implement logic for new parameters while preserving existing behavior
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 4. Fix DataProcessor parsing behaviors
- [x] 4.1 Fix parse_csv error handling
  - Ensure invalid CSV data raises Exception instead of just logging
  - Verify ValueError is raised and not caught silently
  - _Requirements: 2.9_

- [x] 4.2 Fix parse_json object handling
  - When parsing single JSON object, convert to single-row DataFrame
  - Use pd.DataFrame([data]) to wrap dict in list for single-row DataFrame
  - _Requirements: 2.10_

- [x] 4.3 Fix extract_pdf_table test mock
  - Update test to use MagicMock instead of Mock for pdfplumber.open
  - Ensure mock supports context manager protocol with __enter__ and __exit__
  - _Requirements: 3.1, 3.2_

- [x] 5. Add missing AnalysisEngine methods
- [x] 5.1 Add calculate_correlation method
  - Create calculate_correlation method accepting DataFrame and two column names
  - Return correlation coefficient using df[col1].corr(df[col2])
  - _Requirements: 4.2_

- [x] 5.2 Add calculate_percentile method
  - Create calculate_percentile method accepting DataFrame, column, and percentile value
  - Return percentile value using df[column].quantile(percentile / 100)
  - _Requirements: 4.3_

- [x] 5.3 Add normalize_data method
  - Create normalize_data method accepting DataFrame and column name
  - Implement min-max normalization to scale values to 0-1 range
  - Handle edge case where all values are the same (set to 0)
  - Return DataFrame with normalized column
  - _Requirements: 4.5_

- [x] 6. Update AnalysisEngine method signatures
- [x] 6.1 Update calculate_statistics signature
  - Add column parameter (singular) in addition to columns parameter (plural)
  - If column provided, convert to columns=[column] internally
  - Maintain backward compatibility with existing columns parameter
  - _Requirements: 4.1_

- [x] 6.2 Update rank_data signature and return value
  - Add by parameter as alias for column parameter
  - Change return value from Series to DataFrame with 'rank' column added
  - Ensure descending rank order (highest value gets rank 1)
  - _Requirements: 4.4_

- [x] 7. Fix AnalysisEngine edge cases
- [x] 7.1 Fix calculate_statistics for single-row DataFrames
  - When creating DataFrame from scalar statistics, provide index parameter
  - Use pd.DataFrame(results, index=[0]) instead of pd.DataFrame(results)
  - Test with single-row input to verify no ValueError
  - _Requirements: 6.1, 6.3_

- [x] 7.2 Fix calculate_statistics for uniform-value DataFrames
  - Ensure statistics calculation works when all values are identical
  - Verify std=0, min=max=mean for uniform datasets
  - Use same fix as 7.1 (provide index parameter)
  - _Requirements: 6.2, 6.3_

- [x] 7.3 Verify filter_data null handling
  - Ensure null values are properly excluded from filter comparisons
  - Verify pandas comparison operators handle nulls correctly (return False)
  - Test filter operations with DataFrames containing null values
  - _Requirements: 5.4_

- [x] 8. Verify filter comparison operators
  - Verify greater than operator excludes equal values (strict inequality)
  - Verify less than operator excludes equal values (strict inequality)
  - Verify multiple conditions use AND logic correctly
  - Run filter tests to confirm expected behavior
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 9. Run complete test suite and verify all fixes
  - Execute pytest on all three test files
  - Verify all 49 tests pass (15 currently passing + 34 fixed)
  - Check for any regressions in previously passing tests
  - Document any remaining issues
  - _Requirements: All_
