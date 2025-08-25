from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio

anomalies_bp = Blueprint('anomalies', __name__, url_prefix='/anomalies')


@anomalies_bp.route('/')
def anomalies():
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df_anomalies = df[df['anomaly'] == 1].copy()
    df_anomalies['severity'] = df_anomalies['temperature'] * \
        df_anomalies['pressure']

   
    total_anomalies = len(df_anomalies)
    avg_temp = round(df_anomalies['temperature'].mean(), 2)
    max_pressure = round(df_anomalies['pressure'].max(), 2)

    
    fig = px.scatter(
        df_anomalies,
        x='timestamp',
        y='temperature',
        color='pressure',
        size='severity',
        hover_data=['alert'],
        title='Detected Anomalies (Temperature vs Time)'
    )

    fig.update_layout(
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa',
        font=dict(color='#343a40'),
        margin=dict(l=40, r=40, t=40, b=30)
    )

    graph_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

    return render_template(
        'anomalies.html',
        graph_html=graph_html,
        total_anomalies=total_anomalies,
        avg_temp=avg_temp,
        max_pressure=max_pressure
    )
