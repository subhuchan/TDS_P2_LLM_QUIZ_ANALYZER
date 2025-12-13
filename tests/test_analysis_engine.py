"""Unit tests for analysis engine."""

import pytest
import pandas as pd
import numpy as np

from src.analysis_engine import AnalysisEngine


class TestAnalysisEngine:
    """Test suite for AnalysisEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create AnalysisEngine instance."""
        return AnalysisEngine()
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'name': ['John', 'Jane', 'Bob', 'Alice'],
            'age': [30, 25, 35, 28],
            'salary': [50000, 60000, 75000, 55000],
            'department': ['IT', 'HR', 'IT', 'HR']
        })
    
    def test_filter_equal(self, engine, sample_df):
        """Test filtering with equal condition."""
        result = engine.filter_data(sample_df, [{'column': 'department', 'op': '==', 'value': 'IT'}])
        
        assert len(result) == 2
        assert all(result['department'] == 'IT')
    
    def test_filter_greater_than(self, engine, sample_df):
        """Test filtering with greater than condition."""
        result = engine.filter_data(sample_df, [{'column': 'age', 'op': '>', 'value': 28}])
        
        assert len(result) == 2
        assert all(result['age'] > 28)
    
    def test_filter_less_than(self, engine, sample_df):
        """Test filtering with less than condition."""
        result = engine.filter_data(sample_df, [{'column': 'salary', 'op': '<', 'value': 60000}])
        
        assert len(result) == 2
        assert all(result['salary'] < 60000)
    
    def test_filter_multiple_conditions(self, engine, sample_df):
        """Test filtering with multiple conditions."""
        result = engine.filter_data(sample_df, [
            {'column': 'department', 'op': '==', 'value': 'IT'},
            {'column': 'age', 'op': '>', 'value': 30}
        ])
        
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'Bob'
    
    def test_aggregate_sum(self, engine, sample_df):
        """Test sum aggregation."""
        result = engine.aggregate(sample_df, group_by='department', operations={'salary': 'sum'})
        
        assert len(result) == 2
        it_salary = result[result['department'] == 'IT']['salary'].values[0]
        assert it_salary == 125000  # 50000 + 75000
    
    def test_aggregate_mean(self, engine, sample_df):
        """Test mean aggregation."""
        result = engine.aggregate(sample_df, group_by='department', operations={'age': 'mean'})
        
        assert len(result) == 2
        it_avg_age = result[result['department'] == 'IT']['age'].values[0]
        assert it_avg_age == 32.5  # (30 + 35) / 2
    
    def test_aggregate_count(self, engine, sample_df):
        """Test count aggregation."""
        result = engine.aggregate(sample_df, group_by='department', operations={'name': 'count'})
        
        assert len(result) == 2
        it_count = result[result['department'] == 'IT']['name'].values[0]
        assert it_count == 2
    
    def test_aggregate_multiple_operations(self, engine, sample_df):
        """Test multiple aggregation operations."""
        result = engine.aggregate(sample_df, group_by='department', operations={
            'salary': 'sum',
            'age': 'mean',
            'name': 'count'
        })
        
        assert len(result) == 2
        assert 'salary' in result.columns
        assert 'age' in result.columns
        assert 'name' in result.columns
    
    def test_sort_ascending(self, engine, sample_df):
        """Test sorting in ascending order."""
        result = engine.sort_data(sample_df, by='age', ascending=True)
        
        assert result.iloc[0]['name'] == 'Jane'  # age 25
        assert result.iloc[-1]['name'] == 'Bob'  # age 35
    
    def test_sort_descending(self, engine, sample_df):
        """Test sorting in descending order."""
        result = engine.sort_data(sample_df, by='salary', ascending=False)
        
        assert result.iloc[0]['name'] == 'Bob'  # salary 75000
        assert result.iloc[-1]['name'] == 'John'  # salary 50000
    
    def test_calculate_statistics(self, engine, sample_df):
        """Test calculating statistics."""
        stats = engine.calculate_statistics(sample_df, column='age')
        
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert stats['mean'] == 29.5
        assert stats['min'] == 25
        assert stats['max'] == 35
    
    def test_calculate_correlation(self, engine, sample_df):
        """Test calculating correlation."""
        corr = engine.calculate_correlation(sample_df, 'age', 'salary')
        
        assert isinstance(corr, float)
        assert -1 <= corr <= 1
    
    def test_filter_empty_result(self, engine, sample_df):
        """Test filtering that returns empty result."""
        result = engine.filter_data(sample_df, [{'column': 'age', 'op': '>', 'value': 100}])
        
        assert len(result) == 0
    
    def test_filter_with_nulls(self, engine):
        """Test filtering data with null values."""
        df = pd.DataFrame({
            'name': ['John', 'Jane', None, 'Bob'],
            'age': [30, None, 35, 28]
        })
        
        result = engine.filter_data(df, [{'column': 'age', 'op': '>', 'value': 28}])
        
        assert len(result) == 2
    
    def test_aggregate_empty_group(self, engine):
        """Test aggregation with empty groups."""
        df = pd.DataFrame({
            'category': ['A', 'A'],
            'value': [10, 20]
        })
        
        result = engine.aggregate(df, group_by='category', operations={'value': 'sum'})
        
        assert len(result) == 1
        assert result.iloc[0]['value'] == 30
    
    def test_percentile_calculation(self, engine, sample_df):
        """Test percentile calculation."""
        p50 = engine.calculate_percentile(sample_df, 'age', 50)
        p75 = engine.calculate_percentile(sample_df, 'age', 75)
        
        assert p50 == 29.0  # Median
        assert p75 > p50
    
    def test_rank_data(self, engine, sample_df):
        """Test ranking data."""
        result = engine.rank_data(sample_df, by='salary')
        
        assert 'rank' in result.columns
        assert result[result['name'] == 'Bob']['rank'].values[0] == 1  # Highest salary
        assert result[result['name'] == 'John']['rank'].values[0] == 4  # Lowest salary
    
    def test_normalize_data(self, engine, sample_df):
        """Test normalizing data."""
        result = engine.normalize_data(sample_df, column='age')
        
        assert result['age'].min() >= 0
        assert result['age'].max() <= 1
    
    def test_handle_edge_case_single_row(self, engine):
        """Test handling single row DataFrame."""
        df = pd.DataFrame({'name': ['John'], 'age': [30]})
        
        stats = engine.calculate_statistics(df, 'age')
        
        assert stats['mean'] == 30
        assert stats['std'] == 0
    
    def test_handle_edge_case_all_same_values(self, engine):
        """Test handling DataFrame with all same values."""
        df = pd.DataFrame({'value': [10, 10, 10, 10]})
        
        stats = engine.calculate_statistics(df, 'value')
        
        assert stats['mean'] == 10
        assert stats['std'] == 0
        assert stats['min'] == 10
        assert stats['max'] == 10
