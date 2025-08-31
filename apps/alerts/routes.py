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
    df['date'] = df['timestamp'].dt.date

    # Dynamically detect anomalies based on temperature thresholds
    df['is_anomaly'] = (df['temperature'] > 82) | (df['temperature'] < 40)

    # Fill or generate alert messages
    df['alert'] = df['alert'].fillna('')
    df.loc[df['is_anomaly'] & (df['alert'] == ''), 'alert'] = df['temperature'].apply(
        lambda t: 'Critical high temperature' if t > 82 else 'Critical low temperature'
    )

    # Group by day
    daily_groups = df.groupby('date')
    charts = []

    for i, (date, group) in enumerate(daily_groups):
        anomalies = group[group['is_anomaly']]

        fig = go.Figure()

        # Main temperature line
        fig.add_trace(go.Scatter(
            x=group['timestamp'],
            y=group['temperature'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='firebrick'),
            marker=dict(size=6)
        ))

        # Anomaly markers
        if not anomalies.empty:
            fig.add_trace(go.Scatter(
                x=anomalies['timestamp'],
                y=anomalies['temperature'],
                mode='markers',
                name='Anomalies',
                marker=dict(color='red', size=10, symbol='x'),
                hovertext=anomalies['alert']
            ))

        fig.update_layout(
            title=f'Temperature Alerts on {date}',
            xaxis_title='Timestamp',
            yaxis_title='Temperature (°C)',
            height=400,
            margin=dict(l=40, r=40, t=40, b=30),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa',
            font=dict(color='#343a40'),
            xaxis=dict(
                tickformat='%H:%M',
                showgrid=True,
                rangeslider=dict(visible=False),
                type='date'
            )
        )

        chart_html = pio.to_html(fig, full_html=False,
                                 include_plotlyjs='cdn' if i == 0 else False)
        charts.append(chart_html)

    return render_template('alerts.html', charts=charts)
