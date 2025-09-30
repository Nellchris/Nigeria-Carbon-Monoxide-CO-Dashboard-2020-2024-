import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import leafmap.foliumap as leafmap
import plotly.graph_objects as go
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import mapclassify

# ---------------------------
# Load data
# ---------------------------
@st.cache_data
def load_data():
    return gpd.read_file("data/nigeria_state_co.geojson")

gdf = load_data()

# ---------------------------
# Streamlit page setup
# ---------------------------
st.set_page_config(layout="wide", page_title="Nigeria CO Dashboard", page_icon="🌍")
st.title("Nigeria Carbon Monoxide (CO) Dashboard (2020 - 2024)")

# ---------------------------
# Reshape for line chart
# ---------------------------
df_new = gdf.melt(
    id_vars=["State"], 
    value_vars=["2020_mean", "2021_mean", "2022_mean", "2023_mean", "2024_mean"], 
    var_name="Year", 
    value_name="CO (mol/m²)"
)
df_new["Year"] = df_new["Year"].str.replace("_mean", "").astype(int)

years = sorted(df_new["Year"].unique())
states = sorted(df_new["State"].unique())

# Layout
col_side, col_map, col_chart = st.columns([1, 3, 1])

# shared year selector above the map and tables
with col_map:
    st.markdown("**Use the dropdown below to select the year for the map and tables.**")
    year_selected = st.selectbox("Select Year", years, index=len(years)-1)


# Filter for year
year_data = df_new[df_new['Year'] == year_selected].copy()


# ---------------------------
# TOP CENTER: Choropleth Map
# ---------------------------
with col_map:
    column_name = f"{year_selected}_mean"
    gdf['CO (mol/m²)'] = gdf[column_name].astype(float)

    m = leafmap.Map(center=[9.082, 8.6753], zoom=6.5, tiles="CartoDB.DarkMatter")

    m.add_data(
        gdf,
        column=column_name,
        scheme="NaturalBreaks",   # ✅ classification
        k=5,                      # 5 classes
        cmap="Greens",            # green gradient
        legend_title=f"CO (mol/m²) {year_selected}",
        popups=["State", column_name],
        
    )

    m.to_streamlit(height=450)


# ---------------------------
top3 = year_data.nlargest(3, 'CO (mol/m²)')[['State', 'CO (mol/m²)']].reset_index(drop=True)
low3 = year_data.nsmallest(3, 'CO (mol/m²)')[['State', 'CO (mol/m²)']].reset_index(drop=True)
with col_side:
    st.markdown("Top 3 (Highest CO)")
    if not top3.empty:
        st.table(top3.set_index("State"))
    else:
        st.write("No data")

    st.markdown("Bottom 3 (Lowest CO)")
    if not low3.empty:
        st.table(low3.set_index("State"))
    else:
        st.write("No data")
    

    # ---- National average ----
    national_avg = year_data["CO (mol/m²)"].mean().round(3)

    # Scale the value between min and max for color mapping
    vmin, vmax = year_data["CO (mol/m²)"].min(), year_data["CO (mol/m²)"].max()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.get_cmap("Greens")  # same as map
    color = mcolors.to_hex(cmap(norm(national_avg)))

    # Create donut chart with value in the middle
    fig_donut = go.Figure(data=[go.Pie(
        values=[1],  # single slice
        hole=0.65,  # donut hole size
        marker_colors=[color],
        textinfo="none"
    )])

    # Add annotation (value in center)
    fig_donut.update_layout(
        annotations=[
            dict(
                text=f"<b>{national_avg} mol/m² </b>",
                x=0.5, y=0.5, font_size=16, showarrow=False,
                font=dict(color="green" if norm(national_avg) > 0.5 else "white")
            )
        ],
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=150,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Show donut chart
    st.plotly_chart(fig_donut, use_container_width=True)

    # Subtitle below the donut
    st.markdown(
        f"<p style='text-align:center; font-size:14px; color:lightgray;'>"
        f"Nigeria's Average CO Level in <b>{year_selected}</b>"
        f"</p>",
        unsafe_allow_html=True
    )
        


# line chart
with col_chart:
    state_selected = st.selectbox("Select State to analyze the CO concentration", states, key="state_chart", index=0)
    state_data = df_new[df_new['State'] == state_selected].sort_values('Year')
    fig = px.line(state_data, x='Year', y='CO (mol/m²)', markers=True, labels={"CO (mol/m²)": "CO (mol/m²)", "Year": "Year"})
    fig.update_traces(mode='markers+lines', line=dict(color='green'))
    st.plotly_chart(fig, use_container_width=True)



# Define the modal function
@st.dialog("Dashboard Information")
def show_info_modal():
    st.markdown("### 🌍 About This Dashboard")
    st.write(
        "This dashboard provides an **interactive visualization of Carbon Monoxide (CO) "
        "levels across Nigeria between 2020 and 2024**. "
        "The data was derived and processed in Google Earth Engine and aggregated by state. "
        "It helps reveal spatial and temporal patterns of CO distribution, highlighting areas "
        "with higher pollution risks and comparing trends across the Country."
    )

    st.write(
        "Key features include:\n"
        "- Interactive map visualization\n"
        "- Top 3 and bottom 3 states highlighted by CO concentration\n"
        "- Line chart showing annual CO trends for selected states\n"
        "- National average CO level displayed in a donut style chart"
    )

    st.markdown("### 👤 Author")
    st.write(
        "This dashboard was created by **Nelson Christopher**, a Geospatial Analyst, "
        "experienced in **data analysis and visualization**. Passionate about applying innovative "
        "technologies to address environmental challenges, while promoting **sustainable management practices** "
        "using GIS and remote sensing."
    )


    # Add a unique key for the button
    if st.button("OK", key="modal_ok_btn"):
        st.session_state.show_info = False
        st.rerun()


# Check session state to show modal on first load
if "show_info" not in st.session_state:
    st.session_state.show_info = True

if st.session_state.show_info:
    show_info_modal()
else:
    with st.sidebar:
        if st.button("View Info", key="sidebar_info_btn"):
            show_info_modal()




