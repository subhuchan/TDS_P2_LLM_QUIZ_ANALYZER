"""Chart generator for creating visualizations and encoding them as base64 URIs."""

import base64
import io
from typing import Any, Dict, Optional, Union

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from src.logging_config import get_logger

logger = get_logger(__name__)


class ChartGenerator:
    """Handles creation of various chart types and base64 encoding."""
    
    # Maximum size for base64 encoded output (1MB)
    MAX_SIZE_BYTES = 1024 * 1024
    
    def __init__(self, dpi: int = 100, figsize: tuple = (10, 6)):
        """
        Initialize the chart generator.
        
        Args:
            dpi: Dots per inch for image resolution
            figsize: Default figure size as (width, height) in inches
        """
        self.dpi = dpi
        self.figsize = figsize
        logger.info(f"ChartGenerator initialized with dpi={dpi}, figsize={figsize}")
    
    def create_chart(
        self,
        data: pd.DataFrame,
        chart_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a chart and return it as a base64-encoded data URI.
        
        Args:
            data: DataFrame containing the data to visualize
            chart_type: Type of chart ('bar', 'line', 'scatter', 'pie')
            config: Optional configuration dict with chart parameters
                Common parameters:
                - x: Column name for x-axis
                - y: Column name(s) for y-axis (can be list for multiple series)
                - title: Chart title
                - xlabel: X-axis label
                - ylabel: Y-axis label
                - color: Color or list of colors
                - figsize: Override default figure size
                - dpi: Override default DPI
        
        Returns:
            Base64-encoded data URI string (data:image/png;base64,...)
        
        Raises:
            ValueError: If chart type is unsupported or data is invalid
            RuntimeError: If encoded output exceeds 1MB size limit
        """
        logger.info(f"Creating {chart_type} chart")
        
        if config is None:
            config = {}
        
        # Get figure parameters
        figsize = config.get('figsize', self.figsize)
        dpi = config.get('dpi', self.dpi)
        
        # Create figure
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        try:
            # Generate chart based on type
            if chart_type == 'bar':
                self._create_bar_chart(ax, data, config)
            elif chart_type == 'line':
                self._create_line_chart(ax, data, config)
            elif chart_type == 'scatter':
                self._create_scatter_chart(ax, data, config)
            elif chart_type == 'pie':
                self._create_pie_chart(ax, data, config)
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
            
            # Apply common styling
            self._apply_styling(ax, config)
            
            # Convert to base64
            base64_uri = self._encode_to_base64(fig)
            
            # Validate size
            if not self.validate_size(base64_uri):
                raise RuntimeError(
                    f"Encoded chart exceeds 1MB limit. "
                    f"Try reducing DPI or figure size."
                )
            
            logger.info(f"Chart created successfully, size: {len(base64_uri)} bytes")
            return base64_uri
            
        finally:
            plt.close(fig)
    
    def _create_bar_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Create a bar chart."""
        x = config.get('x')
        y = config.get('y')
        
        if not x or not y:
            raise ValueError("Bar chart requires 'x' and 'y' parameters in config")
        
        if x not in data.columns:
            raise ValueError(f"Column '{x}' not found in data")
        
        # Handle single or multiple y columns
        if isinstance(y, str):
            if y not in data.columns:
                raise ValueError(f"Column '{y}' not found in data")
            y_cols = [y]
        else:
            y_cols = y
            for col in y_cols:
                if col not in data.columns:
                    raise ValueError(f"Column '{col}' not found in data")
        
        # Get styling parameters
        color = config.get('color')
        horizontal = config.get('horizontal', False)
        stacked = config.get('stacked', False)
        
        # Create bar chart
        if len(y_cols) == 1:
            if horizontal:
                ax.barh(data[x], data[y_cols[0]], color=color)
            else:
                ax.bar(data[x], data[y_cols[0]], color=color)
        else:
            # Multiple series
            x_pos = np.arange(len(data[x]))
            width = 0.8 / len(y_cols) if not stacked else 0.8
            
            for i, col in enumerate(y_cols):
                if stacked:
                    bottom = data[y_cols[:i]].sum(axis=1) if i > 0 else None
                    ax.bar(x_pos, data[col], width, label=col, bottom=bottom)
                else:
                    offset = width * (i - len(y_cols) / 2 + 0.5)
                    ax.bar(x_pos + offset, data[col], width, label=col)
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(data[x])
            ax.legend()
        
        logger.debug(f"Bar chart created with {len(y_cols)} series")
    
    def _create_line_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Create a line chart."""
        x = config.get('x')
        y = config.get('y')
        
        if not x or not y:
            raise ValueError("Line chart requires 'x' and 'y' parameters in config")
        
        if x not in data.columns:
            raise ValueError(f"Column '{x}' not found in data")
        
        # Handle single or multiple y columns
        if isinstance(y, str):
            if y not in data.columns:
                raise ValueError(f"Column '{y}' not found in data")
            y_cols = [y]
        else:
            y_cols = y
            for col in y_cols:
                if col not in data.columns:
                    raise ValueError(f"Column '{col}' not found in data")
        
        # Get styling parameters
        color = config.get('color')
        marker = config.get('marker', 'o')
        linestyle = config.get('linestyle', '-')
        linewidth = config.get('linewidth', 2)
        
        # Create line chart
        for i, col in enumerate(y_cols):
            line_color = color[i] if isinstance(color, list) and i < len(color) else color
            ax.plot(
                data[x],
                data[col],
                marker=marker,
                linestyle=linestyle,
                linewidth=linewidth,
                color=line_color,
                label=col if len(y_cols) > 1 else None
            )
        
        if len(y_cols) > 1:
            ax.legend()
        
        # Rotate x-axis labels if they're dates or long strings
        if data[x].dtype == 'object' or pd.api.types.is_datetime64_any_dtype(data[x]):
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        logger.debug(f"Line chart created with {len(y_cols)} series")
    
    def _create_scatter_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Create a scatter plot."""
        x = config.get('x')
        y = config.get('y')
        
        if not x or not y:
            raise ValueError("Scatter chart requires 'x' and 'y' parameters in config")
        
        if x not in data.columns:
            raise ValueError(f"Column '{x}' not found in data")
        if y not in data.columns:
            raise ValueError(f"Column '{y}' not found in data")
        
        # Get styling parameters
        color = config.get('color', 'blue')
        size = config.get('size', 50)
        alpha = config.get('alpha', 0.6)
        marker = config.get('marker', 'o')
        
        # Handle color by column
        c_col = config.get('color_by')
        if c_col and c_col in data.columns:
            color = data[c_col]
        
        # Handle size by column
        s_col = config.get('size_by')
        if s_col and s_col in data.columns:
            size = data[s_col]
        
        # Create scatter plot
        scatter = ax.scatter(
            data[x],
            data[y],
            c=color,
            s=size,
            alpha=alpha,
            marker=marker
        )
        
        # Add colorbar if color is by column
        if c_col and c_col in data.columns:
            plt.colorbar(scatter, ax=ax, label=c_col)
        
        logger.debug(f"Scatter chart created with {len(data)} points")
    
    def _create_pie_chart(
        self,
        ax: plt.Axes,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> None:
        """Create a pie chart."""
        values = config.get('values')
        labels = config.get('labels')
        
        if not values:
            raise ValueError("Pie chart requires 'values' parameter in config")
        
        if values not in data.columns:
            raise ValueError(f"Column '{values}' not found in data")
        
        # Get labels
        if labels:
            if labels not in data.columns:
                raise ValueError(f"Column '{labels}' not found in data")
            label_data = data[labels]
        else:
            label_data = data.index
        
        # Get styling parameters
        colors = config.get('colors')
        autopct = config.get('autopct', '%1.1f%%')
        startangle = config.get('startangle', 90)
        explode = config.get('explode')
        
        # Create pie chart
        ax.pie(
            data[values],
            labels=label_data,
            colors=colors,
            autopct=autopct,
            startangle=startangle,
            explode=explode
        )
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        logger.debug(f"Pie chart created with {len(data)} slices")
    
    def _apply_styling(
        self,
        ax: plt.Axes,
        config: Dict[str, Any]
    ) -> None:
        """Apply common styling to the chart."""
        # Set title
        title = config.get('title')
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Set axis labels
        xlabel = config.get('xlabel')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=11)
        
        ylabel = config.get('ylabel')
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=11)
        
        # Set grid
        if config.get('grid', True):
            ax.grid(True, alpha=0.3, linestyle='--')
        
        # Tight layout to prevent label cutoff
        plt.tight_layout()
    
    def _encode_to_base64(self, fig: plt.Figure) -> str:
        """
        Encode matplotlib figure to base64 data URI.
        
        Args:
            fig: Matplotlib figure object
        
        Returns:
            Base64-encoded data URI string
        """
        # Save figure to bytes buffer
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        
        # Encode to base64
        image_bytes = buffer.getvalue()
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create data URI
        data_uri = f"data:image/png;base64,{base64_encoded}"
        
        logger.debug(f"Encoded image to base64, size: {len(data_uri)} bytes")
        return data_uri
    
    def validate_size(self, base64_uri: str) -> bool:
        """
        Validate that the base64-encoded output is under 1MB.
        
        Args:
            base64_uri: Base64-encoded data URI string
        
        Returns:
            True if size is valid, False otherwise
        """
        size_bytes = len(base64_uri.encode('utf-8'))
        is_valid = size_bytes <= self.MAX_SIZE_BYTES
        
        if not is_valid:
            logger.warning(
                f"Chart size {size_bytes} bytes exceeds limit of {self.MAX_SIZE_BYTES} bytes"
            )
        else:
            logger.debug(f"Chart size {size_bytes} bytes is within limit")
        
        return is_valid
