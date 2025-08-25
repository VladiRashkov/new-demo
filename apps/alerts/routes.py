from flask import Blueprint, render_template
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


@alerts_bp.route('/')
def alerts():
    # Load and prepare data
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Separate anomalies
    anomalies = df[df['anomaly'] == 1]

    # Create figure
    fig = go.Figure()

    # Main temperature line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['temperature'],
        mode='lines+markers',
        name='Temperature',
        line=dict(color='firebrick'),
        marker=dict(size=6)
    ))

    # Anomaly markers
    fig.add_trace(go.Scatter(
        x=anomalies['timestamp'],
        y=anomalies['temperature'],
        mode='markers',
        name='Anomalies',
        marker=dict(color='red', size=10, symbol='x'),
        hovertext=anomalies['alert']
    ))

    # Layout styling
    fig.update_layout(
        title='Temperature Over Time',
        xaxis_title='Timestamp',
        yaxis_title='Temperature (°C)',
        height=450,
        margin=dict(l=40, r=40, t=40, b=30),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa',
        font=dict(color='#343a40'),
        xaxis=dict(
            tickformat='%Y-%m-%d %H:%M',
            showgrid=True,
            rangeslider=dict(visible=True),
            type='date'
        )
    )

    # Convert to HTML
    chart_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
    return render_template('alerts.html', chart_html=chart_html)
