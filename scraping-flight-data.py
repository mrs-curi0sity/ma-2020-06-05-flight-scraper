import dash
import dash_core_components as dcc
import dash_html_components as html

from dash.dependencies import Input, Output

import plotly.graph_objs as go

import os.path
import requests
from datetime import datetime
import pandas as pd

import dash_auth


USERNAME_PASSWORD_PAIRS = [['peter', 'lustig'], ['schnett', 'schnoo']]

app = dash.Dash()
auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)

# make app deployable
server = app.server

# scrape every 30 seconds
INTERVAL_IN_MS = 30000
flight_count_path = 'flight_count.csv'

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

# file already exists
if os.path.isfile(flight_count_path):
    df_previous_flight_count = pd.read_csv(flight_count_path, parse_dates=['timestamp'],  index_col = False)
# first recording:
else:
    df_previous_flight_count = pd.DataFrame(columns = ['timestamp', 'active_flights_count'])

timestamp_list = list(df_previous_flight_count['timestamp'])
counter_list = list(df_previous_flight_count['active_flights_count'])


@app.callback(Output('counter-text', 'children'),
             [Input('interval-component', 'n_intervals')])
def update_flights(n):
    url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?faa=1\
           &mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&stats=1"
    res = requests.get(url, headers = {'User-Agent': 'Mozilla/5.0'})
    data = res.json()
    counter = 0
    for element in data["stats"]["total"]:
        counter += data["stats"]["total"][element]
    counter_list.append(counter)
    timestamp_list.append(datetime.now())
    print(f'[INFO] {len(counter_list)} now: {timestamp_list[-1]}, counter: {counter}')

    df_flight_counter_current = pd.DataFrame({'timestamp': timestamp_list, 'active_flights_count': counter_list})
    df_flight_count_all = pd.concat([df_previous_flight_count, df_flight_counter_current]).sort_values(by = 'timestamp').drop_duplicates()
    df_flight_count_all.to_csv(flight_count_path, index = False)
    
    return f'active flights right now: {counter}'


@app.callback(Output('graph-number-of-flights', 'figure'),
             [Input('interval-component', 'n_intervals')])
def update_graph(n):
    df_flight_count_all = pd.read_csv(flight_count_path).sort_values(by = 'timestamp')
    figure = go.Figure(
        data = [go.Scatter(
            x = df_flight_count_all['timestamp'],
            #x = list(range(len(counter_list))),
            y = df_flight_count_all['active_flights_count'],
            mode = 'lines+markers'
        )]
    ) 
    return figure


if __name__ == '__main__':
    app.run_server()