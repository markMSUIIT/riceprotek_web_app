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
