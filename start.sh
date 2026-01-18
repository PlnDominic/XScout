#!/bin/bash

# Force Rebuild 2

echo "[StartScript] Launching XScout Agent..."
# Use unbuffered output (-u) so logs appear in Railway immediately
python -u main.py &

echo "[StartScript] Waiting for agent to initialize..."
sleep 5

echo "[StartScript] Launching Streamlit..."
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false
