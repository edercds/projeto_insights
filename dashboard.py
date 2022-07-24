import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns

pd.set_option('display.float_format', lambda x: '%.2f' % x)
st.set_page_config(layout='wide')


@st.cache(allow_output_mutation=True)
def get_data(path):
    data = pd.read_csv(path)
    data['date'] = pd.to_datetime(data['date'])
    return data

def map_plot(data):

    st.title('House Rocket Map')

    #filters
    price_min = int(data['price'].min())
    price_max = int(data['price'].max())
    price_mean = int(data['price'].mean())

    st.sidebar.title('Map filter')
    price_slider = st.sidebar.slider('Price Range', price_min,price_max,price_mean)


    #select rows
    houses = data[data['price'] < price_slider][['id','lat','long','price','zipcode']]

    #draw map
    fig = px.scatter_mapbox(
        houses,
        lat='lat',
        lon='long',
        hover_data=['price'],
        size='price',
        color='price',
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=15,
        zoom=10)
        
    fig.update_layout(mapbox_style='open-street-map')
    fig.update_layout(height=600, width=800, margin={'l':0,'r':0,'t':0,'b':0})

    #show map
    st.plotly_chart(fig)

    return None

def show_data(data):
    st.title('Data')
    st.sidebar.title('Data filter')
    f_attributes = st.sidebar.multiselect('Enter columns: ', data.columns, default=list(data.columns))
    st.dataframe(data[f_attributes])

    return None

def descriptive_analysis(data):
    st.title('Descriptive Analysis')
    st.write(data.describe().transpose())

    return None

def data_overview(data):
    show_data(data)
    descriptive_analysis(data)
    

    return None

def reports(data):
    
    # Report 1 - Houses to buy

    st.title('Houses to Buy Report')

    #Create a temporary dataset with the median of the prices by zipcode
    median_per_zipcode = data[['zipcode','price']].groupby('zipcode').median().reset_index()

    #Merge the temporary dataset with the full dataset
    houses2 = pd.merge(data, median_per_zipcode, on='zipcode', how='inner')

    #Change the names of the equal columns named 'price'
    houses2.rename(columns={'price_x':'price', 'price_y':'median_price'}, inplace=True)

    #Create a new column showing the houses to buy based on the attributes price, median_price and condition
    for index, row in houses2.iterrows():
        if (row['price']<row['median_price']) & (row['condition']>=3):
            houses2.loc[index,'buy'] = 'yes'
        else:
            houses2.loc[index,'buy'] = 'no'

    report_one = houses2[['id', 'zipcode', 'price', 'median_price', 'condition', 'buy']]

    st.dataframe(report_one)


    # Report 2 - Houses to sell

    st.title('Houses to Sell Report')

    #Select only bought houses
    bought_houses = houses2[houses2['buy']=='yes'].copy()

    #Adding 'Season' column
    bought_houses['season'] = 'season'

    for index, row in bought_houses.iterrows():
        if row['date'].month in (1,2,3):
            bought_houses.loc[index,'season'] = 'winter'
        elif row['date'].month in (4,5,6):
            bought_houses.loc[index,'season'] = 'spring'
        elif row['date'].month in (7,8,9):
            bought_houses.loc[index,'season'] = 'summer'
        else:
            bought_houses.loc[index,'season'] = 'autumn'

        if (row['date'].month == 3) and (row['date'].day > 19):
            bought_houses.loc[index,'season'] = 'spring'
        elif (row['date'].month == 6) and (row['date'].day > 20):
            bought_houses.loc[index,'season'] = 'summer'
        elif (row['date'].month == 9) and (row['date'].day > 21):
            bought_houses.loc[index,'season'] = 'autumn'
        elif (row['date'].month == 12) and (row['date'].day > 20):
            bought_houses.loc[index,'season'] = 'winter'

    #Adding median price per zipcode and season column
    median_zipcode_season = bought_houses[['zipcode', 'season', 'price']].groupby(['zipcode','season']).median().reset_index()
    houses3 = pd.merge(bought_houses, median_zipcode_season, on=['zipcode','season'],how='inner')

    #Constructing Report Two with Profit column
    report_two = houses3[['id', 'zipcode', 'season', 'price_y', 'price_x']]

    report_two = report_two.rename(columns={'price_y':'median_zipcode_season', 'price_x':'price'})

    for index, row in report_two.iterrows():
        if row['price'] < row['median_zipcode_season']:
            report_two.loc[index,'sell_value'] = row['price'] * 1.3
            report_two.loc[index,'profit'] = row['price'] * 0.3
        elif row['price'] >= row['median_zipcode_season']:
            report_two.loc[index,'sell_value'] = row['price'] * 1.1
            report_two.loc[index,'profit'] = row['price'] * 0.1

    st.dataframe(report_two)

def hipothesys_one(data):
    # H1: Imóveis que possuem vista para a água são 20% mais caros na média

    st.header('H1: Waterfront houses are 20% more expensive on average')

    waterfront = data[['waterfront','price']].groupby('waterfront').mean().reset_index()
    waterfront['var_pct'] = waterfront['price'].sort_values().pct_change()*100

    ax1 = px.bar(waterfront,x='waterfront',y='price', title='Average house prices by waterfront', text_auto='.2s')

    st.write(waterfront)
    st.plotly_chart(ax1)
    st.subheader('False: Waterfront houses are 212% more expensive on average')

    return None

def hypothesis_two(data):
    # H2: Imóveis com data de construção menor que 1955 são 50% mais baratos na média

    st.header('H2: Houses built before 1955 are 20% less expensive on average')

    fifty_five = data.copy()

    fifty_five['1955'] = fifty_five['yr_built'].apply(lambda x: 'before' if x < 1955 else 'after')

    afbf = fifty_five[['1955','price']].groupby('1955').mean().reset_index()
    afbf['var_pct'] = afbf['price'].pct_change()*100

    ax2 = px.bar(afbf,x='1955',y='price', title='Average house prices before and after 1955', text_auto='.3s')

    st.write(afbf)
    st.plotly_chart(ax2)
    st.subheader('False: Houses built before 1955 are 0.78% less expensive on average')

    return None

def hypothesis_three(data):
    # H3: Imóveis sem porão possuem sqrt_lot, são 50% maiores do que com porão.

    st.header('H3: Houses without basement are 50% bigger on average')

    basement = data.copy()

    basement['basement'] = basement['sqft_basement'].apply(lambda x: 'no' if x == 0 else 'yes')

    base = basement[['basement','sqft_lot']].groupby('basement').mean().reset_index()

    base['var'] = base['sqft_lot'].sort_values().pct_change()*100

    sns.barplot(data=base, x='basement', y='sqft_lot')

    ax3 = px.bar(base,x='basement',y='sqft_lot', title='Houses sizes (squarefoot)', text_auto='.3s')

    st.write(base.sort_values('sqft_lot'))
    st.plotly_chart(ax3)
    st.subheader('False: Houses without basement are 22.56% bigger on average')

    return None

def hypothesis_four(data):
    # H4: O crescimento do preço dos imóveis YoY ( Year over Year ) é de 10%

    st.header('H4: House prices increases 10% YoY')

    may = data[data['date'].dt.month ==5].copy()
    may['year'] = may['date'].dt.year
    yoy = may[['year','price']].groupby('year').mean().reset_index()
    yoy['var_pct'] = yoy['price'].pct_change()*100

    ax4 = px.bar(yoy,x='year',y='price', title='Houses prices increasing YoY', text_auto='.3s')

    st.write(yoy)
    st.plotly_chart(ax4)
    st.subheader('False: House prices increases 1.83% YoY')

    return None

def hypothesis_five(data):
    # H5: Imóveis com 3 banheiros tem um crescimento MoM ( Month over Month ) de 15%

    st.header('H5: Three bathrooms house prices increases 15% MoM')

    houses_three_baths = data[data['bathrooms'] == 3].copy()
    houses_three_baths['year'] = houses_three_baths['date'].dt.year
    houses_three_baths = houses_three_baths[houses_three_baths['year'] == 2015].copy()

    houses_three_baths['month'] = houses_three_baths['date'].dt.month


    mom = houses_three_baths[['month','price']].groupby('month').mean().reset_index()

    mom['var_pct'] = mom['price'].pct_change()*100

    ax5 = px.bar(mom,x='month',y='var_pct', title='Houses prices variations MoM', text_auto='.3s')

    st.write(mom)
    st.plotly_chart(ax5)
    st.subheader('False: There was an increase of 10.3% in March,\
                  but the average price has been decreasing and maybe its a good time to buy a house')
    return None

def data_exploration(data):
    st.title('Data exploration - Hypothesis')
    hipothesys_one(data)
    hypothesis_two(data)
    hypothesis_three(data)
    hypothesis_four(data)
    hypothesis_five(data)

    return None

if __name__ == '__main__':

    #load data
    data = get_data('kc_house_data.csv')
    
    #dashboard
    map_plot(data)
    data_overview(data)
    reports(data)
    data_exploration(data)