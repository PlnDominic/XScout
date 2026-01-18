@echo off
echo Starting XScout Agent & Dashboard...
echo Access the Dashboard at: http://localhost:8501
echo To stop, press Ctrl+C in this window.

:: Start the Agent in background
start "XScout Agent" cmd /k ".\venv\Scripts\python main.py"

:: Start the Dashboard
.\venv\Scripts\streamlit run dashboard.py
