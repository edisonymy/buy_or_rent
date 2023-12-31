import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from main import Buy_or_Rent_Model, generate_combinations_and_calculate_npv, graph_kde_plots
from utils.general import get_param_distribution
# from utils.ga import add_analytics_tag

# # Google Analytics for usage tracking, no personal data is collected
# add_analytics_tag()
# Streamlit app title
st.title('Open Source UK Buy or Rent Simulation Model')
st.write("---")
st.write("Not sure whether it is financially better to buy a property or rent and invest? We use simulations to show possible returns for buying a property or renting given your assumptions. All parameters are assumed to be uncorrelated.")

st.markdown("***This app is currently in Beta. It assumes that you are in England, UK. Different countries may have different tax rules. No data is collected by this app. The source code can be found at: https://github.com/edisonymy/buy_or_rent***")
st.write("---")

n_samples = 500
n_bins = 30

np.random.seed(123)

# User-enterable parameters for data generation
st.subheader('Your Assumptions')
with st.expander("Expand", expanded=True):
    # st.sidebar.subheader('Fixed Model Parameters:')
    house_price = st.number_input("Property Price", value=300000, step = 5000)
    # rental_yield = st.sidebar.number_input("Rental Yield (used to calculate monthly rent for equivalent property):", value=0.043, step = 0.001, format="%.3f") #st.sidebar.slider('Rental Yield (used to calculate monthly rent for equivalent property):', min_value=0.01, max_value=1.0, value=0.044, format="%.3f")
    # implied_monthly_rent = house_price * rental_yield / 12
    # st.sidebar.write(f"Monthly Rent: {implied_monthly_rent:.0f}")
    monthly_rent = st.number_input("Monthly Rent:", value=int(house_price*0.043/12), step = 100)
    rental_yield = (12 * monthly_rent)/ house_price
    st.markdown(f"<span style='font-size: 12px;'>Implied Rental Yield: {rental_yield:.3f}</span>", unsafe_allow_html=True)
    text = 'Checkout a rental yield map here: https://www.home.co.uk/company/press/rental_yield_heat_map_london_postcodes.pdf'
    st.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)

    deposit = st.slider('Deposit:', min_value=0, max_value=house_price, value=int(0.4*house_price), step = 1000)
    deposit_mult = deposit/house_price
    # deposit_mult = st.sidebar.slider('Deposit percentage:', min_value=0.01, max_value=1.0, value=0.4)
    # st.sidebar.markdown(f"<span style='font-size: 12px;'>Deposit Amount: {deposit:,.0f}</span>", unsafe_allow_html=True)
    mortgage_length = st.slider('Mortgage Length:', min_value=15, max_value=35, value=30, step = 1)
    
    st.markdown("***For advanced options, please use the left sidebar (mobile users please press the top left button).***")

# sidebar 
st.write("---")
st.sidebar.subheader('Additional Parameters:')
stamp_duty_bol = st.sidebar.checkbox('I pay Stamp Duty.', value = False, help="Stamp Duty (UK): A tax paid by the buyer when purchasing property in the United Kingdom. The amount of Stamp Duty depends on the property's purchase price and may include additional rates for second homes and buy-to-let properties.") 
cgt_bol = st.sidebar.checkbox('I pay capital gains tax on the property.', value = False, help = "Capital Gains Tax (CGT): A tax levied on the profit (capital gain) made from the sale or disposal of assets such as property, investments, or valuable possessions. The amount of CGT owed is typically calculated based on the difference between the purchase price and the selling price of the asset. Different rates may apply to individuals and businesses, and there are often exemptions and allowances that can reduce the taxable amount.")
cgt_investment_bol = st.sidebar.checkbox('I pay capital gains tax on the investment.', value = False, help = "Capital Gains Tax (CGT): A tax levied on the profit (capital gain) made from the sale or disposal of assets such as property, investments, or valuable possessions. The amount of CGT owed is typically calculated based on the difference between the purchase price and the selling price of the asset. Different rates may apply to individuals and businesses, and there are often exemptions and allowances that can reduce the taxable amount.")
ongoing_cost = st.sidebar.number_input("Annual combined maintenance and service charge:", value=int(house_price*0.006), step = 100, help="The total annual cost associated with maintaining and servicing a property, including expenses such as property management fees, maintenance fees, and other related charges.")
buying_cost = st.sidebar.number_input("Buying cost (excluding stamp duty):", value=3000, step = 100, help="This includes laywer's fee, mortgage lender fees, surveyor's fee, valuation fees and other fees you expect to pay at the time of purchase.")
annual_income = st.sidebar.number_input("Annual Salary", value=20000, step = 100, help="This should be set to the expected salary at time of sale, required to calculate capital gains tax.")
selling_cost_no_cgt = st.sidebar.number_input("Selling cost (excluding Capital Gains Tax):", value=int(house_price*0.02), step = 100, help= "Total expense incurred when selling a property. This typically include real estate agent commissions, legal fees, advertising expenses, and any necessary repairs or renovations to prepare the property for sale.")
inflation = st.sidebar.number_input('Inflation:', min_value=0.0, max_value=1.0, value=0.02, step = 0.001, format="%.3f", help="Used for inflation adjustment only. It does not affect the model.")
# uncertain parameters
st.sidebar.subheader('Advanced Model Parameters:')
st.sidebar.write("It's hard to predict the future, so this section allows the simulations to reflect your uncertainty. The more uncertain you are about a paramter, the higher the standard deviation (sd) you should assume.")
mortgage_interest_annual_mean = st.sidebar.slider('Mortgage Interest Rate Mean:', min_value=0.01, max_value=0.1, value=0.055, step = 0.001, format="%.3f")
mortgage_interest_annual_std = st.sidebar.slider('Mortgage Interest Rate sd:', min_value=0.0, max_value=0.1, value=0.012, step = 0.001, format="%.3f")
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
rent_increase_mean = st.sidebar.slider('Rent Increase Mean:', min_value=0.01, max_value=0.1, value=0.02, step = 0.001, format="%.3f")
rent_increase_std = st.sidebar.slider('Rent Increase sd:', min_value=0.0, max_value=0.05, value=0.01, step = 0.001, format="%.3f")
text = 'Checkout historical rent increases here: https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/indexofprivatehousingrentalprices/july2023'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
rent_increase_list = get_param_distribution(rent_increase_mean, rent_increase_std, n_samples, n_bins, title ='Assumed Distribution for Average Annual Rent Increase')
st.sidebar.write("---")
investment_return_annual_mean = st.sidebar.slider('Investment Return Mean:', min_value=0.01, max_value=0.2, value=0.06, step = 0.001, format="%.3f")
investment_return_annual_std = st.sidebar.slider('Investment Return sd:', min_value=0.0, max_value=0.05, value=0.02, step = 0.001, format="%.3f")
text = 'Check out historical stock market returns here: https://www.investopedia.com/ask/answers/042415/what-average-annual-return-sp-500.asp'
st.sidebar.markdown(f"<span style='font-size: 11px;'>{text}</span>", unsafe_allow_html=True)
investment_return_annual_list = get_param_distribution(investment_return_annual_mean, investment_return_annual_std, n_samples, n_bins, title ='Assumed Distribution for Average Investment Rate of Return')
st.sidebar.write("---")
years_until_sell_mean = st.sidebar.slider('Years Until Sell Mean:', min_value=0, max_value=100, value=15)
years_until_sell_std = st.sidebar.slider('Years Until Sell sd:', min_value=0, max_value=10, value=5)
years_until_sell_list = get_param_distribution(years_until_sell_mean, years_until_sell_std, n_samples, n_bins, as_int=True, title ='Assumed Distribution for Years Until Property Is Sold')
st.sidebar.write("---")
# n_samples = st.sidebar.slider('Number of Samples:', min_value=100, max_value=50000, value=10000)
# n_bins = st.sidebar.slider('Number of Bins:', min_value=10, max_value=100, value=30)
st.sidebar.subheader('Simulation Settings:')
n_samples_simulation = st.sidebar.slider('Number of Simulation Samples:', min_value=100, max_value=10000, value=500)

# Initialize the model
model = Buy_or_Rent_Model()
model.HOUSE_PRICE = house_price
model.DEPOSIT_MULT = deposit_mult
model.RENTAL_YIELD = rental_yield
model.MORTGAGE_LENGTH = mortgage_length
model.ANNUAL_SALARY = annual_income
model.ONGOING_COST_MULT = ongoing_cost/house_price
model.BUYING_COST_FLAT = buying_cost
model.STAMP_DUTY_BOL = stamp_duty_bol
model.CGT_BOL = cgt_bol
model.CGT_INVESTMENT_BOL = cgt_investment_bol
model.inflation = inflation

# Generate combinations and calculate NPV
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
# st.subheader('Correlations Between Parameters and Buying NPV')
with st.expander('Correlations Between Parameters and Buying NPV', expanded=False):
    st.write(results_df.corr().iloc[0,1:])

st.write('---')
st.write("If you found this useful and want to support me, consider buying me a coffee here:")
# Embed the "Buy Me a Coffee" button script with custom CSS
buy_me_a_coffee_html = """
<script type="text/javascript" src="https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js"
    data-name="bmc-button" data-slug="edisonymyt" data-color="#FFDD00" data-emoji="☕" data-font="Cookie"
    data-text="Buy me a coffee" data-outline-color="#000000" data-font-color="#000000"
    data-coffee-color="#ffffff" ></script>
"""

# Display the custom CSS and the button in the Streamlit app
st.components.v1.html(buy_me_a_coffee_html)
# plot_button = st.button("Plot Additional Graphs")

# Check if the button is clicked
# if plot_button:
#     FEATURES = ['mortgage_interest_annual', 'property_price_growth_annual', 'rent_increase', 'investment_return_annual', 'years_until_sell']
#     graph_kde_plots(results_df,FEATURES)
