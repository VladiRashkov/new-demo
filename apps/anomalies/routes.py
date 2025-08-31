from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio

anomalies_bp = Blueprint('anomalies', __name__, url_prefix='/anomalies')


@anomalies_bp.route('/')
def anomalies():
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Filter anomalies
    df_anomalies = df[df['anomaly'] == 1].copy()
    df_anomalies['severity'] = df_anomalies['temperature'] * \
        df_anomalies['pressure']
    df_anomalies['date'] = df_anomalies['timestamp'].dt.date

    # Summary stats
    total_anomalies = len(df_anomalies)
    avg_temp = round(df_anomalies['temperature'].mean(), 2)
    max_pressure = round(df_anomalies['pressure'].max(), 2)

    # Generate one chart per day
    charts = []
    for i, (date, group) in enumerate(df_anomalies.groupby('date')):
        fig = px.scatter(
            group,
            x='timestamp',
            y='temperature',
            color='pressure',
            size='severity',
            hover_data=['alert'],
            title=f'Anomalies on {date}'
        )
        fig.update_layout(
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa',
            font=dict(color='#343a40'),
            margin=dict(l=40, r=40, t=40, b=30)
        )
        chart_html = pio.to_html(fig, full_html=False,
                                 include_plotlyjs='cdn' if i == 0 else False)
        charts.append(chart_html)

    return render_template(
        'anomalies.html',
        charts=charts,
        total_anomalies=total_anomalies,
        avg_temp=avg_temp,
        max_pressure=max_pressure
    )
