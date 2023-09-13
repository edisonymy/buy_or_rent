import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from main import Buy_or_Rent_Model, generate_combinations_and_calculate_npv, graph_kde_plots
from utils.general import get_param_distribution

# Streamlit app title
st.title('Open Source Buy or Rent Simulation Model')
st.write("Not sure whether it is financially better to buy a property or rent? We use simulations to show possible returns for buying a property or renting given your assumptions.")
st.write("Adjust your assumptions on the left sidebar.")
st.write("---")
# left_column, right_column = st.columns(2)

n_samples = 10000
n_bins = 30
# User-enterable parameters for data generation
st.sidebar.header('Your Assumptions')
# st.sidebar.subheader('Fixed Model Parameters:')
house_price = st.sidebar.number_input("Property Price", value=800000, step = 10000)
# rental_yield = st.sidebar.number_input("Rental Yield (used to calculate monthly rent for equivalent property):", value=0.043, step = 0.001, format="%.3f") #st.sidebar.slider('Rental Yield (used to calculate monthly rent for equivalent property):', min_value=0.01, max_value=1.0, value=0.044, format="%.3f")
# implied_monthly_rent = house_price * rental_yield / 12
# st.sidebar.write(f"Monthly Rent: {implied_monthly_rent:.0f}")
monthly_rent = st.sidebar.number_input("Monthly Rent:", value=int(house_price*0.043/12), step = 100)
rental_yield = (12 * monthly_rent)/ house_price
st.sidebar.markdown(f"<span style='font-size: 12px;'>Implied Rental Yield: {rental_yield:.3f}</span>", unsafe_allow_html=True)
text = 'Checkout a rental yield map here: https://www.home.co.uk/company/press/rental_yield_heat_map_london_postcodes.pdf'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)

deposit = st.sidebar.slider('Deposit:', min_value=0, max_value=house_price, value=int(0.4*house_price), step = 1000)
deposit_mult = deposit/house_price
# deposit_mult = st.sidebar.slider('Deposit percentage:', min_value=0.01, max_value=1.0, value=0.4)
st.sidebar.markdown(f"<span style='font-size: 12px;'>Deposit Amount: {deposit:,.0f}</span>", unsafe_allow_html=True)
mortgage_length = st.sidebar.slider('Mortgage Length:', min_value=15, max_value=35, value=30, step = 1)

st.sidebar.write("---")
st.sidebar.subheader('Uncertain Model Parameters:')
st.sidebar.write("It's hard to predict the future, so this section allows the simulations to reflect your uncertainty. The more uncertain you are about a paramter, the higher the standard deviation (sd) you should assume.")
mortgage_interest_annual_mean = st.sidebar.slider('Mortgage Interest Mean:', min_value=0.01, max_value=0.1, value=0.06, step = 0.001, format="%.3f")
mortgage_interest_annual_std = st.sidebar.slider('Mortgage Interest sd:', min_value=0.0, max_value=0.1, value=0.01, step = 0.001, format="%.3f")
text = 'Check out historical mortgage rates here: https://tradingeconomics.com/united-kingdom/mortgage-rate'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
mortgage_interest_annual_list = get_param_distribution(mortgage_interest_annual_mean, mortgage_interest_annual_std, n_samples, n_bins, title ='Assumed Distribution for Average Mortgage Interest Rate')
st.sidebar.write("---")
property_price_growth_annual_mean = st.sidebar.slider('Property Price Growth Mean:', min_value=0.01, max_value=0.1, value=0.03, step = 0.001, format="%.3f")
property_price_growth_annual_std = st.sidebar.slider('Property Price Growth sd:', min_value=0.0, max_value=0.05, value=0.01, step = 0.001, format="%.3f")
text = 'Check out historical property price growth here: https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/housepriceindex/june2023'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
property_price_growth_annual_list = get_param_distribution(property_price_growth_annual_mean, property_price_growth_annual_std, n_samples, n_bins, title ='Assumed Distribution for Annual Property Value Growth')
st.sidebar.write("---")
rent_increase_mean = st.sidebar.slider('Rent Increase Mean:', min_value=0.01, max_value=0.1, value=0.01325, step = 0.001, format="%.3f")
rent_increase_std = st.sidebar.slider('Rent Increase sd:', min_value=0.0, max_value=0.05, value=0.01, step = 0.001, format="%.3f")
text = 'Checkout historical rent increases here: https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/indexofprivatehousingrentalprices/july2023'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
rent_increase_list = get_param_distribution(rent_increase_mean, rent_increase_std, n_samples, n_bins, title ='Assumed Distribution for Average Annual Rent Increase')
st.sidebar.write("---")
investment_return_annual_mean = st.sidebar.slider('Investment Return Mean:', min_value=0.01, max_value=0.1, value=0.06, step = 0.001, format="%.3f")
investment_return_annual_std = st.sidebar.slider('Investment Return sd:', min_value=0.0, max_value=0.05, value=0.02, step = 0.001, format="%.3f")
text = 'Check out historical stock market returns here: https://www.investopedia.com/ask/answers/042415/what-average-annual-return-sp-500.asp'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
investment_return_annual_list = get_param_distribution(investment_return_annual_mean, investment_return_annual_std, n_samples, n_bins, title ='Assumed Distribution for Average Investment Rate of Return')
st.sidebar.write("---")
years_until_sell_mean = st.sidebar.slider('Years Until Sell Mean:', min_value=0, max_value=25, value=15)
years_until_sell_std = st.sidebar.slider('Years Until Sell sd:', min_value=0, max_value=10, value=5)
years_until_sell_list = get_param_distribution(years_until_sell_mean, years_until_sell_std, n_samples, n_bins, as_int=True, title ='Assumed Distribution for Years Until Property Is Sold')
st.sidebar.write("---")
# n_samples = st.sidebar.slider('Number of Samples:', min_value=100, max_value=50000, value=10000)
# n_bins = st.sidebar.slider('Number of Bins:', min_value=10, max_value=100, value=30)
st.sidebar.subheader('Simulation Settings:')
n_samples_simulation = st.sidebar.slider('Number of Simulation Samples:', min_value=100, max_value=10000, value=1000)

# # Generate data
# st.header('Generate Data')

# Display data
# st.subheader('Sample Data:')
# st.write("mortgage_interest_annual_list:", mortgage_interest_annual_list)
# st.write("property_price_growth_annual_list:", property_price_growth_annual_list)
# st.write("rent_increase_list:", rent_increase_list)
# st.write("investment_return_annual_list:", investment_return_annual_list)
# st.write("years_until_sell_list:", years_until_sell_list)

# Initialize the model
model = Buy_or_Rent_Model()
model.HOUSE_PRICE = house_price
model.DEPOSIT_MULT = deposit_mult
model.RENTAL_YIELD = rental_yield

# Generate combinations and calculate NPV
# st.header('Generate Combinations and Calculate NPV')

percentiles_df, results_df = generate_combinations_and_calculate_npv(
    n_samples_simulation,
    model,
    mortgage_interest_annual_list=mortgage_interest_annual_list,
    property_price_growth_annual_list=property_price_growth_annual_list,
    rent_increase_list=rent_increase_list,
    investment_return_annual_list=investment_return_annual_list,
    years_until_sell_list=years_until_sell_list
)

# Display the results DataFrame
st.subheader('Correlations Between Parameters and Buying NPV')
st.write(results_df.corr().iloc[0,1:])
plot_button = st.button("Plot Additional Graphs")

# Check if the button is clicked
if plot_button:
    FEATURES = ['mortgage_interest_annual', 'property_price_growth_annual', 'rent_increase', 'investment_return_annual', 'years_until_sell']
    graph_kde_plots(results_df,FEATURES)
