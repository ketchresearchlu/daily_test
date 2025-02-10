import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import io
import datetime

# Load and filter dataset
def load_data():
    df = pd.read_excel("SAMPLE_dashboard_output.xlsx")  # Update with actual file path
    df = df[df["Country"].isin(["Germany", "Austria", "Belgium", "Switzerland"])]
    df = df[df["Analysis topic"].isin(["smart #1", "smart #2", "smart #3", "smart #4", "smart #5", "smart #6"])]
    return df

df = load_data()
df["Date"] = pd.to_datetime(df["Date"])
latest_date = df["Date"].max()
#latest_date = '2025-01-31'

# Get min/max dates
min_date = df["Date"].min()
max_date = df["Date"].max()
total_days = (max_date - min_date).days

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Daily News", style={'color': 'white', 'textAlign': 'center'}),

    dcc.Dropdown(
        id='country-filter',
        options=[{"label": "All", "value": "All"}] +
                [{"label": c, "value": c} for c in df["Country"].unique()],
        value="All",
        clearable=False,
        style={'width': '200px', 'display': 'inline-block', 'color': 'black'}
    ),

    dcc.Graph(id='mentions-over-time'),

    # Date Slider with formatted marks
    dcc.RangeSlider(
        id='date-slider',
        min=0,
        max=total_days,
        value=[0, total_days],  
        marks={i: (min_date + datetime.timedelta(days=i)).strftime('%Y-%m-%d') 
               for i in range(0, total_days+1, max(1, total_days // 10))},  
        step=1,
        tooltip={"placement": "bottom", "always_visible": True}, 
    ),

    html.Button("Export Graph Data (Excel)", id="export-graph-btn", n_clicks=0, style={'margin': '10px'}),
    dcc.Download(id="download-graph-data"),

    html.H2("Article Summaries", style={'color': 'white', 'text-align': 'center'}),

    dcc.DatePickerSingle(
        id='date-picker',
        date=latest_date.strftime('%Y-%m-%d'),
        #date=latest_date,
        display_format='YYYY-MM-DD',
        style={'color': 'black'},
    ),

    html.Button("Reset to Latest", id="latest-button", n_clicks=0, style={'margin-left': '10px'}),

    html.Div(id="news-entries"),

    html.Button("Export News Data (Excel)", id="export-news-btn", n_clicks=0, style={'margin': '10px'}),
    dcc.Download(id="download-news-data")
], style={'backgroundColor': '#001f3f', 'color': 'white', 'padding': '20px'})

# Update Graph
@app.callback(
    Output("mentions-over-time", "figure"),
    [Input("date-slider", "value"), Input("country-filter", "value")]
)
def update_graph(slider_range, country):
    start_date = min_date + datetime.timedelta(days=slider_range[0])
    end_date = min_date + datetime.timedelta(days=slider_range[1])

    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    if country != "All":
        filtered_df = filtered_df[filtered_df["Country"] == country]

    grouped_df = filtered_df.groupby(["Date", "Analysis topic"]).size().reset_index(name="count")
    fig = px.line(grouped_df, x="Date", y="count", color="Analysis topic",
                  title=f"Mentions from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    fig.update_traces(hovertemplate='%{x|%Y-%m-%d}<br>Mentions: %{y}')
    fig.update_layout(plot_bgcolor='#001f3f', paper_bgcolor='#001f3f', font_color='white')

    return fig

# Update News Entries
@app.callback(
    Output("news-entries", "children"),
    [Input("date-picker", "date")]
)
def update_news(selected_date):
    selected_date = pd.to_datetime(selected_date)
    daily_df = df[df["Date"] == selected_date]

    content = []
    if not daily_df.empty:
        for topic in daily_df["Analysis topic"].unique():
            topic_entries = daily_df[daily_df["Analysis topic"] == topic]
            content.append(html.H2(topic, style={'color': 'white'}))
            for _, row in topic_entries.iterrows():
                content.append(html.Div([
                    html.H4(row["Headline"], style={'color': 'white'}),
                    html.P(row["Snippet"], style={'color': 'white'}),
                    html.A("Read more", href=row["Original Link"], target="_blank", style={'color': 'lightblue'})
                ]))
    return content

# Reset Date Picker
@app.callback(
    Output("date-picker", "date"),
    [Input("latest-button", "n_clicks")]
)
def set_latest_date(n_clicks):
    return latest_date
    #return latest_date.strftime('%Y-%m-%d')

# Export Graph Data
@app.callback(
    Output("download-graph-data", "data"),
    [Input("export-graph-btn", "n_clicks")],
    [State("date-slider", "value"), State("country-filter", "value")],
    prevent_initial_call=True
)
def export_graph_data(n_clicks, slider_range, country):
    start_date = min_date + datetime.timedelta(days=slider_range[0])
    end_date = min_date + datetime.timedelta(days=slider_range[1])

    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    if country != "All":
        filtered_df = filtered_df[filtered_df["Country"] == country]

    grouped_df = filtered_df.groupby(["Date", "Analysis topic"]).size().reset_index(name="count")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        grouped_df.to_excel(writer, index=False, sheet_name="Graph Data")

    output.seek(0)
    return dcc.send_bytes(output.getvalue(), "filtered_graph_data.xlsx")

# Export News Data
@app.callback(
    Output("download-news-data", "data"),
    [Input("export-news-btn", "n_clicks")],
    [State("date-picker", "date")],
    prevent_initial_call=True
)
def export_news_data(n_clicks, selected_date):
    selected_date = pd.to_datetime(selected_date)
    daily_df = df[df["Date"] == selected_date]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        daily_df.to_excel(writer, index=False, sheet_name="News Data")

    output.seek(0)
    return dcc.send_bytes(output.getvalue(), "filtered_news_data.xlsx")

# Run Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
