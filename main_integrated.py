import streamlit as st
from streamlit_app import StreamlitApp
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point using integrated architecture"""
    app = StreamlitApp()
    app.run_screener()

if __name__ == "__main__":
    main()