import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Set page config
st.set_page_config(page_title="Stock Outperformance Screener", layout="wide")

# App title and description
st.title("Stock Outperformance Screener")
st.markdown("""
Compare stocks against benchmarks using advanced statistical metrics.
Data source: Yahoo Finance
""")

# Sidebar for inputs
st.sidebar.header("Parameters")

# Date range selection
today = datetime.today()
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", today)

# Benchmark selection
benchmark_options = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Nasdaq 100 Technology": "^NDXT",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT"
}
selected_benchmark = st.sidebar.selectbox(
    "Select Benchmark",
    list(benchmark_options.keys())
)
benchmark_ticker = benchmark_options[selected_benchmark]

# Lookback period for calculations
lookback_period = st.sidebar.slider("Lookback Period (days)",
                                   min_value=10, max_value=252, value=60)

# Stock selection
default_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
stocks_input = st.sidebar.text_area("Enter Stock Tickers (comma separated)",
                                   ",".join(default_stocks))
stock_list = [ticker.strip() for ticker in stocks_input.split(",")]

# Function to calculate metrics
def calculate_metrics(stock_data, benchmark_data, lookback):
    metrics = {}

    # Calculate returns
    stock_returns = stock_data.pct_change().dropna()
    benchmark_returns = benchmark_data.pct_change().dropna()

    # Align the data
    aligned_data = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
    if len(aligned_data) < lookback:
        return None

    # Extract aligned returns
    stock_returns = aligned_data.iloc[:, 0]
    benchmark_returns = aligned_data.iloc[:, 1]

    # Calculate excess returns
    excess_returns = stock_returns - benchmark_returns

    # Information Ratio
    mean_excess = excess_returns.rolling(window=lookback).mean().iloc[-1]
    tracking_error = excess_returns.rolling(window=lookback).std().iloc[-1]
    if tracking_error != 0:
        metrics['Information Ratio'] = mean_excess / tracking_error
    else:
        metrics['Information Ratio'] = np.nan

    # Beta
    covariance = stock_returns.rolling(window=lookback).cov(benchmark_returns).iloc[-1]
    benchmark_variance = benchmark_returns.rolling(window=lookback).var().iloc[-1]
    if benchmark_variance != 0:
        beta = covariance / benchmark_variance
    else:
        beta = np.nan
    metrics['Beta'] = beta

    # Alpha (annualized)
    risk_free_rate = 0.03 / 252  # Approximate daily risk-free rate
    expected_return = risk_free_rate + beta * (benchmark_returns.mean() - risk_free_rate)
    alpha = stock_returns.mean() - expected_return
    metrics['Alpha (daily)'] = alpha
    metrics['Alpha (annualized)'] = alpha * 252

    # Relative Strength
    stock_cumulative = (1 + stock_returns).cumprod().iloc[-1]
    benchmark_cumulative = (1 + benchmark_returns).cumprod().iloc[-1]
    metrics['Relative Strength'] = stock_cumulative / benchmark_cumulative

    # Total Return
    metrics['Total Return'] = stock_cumulative - 1

    # Sharpe Ratio (annualized)
    sharpe = (stock_returns.mean() - risk_free_rate) / stock_returns.std() * np.sqrt(252)
    metrics['Sharpe Ratio'] = sharpe

    return metrics

def safe_download(ticker, start_date, end_date):
    """Safely download and extract Adj Close data"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if data.empty:
            return None
            
        # Debug: print column structure
        print(f"Columns for {ticker}: {data.columns.tolist()}")
        
        # Try different ways to get Adj Close
        if 'Adj Close' in data.columns:
            return data['Adj Close']
        elif hasattr(data.columns, 'levels') and 'Adj Close' in data.columns.levels[0]:
            return data['Adj Close'].iloc[:, 0]
        elif 'Close' in data.columns:
            return data['Close']  # Fallback to Close
        else:
            return None
            
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None

# Main function to run the app
def run_screener():
    with st.spinner('Fetching data and calculating metrics...'):
        # Get benchmark data with error handling
        benchmark_data = safe_download(benchmark_ticker, start_date, end_date)
        
        if benchmark_data is None or benchmark_data.empty:
            st.error(f"Cannot fetch benchmark data for {benchmark_ticker}. Check ticker symbol.")
            return

        # Initialize results dataframe
        results = []

        # Process each stock
        for ticker in stock_list:
            try:
                # Get stock data
                stock_data = safe_download(ticker, start_date, end_date)

                if stock_data is None or stock_data.empty:
                    st.warning(f"No data available for {ticker}")
                    continue

                # Calculate metrics
                metrics = calculate_metrics(stock_data, benchmark_data, lookback_period)

                if metrics:
                    metrics['Ticker'] = ticker
                    results.append(metrics)
                else:
                    st.warning(f"Not enough data for {ticker}")
            except Exception as e:
                st.error(f"Error processing {ticker}: {e}")

        # Create dataframe from results
        if results:
            df_results = pd.DataFrame(results)
            df_results.set_index('Ticker', inplace=True)

            # Sort by Information Ratio by default
            df_results = df_results.sort_values('Information Ratio', ascending=False)

            # Format the dataframe
            formatted_df = df_results.copy()
            for col in formatted_df.columns:
                if col in ['Information Ratio', 'Alpha (daily)', 'Alpha (annualized)',
                          'Sharpe Ratio', 'Beta']:
                    formatted_df[col] = formatted_df[col].round(3)
                elif col in ['Relative Strength', 'Total Return']:
                    formatted_df[col] = formatted_df[col].round(4)

            # Display results
            st.subheader(f"Stock Performance vs {selected_benchmark}")
            st.dataframe(formatted_df)

            # Visualization
            st.subheader("Visual Comparison")

            # Create tabs for different visualizations
            tab1, tab2 = st.tabs(["Performance Chart", "Metrics Comparison"])

            with tab1:
                # Get price data for visualization
                all_tickers = stock_list + [benchmark_ticker]
                prices_data = yf.download(all_tickers, start=start_date, end=end_date)
                
                # Extract Adj Close safely
                if prices_data.empty:
                    st.error("No price data available for visualization")
                    return
                
                # Handle different column structures
                if isinstance(prices_data.columns, pd.MultiIndex):
                    if 'Adj Close' in prices_data.columns.get_level_values(0):
                        prices = prices_data['Adj Close']
                    else:
                        prices = prices_data['Close']
                else:
                    if 'Adj Close' in prices_data.columns:
                        prices = prices_data[['Adj Close']]
                    else:
                        prices = prices_data[['Close']]

                # Normalize prices
                normalized = prices.div(prices.iloc[0]).mul(100)

                # Create plot
                fig = go.Figure()

                # Add benchmark
                fig.add_trace(go.Scatter(
                    x=normalized.index,
                    y=normalized[benchmark_ticker],
                    mode='lines',
                    name=selected_benchmark,
                    line=dict(color='black', width=2, dash='dash')
                ))

                # Add stocks
                for ticker in stock_list:
                    if ticker in normalized.columns:
                        fig.add_trace(go.Scatter(
                            x=normalized.index,
                            y=normalized[ticker],
                            mode='lines',
                            name=ticker
                        ))

                fig.update_layout(
                    title=f"Normalized Price Performance (Base=100)",
                    xaxis_title="Date",
                    yaxis_title="Normalized Price",
                    height=600,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                # Create bar charts for key metrics
                metrics_to_plot = ['Information Ratio', 'Alpha (annualized)', 'Relative Strength']

                fig = make_subplots(rows=len(metrics_to_plot), cols=1,
                                   subplot_titles=metrics_to_plot,
                                   vertical_spacing=0.1)

                for i, metric in enumerate(metrics_to_plot):
                    sorted_df = df_results.sort_values(metric, ascending=False)
                    colors = ['green' if val > 0 else 'red' for val in sorted_df[metric]]

                    fig.add_trace(
                        go.Bar(
                            x=sorted_df.index,
                            y=sorted_df[metric],
                            marker_color=colors,
                            name=metric
                        ),
                        row=i+1, col=1
                    )

                fig.update_layout(height=300*len(metrics_to_plot), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Download button for results
            csv = df_results.to_csv()
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"stock_screener_results_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No results to display. Try different stocks or parameters.")

# Run the app
if __name__ == "__main__":
    run_screener()
