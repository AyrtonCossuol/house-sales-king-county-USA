import pandas as pd
import numpy as np
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import MarkerCluster
import plotly.express as px

st.set_page_config(layout = 'wide')

@st.cache(allow_output_mutation=True)
def get_data(path):
    data = pd.read_csv(path)
    return data

def set_feature(data):
    data['price_m2'] = data['price'] / data['sqft_lot']
    return data

def overview_data(data):
    f_attributes = st.sidebar.multiselect('Enter columns', data.columns)
    f_zipcode = st.sidebar.multiselect('Enter zipcode', 
                                        data['zipcode'].unique())

    st.title('Data Overview')

    if f_zipcode != [] and f_attributes != []:
        data = data.loc[data['zipcode'].isin(f_zipcode), f_attributes]
    elif f_zipcode != [] and f_attributes == []:
        data = data.loc[data['zipcode'].isin(f_zipcode), : ]
    elif f_zipcode == [] and f_attributes != []:
        data = data.loc[:, f_attributes ]
    else:
        data = data.copy()

    st.dataframe(data)

    c1, c2 = st.beta_columns((1, 1))
    # Average metrics
    df1 = data[['id', 'zipcode']].groupby('zipcode').count().reset_index()
    df2 = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()
    df3 = data[['sqft_living', 'zipcode']].groupby('zipcode').mean().reset_index()
    df4 = data[['price_m2', 'zipcode']].groupby('zipcode').mean().reset_index()

    # Merge dataset
    m1 = pd.merge(df1, df2, on = 'zipcode', how = 'inner')
    m2 = pd.merge(m1, df3, on = 'zipcode', how = 'inner')
    df = pd.merge(m2, df4, on = 'zipcode', how = 'inner')

    df.columns = ['zipcode', 'total_houses', 'price', 'sqrt_living', 'price_m2']

    c1.header('Average Values')
    c1.dataframe(df, height = 500)

    # Statistic Descriptive
    num_attributes = data.select_dtypes(include = ['int64', 'float64'])
    media = pd.DataFrame(num_attributes.apply(np.mean))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))

    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([max_, min_, media, mediana, std], axis = 1).reset_index()
    df1.columns = ['attributes', 'max', 'min', 'mean', 'median', 'std']

    c2.header('Descriptive Analysis')
    c2.dataframe(df1, height = 500)

    
    return None

def portfolio_density(data):
    st.title('Region Overview')

    c1, c2 = st.beta_columns((5, 1))
    c1.header('Portifolio Density')

    df = data.sample(100)

    # Base Map - Folium
    density_map = folium.Map(location = [
                                data['lat'].mean(), 
                                data['long'].mean()],
                                default_zoom_star = 15)
    marker_cluster = MarkerCluster().add_to(density_map)

    for name, row in df.iterrows():
        folium.Marker([row['lat'], row['long']], 
                        popup = 'Price RS{0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bethrooms, year built: {5}'.format(row['price'], 
                                                                                                                            row['date'],
                                                                                                                            row['sqft_living'],
                                                                                                                            row['bedrooms'], 
                                                                                                                            row['bathrooms'],
                                                                                                                            row['yr_built'])).add_to(marker_cluster)
    with c1:
        folium_static(density_map)  

    return None

def commercial(data):
    st.sidebar.title('Commercial Options')
    st.title('Commercial Attributes')

    # ----------- Average Price per Year

    data['data'] = pd.to_datetime(data['date'])

    # filters
    min_year_built = int(data['yr_built'].min())
    max_year_built = int(data['yr_built'].max())

    st.sidebar.subheader('Select Max Year Built')
    f_year_built = st.sidebar.slider('Year Built', min_year_built, max_year_built, min_year_built)

    st.header('Average Price per Year Built')

    # Data selection
    df = data.loc[data['yr_built'] < f_year_built]
    df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

    # PLot 
    fig = px.line(df, x = 'yr_built', y = 'price')
    st.plotly_chart(fig, use_container_width = True)

    # ----------- Average Price per Year
    st.header('Average Price per Day')
    st.sidebar.subheader('Select Max Date')

    st.write(pd.to_datetime(data['date']).dt.strftime("%Y-%m-%d").min())
    # filters
    min_date = pd.to_datetime(data['date']).dt.strftime("%Y-%m-%d").min()
    max_date = pd.to_datetime(data['date']).dt.strftime("%Y-%m-%d").max()

    f_date = st.sidebar.slider('Date', min_date, max_date, min_date)

    # Date filtering
    data['price'] = pd.to_datetime(data['date'])
    df = data.loc[data['date'] < f_date]
    df = data[['date', 'price']].groupby('date').mean().reset_index()

    # Plot
    fig = px.line(df, x = 'date', y = 'price')
    st.plotly_chart(fig, use_container_width = True)


    # ==================
    # Histogram
    # ==================
    st.header('Price Distribution')
    st.sidebar.subheader('Select Max Price')

    # filter
    min_price = int(data['price'].min())
    max_price = int(data['price'].max())
    mean_price = int(data['price'].mean())

    f_price = st.sidebar.slider('Price', min_price, max_price, mean_price)
    df = data.loc[data['price'] < f_price]

    # Data Plot
    fig = px.histogram(df, x = 'price', nbins = 50)
    st.plotly_chart(fig, use_container_width = True)

    return None

if __name__ == '__main__':
    # Data Extraction
    PATH = 'base/kc_house_data.csv'
    
    data = get_data(PATH)
    
    # Transformation
    data = set_feature(data)
    overview_data(data)
    portfolio_density(data)
    st.text('By Ayrton Cossuol')