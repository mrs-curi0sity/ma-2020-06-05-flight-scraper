import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output

import plotly.graph_objs as go

import io
import os
import requests
from datetime import datetime
import pandas as pd

import dash_auth

import logging
import boto3
from botocore.exceptions import ClientError

# aws s3 config
# workaround for missing credentials
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
s3_client = boto3.client('s3')
BUCKET_NAME = 'ma-2020-06-flight-scraper'
FILE_NAME = 'flight_count.csv'

# dash credentials
USERNAME_PASSWORD_PAIRS = [['peter', 'lustig'], ['schnett', 'schnoo']]
app = dash.Dash()
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)

# make app deployable
server = app.server

# scrape every 30 seconds
INTERVAL_IN_MS = 30000



app.layout = html.Div([
    html.H1('Scraping flight data'),
    html.Div([
        html.Iframe(src = 'https://www.flightradar24.com/',
                width = 1200, 
                height = 500)
    ]),
    html.Div([
        html.Pre(id = 'counter-text',
                children = 'Number of flights right now'),
        dcc.Interval(id = 'interval-component',
                    interval = INTERVAL_IN_MS, 
                    n_intervals = 0),
        dcc.Graph(id = 'graph-number-of-flights', 
                 style = {'widht': 1200})
    ])
])


@app.callback(Output('counter-text', 'children'),
             [Input('interval-component', 'n_intervals')])
def update_flights(n):
    # read in previous data
    obj = s3_client.get_object(Bucket= BUCKET_NAME , Key = FILE_NAME)
    df_previous_flight_count = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8', index_col = False)
    df_previous_flight_count.columns = ['timestamp', 'active_flights_count']
    
    # scrape count
    url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1\
           &mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&stats=1"
    res = requests.get(url, headers = {'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    counter = 0
    for element in data["stats"]["total"]:
        counter += data["stats"]["total"][element]
    
    # add line to df_flight_count_all
    df_flight_counter_current = pd.DataFrame({'timestamp': [datetime.now()], 'active_flights_count': counter})
    df_flight_count_all = pd.concat([df_previous_flight_count, df_flight_counter_current])#.sort_values(by = 'timestamp').drop_duplicates()
    
    print(f'[INFO previous] {df_previous_flight_count.tail(2)}')
    print(f'\n[INFO current] {df_flight_counter_current}')
    print(f'\n[INFO all] {df_flight_count_all.tail(2)}')
    df_flight_count_all.to_csv('flight_count_backup_real_data_is_on_s3.csv', index = False)
    
    print('[INFO] writing to S3')
    # df_flight_count_all.to_csv(flight_count_path, index = False)
    df_flight_count_all.to_csv(f's3://{BUCKET_NAME}/{FILE_NAME}', index = False)
    
    return f'active flights right now: {counter}'


@app.callback(Output('graph-number-of-flights', 'figure'),
             [Input('interval-component', 'n_intervals')])
def update_graph(n):
    # df_flight_count_all = pd.read_csv(flight_count_path).sort_values(by = 'timestamp')
    obj = s3_client.get_object(Bucket= BUCKET_NAME , Key = FILE_NAME)
    flight_count = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')
    
    figure = go.Figure(
        data = [go.Scatter(
            x = flight_count['timestamp'],
            y = flight_count['active_flights_count'],
            mode = 'lines+markers'
        )]
    ) 
    return figure


if __name__ == '__main__':
    app.run_server()
