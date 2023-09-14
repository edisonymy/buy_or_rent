# Opensource Buy or Rent Calculator
https://buy-or-rent.streamlit.app/

tl;dr: I was frustrated by online buy vs rent calculators because they 1. tend to ignore the time value of money, and 2. Don't reflect risk and uncertainty. So I made my own open-source calculator.

To give an example, this calculator (https://smartmoneytools.co.uk/tools/rent-vs-buy/) simply adds up all the costs and returns regardless of time. This means that £100 today is treated the same as £100 in 10 years. This is highly inaccurate because it fails to take into account the time value of money. This way of calculating the result underestimates the impact of periodic payments like rent and mortgage as well as initial payments like stamp duty, compared to the future property value.

Moreover, the uncertainty involved in comparing buying vs renting is really why I wanted to make this. Online calculators allow you to set a single number for parameters like the mortgage rate, but no one can really be certain what these numbers will be. Whether you choose 2% or 3% is mostly arbitrary, so I wanted to see what happens if you allow the input to be a probability density function.
