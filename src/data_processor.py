"""Data processor for parsing and processing various file formats."""

import io
import json
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import pdfplumber
from PIL import Image

from src.logging_config import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """Handles parsing and processing of various file formats."""
    
    def __init__(self):
        """Initialize the data processor."""
        logger.info("DataProcessor initialized")
    
    def extract_pdf_table(
        self, 
        pdf_bytes: bytes, 
        page: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Extract table from PDF file using pdfplumber.
        
        Args:
            pdf_bytes: PDF file content as bytes
            page: Specific page number to extract (1-indexed), None for all pages
        
        Returns:
            DataFrame containing extracted table data
        
        Raises:
            ValueError: If no tables found or invalid page number
        """
        logger.info(f"Extracting PDF table from page: {page if page else 'all pages'}")
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_pages = len(pdf.pages)
                logger.debug(f"PDF has {total_pages} pages")
                
                if page is not None:
                    # Convert to 0-indexed
                    page_idx = page - 1
                    if page_idx < 0 or page_idx >= total_pages:
                        raise ValueError(f"Invalid page number {page}. PDF has {total_pages} pages")
                    
                    pages_to_process = [pdf.pages[page_idx]]
                else:
                    pages_to_process = pdf.pages
                
                all_tables = []
                for pg in pages_to_process:
                    tables = pg.extract_tables()
                    if tables:
                        for table in tables:
                            all_tables.append(table)
                
                if not all_tables:
                    raise ValueError("No tables found in PDF")
                
                # Convert first table to DataFrame
                # First row is typically headers
                df = pd.DataFrame(all_tables[0][1:], columns=all_tables[0][0])
                logger.info(f"Extracted table with shape: {df.shape}")
                
                return df
                
        except Exception as e:
            logger.error(f"Error extracting PDF table: {str(e)}")
            raise
    
    def parse_csv(
        self, 
        csv_bytes: bytes, 
        encoding: str = 'utf-8',
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse CSV file into pandas DataFrame.
        
        Args:
            csv_bytes: CSV file content as bytes
            encoding: Character encoding (default: utf-8)
            **kwargs: Additional arguments passed to pd.read_csv
        
        Returns:
            DataFrame containing CSV data
        
        Raises:
            ValueError: If CSV parsing fails
        """
        logger.info("Parsing CSV file")
        
        try:
            df = pd.read_csv(
                io.BytesIO(csv_bytes),
                encoding=encoding,
                **kwargs
            )
            logger.info(f"Parsed CSV with shape: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {str(e)}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")
    
    def parse_json(
        self, 
        json_bytes: bytes,
        normalize: bool = True
    ) -> Union[pd.DataFrame, Dict, List]:
        """
        Parse JSON file and optionally normalize to DataFrame.
        
        Args:
            json_bytes: JSON file content as bytes
            normalize: If True, attempt to normalize to DataFrame
        
        Returns:
            DataFrame if normalize=True and data is suitable, otherwise dict/list
        
        Raises:
            ValueError: If JSON parsing fails
        """
        logger.info("Parsing JSON file")
        
        try:
            data = json.loads(json_bytes.decode('utf-8'))
            logger.debug(f"Parsed JSON type: {type(data)}")
            
            if not normalize:
                return data
            
            # Try to normalize to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
                logger.info(f"Normalized JSON list to DataFrame with shape: {df.shape}")
                return df
            elif isinstance(data, dict):
                # Check if it's a dict of lists (common JSON structure)
                if all(isinstance(v, list) for v in data.values()):
                    df = pd.DataFrame(data)
                    logger.info(f"Normalized JSON dict to DataFrame with shape: {df.shape}")
                    return df
                else:
                    # Convert single JSON object to single-row DataFrame
                    df = pd.DataFrame([data])
                    logger.info(f"Normalized JSON object to DataFrame with shape: {df.shape}")
                    return df
            else:
                logger.warning(f"Cannot normalize JSON type {type(data)} to DataFrame")
                return data
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {str(e)}")
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing JSON: {str(e)}")
            raise ValueError(f"Failed to parse JSON: {str(e)}")
    
    def clean_data(
        self, 
        df: pd.DataFrame,
        drop_na: bool = False,
        strip_strings: bool = True,
        convert_numeric: bool = True,
        remove_nulls: Optional[bool] = None,
        fill_value: Optional[Any] = None,
        remove_duplicates: bool = False,
        strip_whitespace: Optional[bool] = None
    ) -> pd.DataFrame:
        """
        Apply common data cleaning operations to DataFrame.
        
        Args:
            df: Input DataFrame
            drop_na: If True, drop rows with any NA values
            strip_strings: If True, strip whitespace from string columns
            convert_numeric: If True, attempt to convert string columns to numeric
            remove_nulls: Alias for drop_na (for backward compatibility)
            fill_value: Value to fill NA values with (if provided)
            remove_duplicates: If True, drop duplicate rows
            strip_whitespace: Alias for strip_strings (for backward compatibility)
        
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning data")
        df_clean = df.copy()
        
        # Handle parameter aliases
        if remove_nulls is not None:
            drop_na = remove_nulls
        if strip_whitespace is not None:
            strip_strings = strip_whitespace
        
        # Strip whitespace from string columns
        if strip_strings:
            string_cols = df_clean.select_dtypes(include=['object']).columns
            for col in string_cols:
                df_clean[col] = df_clean[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
            logger.debug(f"Stripped whitespace from {len(string_cols)} string columns")
        
        # Convert numeric strings to numbers
        if convert_numeric:
            for col in df_clean.columns:
                try:
                    df_clean[col] = pd.to_numeric(df_clean[col])
                    logger.debug(f"Converted column '{col}' to numeric")
                except (ValueError, TypeError):
                    pass
        
        # Fill NA values if fill_value is provided
        if fill_value is not None:
            df_clean = df_clean.fillna(fill_value)
            logger.debug(f"Filled NA values with {fill_value}")
        
        # Drop NA values
        if drop_na:
            original_rows = len(df_clean)
            df_clean = df_clean.dropna()
            dropped = original_rows - len(df_clean)
            if dropped > 0:
                logger.debug(f"Dropped {dropped} rows with NA values")
        
        # Remove duplicate rows
        if remove_duplicates:
            original_rows = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            dropped = original_rows - len(df_clean)
            if dropped > 0:
                logger.debug(f"Dropped {dropped} duplicate rows")
        
        logger.info(f"Cleaned data shape: {df_clean.shape}")
        return df_clean
    
    def transform_data(
        self,
        df: pd.DataFrame,
        operations: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Apply transformation operations to DataFrame.
        
        Args:
            df: Input DataFrame
            operations: List of operation dicts with 'type' and parameters
                Supported types: 'rename', 'select', 'filter', 'sort', 'groupby'
        
        Returns:
            Transformed DataFrame
        """
        logger.info(f"Applying {len(operations)} transformation operations")
        df_transformed = df.copy()
        
        for op in operations:
            op_type = op.get('type')
            
            if op_type == 'rename':
                # Rename columns: {'type': 'rename', 'columns': {'old': 'new'}}
                df_transformed = df_transformed.rename(columns=op.get('columns', {}))
                logger.debug(f"Renamed columns: {op.get('columns')}")
            
            elif op_type == 'select':
                # Select columns: {'type': 'select', 'columns': ['col1', 'col2']}
                cols = op.get('columns', [])
                df_transformed = df_transformed[cols]
                logger.debug(f"Selected columns: {cols}")
            
            elif op_type == 'filter':
                # Filter rows: {'type': 'filter', 'column': 'col', 'operator': '==', 'value': 10}
                col = op.get('column')
                operator = op.get('operator', '==')
                value = op.get('value')
                
                if operator == '==':
                    df_transformed = df_transformed[df_transformed[col] == value]
                elif operator == '!=':
                    df_transformed = df_transformed[df_transformed[col] != value]
                elif operator == '>':
                    df_transformed = df_transformed[df_transformed[col] > value]
                elif operator == '<':
                    df_transformed = df_transformed[df_transformed[col] < value]
                elif operator == '>=':
                    df_transformed = df_transformed[df_transformed[col] >= value]
                elif operator == '<=':
                    df_transformed = df_transformed[df_transformed[col] <= value]
                
                logger.debug(f"Filtered: {col} {operator} {value}")
            
            elif op_type == 'sort':
                # Sort: {'type': 'sort', 'by': 'col', 'ascending': True}
                by = op.get('by')
                ascending = op.get('ascending', True)
                df_transformed = df_transformed.sort_values(by=by, ascending=ascending)
                logger.debug(f"Sorted by {by}, ascending={ascending}")
            
            elif op_type == 'groupby':
                # Group and aggregate: {'type': 'groupby', 'by': 'col', 'agg': {'col2': 'sum'}}
                by = op.get('by')
                agg = op.get('agg', {})
                df_transformed = df_transformed.groupby(by).agg(agg).reset_index()
                logger.debug(f"Grouped by {by} with aggregations: {agg}")
        
        logger.info(f"Transformed data shape: {df_transformed.shape}")
        return df_transformed
    
    def extract_text_from_pdf(
        self,
        pdf_bytes: bytes,
        page: Optional[int] = None
    ) -> str:
        """
        Extract text content from PDF.
        
        Args:
            pdf_bytes: PDF file content as bytes
            page: Specific page number to extract (1-indexed), None for all pages
        
        Returns:
            Extracted text content
        """
        logger.info(f"Extracting text from PDF page: {page if page else 'all pages'}")
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                total_pages = len(pdf.pages)
                
                if page is not None:
                    page_idx = page - 1
                    if page_idx < 0 or page_idx >= total_pages:
                        raise ValueError(f"Invalid page number {page}. PDF has {total_pages} pages")
                    
                    text = pdf.pages[page_idx].extract_text()
                else:
                    text = '\n\n'.join(pg.extract_text() for pg in pdf.pages if pg.extract_text())
                
                logger.info(f"Extracted {len(text)} characters of text")
                return text
                
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
    
    def extract_pdf_text(
        self,
        pdf_bytes: bytes,
        page: Optional[int] = None
    ) -> str:
        """
        Extract text content from PDF (alias for extract_text_from_pdf).
        
        Args:
            pdf_bytes: PDF file content as bytes
            page: Specific page number to extract (0-indexed), None for all pages
        
        Returns:
            Extracted text content
        """
        # Convert 0-indexed to 1-indexed for extract_text_from_pdf
        page_1indexed = page + 1 if page is not None else None
        return self.extract_text_from_pdf(pdf_bytes, page_1indexed)
    
    def process_image(
        self,
        image_bytes: bytes
    ) -> Image.Image:
        """
        Load and process image from bytes.
        
        Args:
            image_bytes: Image file content as bytes
        
        Returns:
            PIL Image object
        """
        logger.info("Processing image")
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Loaded image with size: {image.size}, mode: {image.mode}")
            return image
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise ValueError(f"Failed to process image: {str(e)}")
    
    def convert_types(
        self,
        df: pd.DataFrame,
        type_map: Dict[str, type]
    ) -> pd.DataFrame:
        """
        Convert column types in DataFrame.
        
        Args:
            df: Input DataFrame
            type_map: Dictionary mapping column names to target types
        
        Returns:
            DataFrame with converted types
        """
        logger.info(f"Converting types for columns: {list(type_map.keys())}")
        df_converted = df.copy()
        
        for col, dtype in type_map.items():
            if col in df_converted.columns:
                df_converted[col] = df_converted[col].astype(dtype)
                logger.debug(f"Converted column '{col}' to {dtype}")
            else:
                logger.warning(f"Column '{col}' not found in DataFrame")
        
        return df_converted
    
    def filter_data(
        self,
        df: pd.DataFrame,
        column: str,
        operator: str,
        value: Any
    ) -> pd.DataFrame:
        """
        Filter DataFrame rows based on condition.
        
        Args:
            df: Input DataFrame
            column: Column name to filter on
            operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
            value: Value to compare against
        
        Returns:
            Filtered DataFrame
        """
        logger.info(f"Filtering data: {column} {operator} {value}")
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame")
        
        if operator == '>':
            result = df[df[column] > value]
        elif operator == '<':
            result = df[df[column] < value]
        elif operator == '>=':
            result = df[df[column] >= value]
        elif operator == '<=':
            result = df[df[column] <= value]
        elif operator == '==':
            result = df[df[column] == value]
        elif operator == '!=':
            result = df[df[column] != value]
        else:
            raise ValueError(f"Unknown operator: {operator}")
        
        logger.info(f"Filtered from {len(df)} to {len(result)} rows")
        return result
    
    def aggregate_data(
        self,
        df: pd.DataFrame,
        group_by: str,
        agg_func: str,
        agg_column: str
    ) -> pd.DataFrame:
        """
        Aggregate DataFrame data by grouping.
        
        Args:
            df: Input DataFrame
            group_by: Column to group by
            agg_func: Aggregation function ('sum', 'mean', 'count', 'min', 'max', etc.)
            agg_column: Column to aggregate
        
        Returns:
            Aggregated DataFrame
        """
        logger.info(f"Aggregating {agg_column} by {group_by} using {agg_func}")
        
        if group_by not in df.columns:
            raise ValueError(f"Group by column '{group_by}' not found in DataFrame")
        if agg_column not in df.columns:
            raise ValueError(f"Aggregation column '{agg_column}' not found in DataFrame")
        
        result = df.groupby(group_by)[agg_column].agg(agg_func).reset_index()
        logger.info(f"Aggregated to {len(result)} rows")
        
        return result
