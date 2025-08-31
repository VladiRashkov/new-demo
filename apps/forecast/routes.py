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
    df = df[['timestamp', 'temperature', 'alert']].rename(
        columns={'timestamp': 'ds', 'temperature': 'y'})

    df['date'] = df['ds'].dt.date
    daily_groups = df.groupby('date')

    charts = []
    statuses = []

    for i, (date, group) in enumerate(daily_groups):
        if len(group) < 12:
            continue

        model = Prophet()
        model.fit(group[['ds', 'y']])

        last_time = group['ds'].max()
        future = model.make_future_dataframe(periods=24, freq='H')
        future = future[future['ds'] > last_time]
        forecast = model.predict(future)

        # Generate status message
        max_temp = forecast['yhat'].max()
        trend = forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[0]

        if max_temp > 82 and trend > 0:
            status = "🔥 Critical temperature detected. Rising trend observed — initiate cooling protocols."
        elif max_temp > 82:
            status = "⚠️ High temperature detected. Maintain monitoring and prepare for intervention."
        else:
            status = "✅ Optimal performance. Temperature forecast is within safe range."

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=group['ds'], y=group['y'], mode='lines+markers', name='Historical', line=dict(color='firebrick')))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'],
                      mode='lines', name='Forecast', line=dict(color='blue', dash='dash')))

        fig.update_layout(
            title=f'Temperature Forecast from {date}',
            xaxis_title='Time',
            yaxis_title='Temp (°C)',
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(tickformat='%H:%M'),
            plot_bgcolor='#ffffff',
            paper_bgcolor='#f8f9fa',
            font=dict(color='#343a40')
        )

        charts.append(pio.to_html(fig, full_html=False,
                      include_plotlyjs='cdn' if i == 0 else False))
        statuses.append(status)

    return render_template('forecast.html', chart_status_pairs=zip(charts, statuses))
