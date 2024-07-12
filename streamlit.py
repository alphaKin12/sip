import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date

st.title(":green[SIP] Calculator :chart_with_upwards_trend:")

# Remove Streamlit menu and footer
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# Sliders for input
monthly_investment = st.slider("Monthly Investment Amount (₹)", min_value=500, max_value=50000, value=2000, step=500)
investment_period = st.slider("Investment Period (Years)", min_value=2, max_value=30, value=4, step=1)
expected_return_rate = st.slider("Expected Annual Return Rate (%)", min_value=6.0, max_value=25.0, value=12.0, step=0.1)
adjust_for_inflation = st.checkbox("Adjust for Inflation (5% annually)")

# Radio buttons for investment type
investment_type = st.radio("Choose Investment Type", ["Monthly", "Quarterly", "One-time"])

# Calculate SIP returns
def calculate_sip_returns(monthly_investment, investment_period, expected_return_rate, adjust_for_inflation, investment_type):
    if investment_type == "Monthly":
        periods_per_year = 12
        investment_amount_per_period = monthly_investment
    elif investment_type == "Quarterly":
        periods_per_year = 4
        investment_amount_per_period = monthly_investment * 3  # Quarterly investment
    elif investment_type == "One-time":
        periods_per_year = 1
        investment_amount_per_period = monthly_investment * 12 * investment_period  # One-time investment

    months = investment_period * periods_per_year
    monthly_rate = (expected_return_rate / 100) / periods_per_year
    
    if adjust_for_inflation:
        # Adjust expected return rate for inflation (5% annually)
        inflation_adjusted_rate = expected_return_rate - 5.0
        monthly_rate = (inflation_adjusted_rate / 100) / periods_per_year
    
    invested_amount = investment_amount_per_period * (months / periods_per_year)
    future_value = investment_amount_per_period * ((((1 + monthly_rate) ** months) - 1) / monthly_rate) * (1 + monthly_rate)
    
    return invested_amount, future_value

# Calculate button
if st.button("Calculate"):
    invested_amount, future_value = calculate_sip_returns(monthly_investment, investment_period, expected_return_rate, adjust_for_inflation, investment_type)
    
    # Display results
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Investment", f"₹{invested_amount:,.0f}")
    col2.metric("Expected Returns", f"₹{future_value - invested_amount:,.0f}")
    col3.metric("Total Value", f"₹{future_value:,.0f}")
       
    # Create DataFrame for plotting
    periods_per_year = 12 if investment_type == "Monthly" else 4 if investment_type == "Quarterly" else 1
    months = np.arange(1, investment_period * periods_per_year + 1)
    invested_values = investment_amount_per_period * (months / periods_per_year)
    future_values = [calculate_sip_returns(monthly_investment, m/periods_per_year, expected_return_rate, adjust_for_inflation, investment_type)[1] for m in months]
    
    start_date = date.today()
    df = pd.DataFrame({
        'Month': pd.date_range(start=start_date, periods=len(months), freq='M'),
        'Invested Amount': invested_values,
        'Future Value': future_values
    })
    
    # Create Altair chart
    brush = alt.selection_interval(encodings=["x"])
    
    base = alt.Chart(df).encode(
        x='Month:T',
        y=alt.Y('Amount:Q', axis=alt.Axis(title='Amount (₹)', format=',.0f'))
    ).properties(
        width=600,
        height=400
    )

    lines = base.mark_line().encode(
        color=alt.Color('Variable:N', scale=alt.Scale(domain=['Invested Amount', 'Future Value'],
                                                      range=['#1f77b4', '#2ca02c']))
    ).transform_fold(
        ['Invested Amount', 'Future Value'],
        as_=['Variable', 'Amount']
    )

    points = lines.mark_point().encode(
        opacity=alt.condition(brush, alt.value(1), alt.value(0.2))
    ).add_selection(brush)

    chart = (lines + points).properties(
        title='SIP Growth Over Time'
    ).interactive()

    # Display the Altair chart with Streamlit theme
    st.altair_chart(chart, theme="streamlit", use_container_width=True)
    
    # Create yearly breakdown data
    yearly_data = df[df.index % periods_per_year == 0].copy()
    yearly_data['Year'] = yearly_data.index // periods_per_year + 1
    yearly_data = yearly_data[['Year', 'Invested Amount', 'Future Value']]
    yearly_data = yearly_data.melt('Year', var_name='Category', value_name='Amount')

    # Create Altair chart for bar plot
    click = alt.selection_multi(encodings=['color'])

    bars = alt.Chart(yearly_data).mark_bar().encode(
        x='Year:O',
        y='Amount:Q',
        color=alt.condition(click, 'Category:N', alt.value('lightgray')),
        tooltip=['Year', 'Category', 'Amount']
    ).properties(
        width=600,
        height=400,
        title='Yearly Breakdown'
    ).add_selection(click)

    # Display the bar chart
    st.altair_chart(bars, theme="streamlit", use_container_width=True)

#st.info("Note: This calculator assumes a constant rate of return. Actual returns may vary based on market conditions.")
