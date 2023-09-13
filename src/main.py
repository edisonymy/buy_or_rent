import streamlit as st
import pandas as pd
import numpy as np
import numpy_financial as npf
from scipy.stats import norm, skew
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from utils.general import calculate_percentiles, bin_continuous_features, get_param_distribution
from utils.finance import get_stamp_duty_next_home, annuity_pv, annuity_fv, annuity_payment, pv_future_payment, fv_present_payment

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
matplotlib.rcParams["axes.formatter.limits"] = (-99, 99)

def format_with_commas(x, pos):
    return '{:,.0f}'.format(x)

class Buy_or_Rent_Model():
    def __init__(self) -> None:
        # PARAMS
        # Fixed (in expectation)
        self.HOUSE_PRICE = 800000 #including upfront repairs and renovations 
        self.RENTAL_YIELD = 0.043 # assumed rent as a proportion of house price https://www.home.co.uk/company/press/rental_yield_heat_map_london_postcodes.pdf
        self.DEPOSIT_MULT = 0.5
        self.MORTGAGE_LENGTH = 30
        self.BUYING_COST_FLAT = 3000 #https://www.movingcostscalculator.co.uk/calculator/
        self.SELLING_COST_MULT = 0.02 #https://www.movingcostscalculator.co.uk/calculator/
        self.ONGOING_COST_MULT = 0.006 # service charge + repairs, council tax and bills are omitted since they are the same whether buying or renting
        self.ANNUAL_SALARY = 55000
        self.CGT_ALLOWANCE = 6000
        self.PERSONAL_ALLOWANCE = 12570
        # Probability distribution
        self.rent_increase = 0.01325 # historical: https://www.ons.gov.uk/economy/inflationandpriceindices/bulletins/indexofprivatehousingrentalprices/april2023
        self.property_price_growth_annual = 0.025 # historical average = 0.034 over the last 8 year, adjusted down due to end to abnormally low interest rates; source for historical data: https://www.statista.com/statistics/620414/monthly-house-price-index-in-london-england-uk/
        self.mortgage_interest_annual = 0.05
        self.investment_return_annual = 0.06
        self.years_until_sell = 20
        # financial modelling params
        self.inflation = 0.02 #on ongoing costs, also for converting fv
        self.adjust_for_inflation = 0

    def get_capital_gains_tax(self):
        cgt = 0
        taxable_gains = self.future_house_price - self.HOUSE_PRICE
        if self.ANNUAL_SALARY > 50271:
            cgt = taxable_gains * 0.28
        else:
            taxable_income = self.ANNUAL_SALARY - self.PERSONAL_ALLOWANCE
            if taxable_gains - self.CGT_ALLOWANCE + taxable_income <= 50270:
                cgt = (taxable_gains - self.CGT_ALLOWANCE) * 0.18
            else:
                cgt += (50271 - taxable_income) * 0.18
                cgt += (taxable_gains - self.CGT_ALLOWANCE - 50271) * 0.28
        return cgt

    def run_calculations(self, adjust_for_inflation_bool = False):
        self.future_house_price = self.HOUSE_PRICE * (1+self.property_price_growth_annual)**self.years_until_sell
        self.CGT = self.get_capital_gains_tax()
        self.SELLING_COST = self.future_house_price * self.SELLING_COST_MULT + self.CGT
        if adjust_for_inflation_bool:
            self.adjust_for_inflation = self.inflation
            # self.SELLING_COST = self.SELLING_COST / float(1+self.adjust_for_inflation)**(self.years_until_sell)
            # self.future_house_price = self.future_house_price / float(1+self.adjust_for_inflation)**(self.years_until_sell)
        self.monthly_rent = self.HOUSE_PRICE * self.RENTAL_YIELD /12
        self.STAMP_DUTY = get_stamp_duty_next_home(self.HOUSE_PRICE)
        self.discount_rate = self.investment_return_annual
        self.DEPOSIT = self.HOUSE_PRICE * self.DEPOSIT_MULT
        
        self.mortgage_calculations()
        self.get_house_buying_npv()
        self.get_house_buying_fv()
        self.get_renting_fv()

    def mortgage_calculations(self):
        self.mortgage_amount = self.HOUSE_PRICE * (1 - self.DEPOSIT_MULT)
        self.annual_mortgage_payment = annuity_payment(self.mortgage_amount, self.mortgage_interest_annual,self.MORTGAGE_LENGTH,0)
        self.pv_mortage_payments = annuity_pv(self.annual_mortgage_payment, self.discount_rate, self.MORTGAGE_LENGTH, 0)
        self.fv_mortgage_payments = pv_future_payment(annuity_fv(self.annual_mortgage_payment, self.discount_rate, self.MORTGAGE_LENGTH, 0), self.discount_rate, self.MORTGAGE_LENGTH - self.years_until_sell)/ float(1+self.adjust_for_inflation)**(self.years_until_sell)#annuity_fv(self.annual_mortgage_payment, self.discount_rate, self.MORTGAGE_LENGTH, 0)

    def get_house_buying_npv(self):
        pv_of_future_house_price = pv_future_payment(self.future_house_price, self.discount_rate, self.years_until_sell)
        pv_of_selling_cost = pv_future_payment(self.SELLING_COST, self.discount_rate, self.years_until_sell)
        pv_ongoing_cost = annuity_pv(self.HOUSE_PRICE * self.ONGOING_COST_MULT,self.discount_rate, self.years_until_sell, self.inflation)
        # rent saved
        self.pv_rent_saved = annuity_pv(self.HOUSE_PRICE*self.RENTAL_YIELD, self.discount_rate, self.years_until_sell, self.rent_increase)
        # sum it up
        self.buying_npv = pv_of_future_house_price + self.pv_rent_saved - self.pv_mortage_payments- pv_ongoing_cost - self.DEPOSIT  - self.BUYING_COST_FLAT - self.STAMP_DUTY - pv_of_selling_cost

    def get_house_buying_fv(self): # not accounting for deposit,  immediate costs, and rent saved. ongoing costs and mortgage are rolled up and deducted from fv
        if self.adjust_for_inflation > 0:
            self.SELLING_COST = self.SELLING_COST / float(1+self.adjust_for_inflation)**(self.years_until_sell)
            self.future_house_price = self.future_house_price / float(1+self.adjust_for_inflation)**(self.years_until_sell)
        fv_ongoing_cost = annuity_fv(self.HOUSE_PRICE * self.ONGOING_COST_MULT,self.discount_rate, self.years_until_sell, self.inflation, adjust_for_inflation = self.adjust_for_inflation)
        self.rent_fv = annuity_fv(self.HOUSE_PRICE*self.RENTAL_YIELD, self.discount_rate, self.years_until_sell, self.rent_increase, adjust_for_inflation = self.adjust_for_inflation)
        self.buying_fv = self.future_house_price + self.rent_fv - self.SELLING_COST - fv_ongoing_cost -  self.fv_mortgage_payments
        # self.buying_fv_inflation_adjusted = pv_future_payment(self.buying_fv, self.inflation, self.years_until_sell)

    def get_renting_fv(self): # assumes that buying costs and stamp duty are invested, rent is rolled up and deducted
        fv_buying_cost = fv_present_payment(self.BUYING_COST_FLAT, self.discount_rate, self.years_until_sell, adjust_for_inflation = self.adjust_for_inflation)
        fv_STAMP_DUTY = fv_present_payment(self.STAMP_DUTY, self.discount_rate, self.years_until_sell, adjust_for_inflation = self.adjust_for_inflation)
        deposit_fv = fv_present_payment(self.DEPOSIT, self.discount_rate, self.years_until_sell, adjust_for_inflation = self.adjust_for_inflation)
        self.renting_fv = deposit_fv + fv_buying_cost + fv_STAMP_DUTY #- self.rent_fv
        # self.renting_fv_inflation_adjusted = pv_future_payment(self.renting_fv, self.inflation, self.years_until_sell)

def plot_kde_from_list(arrays, st, figsize=(7, 2), main_colors = ['green'], legends = None, title = 'Net Present Value Probability Distribution', xlabel = 'Net Present Value For Property Purchase'):
    fig, ax = plt.subplots(figsize=figsize)
    for num, array in enumerate(arrays):
        # Plot the entire KDE plot in one color
        sns.kdeplot(data=array, ax=ax, color=main_colors[num-1], fill=True, bw_adjust = 2, label='Entire KDE')

        # Plot the shaded area to the left of 0 in a different color
        sns.kdeplot(data=array, ax=ax, color='red', fill=True, bw_adjust = 2, label='Shaded Area', clip=(None, 0))
        # x_low_percentile = np.percentile(array, 0.001)
        # x_high_percentile = np.percentile(array, 99)
        x_mean = np.mean(array)
        x_std = np.std(array)
    
    # Set the axis limits based on the 95th percentile
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_with_commas))
    ax.set_xlim(x_mean-3*x_std, x_mean+3*x_std)
    ax.set_xlabel(xlabel)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    ax.set_title(title)
    if legends:
        plt.legend(labels=legends)
    st.pyplot(fig)


def generate_combinations_and_calculate_npv(
        n_combinations,
        model,
        mortgage_interest_annual_list=[0.05],
        property_price_growth_annual_list=[0.026],
        rent_increase_list=[0.01325],
        investment_return_annual_list=[0.06],
        years_until_sell_list=[20]
        ):
        buying_npv_list = []
        buying_fv_list = []
        renting_fv_list = []
        mortgage_interest_annual_list_chosen=[]
        property_price_growth_annual_list_chosen=[]
        rent_increase_list_chosen=[]
        investment_return_annual_list_chosen=[]
        years_until_sell_list_chosen=[]
        adjust_for_inflation_bool = st.toggle('Adjust for inflation (2% a year)')

        for n in range(n_combinations):

                model.rent_increase = np.random.choice(rent_increase_list)
                model.property_price_growth_annual = np.random.choice(property_price_growth_annual_list)
                model.mortgage_interest_annual = np.random.choice(mortgage_interest_annual_list)
                model.investment_return_annual = np.random.choice(investment_return_annual_list)
                model.years_until_sell = np.random.choice(years_until_sell_list)
                
                model.run_calculations(adjust_for_inflation_bool = adjust_for_inflation_bool)
                buying_npv_list.append(model.buying_npv)
                buying_fv_list.append(model.buying_fv)
                renting_fv_list.append(model.renting_fv)
                mortgage_interest_annual_list_chosen.append(model.mortgage_interest_annual)
                property_price_growth_annual_list_chosen.append(model.property_price_growth_annual)
                rent_increase_list_chosen.append(model.rent_increase)
                investment_return_annual_list_chosen.append(model.investment_return_annual)
                years_until_sell_list_chosen.append(model.years_until_sell)
        model.rent_increase = np.median(rent_increase_list)
        model.property_price_growth_annual =  np.median(property_price_growth_annual_list)
        model.mortgage_interest_annual =  np.median(mortgage_interest_annual_list)
        model.investment_return_annual =  np.median(investment_return_annual_list)
        model.years_until_sell =  int(np.median(years_until_sell_list))
        model.run_calculations(adjust_for_inflation_bool = adjust_for_inflation_bool)

        results_dict = {'buying_npv':buying_npv_list,
                        'mortgage_interest_annual':mortgage_interest_annual_list_chosen,
                        'property_price_growth_annual':property_price_growth_annual_list_chosen,
                        'rent_increase':rent_increase_list_chosen,
                        'investment_return_annual':investment_return_annual_list_chosen,
                        'years_until_sell':years_until_sell_list_chosen}
        results_df = pd.DataFrame(results_dict)
        percentiles_df = calculate_percentiles(buying_npv_list,model.DEPOSIT)
        # st.write(f'Capital Invested: £{model.DEPOSIT:.2f}')
        # st.write(f'Assumed Monthly Rent: £{model.monthly_rent:.2f}')
        # st.write(f'NPV mean: £{np.mean(buying_npv_list):.2f}')
        # st.write(f'NPV mean (as % of invested capital): {np.mean(buying_npv_list)/model.DEPOSIT*100:.2f}%')
        # st.write(f'NPV std: £{np.std(buying_npv_list):.2f}')
        # st.write(f'NPV std (as % of invested capital): {np.std(buying_npv_list)/model.DEPOSIT*100:.2f}%')
        # st.write(f'NPV skew: {skew(buying_npv_list):.2f}')
        if model.buying_fv > model.renting_fv:
            text="Under current assumptions, typical return is higher if you buy."
        else:
            text="Under current assumptions, typical return is higher if you rent and invest the deposit."
        # st.markdown(f'**<p style="background-color:#F0F2F6;font-size:32px;border-radius:0%; font-style: italic;">{text}</p>**', unsafe_allow_html=True)
        st.markdown(f'**<span style="font-size: 32px; font-style: italic;">{text}</span>**', unsafe_allow_html=True)
        left_column, right_column = st.columns(2)
        right_column.write(f"### Buy - Asset value after {model.years_until_sell} years")
        right_column.markdown(f"**Typical Total Asset Value: £{model.buying_fv:,.0f}**")
        right_column.markdown(f"***Breakdown:***")
        right_column.markdown(f" - Capital Invested (deposit plus buying cost): £{model.DEPOSIT + model.BUYING_COST_FLAT + model.STAMP_DUTY:,.0f}")
        right_column.markdown(f" - Property Price at Sale: :green[£{model.future_house_price:,.0f}]")
        right_column.markdown(f" - Selling cost (including Capital Gains Tax): :red[ -£{model.SELLING_COST:,.0f}]")
        right_column.markdown(f" - Total Mortgage Payments (future value at time of sale): :red[ -£{model.fv_mortgage_payments:,.0f}]")
        right_column.markdown(f" - Total Rent Saved (future value at time of sale): :green[£{model.rent_fv:,.0f}]")
        

        left_column.write(f"### Rent and invest - Asset value after {model.years_until_sell} years")
        # plot_kde_from_list(renting_fv_list, left_column, figsize=(5, 2), title = 'Asset Value Probability Distribution', xlabel = 'Asset Value')
        left_column.markdown(f"**Typical Total Asset Value: £{model.renting_fv:,.0f}**")
        left_column.markdown(f"***Breakdown:***")
        left_column.markdown(f" - Capital Invested (deposit plus buying cost): £{model.DEPOSIT + model.BUYING_COST_FLAT + model.STAMP_DUTY:,.0f}")
        if model.renting_fv - (model.DEPOSIT + model.BUYING_COST_FLAT + model.STAMP_DUTY) >= 0:
            left_column.markdown(f" - Assumed Typical Capital Growth: :green[£{model.renting_fv - (model.DEPOSIT + model.BUYING_COST_FLAT + model.STAMP_DUTY):,.0f}]")
        else:
            left_column.markdown(f" - Assumed Typical Capital Growth: :red[£{model.renting_fv - (model.DEPOSIT + model.BUYING_COST_FLAT + model.STAMP_DUTY):,.0f}]")
        st.write('---')
        plot_kde_from_list([buying_fv_list,renting_fv_list], st, figsize=(7, 2), legends = ['Buying', 'Renting'],main_colors = ['orange', 'blue'], title = 'Asset Value Probability Distribution', xlabel = 'Asset Value')
        plot_kde_from_list([buying_npv_list], st, title = 'Net Present Value Probability Distribution', xlabel = 'Net Present Value For Property Purchase')
        st.markdown("<span style='font-size: 14px; font-style: italic;'>Net Present Value represents the net gain/loss that result in purchasing the property in present value. If it is positive, then it is financially better to buy a property. Present value is calculated using a future discount rate equal to your assumed investment return. This is equivalent to assuming that any amount you save on rent or mortgage will be invested. </span>", unsafe_allow_html=True)
        # st.write("### Net Present Value Statistics")
        with st.expander("### Net Present Value Statistics", expanded=False):
            st.write(f'- Buying is better {100-percentiles_df.loc[5,"Percentile"]:.0f}% of the time')
            st.write(f"- Mean: £{np.mean(buying_npv_list):,.0f}")
            st.write(f"- Mean (as % of deposit): {np.mean(buying_npv_list)/model.DEPOSIT*100:.0f}%")
            st.write(f"- Standard Deviation: £{np.std(buying_npv_list):,.0f}")
            st.write(f"- Standard Deviation (as % of deposit): {np.std(buying_npv_list)/model.DEPOSIT*100:.0f}%")
            st.write(f"- Skew: {skew(buying_npv_list):.2f}")
        return percentiles_df, results_df

def graph_kde_plots(results_df, FEATURES, num_cols = 2):
    
    # Calculate the number of rows and columns needed for subplots
    num_features = len(FEATURES)
    
    num_rows = (num_features + num_cols - 1) // num_cols

    # Create a figure and axis for subplots
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(15, 5 * num_rows))

    # Flatten the axes if necessary (in case there's only one row)
    if num_rows == 1:
        axes = axes.reshape(1, -1)

    # Loop through each feature and plot it
    for i, feature in enumerate(FEATURES):
        row = i // num_cols
        col = i % num_cols
        ax = axes[row, col]
        
        sns.kdeplot(data=results_df, x=feature, y="buying_npv", bw_adjust = 2, ax=ax, fill=True)
        ax.set_title(f"{feature} vs. buying_npv")
        ax.set_ylabel("buying_npv")
        ax.set_xlabel(feature)
         # Calculate the 95th percentile for x and y axes
        x_low_percentile = np.percentile(results_df[feature], 0.1)
        y_low_percentile = np.percentile(results_df['buying_npv'], 0.1)
        x_high_percentile = np.percentile(results_df[feature], 99.9)
        y_high_percentile = np.percentile(results_df['buying_npv'], 99.9)
        
        # Set the axis limits based on the 95th percentile
        ax.set_xlim(x_low_percentile, x_high_percentile)
        ax.set_ylim(y_low_percentile, y_high_percentile)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(format_with_commas))
    
        # ax.set_xticklabels(ax.get_xticklabels(), rotation=45)  # Adjust the rotation angle as needed
        
    # Remove any empty subplots
    for i in range(len(FEATURES), num_rows * num_cols):
        fig.delaxes(axes.flatten()[i])

    # Adjust spacing between subplots
    plt.tight_layout()

    # Show the plots
    plt.show()
    st.pyplot(fig)