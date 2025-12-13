"""Unit tests for data processor."""

import pytest
import pandas as pd
import io
from unittest.mock import Mock, patch

from src.data_processor import DataProcessor


class TestDataProcessor:
    """Test suite for DataProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create DataProcessor instance."""
        return DataProcessor()
    
    def test_parse_csv_basic(self, processor):
        """Test parsing basic CSV data."""
        csv_data = b"name,age,city\nJohn,30,NYC\nJane,25,LA"
        
        df = processor.parse_csv(csv_data)
        
        assert len(df) == 2
        assert list(df.columns) == ['name', 'age', 'city']
        assert df.iloc[0]['name'] == 'John'
        assert df.iloc[0]['age'] == 30
    
    def test_parse_csv_with_quotes(self, processor):
        """Test parsing CSV with quoted fields."""
        csv_data = b'name,description\n"John Doe","A person, with comma"\n"Jane","Normal"'
        
        df = processor.parse_csv(csv_data)
        
        assert len(df) == 2
        assert df.iloc[0]['description'] == 'A person, with comma'
    
    def test_parse_csv_empty(self, processor):
        """Test parsing empty CSV."""
        csv_data = b"name,age\n"
        
        df = processor.parse_csv(csv_data)
        
        assert len(df) == 0
        assert list(df.columns) == ['name', 'age']
    
    def test_parse_csv_with_nulls(self, processor):
        """Test parsing CSV with null values."""
        csv_data = b"name,age,city\nJohn,30,NYC\nJane,,LA\nBob,35,"
        
        df = processor.parse_csv(csv_data)
        
        assert len(df) == 3
        assert pd.isna(df.iloc[1]['age'])
        assert pd.isna(df.iloc[2]['city'])
    
    def test_parse_json_array(self, processor):
        """Test parsing JSON array."""
        json_data = b'[{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]'
        
        df = processor.parse_json(json_data)
        
        assert len(df) == 2
        assert df.iloc[0]['name'] == 'John'
        assert df.iloc[1]['age'] == 25
    
    def test_parse_json_object(self, processor):
        """Test parsing JSON object."""
        json_data = b'{"name": "John", "age": 30, "city": "NYC"}'
        
        result = processor.parse_json(json_data)
        
        # Result should be a DataFrame with one row
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'John'
        assert result.iloc[0]['age'] == 30
    
    def test_clean_data_remove_nulls(self, processor):
        """Test cleaning data by removing null values."""
        df = pd.DataFrame({
            'name': ['John', None, 'Jane'],
            'age': [30, 25, None]
        })
        
        cleaned = processor.clean_data(df, remove_nulls=True)
        
        assert len(cleaned) == 1  # Only John's row is complete
        assert cleaned.iloc[0]['name'] == 'John'
    
    def test_clean_data_fill_nulls(self, processor):
        """Test cleaning data by filling null values."""
        df = pd.DataFrame({
            'name': ['John', None, 'Jane'],
            'age': [30, 25, None]
        })
        
        cleaned = processor.clean_data(df, fill_value=0)
        
        assert len(cleaned) == 3
        assert cleaned.iloc[2]['age'] == 0
    
    def test_clean_data_remove_duplicates(self, processor):
        """Test removing duplicate rows."""
        df = pd.DataFrame({
            'name': ['John', 'John', 'Jane'],
            'age': [30, 30, 25]
        })
        
        cleaned = processor.clean_data(df, remove_duplicates=True)
        
        assert len(cleaned) == 2
    
    def test_clean_data_strip_whitespace(self, processor):
        """Test stripping whitespace from strings."""
        df = pd.DataFrame({
            'name': ['  John  ', 'Jane  ', '  Bob'],
            'city': ['NYC  ', '  LA', 'SF']
        })
        
        cleaned = processor.clean_data(df, strip_whitespace=True)
        
        assert cleaned.iloc[0]['name'] == 'John'
        assert cleaned.iloc[1]['city'] == 'LA'
    
    def test_extract_pdf_text(self, processor):
        """Test extracting text from PDF."""
        # Mock PDF content
        from unittest.mock import MagicMock
        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample PDF text"
        mock_pdf.pages = [mock_page]
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            text = processor.extract_pdf_text(b"fake pdf bytes", page=0)
            
            assert text == "Sample PDF text"
    
    def test_extract_pdf_table(self, processor):
        """Test extracting table from PDF."""
        # Mock PDF table
        from unittest.mock import MagicMock
        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_page = Mock()
        mock_page.extract_tables.return_value = [[
            ['Name', 'Age'],
            ['John', '30'],
            ['Jane', '25']
        ]]
        mock_pdf.pages = [mock_page]
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            df = processor.extract_pdf_table(b"fake pdf bytes", page=1)
            
            assert len(df) == 2
            assert list(df.columns) == ['Name', 'Age']
            assert df.iloc[0]['Name'] == 'John'
    
    def test_extract_pdf_specific_page(self, processor):
        """Test extracting from specific PDF page."""
        from unittest.mock import MagicMock
        mock_pdf = MagicMock()
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2"
        mock_pdf.pages = [mock_page1, mock_page2]
        
        with patch('pdfplumber.open', return_value=mock_pdf):
            text = processor.extract_pdf_text(b"fake pdf bytes", page=1)
            
            assert text == "Page 2"
    
    def test_convert_types(self, processor):
        """Test converting column types."""
        df = pd.DataFrame({
            'age': ['30', '25', '35'],
            'price': ['10.5', '20.3', '15.7']
        })
        
        converted = processor.convert_types(df, {
            'age': int,
            'price': float
        })
        
        assert converted['age'].dtype == int
        assert converted['price'].dtype == float
        assert converted.iloc[0]['age'] == 30
        assert converted.iloc[0]['price'] == 10.5
    
    def test_filter_data(self, processor):
        """Test filtering data."""
        df = pd.DataFrame({
            'name': ['John', 'Jane', 'Bob'],
            'age': [30, 25, 35]
        })
        
        filtered = processor.filter_data(df, 'age', '>', 28)
        
        assert len(filtered) == 2
        assert 'Jane' not in filtered['name'].values
    
    def test_aggregate_data(self, processor):
        """Test aggregating data."""
        df = pd.DataFrame({
            'category': ['A', 'A', 'B', 'B'],
            'value': [10, 20, 30, 40]
        })
        
        aggregated = processor.aggregate_data(df, group_by='category', agg_func='sum', agg_column='value')
        
        assert len(aggregated) == 2
        assert aggregated[aggregated['category'] == 'A']['value'].values[0] == 30
        assert aggregated[aggregated['category'] == 'B']['value'].values[0] == 70
    
    def test_handle_invalid_csv(self, processor):
        """Test handling invalid CSV data."""
        # Use truly invalid CSV (binary data that can't be decoded)
        invalid_csv = b"\x80\x81\x82\x83"
        
        with pytest.raises(Exception):
            processor.parse_csv(invalid_csv)
    
    def test_handle_invalid_json(self, processor):
        """Test handling invalid JSON data."""
        invalid_json = b"{invalid json}"
        
        with pytest.raises(Exception):
            processor.parse_json(invalid_json)
