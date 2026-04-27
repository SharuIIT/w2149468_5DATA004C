
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(layout="wide")

# --- Title of the App ---
st.title("GHG Emissions Data Analysis")

# --- Data Loading ---
@st.cache_data
def load_data():
    df = pd.read_csv('UNFCCC_v30_2016-2024.csv')
    # The cleaned_data.csv should already have 'All greenhouse gases - (CO2 equivalent)' removed
    # as per previous notebook steps, but adding this line for robustness just in case.
    df = df[df['Pollutant_name'] != 'All greenhouse gases - (CO2 equivalent)']
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")

# Year Slider
min_year = int(df['Year'].min())
max_year = int(df['Year'].max())
selected_year = st.sidebar.slider("Select Year", min_value=min_year, max_value=max_year, value=min_year)

# Pollutant Dropdown
pollutant_options = sorted(df['Pollutant_name'].unique())
selected_pollutant = st.sidebar.selectbox("Select Pollutant", pollutant_options, index=pollutant_options.index('CH4') if 'CH4' in pollutant_options else 0)

# Sector Dropdown
sector_options = sorted(df['Sector_name'].unique())
selected_sector = st.sidebar.selectbox("Select Sector", sector_options, index=sector_options.index('Cars') if 'Cars' in sector_options else 0)

# Country Multi-select for Time Series
all_countries = sorted(df['Country'].unique())
default_countries_ts = ['Germany', 'France', 'Italy', 'Spain', 'United Kingdom']
# Filter default countries to only include those present in the dataset
default_countries_ts = [c for c in default_countries_ts if c in all_countries]
selected_countries_ts = st.sidebar.multiselect(
    "Select Countries for Time Series",
    all_countries,
    default=default_countries_ts
)

# --- Plotly Template ---
plotly_template = 'plotly_white'

# --- Visualisation 1: Choropleth Map ---
st.subheader("1. Total Emissions per Country (Europe, Selected Year & Pollutant)")
df_map = df[(df['Year'] == selected_year) & (df['Pollutant_name'] == selected_pollutant)]
choropleth_data = df_map.groupby(['Country', 'Country_code_3'])['emissions'].sum().reset_index()

fig_choropleth = px.choropleth(
    choropleth_data,
    locations='Country_code_3',
    color='emissions',
    hover_name='Country',
    color_continuous_scale=px.colors.sequential.Plasma,
    title=f'Total {selected_pollutant} Emissions in Europe ({selected_year})',
    template=plotly_template,
    scope='europe'
)
st.plotly_chart(fig_choropleth, use_container_width=True)

# --- Visualisation 2: Time Series Line Chart ---
st.subheader("2. Total Emissions: Multiple Countries, Filtered by Pollutant & Sector (2016-2024)")
if selected_countries_ts:
    df_ts = df[
        (df['Country'].isin(selected_countries_ts)) &
        (df['Pollutant_name'] == selected_pollutant) &
        (df['Sector_name'] == selected_sector)
    ]
    time_series_data = df_ts.groupby(['Year', 'Country'])['emissions'].sum().reset_index()

    fig_ts = px.line(
        time_series_data,
        x='Year',
        y='emissions',
        color='Country',
        title=f'Total {selected_pollutant} Emissions from {selected_sector} (2016-2024)',
        labels={'emissions': 'Total Emissions'},
        template=plotly_template
    )

    fig_ts.add_vline(
        x=2020,
        line_width=2,
        line_dash="dash",
        line_color="red",
        annotation_text="COVID-19",
        annotation_position="top right"
    )
    st.plotly_chart(fig_ts, use_container_width=True)
else:
    st.info("Please select countries for the Time Series Line Chart from the sidebar.")

# --- Visualisation 3: Stacked Bar Chart ---
st.subheader("3. Total Emissions per Country (Stacked by Top 10 Sectors)")
df_stacked = df[
    (df['Year'] == selected_year) &
    (df['Pollutant_name'] == selected_pollutant)
]

stacked_bar_data = df_stacked.groupby(['Country', 'Sector_name'])['emissions'].sum().reset_index()

# Identify top 10 sectors by total emissions for readability
top_10_sectors = stacked_bar_data.groupby('Sector_name')['emissions'].sum().nlargest(10).index
stacked_bar_data_filtered = stacked_bar_data[stacked_bar_data['Sector_name'].isin(top_10_sectors)]

fig_stacked = px.bar(
    stacked_bar_data_filtered,
    x='Country',
    y='emissions',
    color='Sector_name',
    title=f'Total {selected_pollutant} Emissions by Country and Top 10 Sectors ({selected_year})',
    labels={'emissions': 'Total Emissions'},
    template=plotly_template
)
st.plotly_chart(fig_stacked, use_container_width=True)

# --- Visualisation 4: Top N Emitters Horizontal Bar Chart ---
st.subheader("4. Top 10 Emitters by Total Emissions")
df_top_emitters = df[
    (df['Year'] == selected_year) &
    (df['Pollutant_name'] == selected_pollutant)
]
top_emitters_data = df_top_emitters.groupby('Country')['emissions'].sum().nlargest(10).reset_index()

# Sort data for the horizontal bar chart
top_emitters_data = top_emitters_data.sort_values(by='emissions', ascending=True)

fig_top_emitters = px.bar(
    top_emitters_data,
    x='emissions',
    y='Country',
    orientation='h',
    title=f'Top 10 Countries by Total {selected_pollutant} Emissions ({selected_year})',
    labels={'emissions': 'Total Emissions'},
    template=plotly_template
)
st.plotly_chart(fig_top_emitters, use_container_width=True)

# --- Visualisation 5: Sector vs Country Heatmap ---
st.subheader("5. Emissions Heatmap: Top 15 Sectors vs Countries")
df_heatmap = df[
    (df['Year'] == selected_year) &
    (df['Pollutant_name'] == selected_pollutant)
]

# Aggregate emissions by sector and country
heatmap_data = df_heatmap.groupby(['Sector_name', 'Country'])['emissions'].sum().reset_index()

# Identify top 15 sectors by total emissions
top_15_sectors_heatmap = heatmap_data.groupby('Sector_name')['emissions'].sum().nlargest(15).index
heatmap_data_filtered = heatmap_data[heatmap_data['Sector_name'].isin(top_15_sectors_heatmap)]

# Pivot the data to create the matrix for the heatmap
if not heatmap_data_filtered.empty:
    heatmap_pivot = heatmap_data_filtered.pivot_table(index='Sector_name', columns='Country', values='emissions', fill_value=0)

    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale=px.colors.sequential.Plasma
    ))

    fig_heatmap.update_layout(
        title=f'Emissions Heatmap: Top 15 Sectors vs Countries ({selected_pollutant}, {selected_year})',
        xaxis_title='Country',
        yaxis_title='Sector Name',
        template=plotly_template
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
else:
    st.info(f"No data available for heatmap with selected year ({selected_year}) and pollutant ({selected_pollutant}).")
