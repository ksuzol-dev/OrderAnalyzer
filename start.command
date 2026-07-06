#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "OrderAnalyzer starting..."
echo "Project folder: $(pwd)"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found. Please install Python 3 first."
  read -p "Press Enter to exit..."
  exit 1
fi

if [ ! -f "requirements.txt" ]; then
  echo "ERROR: requirements.txt was not found. Please run this script inside the OrderAnalyzer folder."
  read -p "Press Enter to exit..."
  exit 1
fi

echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

echo
echo "Launching Streamlit..."
python3 -m streamlit run app.py
