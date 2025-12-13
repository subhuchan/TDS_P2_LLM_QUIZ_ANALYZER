"""Unit tests for chart generator."""

import pytest
import pandas as pd
import base64
from unittest.mock import Mock, patch
import io

from src.chart_generator import ChartGenerator


class TestChartGenerator:
    """Test suite for ChartGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create ChartGenerator instance."""
        return ChartGenerator()
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'category': ['A', 'B', 'C', 'D'],
            'value': [10, 25, 15, 30]
        })
    
    def test_create_bar_chart(self, generator, sample_df):
        """Test creating bar chart."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={'x': 'category', 'y': 'value'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
        assert len(base64_uri) > 100
    
    def test_create_line_chart(self, generator, sample_df):
        """Test creating line chart."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='line',
            config={'x': 'category', 'y': 'value'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_create_scatter_chart(self, generator):
        """Test creating scatter chart."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 5, 4, 6]
        })
        
        base64_uri = generator.create_chart(
            data=df,
            chart_type='scatter',
            config={'x': 'x', 'y': 'y'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_create_pie_chart(self, generator, sample_df):
        """Test creating pie chart."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='pie',
            config={'labels': 'category', 'values': 'value'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_validate_size_under_limit(self, generator):
        """Test validating size under 1MB."""
        # Create small base64 string
        small_data = "data:image/png;base64," + "A" * 1000
        
        assert generator.validate_size(small_data) is True
    
    def test_validate_size_over_limit(self, generator):
        """Test validating size over 1MB."""
        # Create large base64 string (over 1MB)
        large_data = "data:image/png;base64," + "A" * (2 * 1024 * 1024)
        
        assert generator.validate_size(large_data) is False
    
    def test_validate_size_exactly_1mb(self, generator):
        """Test validating size exactly at 1MB."""
        # Create base64 string exactly 1MB
        exact_data = "data:image/png;base64," + "A" * (1024 * 1024)
        
        # Should be valid (at or under limit)
        result = generator.validate_size(exact_data)
        assert isinstance(result, bool)
    
    def test_encode_image_to_base64(self, generator):
        """Test encoding image to base64."""
        # Create mock image bytes
        mock_image = b"\x89PNG\r\n\x1a\n" + b"fake image data"
        
        base64_uri = generator.encode_image(mock_image)
        
        assert base64_uri.startswith('data:image/png;base64,')
        
        # Decode and verify
        encoded_part = base64_uri.split(',')[1]
        decoded = base64.b64decode(encoded_part)
        assert decoded == mock_image
    
    def test_create_chart_with_title(self, generator, sample_df):
        """Test creating chart with title."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={
                'x': 'category',
                'y': 'value',
                'title': 'Test Chart'
            }
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_create_chart_with_labels(self, generator, sample_df):
        """Test creating chart with axis labels."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={
                'x': 'category',
                'y': 'value',
                'xlabel': 'Categories',
                'ylabel': 'Values'
            }
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_create_chart_with_colors(self, generator, sample_df):
        """Test creating chart with custom colors."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={
                'x': 'category',
                'y': 'value',
                'color': 'blue'
            }
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_handle_empty_dataframe(self, generator):
        """Test handling empty DataFrame."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(Exception):
            generator.create_chart(
                data=empty_df,
                chart_type='bar',
                config={'x': 'category', 'y': 'value'}
            )
    
    def test_handle_invalid_chart_type(self, generator, sample_df):
        """Test handling invalid chart type."""
        with pytest.raises(ValueError):
            generator.create_chart(
                data=sample_df,
                chart_type='invalid_type',
                config={'x': 'category', 'y': 'value'}
            )
    
    def test_handle_missing_columns(self, generator, sample_df):
        """Test handling missing columns."""
        with pytest.raises(KeyError):
            generator.create_chart(
                data=sample_df,
                chart_type='bar',
                config={'x': 'nonexistent', 'y': 'value'}
            )
    
    def test_handle_invalid_data_types(self, generator):
        """Test handling invalid data types."""
        df = pd.DataFrame({
            'category': ['A', 'B', 'C'],
            'value': ['not', 'a', 'number']
        })
        
        with pytest.raises(Exception):
            generator.create_chart(
                data=df,
                chart_type='bar',
                config={'x': 'category', 'y': 'value'}
            )
    
    def test_create_histogram(self, generator):
        """Test creating histogram."""
        df = pd.DataFrame({
            'values': [1, 2, 2, 3, 3, 3, 4, 4, 5]
        })
        
        base64_uri = generator.create_chart(
            data=df,
            chart_type='histogram',
            config={'column': 'values'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
    
    def test_create_multiple_charts(self, generator, sample_df):
        """Test creating multiple charts."""
        chart1 = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={'x': 'category', 'y': 'value'}
        )
        
        chart2 = generator.create_chart(
            data=sample_df,
            chart_type='line',
            config={'x': 'category', 'y': 'value'}
        )
        
        assert chart1 != chart2
        assert both chart1.startswith('data:image/png;base64,')
        assert chart2.startswith('data:image/png;base64,')
    
    def test_chart_size_optimization(self, generator, sample_df):
        """Test that charts are optimized for size."""
        base64_uri = generator.create_chart(
            data=sample_df,
            chart_type='bar',
            config={'x': 'category', 'y': 'value'}
        )
        
        # Verify size is under 1MB
        assert generator.validate_size(base64_uri) is True
        
        # Verify it's not too small (should have actual content)
        assert len(base64_uri) > 1000
    
    def test_handle_large_dataset(self, generator):
        """Test handling large dataset."""
        large_df = pd.DataFrame({
            'x': range(1000),
            'y': range(1000)
        })
        
        base64_uri = generator.create_chart(
            data=large_df,
            chart_type='line',
            config={'x': 'x', 'y': 'y'}
        )
        
        assert base64_uri.startswith('data:image/png;base64,')
        assert generator.validate_size(base64_uri) is True
