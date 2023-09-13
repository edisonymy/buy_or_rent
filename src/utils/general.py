import pandas as pd
import numpy as np
import seaborn as sns
import pandas as pddef 
import matplotlib.pyplot as plt
import streamlit as st
def calculate_percentiles(arr, capital_invested):
    """
    Calculate the 10th, 25th, 50th (median), 75th, 90th, and the percentile of the value closest to 0 in an array.
    Also, add a column that represents the values as a percentage of capital invested.

    Args:
    arr (list or numpy.ndarray): Input array.
    capital_invested (float): The amount of capital invested.

    Returns:
    pandas.DataFrame: A DataFrame with percentiles and value as a percentage of capital invested.
    """
    if not isinstance(arr, (list, np.ndarray)):
        raise ValueError("Input must be a list or numpy.ndarray")

    percentiles = [10, 25, 50, 75, 90]
    percentile_values = np.percentile(arr, percentiles)

    # Find the value closest to 0
    closest_value = min(arr, key=lambda x: abs(x - 0))

    # Calculate the percentile of the closest value
    sorted_arr = np.sort(arr)
    index_of_closest = np.where(sorted_arr == closest_value)[0][0]
    closest_percentile = (index_of_closest / (len(sorted_arr) - 1)) * 100

    # Create the DataFrame with the "Value as % of Capital" column
    data = {
        'Percentile': percentiles + [closest_percentile],
        'NPV': np.append(percentile_values, closest_value)
    }

    df = pd.DataFrame(data)
    df['% return'] = (df['NPV'] / capital_invested) * 100

    return df

def bin_continuous_features(df, bin_config):
    """
    Encode continuous features into bins and add them as new columns to the DataFrame.

    Parameters:
    - df: pandas DataFrame
        The DataFrame containing the continuous features.
    - bin_config: dict
        A dictionary specifying the binning configuration for each feature.
        Example: {'feature1': [0, 10, 20, 30], 'feature2': [0, 5, 10]}

    Returns:
    - df: pandas DataFrame
        The DataFrame with binned features added as new columns.
    """

    for feature, bins in bin_config.items():
        # Create a new column with the binned values
        df[f'{feature}_bin'] = pd.cut(df[feature], bins=bins, labels=False)

    return df

def get_param_distribution(mean, std, samples, bins,plot=True, as_int = False, title =''):
    if std <=0:
        return [mean]
    s = np.random.normal(mean, std, samples)
    if plot:
        fig, ax = plt.subplots(figsize=(4, 3))
        # plt.hist(s, bins, density=False)
        sns.kdeplot(s,bw_adjust=5)
        plt.title(title)
        st.sidebar.pyplot(fig)
    if as_int:
        s=s.astype(int) 
    return s