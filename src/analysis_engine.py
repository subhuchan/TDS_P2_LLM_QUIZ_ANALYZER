"""Analysis engine for performing data operations and statistical analysis."""

from typing import Any, Dict, List, Optional, Union, Callable
import pandas as pd
import numpy as np
from scipy import stats

from src.logging_config import get_logger

logger = get_logger(__name__)


class AnalysisEngine:
    """Handles data analysis operations including filtering, aggregation, and statistics."""
    
    def __init__(self):
        """Initialize the analysis engine."""
        logger.info("AnalysisEngine initialized")
    
    def filter_data(
        self,
        df: pd.DataFrame,
        conditions: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> pd.DataFrame:
        """
        Filter DataFrame based on conditions.
        
        Args:
            df: Input DataFrame
            conditions: Single condition dict or list of condition dicts
                Each condition: {'column': str, 'operator': str, 'value': Any}
                Operators: '==', '!=', '>', '<', '>=', '<=', 'in', 'not_in', 'contains', 'startswith', 'endswith'
        
        Returns:
            Filtered DataFrame
        
        Examples:
            filter_data(df, {'column': 'age', 'operator': '>', 'value': 18})
            filter_data(df, [
                {'column': 'age', 'operator': '>', 'value': 18},
                {'column': 'city', 'operator': 'in', 'value': ['NYC', 'LA']}
            ])
        """
        logger.info(f"Filtering data with conditions: {conditions}")
        
        # Normalize to list
        if isinstance(conditions, dict):
            conditions = [conditions]
        
        df_filtered = df.copy()
        
        for condition in conditions:
            col = condition.get('column')
            operator = condition.get('operator') or condition.get('op', '==')
            value = condition.get('value')
            
            if col not in df_filtered.columns:
                logger.warning(f"Column '{col}' not found in DataFrame")
                continue
            
            if operator == '==':
                df_filtered = df_filtered[df_filtered[col] == value]
            elif operator == '!=':
                df_filtered = df_filtered[df_filtered[col] != value]
            elif operator == '>':
                df_filtered = df_filtered[df_filtered[col] > value]
            elif operator == '<':
                df_filtered = df_filtered[df_filtered[col] < value]
            elif operator == '>=':
                df_filtered = df_filtered[df_filtered[col] >= value]
            elif operator == '<=':
                df_filtered = df_filtered[df_filtered[col] <= value]
            elif operator == 'in':
                df_filtered = df_filtered[df_filtered[col].isin(value)]
            elif operator == 'not_in':
                df_filtered = df_filtered[~df_filtered[col].isin(value)]
            elif operator == 'contains':
                df_filtered = df_filtered[df_filtered[col].str.contains(value, na=False)]
            elif operator == 'startswith':
                df_filtered = df_filtered[df_filtered[col].str.startswith(value, na=False)]
            elif operator == 'endswith':
                df_filtered = df_filtered[df_filtered[col].str.endswith(value, na=False)]
            else:
                logger.warning(f"Unknown operator: {operator}")
            
            logger.debug(f"After filter {col} {operator} {value}: {len(df_filtered)} rows")
        
        logger.info(f"Filtered from {len(df)} to {len(df_filtered)} rows")
        return df_filtered
    
    def aggregate(
        self,
        df: pd.DataFrame,
        operations: Dict[str, Union[str, List[str]]],
        group_by: Optional[Union[str, List[str]]] = None
    ) -> Union[pd.DataFrame, pd.Series, Any]:
        """
        Perform aggregation operations on DataFrame.
        
        Args:
            df: Input DataFrame
            operations: Dict mapping column names to aggregation functions
                Functions: 'sum', 'count', 'mean', 'median', 'min', 'max', 'std', 'var', 'first', 'last'
                Can also be a list of functions for multiple aggregations
            group_by: Column(s) to group by before aggregating
        
        Returns:
            Aggregated result (DataFrame, Series, or scalar)
        
        Examples:
            aggregate(df, {'sales': 'sum', 'quantity': 'count'})
            aggregate(df, {'sales': ['sum', 'mean']}, group_by='category')
        """
        logger.info(f"Aggregating data with operations: {operations}, group_by: {group_by}")
        
        if group_by:
            # Group by and aggregate
            grouped = df.groupby(group_by)
            result = grouped.agg(operations)
            
            # Flatten column names if multi-level
            if isinstance(result.columns, pd.MultiIndex):
                result.columns = ['_'.join(col).strip() for col in result.columns.values]
            
            result = result.reset_index()
            logger.info(f"Grouped aggregation result shape: {result.shape}")
        else:
            # Aggregate entire DataFrame
            result = df.agg(operations)
            logger.info(f"Aggregation result: {result}")
        
        return result

    def sort_data(
        self,
        df: pd.DataFrame,
        by: Union[str, List[str]],
        ascending: Union[bool, List[bool]] = True
    ) -> pd.DataFrame:
        """
        Sort DataFrame by one or more columns.
        
        Args:
            df: Input DataFrame
            by: Column name(s) to sort by
            ascending: Sort order (True for ascending, False for descending)
        
        Returns:
            Sorted DataFrame
        """
        logger.info(f"Sorting data by: {by}, ascending: {ascending}")
        
        df_sorted = df.sort_values(by=by, ascending=ascending).reset_index(drop=True)
        logger.info(f"Sorted data shape: {df_sorted.shape}")
        
        return df_sorted
    
    def reshape_data(
        self,
        df: pd.DataFrame,
        operation: str,
        **kwargs
    ) -> pd.DataFrame:
        """
        Reshape DataFrame using pivot, melt, or transpose operations.
        
        Args:
            df: Input DataFrame
            operation: Type of reshape ('pivot', 'melt', 'transpose', 'pivot_table')
            **kwargs: Additional arguments for the reshape operation
        
        Returns:
            Reshaped DataFrame
        
        Examples:
            reshape_data(df, 'pivot', index='date', columns='category', values='sales')
            reshape_data(df, 'melt', id_vars=['id'], value_vars=['col1', 'col2'])
            reshape_data(df, 'pivot_table', index='date', columns='category', values='sales', aggfunc='sum')
        """
        logger.info(f"Reshaping data with operation: {operation}")
        
        if operation == 'pivot':
            result = df.pivot(**kwargs)
        elif operation == 'melt':
            result = df.melt(**kwargs)
        elif operation == 'transpose':
            result = df.transpose()
        elif operation == 'pivot_table':
            result = df.pivot_table(**kwargs)
        else:
            logger.error(f"Unknown reshape operation: {operation}")
            raise ValueError(f"Unknown reshape operation: {operation}")
        
        logger.info(f"Reshaped data shape: {result.shape}")
        return result
    
    def calculate_statistics(
        self,
        df: pd.DataFrame,
        column: Optional[Union[str, List[str]]] = None,
        columns: Optional[List[str]] = None,
        stats: Optional[List[str]] = None
    ) -> Union[pd.DataFrame, Dict[str, Any]]:
        """
        Calculate statistical measures for DataFrame columns.
        
        Args:
            df: Input DataFrame
            column: Single column name (str) or list of columns to analyze
            columns: Alternative parameter for list of columns (for backward compatibility)
            stats: List of statistics to calculate
                Options: 'mean', 'median', 'std', 'var', 'min', 'max', 'count', 'sum', 'quantile'
                If None, calculates common statistics
        
        Returns:
            Dict with statistical measures if single column, DataFrame otherwise
        """
        # Handle column parameter (can be string or list)
        single_column = False
        if column is not None:
            if isinstance(column, str):
                columns = [column]
                single_column = True
            else:
                columns = column
        elif columns is None:
            columns = None
        
        logger.info(f"Calculating statistics for columns: {columns}")
        
        # Select columns
        if columns:
            df_subset = df[columns]
        else:
            df_subset = df.select_dtypes(include=[np.number])
        
        # Default statistics
        if stats is None:
            stats = ['count', 'mean', 'std', 'min', 'max', 'median']
        
        # Calculate statistics
        results = {}
        for stat in stats:
            if stat == 'median':
                results[stat] = df_subset.median()
            elif stat == 'quantile':
                # Calculate quartiles
                results['q25'] = df_subset.quantile(0.25)
                results['q50'] = df_subset.quantile(0.50)
                results['q75'] = df_subset.quantile(0.75)
            else:
                results[stat] = getattr(df_subset, stat)()
        
        # If single column, return dict of scalar values
        if single_column and len(df_subset.columns) == 1:
            scalar_results = {}
            for key, value in results.items():
                if isinstance(value, pd.Series):
                    val = value.iloc[0]
                    # Replace NaN with 0 for std/var in single-value cases
                    if pd.isna(val) and key in ['std', 'var']:
                        val = 0
                    scalar_results[key] = val
                else:
                    scalar_results[key] = value
            logger.info(f"Statistics calculated for single column")
            return scalar_results
        
        # For multiple columns or when columns parameter was used
        result_df = pd.DataFrame(results)
        logger.info(f"Statistics calculated for {len(result_df.columns)} measures")
        
        return result_df
    
    def correlation_analysis(
        self,
        df: pd.DataFrame,
        method: str = 'pearson',
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for DataFrame columns.
        
        Args:
            df: Input DataFrame
            method: Correlation method ('pearson', 'spearman', 'kendall')
            columns: Specific columns to analyze (None for all numeric columns)
        
        Returns:
            Correlation matrix as DataFrame
        """
        logger.info(f"Calculating {method} correlation")
        
        # Select columns
        if columns:
            df_subset = df[columns]
        else:
            df_subset = df.select_dtypes(include=[np.number])
        
        corr_matrix = df_subset.corr(method=method)
        logger.info(f"Correlation matrix shape: {corr_matrix.shape}")
        
        return corr_matrix
    
    def calculate_correlation(
        self,
        df: pd.DataFrame,
        col1: str,
        col2: str
    ) -> float:
        """
        Calculate correlation between two columns.
        
        Args:
            df: Input DataFrame
            col1: First column name
            col2: Second column name
        
        Returns:
            Correlation coefficient
        """
        logger.info(f"Calculating correlation between {col1} and {col2}")
        
        if col1 not in df.columns:
            raise ValueError(f"Column '{col1}' not found in DataFrame")
        if col2 not in df.columns:
            raise ValueError(f"Column '{col2}' not found in DataFrame")
        
        corr = df[col1].corr(df[col2])
        logger.info(f"Correlation: {corr}")
        
        return corr
    
    def percentile_rank(
        self,
        df: pd.DataFrame,
        column: str,
        value: float
    ) -> float:
        """
        Calculate percentile rank of a value in a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            value: Value to find percentile rank for
        
        Returns:
            Percentile rank (0-100)
        """
        logger.info(f"Calculating percentile rank for {value} in column {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        data = df[column].dropna()
        percentile = stats.percentileofscore(data, value, kind='rank')
        
        logger.info(f"Percentile rank: {percentile}")
        return percentile
    
    def calculate_percentile(
        self,
        df: pd.DataFrame,
        column: str,
        percentile: float
    ) -> float:
        """
        Calculate percentile value for a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Value at the specified percentile
        """
        logger.info(f"Calculating {percentile}th percentile for column {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        value = df[column].quantile(percentile / 100)
        logger.info(f"Percentile value: {value}")
        
        return value
    
    def moving_average(
        self,
        df: pd.DataFrame,
        column: str,
        window: int,
        center: bool = False
    ) -> pd.Series:
        """
        Calculate moving average for a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            window: Window size for moving average
            center: If True, center the window
        
        Returns:
            Series with moving average values
        """
        logger.info(f"Calculating moving average for {column} with window {window}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        ma = df[column].rolling(window=window, center=center).mean()
        logger.info(f"Moving average calculated")
        
        return ma
    
    def cumulative_sum(
        self,
        df: pd.DataFrame,
        column: str,
        group_by: Optional[str] = None
    ) -> pd.Series:
        """
        Calculate cumulative sum for a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            group_by: Optional column to group by before calculating cumsum
        
        Returns:
            Series with cumulative sum values
        """
        logger.info(f"Calculating cumulative sum for {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        if group_by:
            cumsum = df.groupby(group_by)[column].cumsum()
        else:
            cumsum = df[column].cumsum()
        
        logger.info(f"Cumulative sum calculated")
        return cumsum
    
    def rank_data(
        self,
        df: pd.DataFrame,
        column: Optional[str] = None,
        by: Optional[str] = None,
        method: str = 'average',
        ascending: bool = True
    ) -> pd.DataFrame:
        """
        Rank values in a column.
        
        Args:
            df: Input DataFrame
            column: Column name to rank
            by: Alias for column parameter
            method: Ranking method ('average', 'min', 'max', 'first', 'dense')
            ascending: If True, rank in ascending order (lowest value gets rank 1)
        
        Returns:
            DataFrame with 'rank' column added
        """
        # Handle by parameter (alias for column)
        if by is not None:
            column = by
        
        if column is None:
            raise ValueError("Either 'column' or 'by' parameter must be provided")
        
        logger.info(f"Ranking data in column {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        df_ranked = df.copy()
        # For descending rank (highest value gets rank 1), use ascending=False
        df_ranked['rank'] = df[column].rank(method=method, ascending=not ascending)
        logger.info(f"Data ranked")
        
        return df_ranked
    
    def outlier_detection(
        self,
        df: pd.DataFrame,
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.Series:
        """
        Detect outliers in a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            method: Detection method ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
                For IQR: multiplier for IQR (default 1.5)
                For Z-score: number of standard deviations (default 1.5)
        
        Returns:
            Boolean Series indicating outliers (True = outlier)
        """
        logger.info(f"Detecting outliers in {column} using {method} method")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        data = df[column].dropna()
        
        if method == 'iqr':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outliers = (df[column] < lower_bound) | (df[column] > upper_bound)
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(data))
            outliers = pd.Series(False, index=df.index)
            outliers.loc[data.index] = z_scores > threshold
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
        
        outlier_count = outliers.sum()
        logger.info(f"Detected {outlier_count} outliers")
        
        return outliers
    
    def binning(
        self,
        df: pd.DataFrame,
        column: str,
        bins: Union[int, List[float]],
        labels: Optional[List[str]] = None
    ) -> pd.Series:
        """
        Bin continuous data into discrete intervals.
        
        Args:
            df: Input DataFrame
            column: Column name to bin
            bins: Number of bins or list of bin edges
            labels: Optional labels for bins
        
        Returns:
            Series with binned values
        """
        logger.info(f"Binning column {column} into {bins} bins")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        binned = pd.cut(df[column], bins=bins, labels=labels)
        logger.info(f"Data binned into {binned.nunique()} categories")
        
        return binned
    
    def value_counts(
        self,
        df: pd.DataFrame,
        column: str,
        normalize: bool = False,
        top_n: Optional[int] = None
    ) -> pd.Series:
        """
        Count unique values in a column.
        
        Args:
            df: Input DataFrame
            column: Column name
            normalize: If True, return proportions instead of counts
            top_n: Return only top N most frequent values
        
        Returns:
            Series with value counts
        """
        logger.info(f"Counting values in column {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        counts = df[column].value_counts(normalize=normalize)
        
        if top_n:
            counts = counts.head(top_n)
        
        logger.info(f"Value counts calculated for {len(counts)} unique values")
        return counts
    
    def cross_tabulation(
        self,
        df: pd.DataFrame,
        index: Union[str, List[str]],
        columns: Union[str, List[str]],
        values: Optional[str] = None,
        aggfunc: str = 'count',
        normalize: bool = False
    ) -> pd.DataFrame:
        """
        Create cross-tabulation of two or more factors.
        
        Args:
            df: Input DataFrame
            index: Column(s) for row index
            columns: Column(s) for column index
            values: Column to aggregate (if None, counts occurrences)
            aggfunc: Aggregation function ('count', 'sum', 'mean', etc.)
            normalize: If True, normalize to show proportions
        
        Returns:
            Cross-tabulation DataFrame
        """
        logger.info(f"Creating cross-tabulation: {index} vs {columns}")
        
        if values:
            result = pd.crosstab(
                df[index] if isinstance(index, str) else [df[col] for col in index],
                df[columns] if isinstance(columns, str) else [df[col] for col in columns],
                values=df[values],
                aggfunc=aggfunc,
                normalize=normalize
            )
        else:
            result = pd.crosstab(
                df[index] if isinstance(index, str) else [df[col] for col in index],
                df[columns] if isinstance(columns, str) else [df[col] for col in columns],
                normalize=normalize
            )
        
        logger.info(f"Cross-tabulation shape: {result.shape}")
        return result
    
    def normalize_data(
        self,
        df: pd.DataFrame,
        column: str
    ) -> pd.DataFrame:
        """
        Normalize column values to 0-1 range using min-max normalization.
        
        Args:
            df: Input DataFrame
            column: Column name to normalize
        
        Returns:
            DataFrame with normalized column
        """
        logger.info(f"Normalizing column {column}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        df_normalized = df.copy()
        col_min = df[column].min()
        col_max = df[column].max()
        
        if col_max != col_min:
            df_normalized[column] = (df[column] - col_min) / (col_max - col_min)
        else:
            # All values are the same, set to 0
            df_normalized[column] = 0
        
        logger.info(f"Normalized column {column}")
        return df_normalized
