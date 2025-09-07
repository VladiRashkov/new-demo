from flask import Blueprint, render_template
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from prophet import Prophet
vibration_bp = Blueprint('vibrations', __name__, url_prefix='/vibrations')


@vibration_bp.route('/vibrations')
def vibration_chart():
    # Load and prepare data
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.rename(columns={'timestamp': 'ds', 'vibration_mm_s_RMS': 'y'})

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
    max_vib = forecast_future['yhat'].max()
    if trend_rise > 1.5 and max_vib > 7.0:
        status_message = "⚠️ Vibration trend is rising toward unsatisfactory levels. Immediate inspection recommended."
    elif trend_rise > 1.5:
        status_message = "📈 Vibration is forecasted to increase. Monitoring advised to prevent mechanical wear."
    else:
        status_message = "✅ Vibration forecast remains within acceptable range."

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
        y0=7.1,
        y1=7.1,
        line=dict(color='red', width=3)
    )
    fig.add_annotation(
        x=forecast['ds'].iloc[-1],
        y=7.1,
        text='Limit 7.1 mm/s RMS',
        showarrow=False,
        font=dict(color='black', size=16),
        yshift=10
    )
    fig.update_layout(
        title='Vibration Forecast',
        title_x=0.5,
        xaxis_title='Time',
        yaxis_title='Vibration (mm/s RMS)',
        height=500,
        width=1300,
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='#fdfdfd',
        paper_bgcolor='#ffffff',
        font=dict(color='#343a40', size=14),
        xaxis=dict(tickformat='%H:%M', showgrid=True,
                   gridcolor='rgba(0,0,0,0.05)', zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False),
        legend=dict(orientation='h', yanchor='bottom', y=0.02, xanchor='center', x=0.5,
                    bgcolor='rgba(255,255,255,0.5)', bordercolor='rgba(0,0,0,0.1)', borderwidth=1)
    )
    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

    # Time window
    end_time = df['ds'].max()
    start_time = end_time.normalize()

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
        name='Vibration',
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
        y0=7.1,
        y1=7.1,
        line=dict(color='red', width=3)
    )
    anomaly_fig.add_annotation(
        x=end_time,
        y=7.1,
        text='Limit 7.1 mm/s RMS',
        showarrow=False,
        font=dict(color='black', size=16),
        yshift=10
    )
    anomaly_fig.update_layout(
        title='Vibration Anomalies',
        title_x=0.5,
        xaxis_title='Time',
        yaxis_title='Vibration (mm/s RMS)',
        height=500,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor='#fdfdfd',
        paper_bgcolor='#ffffff',
        font=dict(color='#343a40', size=14),
        xaxis=dict(range=[start_time, end_time], tickformat='%H:%M',
                   showgrid=True, gridcolor='rgba(0,0,0,0.05)', zeroline=False),
        yaxis=dict(range=[0, 10], dtick=1, showgrid=True,
                   gridcolor='rgba(0,0,0,0.05)', zeroline=False),
        legend=dict(orientation='h', yanchor='bottom',
                    y=0.02, xanchor='center', x=0.5)
    )
    anomaly_chart_html = pio.to_html(
        anomaly_fig, full_html=False, include_plotlyjs=False)

    # Performance chart
    
    return render_template(
        'vibrations.html',
        chart_html=chart_html,
        anomaly_chart_html=anomaly_chart_html,
        status_message=status_message
    )
