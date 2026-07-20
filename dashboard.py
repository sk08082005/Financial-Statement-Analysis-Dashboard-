import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("📊 Financial Statement Analysis Dashboard")
st.write("PSU Infra Companies ka Financial Health Analysis")

companies = {
    "RITES": "RITES.NS",
    "IRCON": "IRCON.NS",
    "RVNL": "RVNL.NS",
    "NBCC": "NBCC.NS",
    "IRFC": "IRFC.NS"
}

selected_company = st.selectbox("Choose Company:", list(companies.keys()))
ticker_symbol = companies[selected_company]
stock = yf.Ticker(ticker_symbol)

# ---------- COMPANY OVERVIEW ----------
info = stock.info

st.subheader(f"🏢 {info.get('longName', selected_company)} - Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sector", info.get('sector', 'N/A'))
col2.metric("Current Price (₹)", info.get('currentPrice', 'N/A'))
col3.metric("Market Cap (₹ Cr)", round(info.get('marketCap', 0)/1e7, 2))
col4.metric("52W High/Low", f"{info.get('fiftyTwoWeekHigh','N/A')} / {info.get('fiftyTwoWeekLow','N/A')}")

with st.expander("📄 Company's Description"):
    st.write(info.get('longBusinessSummary', 'Description not available.'))

# ---------- VALUATION RATIOS ----------
st.subheader("💰 Valuation Ratios")

col1, col2, col3, col4 = st.columns(4)
col1.metric("P/E Ratio", round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 'N/A')
col2.metric("P/B Ratio", round(info.get('priceToBook', 0), 2) if info.get('priceToBook') else 'N/A')
col3.metric("Dividend Yield (%)", round(info.get('dividendYield', 0)*100, 2) if info.get('dividendYield') else 'N/A')
col4.metric("EPS", info.get('trailingEps', 'N/A'))

# ---------- RATIO CALCULATION (Multi-Year) ----------
def calculate_all_years_ratios(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    bs = stock.balance_sheet
    inc = stock.financials

    all_ratios = {}

    for year_col in bs.columns:
        if year_col not in inc.columns:
            continue
        try:
            net_income = inc.loc['Net Income', year_col]
            revenue = inc.loc['Total Revenue', year_col]
            equity = bs.loc['Stockholders Equity', year_col]
            total_assets = bs.loc['Total Assets', year_col]
            current_assets = bs.loc['Current Assets', year_col]
            current_liabilities = bs.loc['Current Liabilities', year_col]
            total_liabilities = bs.loc['Total Liabilities Net Minority Interest', year_col]

            year_label = str(year_col.year)
            all_ratios[year_label] = {
                'Net Profit Margin (%)': round((net_income / revenue) * 100, 2),
                'ROE (%)': round((net_income / equity) * 100, 2),
                'ROA (%)': round((net_income / total_assets) * 100, 2),
                'Current Ratio': round(current_assets / current_liabilities, 2),
                'Debt to Equity': round(total_liabilities / equity, 2)
            }
        except (KeyError, ZeroDivisionError):
            continue

    return pd.DataFrame(all_ratios)

st.subheader(f"📈 {selected_company} - Multi-Year Ratio Trend")
ratio_df = calculate_all_years_ratios(ticker_symbol)
st.dataframe(ratio_df, use_container_width=True)

# ---------- REVENUE VS NET INCOME TREND ----------
st.subheader("Revenue vs Net Income Trend")
inc = stock.financials
revenue = inc.loc['Total Revenue'].dropna()
net_income = inc.loc['Net Income'].dropna()
years = [str(col.year) for col in revenue.index]

fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=revenue.values, mode='lines+markers', name='Revenue'))
fig.add_trace(go.Scatter(x=years, y=net_income.values, mode='lines+markers', name='Net Income'))
st.plotly_chart(fig, use_container_width=True)

# ---------- RAW FINANCIAL STATEMENTS (For Verification) ----------
st.subheader("🔍 Raw Financial Data (Verification Ke Liye)")

tab1, tab2, tab3 = st.tabs(["Balance Sheet", "Income Statement", "Cash Flow"])

with tab1:
    st.dataframe(stock.balance_sheet, use_container_width=True)

with tab2:
    st.dataframe(stock.financials, use_container_width=True)

with tab3:
    st.dataframe(stock.cashflow, use_container_width=True)

# ---------- SINGLE YEAR RATIO CALCULATION (for comparison + insights) ----------
def calculate_ratios(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    bs = stock.balance_sheet
    inc = stock.financials
    latest_year = bs.columns[0]
    ratios = {}
    try:
        net_income = inc.loc['Net Income', latest_year]
        revenue = inc.loc['Total Revenue', latest_year]
        equity = bs.loc['Stockholders Equity', latest_year]
        total_assets = bs.loc['Total Assets', latest_year]
        current_assets = bs.loc['Current Assets', latest_year]
        current_liabilities = bs.loc['Current Liabilities', latest_year]
        total_liabilities = bs.loc['Total Liabilities Net Minority Interest', latest_year]

        ratios['Net Profit Margin (%)'] = round((net_income / revenue) * 100, 2)
        ratios['ROE (%)'] = round((net_income / equity) * 100, 2)
        ratios['ROA (%)'] = round((net_income / total_assets) * 100, 2)
        ratios['Current Ratio'] = round(current_assets / current_liabilities, 2)
        ratios['Debt to Equity'] = round(total_liabilities / equity, 2)
    except KeyError:
        pass
    return ratios

# ---------- INSIGHTS ENGINE ----------
def generate_insights(ratios):
    insights = []

    npm = ratios.get('Net Profit Margin (%)')
    if npm is not None:
        if npm < 5:
            insights.append(("🔴 Low Profitability",
                f"Net Profit Margin is {npm}%. Operating costs (raw material, admin expenses) by reducing or pricing strategy can improve profitability ."))
        elif npm > 15:
            insights.append(("🟢 Strong Profitability",
                f"Net Profit Margin is {npm}%,it is healthy — cost control and revenue generation both are nice."))

    cr = ratios.get('Current Ratio')
    if cr is not None:
        if cr < 1:
            insights.append(("🔴 Liquidity Risk",
                f"Current Ratio {cr} is (less than 1) — The company might face difficulties in paying its short-term bills. It is crucial to improve working capital management (such as collecting receivables faster)"))
        elif cr > 3:
            insights.append(("🟡 Excess Idle Cash",
                f"Current Ratio {cr} is alot high — Meaning, there are significant idle cash/assets available that could be utilized for investment to drive growth."))

    de = ratios.get('Debt to Equity')
    if de is not None:
        if de > 2:
            insights.append(("🔴 High Debt Burden",
                f"Debt-to-Equity Ratio is {de} — company is dependent on loan.It is better to reduce existing loans or consider equity financing before taking on new debt."))
        elif de < 0.5:
            insights.append(("🟢 Conservative Debt Level",
                f"Debt-to-Equity Ratio is {de}, it is healthy — The company is financially stable and can even use a bit of leverage for growth if needed."))

    roe = ratios.get('ROE (%)')
    if roe is not None:
        if roe < 10:
            insights.append(("🔴 Low Return on Equity",
                f"ROE is {roe}% — shareholder's money is not being efficiently used. Asset utilization or profit margins can be improved and ROE can be increased."))
        elif roe > 20:
            insights.append(("🟢 Excellent ROE",
                f"ROE is {roe}%,it is strong enough — company is using shareholder's capital efficiently."))

    roa = ratios.get('ROA (%)')
    if roa is not None and roa < 3:
        insights.append(("🟡 Low Asset Efficiency",
            f"ROA is {roa}% — companies assets are not generating enough as much they should do it. Idle/underutilized assets should be identified and use it in a better way."))

    if not insights:
        insights.append(("ℹ️ No Major Flags", "No major concern on the basis of current data ."))

    return insights

# ---------- INSIGHTS FOR SELECTED COMPANY ----------
st.subheader("💡 Insights & Improvement Recommendations")

selected_ratios = calculate_ratios(ticker_symbol)
insights = generate_insights(selected_ratios)

for title, description in insights:
    st.markdown(f"**{title}**")
    st.write(description)
    st.markdown("---")

# ---------- MULTI-COMPANY COMPARISON ----------
st.subheader("⚖️ Multi-Company Comparison (Latest Year)")

comparison_data = {}
for name, symbol in companies.items():
    comparison_data[name] = calculate_ratios(symbol)
comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, use_container_width=True)