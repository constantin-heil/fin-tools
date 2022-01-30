import finance_helper

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly

silver_list = ["AG", "AUY", "EMX", "EXK", "FNV", "GDX", "ISVLF", "KRRGF", "MMX", "MTA", "NEM", "OR", "RGLD", "SAND", "SILJ"]

q = finance_helper.querySplitter(silver_list, get_infos = True)

opt_dic = [{'label': sym, 'value': sym} for sym in q.syms]
dateix = q.dateix

app = dash.Dash(__name__)
server = app.server

multicand = html.Div([
    html.H2("Candleplots for multiple tickers"),
    dcc.Markdown('''
    * Choose tickers from the dropdown menu
    * Choose a specific range for visualization by dragging on the graph
    * The line is the 200 day rolling mean (only visible for days>200)
    '''),
    dcc.Dropdown(id = 'multicand-select-sym',
                 options = opt_dic,
                 multi = True),
    dcc.Graph(id = 'multi-cand')

])

multiline = html.Div([
    html.H2("Comparable line plots for multiple tickers"),
    dcc.Markdown('''
    * Choose tickers and date range to display
    * All lines are normalized to have same range
    * All lines are also scaled to begin at 0
    '''),
    dcc.Dropdown(id = 'multiline-select-sym',
                 options = opt_dic,
                 multi = True),
    dcc.DatePickerRange(id = 'date-select',
                        min_date_allowed = dateix[0],
                        max_date_allowed = dateix[-1],
                        display_format = "DD.MM.YYYY"),
    dcc.Graph(id = 'multi-line')
])

app.layout = html.Div([
    multicand,
    multiline
    ])

@app.callback(Output('multi-cand', 'figure'), 
              Input('multicand-select-sym', 'value'))
def multi_candleplot(sym):
    """
    return plotly candleplot from subsetted querySplitter
    """
    trace = q.from_symbolsubset(sym).get_tracelist_candlestick()
    return {'data': trace,
            'layout': {'width': 1500,
                       'height': 800}}

@app.callback(Output('multi-line', 'figure'), 
               Input('multiline-select-sym', 'value'), 
               Input('date-select', 'start_date'), 
               Input('date-select', 'end_date'))
def multi_lineplot(sym, start_date, end_date):
    """
    return plotly multi lineplot for close value of selected symbols
    """
    sym_subset = q.from_symbolsubset(sym)
    time_subset = sym_subset.from_timerange(start_date, end_date)
    trace = time_subset.get_tracelist()
    return {'data': trace,
            'layout': {'width': 1000,
                       'height': 700}}



if __name__ == "__main__":
    app.run_server()
