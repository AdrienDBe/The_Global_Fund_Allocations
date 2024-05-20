import streamlit as st
import requests
import pandas as pd
import numpy as np
import wbgapi as wb
import plotly.express as px
import plotly.graph_objects as go
from streamlit_lottie import st_lottie
from datetime import date
from sklearn.cluster import KMeans
from kneed import KneeLocator

# emojis list: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="TGF Allocations API", page_icon="🎗", layout="wide")

# Use local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("style/style.css")

# Remove whitespace from the top of the page and sidebar
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem
                }
        </style>
        """, unsafe_allow_html=True)

st.markdown("""
<style>
div[data-testid="metric-container"] {
   background-color: #12151D;
   border: 1px solid #283648 ;
   border-radius: 5px;
   padding: 1% 1% 1% 5%;
   color: #04AA6D;
   overflow-wrap: break-word;
}
/* breakline for metric text         */
div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
   overflow-wrap: break-word;
   white-space: break-spaces;
   color: white;
}
</style>
""", unsafe_allow_html=True)

# resize expanders
st.markdown("""
<style>
.streamlit-expanderHeader {
    font-size: medium;
    color:#ad8585;   
    }
.st-bd {border-style: none;}
</style>
""", unsafe_allow_html=True)

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Landing page

if 'count' not in st.session_state:
	st.session_state.count = 0

if st.session_state.count == 0:
    arrival_message = st.empty()
    with arrival_message.container():
        st.title("Global Fund API explorer")
        st.subheader("Funding allocations")
        col1,col_mid, col2 = st.columns([4,0.1,1], gap='small')
        col1.write("<p style='text-align: justify;font-size: 18px;'>"
                   "This app imports data from the Global Fund API and displays it in a Streamlit web app."
                   "<br/>It allows the user to navigate between several information dimensions and represent it visually with "
                 "different level of granularity (region, country, disease, stakeholder etc.)"
                   " The data is also grouped by Region, Income level, or Country (using the World Bank API) depending "
                 "on the user's selection.",unsafe_allow_html=True)
        lottie_url = "https://lottie.host/285a7a0c-1d81-4a8f-9df5-c5bebaae5663/UDqNAwwYUo.json"
        lottie_json = load_lottieurl(lottie_url)
        with col2:
            st_lottie(lottie_json, height=150, key="loading_gif2")

        with st.expander("Read more about the Global Fund (TGF), what is an API and how to access TGF API"):
            col1, col2, col3 = st.columns([1, 1, 1], gap='small')
            with col1:
                # GF details
                st.subheader("The Global Fund")
                st.markdown("<p style='text-align: justify;font-size: 18px;'>"
                         "<a href='https://www.theglobalfund.org/en/'>The Global Fund </a> is a partnership designed to accelerate the end of AIDS, tuberculosis and "
                        "malaria as epidemics. <br> It prioritizes: results-based work, accountability, preparing countries"
                        " for graduation from aid, investing in people as assets for development and inclusive governance."
                        " To do so, the Global Fund mobilizes and invests more than US$4 billion a year to support programs "
                        "run by local experts in more than 100 countries in partnership with governments, civil society, "
                        "technical agencies, the private sector and people affected by the diseases. <br> You can visit <a href='https://www.theglobalfund.org/en/funding-model/'>this page</a> to"
                        " learn more about the organization Funding Model.</p>", unsafe_allow_html=True)
            with col2:
                st.subheader("API")
                st.markdown("<p style='text-align: justify;font-size: 18px;'>"
                            "An API, or Application Programming Interface, allows different applications to communicate and exchange data with one another. "
                            "In the case of the World Health Organization (WHO), The Global Fund, and the World Bank, these organizations have created APIs "
                            "to increase transparency and provide better access to information for stakeholders in their activities."
                            "<a href='https://en.wikipedia.org/wiki/API'> <br>Read more on Wikipedia</a></p>",
                            unsafe_allow_html=True)
            with col3:
                st.subheader("The Global Fund API")
                # GF details
                st.markdown("<p style='text-align: justify;font-size: 18px;'>"
                            "The Global Fund API <a href='https://data-service.theglobalfund.org/api'> (link to documentation)</a>"
                            " is providing access to different data including: <br>Lookup Lists, Funding Allocations, Donors & Implementation Partners,"
                            " various Grants information, information on Resource Mobilization and several de-normalized views of all eligibility records."
                            "<br>To offer more visualization options, we also imported the <a href='https://datahelpdesk.worldbank.org/knowledgebase/articles/906519-world-bank-country-and-lending-groups'> World Bank regional groupings and Income group classifications </a> from the World Bank API and merged them with the country list from the WHO.",
                            unsafe_allow_html=True)

        col1, col2 = st.columns([10, 35], gap='small')
        col1.subheader("API status")

        url2 = "https://data-service.theglobalfund.org/v3.3/odata/VGrantAgreementImplementationPeriods"
        response1 = requests.get(url2)
        if response1.status_code != 200:
            col2.warning( "There seems to be an error with the Global Fund API (status code: {})".format(response1.status_code))
            col2.markdown("<p style='text-align: justify;font-size: 18px;'>"
                        "The API is currently unavailable (see <a href='https://data-service.theglobalfund.org/v3.3/odata/VGrantAgreementImplementationPeriods'> this link </a> )".format(response1.status_code)
                        ,unsafe_allow_html=True)
        else:
            col2.success("Connection to the Global Fund API established successfully")

        if response1.status_code != 200 :
            col2.info("This app will be accessible once the connection is back")

        col1, col2 = st.columns([10, 35], gap='small')
        col1.subheader("Disclaimer")
        col2.write("<p style='text-align: justify;font-size: 18px;'>"
            "Please note that the information provided in this page is created and shared by me as an individual and "
            "should not be taken as an official representation of the Global Fund."
            "<br>For accurate and up-to-date information, please consult the Global Fund official data explorer.",
            unsafe_allow_html=True)
        if response1.status_code == 200:
            disclaimer_confirmation = col2.button('I understand')
            if disclaimer_confirmation:
                st.session_state.count = 1
                st.experimental_rerun()

if st.session_state.count >= 1:

    # Use local CSS for background waves
    with open('./style/wave.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

    # Remove whitespace from the top of the page and sidebar
    st.markdown("""
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 0rem
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    div[data-testid="metric-container"] {
    background-color: #12151D;
    border: 1px solid #283648 ;
    border-radius: 5px;
    padding: 1% 1% 1% 5%;
    color: #04AA6D;
    overflow-wrap: break-word;
    }
    /* breakline for metric text         */
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
    overflow-wrap: break-word;
    white-space: break-spaces;
    color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    header_space = st.container()
    with header_space:
        col1, col2, col3 = st.columns([8, 35,8], gap='small')
        col1.markdown(
            "<span style='text-align: justify; font-size: 280% ; color:#ffffff'> **Global Fund <br>API explorer** </span> </p>",
            unsafe_allow_html=True)
        col2.markdown(
            "<span style='text-align: justify; font-size: 280%; color:#04AA6D'> **Funding allocation** </span> <br>"
            "The Global Fund's funding allocation process is designed to strategically distribute resources to fight AIDS, tuberculosis, "
            "and malaria, prioritizing countries with the highest disease burdens and the least ability to pay. The allocation process follows "
            "a comprehensive methodology that takes into account several factors: Disease Burden and Economic Capacity, Performance and Absorptive "
            "Capacity, Catalytic Investments, Eligibility, and Strategic Initiatives. </span> "
            "<span style='color:grey'>Loading takes a few seconds the first time.</span> </p>",
            unsafe_allow_html=True)

    @st.cache_data(show_spinner=False)
    def Loading_API_Allocations():
        service_url0 = 'https://api-gf-api-gf-02.azurewebsites.net/v3.3/odata/Allocations'
        response0 = requests.get(service_url0)
        if response0.ok:
            data0j = response0.json()
            df_allocations = pd.DataFrame(data0j["value"])
            columns_to_keep = [
                'allocationId',
                'geographicAreaId',
                'multiCountryName',
                'componentId',
                'periodStartYear',
                'periodEndYear',
                'allocationAmount'
            ]
            df_allocations = df_allocations[columns_to_keep]
            return df_allocations
        else:
            st.caption("Global Fund API cannot be loaded")
            return None

    @st.cache_data(show_spinner=False)
    def Loading_API_GeographicAreas():
        service_url_areas = 'https://api-gf-api-gf-02.azurewebsites.net/v3.3/odata/GeographicAreas'
        response_areas = requests.get(service_url_areas)
        service_url_levels = 'https://api-gf-api-gf-02.azurewebsites.net/v3.3/odata/GeographicAreaLevels'
        response_levels = requests.get(service_url_levels)

        if response_areas.ok and response_levels.ok:
            data_areas = response_areas.json()
            data_levels = response_levels.json()
            
            df_geographicAreas = pd.DataFrame(data_areas["value"])
            df_geographicLevels = pd.DataFrame(data_levels["value"])

            columns_to_keep = [
                'geographicAreaId',
                'geographicAreaCode_ISO3',
                'geographicAreaLevelId',
                'geographicAreaName',
                'geographicAreaParentId'
            ]
            df_geographicAreas = df_geographicAreas[columns_to_keep]

            df_geographicAreas = df_geographicAreas.merge(
                df_geographicAreas[['geographicAreaId', 'geographicAreaName']],
                left_on='geographicAreaParentId',
                right_on='geographicAreaId',
                how='left',
                suffixes=('', '_parent')
            )

            df_geographicAreas.rename(columns={'geographicAreaName_parent': 'parentGeographicAreaName'}, inplace=True)
            df_geographicAreas.drop(columns=['geographicAreaParentId', 'geographicAreaId_parent'], inplace=True)

            df_geographicAreas = df_geographicAreas.merge(
                df_geographicLevels[['geographicAreaLevelId', 'geographicAreaLevelName']],
                on='geographicAreaLevelId',
                how='left'
            )

            df_geographicAreas.drop(columns=['geographicAreaLevelId'], inplace=True)

            return df_geographicAreas
        else:
            st.caption("Global Fund API cannot be loaded")
            return None

    @st.cache_data(show_spinner=False)
    def Loading_API_Components():
        service_url_components = 'https://api-gf-api-gf-02.azurewebsites.net/v3.3/odata/Components'
        response_components = requests.get(service_url_components)
        if response_components.ok:
            data_components = response_components.json()
            df_components = pd.DataFrame(data_components["value"])
            return df_components[['componentId', 'componentName']]
        else:
            st.caption("Global Fund API cannot be loaded")
            return None

    @st.cache_data(show_spinner=False)
    def Loading_API_MultiCountries():
        service_url_multicountries = 'https://api-gf-api-gf-02.azurewebsites.net/v3.3/odata/MultiCountries'
        response_multicountries = requests.get(service_url_multicountries)
        if response_multicountries.ok:
            data_multicountries = response_multicountries.json()
            df_multicountries = pd.DataFrame(data_multicountries["value"])
            return df_multicountries[['multiCountryName', 'geographicAreaId']]
        else:
            st.caption("Global Fund API cannot be loaded")
            return None

    # Load the data
    df_allocations = Loading_API_Allocations()
    df_geographicAreas = Loading_API_GeographicAreas()
    df_components = Loading_API_Components()
    df_multicountries = Loading_API_MultiCountries()

    # Merge the datasets
    if df_allocations is not None and df_geographicAreas is not None and df_components is not None and df_multicountries is not None:
        
        df_allocations = df_allocations.merge(df_multicountries.rename(columns={'geographicAreaId': 'multicountryGeographicAreaId'}), on='multiCountryName', how='left')

        # Use the geographicAreaId from the multicountry data if the original geographicAreaId is null
        df_allocations['geographicAreaId'] = df_allocations['geographicAreaId'].combine_first(df_allocations['multicountryGeographicAreaId'])
        df_allocations.drop(columns=['multicountryGeographicAreaId'], inplace=True)

        # Merge the updated allocations data with the geographic areas data
        df_combined = df_allocations.merge(df_geographicAreas, on='geographicAreaId', how='left')
        
        # Merge the updated allocations data with the components data
        df_combined = df_combined.merge(df_components, on='componentId', how='left')

        df_combined.drop(columns=['allocationId', 'componentId', 'multiCountryName'], inplace=True)

        # Create a new column capturing either the geographic area name or "Multicountry"
        df_combined['Location'] = df_combined['geographicAreaName'].fillna('Multicountry')   
    else:
        st.caption("No data to display")

    # Convert periodStartYear and periodEndYear to string for better categorical representation
    df_combined['periodStartYear'] = df_combined['periodStartYear'].astype(str)
    df_combined['periodEndYear'] = df_combined['periodEndYear'].astype(str)

    # Create a new column 'Allocation period' by concatenating periodStartYear and periodEndYear
    df_combined['Allocation period'] = df_combined['periodStartYear'] + " - " + df_combined['periodEndYear']

    # Get unique allocation periods for the radio button
    allocation_periods = df_combined['Allocation period'].unique()

    # Find the allocation period corresponding to the latest periodStartYear
    latest_start_year = df_combined['periodStartYear'].max()
    latest_allocation_period = df_combined[df_combined['periodStartYear'] == latest_start_year]['Allocation period'].iloc[0]

    # Create a radio button for selecting the allocation period
    selected_allocation_period = col2.radio(
        'Select the Funding Allocation cycle',
        options=sorted(allocation_periods),
        index=list(sorted(allocation_periods)).index(latest_allocation_period),
        horizontal=True
    )

    # Filter the DataFrame based on the selected start year
    df_filtered = df_combined[df_combined['Allocation period'] == selected_allocation_period]

    # Calculate metrics
    total_allocations = df_filtered['allocationAmount'].sum()
    average_allocations_per_location = df_filtered.groupby('parentGeographicAreaName')['allocationAmount'].sum().mean()

    # Calculate total and average allocation amount per component
    total_per_component = df_filtered.groupby('componentName')['allocationAmount'].sum()
    average_per_component = df_filtered.groupby('componentName')['allocationAmount'].mean().round(2)

    # Calculate percentage of total for each component based on total allocation
    percentage_per_component = (total_per_component / total_allocations * 100).round(0)

    # Function to format numbers in millions or billions
    def format_number(value):
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        else:
            return f"${value:,.2f}"

    # Display main metrics
    with col2:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Selected period", value=selected_allocation_period)
        with col2:
            st.metric(label="Total Allocations", value=format_number(total_allocations))
        with col3:
            st.metric(label="Avg Allocations per Location", value=format_number(average_allocations_per_location))

    # TABS ------------------------------------
    col1, col2, col3 = st.columns([8, 35,8], gap='small')
    tab1, tab2 = col2.tabs(["Components overview 📈","Allocation clustering 🧮"])

    with tab1:
        component_cols = st.columns(len(total_per_component))

        # Define base color
        base_color = "#04AA6D"

        for i, (component, total_allocation) in enumerate(total_per_component.items()):
            percentage = percentage_per_component[component]
            display_value = str(f"{format_number(total_allocation)} ({int(percentage)}%)")
            with component_cols[i]:

                # Merge df_filtered with df_combined to get geographicAreaCode_ISO3
                df_map_data = df_filtered[df_filtered['componentName'] == component]
                # Aggregate the total allocations per location
                total_allocation_per_location = df_map_data.groupby('geographicAreaCode_ISO3')['allocationAmount'].sum().reset_index()

                # Additional EDA metrics for each component
                component_data = df_filtered[df_filtered['componentName'] == component]
                num_allocations = component_data.shape[0]
                avg_allocation = component_data['allocationAmount'].mean()
                subtitle_text = f"{num_allocations} allocations for {format_number(avg_allocation)} on average"

                # Create a choropleth map
                fig_map = px.choropleth(
                    total_allocation_per_location,
                    locations='geographicAreaCode_ISO3',
                    color='allocationAmount',
                    hover_name='geographicAreaCode_ISO3',
                    color_continuous_scale=px.colors.sequential.Plasma,
                    title="{} {}".format(component, display_value)  # Correctly formatted title
                    )

                    # Customize the layout
                fig_map.update_layout(
                        title={
                            'text': "{}: {}<br><sub>{}</sub>".format(component, display_value, subtitle_text),  # Combine title and subtitle
                            'y': 0.95,
                            'x': 0.5,
                            'xanchor': 'center',
                            'yanchor': 'top',
                            'font': {
                                'size': 29
                            }
                        },
                    height=450,
                    geo=dict(
                        showframe=False,
                        showcoastlines=False,
                        projection_type='equirectangular',
                        bgcolor='rgba(0,0,0,0)',
                        showland=True,
                        landcolor='gray'
                    ),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    margin=dict(l=0, r=0, t=30, b=0),
                    coloraxis_showscale=False  # Hide the color scale (legend)
                )

                # Display the map in Streamlit
                st.plotly_chart(fig_map, use_container_width=True)

                # Calculate the total allocation per location
                total_allocation_per_location = df_filtered[df_filtered['componentName'] == component].groupby('Location')['allocationAmount'].sum().reset_index()
                # Sort the locations based on the total allocation amount
                sorted_locations = total_allocation_per_location.sort_values(by='allocationAmount', ascending=False)['Location']
                # Group the data by Location and componentName, then sum the allocationAmount
                df_location_allocations = df_filtered[df_filtered['componentName'] == component].groupby(['Location', 'componentName'])['allocationAmount'].sum().reset_index()
                # Ensure the Location column is ordered by the sorted_locations
                df_location_allocations['Location'] = pd.Categorical(df_location_allocations['Location'], categories=sorted_locations, ordered=True)

                # Create a horizontal bar plot using Plotly
                fig = px.bar(df_location_allocations, 
                            x='allocationAmount', 
                            y='Location', 
                            color='allocationAmount',  # Color based on allocationAmount to apply a gradient
                            orientation='h', 
                            title='{} total allocation per location'.format(component), 
                            labels={'allocationAmount': 'Total Allocation Amount', 'Location': 'Location', 'componentName': 'Component'}, 
                            template='plotly_dark',
                            color_continuous_scale=px.colors.sequential.Plasma)  # Use the Plasma color scale

                # Customize the layout to make the plot clearer and extend the y-axis
                fig.update_layout(
                    title={
                        'text': '{} total allocation per location'.format(component),
                        'y': 1,  # Adjust the title position lower
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {
                            'size': 20
                        }
                    },
                    xaxis=dict(
                        title='Total Allocation Amount',
                        side='top',
                        title_standoff=10  # Increase the space between the x-axis title and the axis itself
                    ),
                    yaxis_title='',
                    height=1800,  # Increase the height of the plot
                    margin=dict(l=200, r=20, t=100, b=20),  # Increase the top margin to provide more space for the title
                    yaxis={'categoryorder': 'total ascending'},  # Ensure y-axis is ordered by total allocation
                    showlegend=False,  # Hide the legend
                    coloraxis_showscale=False,  # Hide the color scale
                    paper_bgcolor='rgba(0,0,0,0)',  # Set the paper background to transparent
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                # Display the plot in Streamlit
                st.plotly_chart(fig)        

    with tab2:
        # Layout columns for the elbow plot and the slider
        col2, col3 = st.columns([5, 25])

        # Select components using a multiselect widget with all components selected by default
        all_components = df_filtered['componentName'].unique()
        selected_components = col2.multiselect("Select components", all_components, default=all_components)

        if not selected_components:
            col2.warning("Select at least one component")
            st.stop()

        # Filter the dataset based on the selected components
        df_filtered_components = df_filtered[df_filtered['componentName'].isin(selected_components)]

        # Pivot the DataFrame so that each componentName has its own column
        df_pivot = df_filtered_components.pivot_table(index='Location', columns='componentName', values='allocationAmount', aggfunc='sum').reset_index()


        # Handle missing values by filling with zero
        df_pivot = df_pivot.fillna(0)

        # Add an elbow plot to find the optimal number of clusters
        sse = []
        for k in range(1, 11):
            kmeans_elbow = KMeans(n_clusters=k)
            kmeans_elbow.fit(df_pivot.iloc[:, 1:])
            sse.append(kmeans_elbow.inertia_)

        # Find the optimal number of clusters using the KneeLocator
        kl = KneeLocator(range(1, 11), sse, curve="convex", direction="decreasing")
        optimal_k = kl.elbow

        # Create the elbow plot
        elbow_fig = go.Figure()
        elbow_fig.add_trace(go.Scatter(x=list(range(1, 11)), y=sse, mode='lines+markers'))
        elbow_fig.update_layout(
            xaxis_title="Number of Clusters",
            yaxis_title="Sum of Squared Distances",
            height=300,
            showlegend=False
        )

        # Add a circle around the optimal number of clusters
        elbow_fig.add_trace(go.Scatter(x=[optimal_k], y=[sse[optimal_k - 1]],
                                    mode="markers", marker=dict(color="#04AA6D", symbol="circle", size=15),
                                    showlegend=False))

        with col2:
            elbow_fig.update_layout(
                title={
                    'text': 'Optimal cluster number: Elbow Method',
                    'y': 0.9,  # Adjust the title position
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {
                        'size': 15
                    }
                }
            )

            # Display the plot with the updated title
            st.plotly_chart(elbow_fig, use_container_width=True, config={'staticPlot': True})
            st.caption("The elbow method is used to determine the optimal number of clusters by finding the point where the sum of squared distances (inertia) starts to diminish. This point represents the optimal number of clusters.")
            num_clusters = st.slider('Select number of clusters', value=4, min_value=2, max_value=10, key="num_clusters_slider")

        # Apply K-means clustering
        kmeans = KMeans(n_clusters=num_clusters)
        df_pivot['Cluster'] = kmeans.fit_predict(df_pivot.iloc[:, 1:])

        # Convert df_filtered to CSV
        csv_data = df_pivot.to_csv(index=False).encode('utf-8')

        # Add a download button
        col2.download_button(
            label="Download data as CSV",
            data=csv_data,
            file_name='filtered_data.csv',
            mime='text/csv',
        )

        with col3:
            if len(selected_components) == 3:
                # Create a 3D scatter plot using Plotly Express
                fig = px.scatter_3d(df_pivot,
                                    x=df_pivot.columns[1],  # First component dimension
                                    y=df_pivot.columns[2],  # Second component dimension
                                    z=df_pivot.columns[3],  # Third component dimension
                                    color=df_pivot['Cluster'].astype(str),  # Color by cluster
                                    size=df_pivot.iloc[:, 1:].sum(axis=1),  # Size based on total allocation amount
                                    text='Location',  # Text for hover info
                                    labels={
                                        df_pivot.columns[1]: df_pivot.columns[1],
                                        df_pivot.columns[2]: df_pivot.columns[2],
                                        df_pivot.columns[3]: df_pivot.columns[3],
                                        'Cluster': 'Cluster number'
                                    })

                # Customize the layout for better readability and set the height to 800
                fig.update_layout(
                    title={
                        'text': '3D Scatter Plot of Allocation Amounts by Component with Clusters',
                        'y': 1,  # Adjust the title position lower
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {
                            'size': 20
                        }
                    },
                    scene=dict(
                        xaxis_title=df_pivot.columns[1],
                        yaxis_title=df_pivot.columns[2],
                        zaxis_title=df_pivot.columns[3],
                        camera=dict(
                            up=dict(x=0, y=0, z=1),
                            center=dict(x=0, y=0, z=-0.3),  # Adjust the center to move the plot up
                            eye=dict(x=1.25, y=1.25, z=1.25)
                        )
                    ),
                    legend_title_text='Cluster number',  # Update legend title
                    template='plotly_dark',
                    height=1000,  # Adjust the height as needed
                    paper_bgcolor='rgba(0,0,0,0)',  # Set the paper background to transparent
                    plot_bgcolor='rgba(0,0,0,0)' 
                )
            elif len(selected_components) == 2:
                # Create a 2D scatter plot using Plotly Express
                fig = px.scatter(df_pivot,
                                x=df_pivot.columns[1],  # First component dimension
                                y=df_pivot.columns[2],  # Second component dimension
                                color=df_pivot['Cluster'].astype(str),  # Color by cluster
                                size=df_pivot.iloc[:, 1:].sum(axis=1),  # Size based on total allocation amount
                                text='Location',  # Text for hover info
                                labels={
                                    df_pivot.columns[1]: df_pivot.columns[1],
                                    df_pivot.columns[2]: df_pivot.columns[2],
                                    'Cluster': 'Cluster number'
                                })

                # Customize the layout for better readability and set the height to 800
                fig.update_layout(
                    title={
                        'text': '2D Scatter Plot of Allocation Amounts by Component with Clusters',
                        'y': 1,  # Adjust the title position lower
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {
                            'size': 20
                        }
                    },
                    xaxis_title=df_pivot.columns[1],
                    yaxis_title=df_pivot.columns[2],
                    legend_title_text='Cluster number',  # Update legend title
                    template='plotly_dark',
                    height=1000,  # Adjust the height as needed
                    paper_bgcolor='rgba(0,0,0,0)',  # Set the paper background to transparent
                    plot_bgcolor='rgba(0,0,0,0)' 
                )
            else:
                # Create a bar plot using Plotly Express
                fig = px.bar(df_pivot,
                            x='Location',  # X-axis set to Location
                            y=selected_components[0],  # Y-axis set to the selected component
                            color=df_pivot['Cluster'].astype(str),  # Color by cluster
                            text='Location',  # Text for hover info
                            labels={
                                'Location': 'Location',
                                selected_components[0]: 'Allocation Amount',
                                'Cluster': 'Cluster number'
                            })

                # Customize the layout for better readability and set the height to 800
                fig.update_layout(
                    title={
                        'text': 'Bar Plot of Allocation Amounts by Location',
                        'y': 1,  # Adjust the title position lower
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {
                            'size': 20
                        }
                    },
                    xaxis_title='Location',
                    yaxis_title='Allocation Amount',
                    legend_title_text='Cluster number',  # Update legend title
                    template='plotly_dark',
                    height=1000,  # Adjust the height as needed
                    paper_bgcolor='rgba(0,0,0,0)',  # Set the paper background to transparent
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                # Display the plot in Streamlit
            st.plotly_chart(fig, use_container_width=True)
