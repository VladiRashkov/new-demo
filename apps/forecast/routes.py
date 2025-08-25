from flask import Blueprint, render_template
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from prophet import Prophet

forecast_bp = Blueprint('forecast', __name__, url_prefix='/forecast')


@forecast_bp.route('/')
def temperature_chart():
    
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[['timestamp', 'temperature']].rename(
        columns={'timestamp': 'ds', 'temperature': 'y'})

    # Train Prophet model
    model = Prophet()
    model.fit(df)

    # Forecast next 48 hours (hourly)
    future = model.make_future_dataframe(periods=48, freq='H')
    forecast = model.predict(future)

    # Plot historical + forecast
    fig = go.Figure()

    # Historical data
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='firebrick')
    ))

    # Forecasted data
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        mode='lines',
        name='Forecast',
        line=dict(color='blue', dash='dash')
    ))

    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_upper'],
        mode='lines',
        name='Upper Bound',
        line=dict(color='lightblue'),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat_lower'],
        mode='lines',
        name='Lower Bound',
        line=dict(color='lightblue'),
        fill='tonexty',
        fillcolor='rgba(173,216,230,0.2)',
        showlegend=False
    ))

    
    fig.update_layout(
        title='Temperature Forecast (Next 48 Hours)',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor='#ffffff',
        paper_bgcolor='#f8f9fa',
        font=dict(color='#343a40'),
        xaxis=dict(
            tickformat='%Y-%m-%d %H:%M',
            showgrid=True,
            rangeslider=dict(visible=True),
            type='date'
        )
    )

    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    return render_template('forecast.html', chart_html=chart_html)
