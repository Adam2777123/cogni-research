#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"
source venv/bin/activate
streamlit run app/streamlit_app.py

