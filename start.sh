#!/bin/bash

# Start the Scheduler Agent in the background
echo "Starting XScout Agent..."
python main.py &

# Start the Streamlit Dashboard in the foreground
echo "Starting Dashboard..."
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0
