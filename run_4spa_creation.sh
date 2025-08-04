#!/bin/bash
# Quick runner for 4-spa mirror creation

echo "🚀 Starting 4-Spa Mirror Data Creation..."
echo "========================================"

cd /Users/yashkabra/Desktop/onsen-scraper-deploy

echo "📁 Current directory: $(pwd)"
echo "📋 Checking required files..."

if [ -f "onsen-scraping-e41c80c00b93.json" ]; then
    echo "✅ Credentials file found"
else
    echo "❌ Credentials file missing!"
    exit 1
fi

if [ -f "test_4spa_creation.py" ]; then
    echo "✅ Script file found"
else
    echo "❌ Script file missing!"
    exit 1
fi

echo ""
echo "🔧 Running 4-spa mirror creation..."
echo "This will create new tabs in your Google Sheet with 4-spa projections"
echo ""

python3 test_4spa_creation.py

echo ""
echo "🏁 Done! Check your Google Sheets for new tabs ending with '_4Spa_Mirror'"
