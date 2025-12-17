import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_pest_trend_chart(df, pest_type='rbb_count'):
    """Create trend chart for pest counts"""
    if 'date' not in df.columns:
        df['date'] = pd.to_datetime(df[['year', 'month', 'day']].rename(
            columns={'year': 'year', 'month': 'month', 'day': 'day'}
        ), errors='coerce')
    
    df_sorted = df.sort_values('date')
    
    fig = px.line(
        df_sorted,
        x='date',
        y=pest_type,
        title=f'{pest_type.upper()} Trend Over Time',
        labels={pest_type: 'Count', 'date': 'Date'},
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_comparison_chart(df):
    """Create comparison chart between RBB and WSB"""
    monthly_data = df.groupby(['year', 'month']).agg({
        'rbb_count': 'sum',
        'wsb_count': 'sum'
    }).reset_index()
    
    monthly_data['period'] = monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str).str.zfill(2)
    
    fig = go.Figure(
        data=[
            go.Bar(name='RBB', x=monthly_data['period'], y=monthly_data['rbb_count']),
            go.Bar(name='WSB', x=monthly_data['period'], y=monthly_data['wsb_count'])
        ]
    )
    
    fig.update_layout(
        title='RBB vs WSB Monthly Comparison',
        xaxis_title='Period',
        yaxis_title='Count',
        barmode='group',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_scatter_plot(df, x_col, y_col, color_col=None):
    """Create scatter plot for correlation analysis"""
    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=f'{y_col} vs {x_col}',
        trendline='ols'
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400
    )
    
    return fig

def create_distribution_chart(df, column):
    """Create distribution histogram"""
    fig = px.histogram(
        df,
        x=column,
        title=f'Distribution of {column}',
        nbins=30
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400
    )
    
    return fig

def create_heatmap(corr_matrix):
    """Create correlation heatmap"""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0
    ))
    
    fig.update_layout(
        title='Correlation Matrix',
        height=500,
        width=600
    )
    
    return fig

def create_environmental_comparison(df, pest_col, env_col):
    """Create comparison between pest and environmental factor"""
    monthly_data = df.groupby(['year', 'month']).agg({
        pest_col: 'sum',
        env_col: 'mean'
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str).str.zfill(2),
        y=monthly_data[pest_col],
        name=pest_col,
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_data['year'].astype(str) + '-' + monthly_data['month'].astype(str).str.zfill(2),
        y=monthly_data[env_col],
        name=env_col,
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f'{pest_col} vs {env_col}',
        xaxis_title='Period',
        yaxis=dict(title=pest_col),
        yaxis2=dict(title=env_col, overlaying='y', side='right'),
        template='plotly_white',
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_area_comparison_chart(df, pest_type='rbb_count'):
    """Create bar chart comparing pest counts across areas"""
    if 'area_code' not in df.columns:
        return None
    
    area_data = df.groupby('area_code').agg({
        pest_type: 'sum'
    }).reset_index()
    
    area_data = area_data.sort_values(pest_type, ascending=False)
    
    fig = px.bar(
        area_data,
        x='area_code',
        y=pest_type,
        title=f'{pest_type.upper()} by Area',
        labels={'area_code': 'Area Code', pest_type: 'Count'},
        color=pest_type,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400
    )
    
    return fig

def create_area_trend_chart(df, area_code, pest_type='rbb_count'):
    """Create trend chart for specific area"""
    area_df = df[df['area_code'] == area_code].copy()
    
    if len(area_df) == 0:
        return None
    
    if 'date' not in area_df.columns:
        area_df['date'] = pd.to_datetime(area_df[['year', 'month', 'day']].rename(
            columns={'year': 'year', 'month': 'month', 'day': 'day'}
        ), errors='coerce')
    
    area_df = area_df.sort_values('date')
    
    fig = px.line(
        area_df,
        x='date',
        y=pest_type,
        title=f'{pest_type.upper()} Trend for Area {area_code}',
        labels={pest_type: 'Count', 'date': 'Date'},
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_area_heatmap(df):
    """Create heatmap of pest counts by area and month"""
    if 'area_code' not in df.columns or 'rbb_count' not in df.columns:
        return None
    
    heatmap_data = df.groupby(['area_code', 'month']).agg({
        'rbb_count': 'sum'
    }).reset_index()
    
    pivot_data = heatmap_data.pivot(index='area_code', columns='month', values='rbb_count').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='YlOrRd'
    ))
    
    fig.update_layout(
        title='RBB Count Heatmap by Area and Month',
        xaxis_title='Month',
        yaxis_title='Area Code',
        height=500
    )
    
    return fig

# ============================================================================
# ENHANCED VISUALIZATION FUNCTIONS
# ============================================================================

def create_pest_density_map(df, area_points_df):
    """Create scatter map showing pest density at different area points"""
    if 'area_point_id' not in df.columns:
        return None
    
    # Merge with area points to get coordinates
    merged = df.merge(area_points_df, on='area_point_id', how='left')
    
    # Aggregate pest counts by area
    agg_data = merged.groupby(['area_point_id', 'latitude', 'longitude', 'name']).agg({
        'count': 'sum',
        'density': 'mean'
    }).reset_index()
    
    fig = px.scatter_mapbox(
        agg_data,
        lat='latitude',
        lon='longitude',
        size='count',
        color='density',
        hover_name='name',
        hover_data={'area_point_id': True, 'count': True, 'density': ':.2f'},
        color_continuous_scale='YlOrRd',
        title='Pest Density Across Area Points'
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        height=600,
        margin={"r":0,"t":40,"l":0,"b":0}
    )
    
    return fig

def create_pest_density_chart(df, pest_type=None):
    """Create density distribution chart for pest observations"""
    if pest_type:
        df = df[df['pest_type'] == pest_type]
    
    if 'density' not in df.columns or len(df) == 0:
        return None
    
    fig = px.histogram(
        df,
        x='density',
        color='pest_type' if 'pest_type' in df.columns else None,
        marginal='box',
        title=f'Pest Density Distribution{" - " + pest_type.upper() if pest_type else ""}',
        labels={'density': 'Density (pests/m²)', 'count': 'Frequency'},
        nbins=30
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400
    )
    
    return fig

def create_pest_shape_plot(df):
    """Create violin plot showing pest count distribution shapes"""
    if 'pest_type' not in df.columns or 'count' not in df.columns:
        return None
    
    fig = px.violin(
        df,
        y='count',
        x='pest_type',
        color='pest_type',
        box=True,
        points='all',
        title='Pest Population Distribution Shape',
        labels={'count': 'Pest Count', 'pest_type': 'Pest Type'}
    )
    
    fig.update_layout(
        template='plotly_white',
        showlegend=False,
        height=500
    )
    
    return fig

def create_pest_vs_climate_timeseries(pest_df, env_df, pest_type='rbb', climate_var='temperature'):
    """Create dual-axis time series comparing pest counts with climate variable"""
    
    # Merge pest and environmental data by date and area
    if 'date' in pest_df.columns and 'date' in env_df.columns:
        merged = pd.merge(pest_df, env_df, on=['date', 'area_point_id'], how='inner')
    else:
        return None
    
    # Filter by pest type
    if 'pest_type' in merged.columns:
        merged = merged[merged['pest_type'] == pest_type]
    
    if len(merged) == 0:
        return None
    
    # Sort by date
    merged = merged.sort_values('date')
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Pest count line
    fig.add_trace(go.Scatter(
        x=merged['date'],
        y=merged['count'],
        name=f'{pest_type.upper()} Count',
        line=dict(color='#ef4444', width=2),
        yaxis='y1'
    ))
    
    # Climate variable line
    fig.add_trace(go.Scatter(
        x=merged['date'],
        y=merged[climate_var],
        name=climate_var.replace('_', ' ').title(),
        line=dict(color='#3b82f6', width=2, dash='dash'),
        yaxis='y2'
    ))
    
    # Update layout with dual axes
    fig.update_layout(
        title=f'{pest_type.upper()} Population vs {climate_var.replace("_", " ").title()} Over Time',
        xaxis=dict(title='Date'),
        yaxis=dict(
            title=f'{pest_type.upper()} Count',
            titlefont=dict(color='#ef4444'),
            tickfont=dict(color='#ef4444')
        ),
        yaxis2=dict(
            title=climate_var.replace('_', ' ').title(),
            titlefont=dict(color='#3b82f6'),
            tickfont=dict(color='#3b82f6'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_white',
        height=500
    )
    
    return fig

def create_area_comparison_scatter(df, x_metric='rbb_count', y_metric='wsb_count'):
    """Create scatter plot comparing two metrics across area points"""
    if 'area_point_id' not in df.columns:
        return None
    
    # Aggregate by area
    agg_data = df.groupby('area_point_id').agg({
        x_metric: 'sum',
        y_metric: 'sum',
        'count': 'count'
    }).reset_index()
    
    fig = px.scatter(
        agg_data,
        x=x_metric,
        y=y_metric,
        size='count',
        text='area_point_id',
        title=f'{x_metric.upper()} vs {y_metric.upper()} by Area Point',
        labels={
            x_metric: x_metric.replace('_', ' ').title(),
            y_metric: y_metric.replace('_', ' ').title(),
            'count': 'Observation Count'
        }
    )
    
    fig.update_traces(textposition='top center')
    fig.update_layout(template='plotly_white', height=500)
    
    return fig

def create_weekly_pest_pattern(df, pest_type=None):
    """Create visualization of pest patterns across weeks"""
    if 'week_number' not in df.columns:
        return None
    
    if pest_type and 'pest_type' in df.columns:
        df = df[df['pest_type'] == pest_type]
    
    weekly_data = df.groupby('week_number').agg({
        'count': 'mean'
    }).reset_index()
    
    fig = px.line(
        weekly_data,
        x='week_number',
        y='count',
        title=f'Average Pest Count by Week of Year{" - " + pest_type.upper() if pest_type else ""}',
        labels={'week_number': 'Week Number', 'count': 'Average Count'},
        markers=True
    )
    
    fig.update_layout(
        template='plotly_white',
        height=400,
        xaxis=dict(dtick=4)
    )
    
    return fig

def create_environmental_correlation_matrix(env_df, pest_df):
    """Create correlation heatmap between environmental factors and pest counts"""
    
    # Merge datasets
    if 'date' in env_df.columns and 'date' in pest_df.columns:
        merged = pd.merge(env_df, pest_df, on=['date', 'area_point_id'], how='inner')
    else:
        return None
    
    # Select numeric columns
    numeric_cols = merged.select_dtypes(include=['float64', 'int64']).columns
    
    # Calculate correlation matrix
    corr_matrix = merged[numeric_cols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values.round(2),
        texttemplate='%{text}',
        textfont={"size": 8}
    ))
    
    fig.update_layout(
        title='Environmental-Pest Correlation Matrix',
        height=600,
        width=700
    )
    
    return fig
