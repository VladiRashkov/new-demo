from flask import Blueprint, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio
from prophet import Prophet

noise_bp = Blueprint('noise', __name__, url_prefix='/noise')


@noise_bp.route('/')
def noise_forecast():
    df = pd.read_csv('data/mock_data.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Summary stats
    total_deviations = df['deviation'].sum()
    avg_noise = round(df['noise_level_dB'].mean(), 2)
    max_noise = round(df['noise_level_dB'].max(), 2)

    # Prepare data for Prophet
    prophet_df = df[['timestamp', 'noise_level_dB']].rename(columns={
        'timestamp': 'ds',
        'noise_level_dB': 'y'
    })

    model = Prophet()
    model.fit(prophet_df)


    # Generate future timestamps starting from the last timestamp
    # Generate timestamps covering full historical range + future
    full_range = pd.date_range(
        start=df['timestamp'].min(), end=df['timestamp'].max(), freq='H')
    future_extra = pd.date_range(start=df['timestamp'].max(), periods=6, freq='H')
    future_all = pd.DataFrame({'ds': full_range.append(future_extra)})

    forecast = model.predict(future_all)

    forecast_df = forecast[['ds', 'yhat']].rename(columns={
        'ds': 'timestamp',
        'yhat': 'noise_level_dB'
    })

    # Generate forecast message
    forecast_max = forecast_df['noise_level_dB'].max()
    forecast_min = forecast_df['noise_level_dB'].min()
    forecast_start = forecast_df['noise_level_dB'].iloc[0]
    forecast_end = forecast_df['noise_level_dB'].iloc[-1]

    if forecast_max > 55:
        forecast_message = "🔴 Warning: forecasted noise exceeds 55 dB threshold."
    elif forecast_end > forecast_start:
        forecast_message = "🟠 Noise levels are expected to rise gradually."
    elif forecast_end < forecast_start:
        forecast_message = "🟢 Noise levels are expected to decline."
    else:
        forecast_message = "🔵 Noise levels are expected to remain stable."


    # Chart generation
    charts = []
    for i, (date, group) in enumerate(df.groupby(df['timestamp'].dt.date)):
        full_day = df[df['timestamp'].dt.date == date]

        # Filter forecast to start after the last timestamp of the current day
        last_time = full_day['timestamp'].max()
        forecast_day = forecast_df[forecast_df['timestamp'] > last_time]

        fig = px.line(
            full_day,
            x='timestamp',
            y='noise_level_dB',
            title=f'Noise Levels and Forecast on {date}',
            labels={'noise_level_dB': 'Noise Level (dB)'}
        )

        # Add forecast line starting from last timestamp
        fig.add_scatter(
            x=forecast_day['timestamp'],
            y=forecast_day['noise_level_dB'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='blue', dash='dot')
        )

        # Add transparent scatter to trigger color scale
        fig.add_scatter(
            x=full_day['timestamp'],
            y=full_day['noise_level_dB'],
            mode='markers',
            marker=dict(
                size=0.1,
                color=full_day['noise_level_dB'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Noise Level (dB)'),
                opacity=0.0
            ),
            hoverinfo='skip',
            showlegend=False
        )

        # Threshold line
        fig.add_shape(
            type='line',
            x0=full_day['timestamp'].min(),
            x1=forecast_df['timestamp'].max(),
            y0=55,
            y1=55,
            line=dict(color='red', width=3, dash='dash')
        )

        fig.add_annotation(
            x=full_day['timestamp'].min(),
            y=55,
            text='Threshold: 55 dB',
            showarrow=False,
            yshift=20,
            font=dict(color='red')
        )

        fig.update_layout(
            legend=dict(
                y=1.05,
                yanchor='top',
                x=0.9,
                xanchor='left',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='LightGrey',
                borderwidth=1
            ),
            plot_bgcolor='#f8f9fa',
            paper_bgcolor='#f8f9fa',
            font=dict(color='#343a40'),
            margin=dict(l=40, r=40, t=40, b=30)
        )

        chart_html = pio.to_html(fig, full_html=False,
                                 include_plotlyjs='cdn' if i == 0 else False)
        charts.append(chart_html)
        

        # Detect anomalies: compare actual vs predicted
   # Detect trend reversals in actual noise data
    df_sorted = df.sort_values('timestamp').reset_index(drop=True)


# Identify local maxima and minima
    # Sort and reset index
    df_sorted = df.sort_values('timestamp').reset_index(drop=True)

    # Identify local maxima and minima
    df_sorted['prev'] = df_sorted['noise_level_dB'].shift(1)
    df_sorted['next'] = df_sorted['noise_level_dB'].shift(-1)

    df_sorted['is_reversal'] = (
        # local max
        ((df_sorted['noise_level_dB'] > df_sorted['prev']) & (df_sorted['noise_level_dB'] > df_sorted['next'])) |
        ((df_sorted['noise_level_dB'] < df_sorted['prev']) & (
            df_sorted['noise_level_dB'] < df_sorted['next']))    # local min
    )

    trend_reversals = df_sorted[df_sorted['is_reversal']]
    total_anomalies = int(df_sorted['is_reversal'].sum())



    # Create trend reversal chart
    fig_trend = px.line(
        df_sorted,
        x='timestamp',
        y='noise_level_dB',
        title='Trend Reversals in Noise Levels',
        labels={'noise_level_dB': 'Noise Level (dB)'}
    )

    fig_trend.add_scatter(
        x=trend_reversals['timestamp'],
        y=trend_reversals['noise_level_dB'],
        mode='markers',
        name='Anomalies',
        marker=dict(
            size=10,
            color='red',
            symbol='circle',
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=["Anomalities" for _ in trend_reversals['timestamp']],
        hoverinfo='text+x+y'
    )

    fig_trend.add_shape(
        type='line',
        x0=df_sorted['timestamp'].min(),
        x1=df_sorted['timestamp'].max(),
        y0=55,
        y1=55,
        line=dict(color='red', width=2, dash='dash')
    )

    fig_trend.add_annotation(
        x=df_sorted['timestamp'].min() + pd.Timedelta(hours=2),
        y=55,
        text='Threshold: 55 dB',
        showarrow=False,
        yshift=20,
        font=dict(color='red')
    )

    fig_trend.update_layout(
        legend=dict(
            y=1.05,
            yanchor='top',
            x=0.9,
            xanchor='left',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='LightGrey',
            borderwidth=1
        ),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='#f8f9fa',
        font=dict(color='#343a40'),
        margin=dict(l=40, r=40, t=40, b=30)
    )
    fig_trend.add_scatter(
        x=full_day['timestamp'],
        y=full_day['noise_level_dB'],
        mode='markers',
        marker=dict(
            size=0.1,
            color=full_day['noise_level_dB'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Noise Level (dB)'),
            opacity=0.0
        ),
        hoverinfo='skip',
        showlegend=False
    )

    trend_chart_html = pio.to_html(
        fig_trend, full_html=False, include_plotlyjs=False)
    charts.append(trend_chart_html)



    return render_template(
        'noise.html',
        charts=charts,
        total_deviations=total_deviations,
        avg_noise=avg_noise,
        max_noise=max_noise,
        forecast_message=forecast_message,
        total_anomalies=total_anomalies
    )
