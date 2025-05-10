# Data formatting utilities
"""Data formatting utilities for the application."""

import json
from typing import Dict, List, Any, Union, Optional
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, date

def format_df_to_markdown(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Format a DataFrame as a Markdown table.
    
    Args:
        df: DataFrame to format
        max_rows: Maximum number of rows to include
        
    Returns:
        Markdown table
    """
    if df.empty:
        return "No data available"
    
    # Truncate if needed
    if len(df) > max_rows:
        df = df.head(max_rows)
        footer = f"\n\n*Showing {max_rows} of {len(df)} rows*"
    else:
        footer = ""
    
    # Convert to markdown
    md_table = df.to_markdown(index=False)
    
    return md_table + footer

def format_dict_to_markdown(data: Dict[str, Any], title: str = None) -> str:
    """Format a dictionary as a Markdown list.
    
    Args:
        data: Dictionary to format
        title: Optional title for the list
        
    Returns:
        Markdown list
    """
    if not data:
        return "No data available"
    
    # Start with title if provided
    md_text = f"## {title}\n\n" if title else ""
    
    # Format each key-value pair
    for key, value in data.items():
        # Format key for display
        display_key = key.replace('_', ' ').title()
        
        # Format value based on type
        if isinstance(value, (datetime, date)):
            display_value = value.strftime("%B %d, %Y")
        elif isinstance(value, float):
            # Format as currency if it seems like a monetary value
            if 'price' in key.lower() or 'cost' in key.lower() or 'budget' in key.lower():
                display_value = f"${value:,.2f}"
            else:
                display_value = f"{value:,.2f}"
        elif isinstance(value, dict):
            # Format nested dictionary
            nested_items = [f"  - {k.replace('_', ' ').title()}: {v}" for k, v in value.items()]
            display_value = "\n" + "\n".join(nested_items)
        elif isinstance(value, list):
            # Format list
            if value:
                if isinstance(value[0], dict):
                    # List of dictionaries
                    nested_items = []
                    for item in value:
                        item_str = "\n".join([f"    - {k.replace('_', ' ').title()}: {v}" for k, v in item.items()])
                        nested_items.append(f"  - Item:\n{item_str}")
                    display_value = "\n" + "\n".join(nested_items)
                else:
                    # Simple list
                    display_value = ", ".join(str(v) for v in value)
            else:
                display_value = "None"
        else:
            display_value = str(value)
        
        md_text += f"- **{display_key}**: {display_value}\n"
    
    return md_text

def generate_chart(data: Union[Dict[str, float], pd.DataFrame], 
                  chart_type: str = 'bar',
                  title: str = '',
                  x_label: str = '',
                  y_label: str = '',
                  legend_title: str = '',
                  figsize: tuple = (10, 6)) -> str:
    """Generate a chart and return as base64 encoded string.
    
    Args:
        data: Data for the chart (dict or DataFrame)
        chart_type: Type of chart ('bar', 'pie', 'line')
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        legend_title: Legend title
        figsize: Figure size (width, height)
        
    Returns:
        Base64 encoded image string
    """
    plt.figure(figsize=figsize)
    
    # Convert dict to DataFrame if needed
    if isinstance(data, dict):
        df = pd.DataFrame({'value': list(data.values())}, index=list(data.keys()))
    else:
        df = data
    
    # Create chart based on type
    if chart_type == 'bar':
        if isinstance(data, dict):
            plt.bar(df.index, df['value'])
        else:
            df.plot(kind='bar', ax=plt.gca())
        plt.xticks(rotation=45, ha='right')
        
    elif chart_type == 'pie':
        if isinstance(data, dict):
            plt.pie(df['value'], labels=df.index, autopct='%1.1f%%')
        else:
            df.plot(kind='pie', y=df.columns[0], autopct='%1.1f%%', ax=plt.gca())
        
    elif chart_type == 'line':
        if isinstance(data, dict):
            plt.plot(df.index, df['value'], marker='o')
        else:
            df.plot(kind='line', marker='o', ax=plt.gca())
        plt.xticks(rotation=45, ha='right')
    
    elif chart_type == 'stacked_bar':
        df.plot(kind='bar', stacked=True, ax=plt.gca())
        plt.xticks(rotation=45, ha='right')
        
    elif chart_type == 'area':
        df.plot(kind='area', stacked=False, alpha=0.5, ax=plt.gca())
    
    # Set labels and title
    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    
    if legend_title and chart_type != 'pie':
        plt.legend(title=legend_title)
    
    plt.tight_layout()
    
    # Save plot to bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    
    # Encode plot as base64 string
    image_png = buffer.getvalue()
    image_base64 = base64.b64encode(image_png).decode('utf-8')
    
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"

def format_project_status(project: Dict[str, Any]) -> str:
    """Format project status for display.
    
    Args:
        project: Project data dictionary
        
    Returns:
        Formatted status string
    """
    if not project:
        return "Project data not available"
    
    status = project.get('status', 'Unknown')
    completion = project.get('completion_percentage', 0)
    
    # Define status emoji
    status_emoji = {
        'Not Started': '🔴',
        'Planning': '🟠',
        'In Progress': '🔵',
        'On Hold': '⚠️',
        'Completed': '✅',
        'Cancelled': '⛔',
    }
    
    emoji = status_emoji.get(status, '❓')
    
    # Format the status line
    status_line = f"{emoji} **Status**: {status} ({completion:.1f}% complete)"
    
    # Add timeline information if available
    timeline = []
    if 'start_date' in project and project['start_date']:
        start_date = project['start_date']
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        timeline.append(f"Start: {start_date.strftime('%b %d, %Y')}")
    
    if 'end_date' in project and project['end_date']:
        end_date = project['end_date']
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        timeline.append(f"End: {end_date.strftime('%b %d, %Y')}")
    
    if timeline:
        status_line += f"\n📅 **Timeline**: {' → '.join(timeline)}"
    
    return status_line

def format_budget_summary(budget: Dict[str, Any]) -> str:
    """Format budget summary for display.
    
    Args:
        budget: Budget data dictionary
        
    Returns:
        Formatted budget summary string
    """
    if not budget:
        return "Budget data not available"
    
    total = budget.get('total_budget', 0)
    spent = budget.get('spent', 0)
    remaining = budget.get('remaining', total - spent)
    
    # Calculate percentage spent
    if total > 0:
        percentage = (spent / total) * 100
    else:
        percentage = 0
    
    # Format the budget lines
    lines = [
        f"💰 **Total Budget**: ${total:,.2f}",
        f"💸 **Spent**: ${spent:,.2f} ({percentage:.1f}%)",
        f"💵 **Remaining**: ${remaining:,.2f}"
    ]
    
    # Add warning if over budget
    if remaining < 0:
        lines.append(f"⚠️ **Warning**: Over budget by ${abs(remaining):,.2f}")
    
    return "\n".join(lines)

def format_json_response(data: Any, indent: int = 2) -> str:
    """Format data as a JSON string.
    
    Args:
        data: Data to format
        indent: Indentation level
        
    Returns:
        Formatted JSON string
    """
    class CustomEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return super().default(obj)
    
    return json.dumps(data, indent=indent, cls=CustomEncoder)