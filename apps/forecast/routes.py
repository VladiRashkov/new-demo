from flask import Blueprint, render_template
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from prophet import Prophet

forecast_bp = Blueprint('forecast', __name__, url_prefix='/forecast')


@forecast_bp.route('/')
def temperature_chart():
    # Load and prepare data
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.rename(columns={'timestamp': 'ds', 'temperature': 'y'})

    # Prophet forecast
    model = Prophet()
    model.fit(df[['ds', 'y']])
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    last_timestamp = df['ds'].max()
    forecast_future = forecast[forecast['ds'] > last_timestamp]

    # Status message
    trend_rise = forecast_future['yhat'].iloc[-1] - \
        forecast_future['yhat'].iloc[0]
    max_temp = forecast_future['yhat'].max()
    if trend_rise > 2 and max_temp > 65:
        status_message = "⚠️ Forecast indicates a rising temperature trend approaching critical levels. Please ensure cooling protocols and safety measures are in place."
    elif trend_rise > 2:
        status_message = "📈 Temperature is forecasted to rise steadily. Monitoring is advised to prevent overheating."
    else:
        status_message = "✅ Temperature forecast remains stable. No immediate action required."

    # Forecast chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines+markers',
        name='Historical',
        line=dict(color='black', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=forecast_future['ds'],
        y=forecast_future['yhat'],
        mode='lines',
        name='Forecast',
        line=dict(color='orange', width=4, dash='dot'),
        fill='tozeroy',
        fillcolor='rgba(255,255,255,0.1)'
    ))
    fig.add_shape(
        type='line',
        x0=df['ds'].min(),
        x1=forecast['ds'].max(),
        y0=80,
        y1=80,
        line=dict(color='red', width=3)
    )
    fig.add_annotation(
        x=forecast['ds'].iloc[-1],
        y=80,
        text='80°C',
        showarrow=False,
        font=dict(color='black', size=16),
        yshift=10
    )
    fig.update_layout(
        title='Temperature Forecast',
        title_x=0.5,
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        height=500,
        width=700,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='#fdfdfd',
        paper_bgcolor='#ffffff',
        font=dict(color='#343a40', size=14),
        xaxis=dict(
            tickformat='%H:%M',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=0.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(255,255,255,0.5)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        )
    )
    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

    # Define custom time window for anomaly and performance charts
    end_time = df['ds'].max()
    start_time = end_time.normalize()  # 00:00 of the same day

    # Anomaly chart
    df['prev'] = df['y'].shift(1)
    df['next'] = df['y'].shift(-1)
    df['anomaly'] = ((df['y'] > df['prev']) & (df['y'] > df['next'])) | (
        (df['y'] < df['prev']) & (df['y'] < df['next']))
    anomaly_points = df[df['anomaly']]

    anomaly_fig = go.Figure()
    anomaly_fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Temperature',
        line=dict(color='black', width=4)
    ))
    anomaly_fig.add_trace(go.Scatter(
        x=anomaly_points['ds'],
        y=anomaly_points['y'],
        mode='markers',
        name='Anomalies',
        marker=dict(symbol='x', color='red', size=10),
        showlegend=True
    ))
    anomaly_fig.add_shape(
        type='line',
        x0=start_time,
        x1=end_time,
        y0=80,
        y1=80,
        line=dict(color='red', width=3)
    )
    anomaly_fig.add_annotation(
        x=end_time,
        y=80,
        text='80°C',
        showarrow=False,
        font=dict(color='black', size=16),
        yshift=10
    )
    anomaly_fig.update_layout(
        title='Anomalies',
        title_x=0.5,
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor='#fdfdfd',
        paper_bgcolor='#ffffff',
        font=dict(color='#343a40', size=14),
        xaxis=dict(
            range=[start_time, end_time],
            tickformat='%H:%M',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        yaxis=dict(
            range=[0, 100],
            dtick=10,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=0.02,
            xanchor='center',
            x=0.5
        )
    )
    anomaly_chart_html = pio.to_html(
        anomaly_fig, full_html=False, include_plotlyjs=False)

    # Performance chart
    df['delta'] = df['y'] - df['ambient_temperature']
    performance_fig = go.Figure()
    performance_fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['y'],
        mode='lines',
        name='Water Heater Temp',
        line=dict(color='black', width=4)
    ))
    performance_fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['ambient_temperature'],
        mode='lines',
        name='Ambient Temp',
        line=dict(color='green', width=4)
    ))
    performance_fig.add_trace(go.Scatter(
        x=df['ds'],
        y=df['delta'],
        mode='lines',
        name='Delta',
        line=dict(color='blue', width=4, dash='dot')
    ))
    performance_fig.add_shape(
        type='line',
        x0=start_time,
        x1=end_time,
        y0=80,
        y1=80,
        line=dict(color='red', width=3)
    )
    performance_fig.add_annotation(
        x=end_time,
        y=80,
        text='80°C',
        showarrow=False,
        font=dict(color='black', size=16),
        yshift=10
    )
    performance_fig.update_layout(
        title='Water Heater & Ambient Temperature',
        title_x=0.5,
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor='#fdfdfd',
        paper_bgcolor='#ffffff',
        font=dict(color='#343a40', size=14),
        xaxis=dict(
            range=[start_time, end_time],
            tickformat='%H:%M',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        yaxis=dict(
            range=[0, 100],
            dtick=10,
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=0.02,
            xanchor='center',
            x=0.5
        )
    )
    performance_chart_html = pio.to_html(
        performance_fig, full_html=False, include_plotlyjs=False)

    return render_template(
        'forecast.html',
        chart_html=chart_html,
        anomaly_chart_html=anomaly_chart_html,
        performance_chart_html=performance_chart_html,
        status_message=status_message
    )
