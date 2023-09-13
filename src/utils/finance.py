def get_stamp_duty_next_home(HOUSE_PRICE):
    if HOUSE_PRICE <=250000:
        return 0
    elif HOUSE_PRICE <=925000:
        return (HOUSE_PRICE-250000) * 0.05
    elif HOUSE_PRICE <=1500000:
        return (HOUSE_PRICE-925000) * 0.10 + (925000-250000) * 0.05
    else:
        return (HOUSE_PRICE-1500000) * 0.12 + (925000-250000) * 0.05 + (1500000-925000) * 0.10
    
def annuity_pv(payment, discount_rate, n_periods, growth_rate):
    pv = 0
    for i in range(1, n_periods+1):
        pv += payment*(1+growth_rate)**(i-1) /(1+discount_rate)**(i)
    return pv

def annuity_fv(payment, discount_rate, n_periods, growth_rate):
    pv = 0
    for i in range(1, n_periods+1):
        pv += payment*(1+growth_rate)**(i-1) *(1+discount_rate)**(n_periods-i)
    return pv

def annuity_payment(pv, discount_rate, n_periods, growth_rate):
    return pv* (discount_rate - growth_rate) / (1- (1+growth_rate)**n_periods * (1+discount_rate)**(-1*n_periods))


def pv_future_payment(payment, discount_rate, n_periods):
    return payment/(1+discount_rate)**(n_periods)

def fv_present_payment(payment, discount_rate, n_periods):
    return payment*(1+discount_rate)**(n_periods)