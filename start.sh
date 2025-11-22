#!/bin/bash
# VastraVista - Quick Start

echo "🎨 VastraVista"
echo "==============="

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate
bash scripts/cleanup.sh

echo ""
echo "🚀 Starting server at http://localhost:8080"
echo "Press CTRL+C to stop"
echo ""

python run.py
