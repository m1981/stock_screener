import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from screener_engine import ScreenerEngine
from config import ScreenerConfig
from datetime import datetime, timedelta
from typing import Dict

class StreamlitApp:
    """Streamlit UI as specified in docs/specification.md"""
    
    def __init__(self):
        self.config = ScreenerConfig()
        self.engine = ScreenerEngine(self.config)
    
    def run_screener(self):
        """Main application entry point"""
        st.set_page_config(page_title="Stock Outperformance Screener", layout="wide")
        st.title("Stock Outperformance Screener")
        
        # Handle user input
        params = self.handle_user_input()
        
        if st.button("Run Screening"):
            with st.spinner('Analyzing stocks...'):
                try:
                    results = self.engine.screen_stocks(
                        params['tickers'], 
                        params['benchmark'], 
                        params['lookback']
                    )
                    
                    if not results.empty:
                        self.display_results(results)
                        self.create_visualizations(results)
                    else:
                        st.warning("No results to display")
                        
                except Exception as e:
                    st.error(f"Error during screening: {e}")
    
    def handle_user_input(self) -> Dict:
        """Handle user input from sidebar"""
        st.sidebar.header("Parameters")
        
        # Date range
        today = datetime.today()
        start_date = st.sidebar.date_input("Start Date", today - timedelta(days=500))
        end_date = st.sidebar.date_input("End Date", today)
        
        # Benchmark selection
        benchmark_options = {
            "S&P 500": "^GSPC",
            "Nasdaq 100": "^NDX",
            "Dow Jones": "^DJI"
        }
        selected_benchmark = st.sidebar.selectbox("Benchmark", list(benchmark_options.keys()))
        
        # Lookback period
        lookback = st.sidebar.slider("Lookback Period", 10, 252, 60)
        
        # Stock selection
        stocks_input = st.sidebar.text_area("Stock Tickers", "AAPL,MSFT,NVDA")
        tickers = [t.strip() for t in stocks_input.split(",")]
        
        return {
            'tickers': tickers,
            'benchmark': benchmark_options[selected_benchmark],
            'lookback': lookback,
            'start_date': start_date,
            'end_date': end_date
        }
    
    def display_results(self, results: pd.DataFrame):
        """Display screening results"""
        st.subheader("Screening Results")
        
        # Format the dataframe for better display
        formatted_df = results.copy()
        for col in formatted_df.columns:
            if col in ['Information Ratio', 'Alpha', 'Sharpe Ratio', 'Beta']:
                formatted_df[col] = formatted_df[col].round(3)
            elif col in ['Relative Strength', 'Total Return']:
                formatted_df[col] = formatted_df[col].round(4)
        
        st.dataframe(formatted_df, use_container_width=True)
    
    def create_visualizations(self, results: pd.DataFrame):
        """Create charts and visualizations"""
        st.subheader("Performance Visualization")
        
        # Create tabs for different visualizations
        tab1, tab2 = st.tabs(["Metrics Comparison", "Performance Rankings"])
        
        with tab1:
            # Bar chart for key metrics
            metrics_to_plot = ['Information Ratio', 'Alpha', 'Sharpe Ratio']
            
            fig = make_subplots(
                rows=len(metrics_to_plot), 
                cols=1,
                subplot_titles=metrics_to_plot,
                vertical_spacing=0.1
            )
            
            for i, metric in enumerate(metrics_to_plot):
                if metric in results.columns:
                    sorted_df = results.sort_values(metric, ascending=False)
                    colors = ['green' if val > 0 else 'red' for val in sorted_df[metric]]
                    
                    fig.add_trace(
                        go.Bar(
                            x=sorted_df.index,
                            y=sorted_df[metric],
                            marker_color=colors,
                            name=metric,
                            showlegend=False
                        ),
                        row=i+1, col=1
                    )
            
            fig.update_layout(height=300*len(metrics_to_plot))
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Rankings table
            st.subheader("Stock Rankings")
            rankings = results.copy()
            rankings['Rank'] = range(1, len(rankings) + 1)
            st.dataframe(rankings[['Rank'] + list(rankings.columns[:-1])], use_container_width=True)