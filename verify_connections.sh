#!/bin/bash
# VastraVista - Connection Verification Script
# Tests all major endpoints to ensure everything is connected properly

BASE_URL="http://127.0.0.1:5002"
PASS="✅"
FAIL="❌"

echo "🧪 VastraVista Connection Verification"
echo "======================================"
echo ""

# Test 1: Health Check
echo "1️⃣  Testing health endpoint..."
HEALTH=$(curl -s "${BASE_URL}/api/health" | grep -c "healthy")
if [ $HEALTH -eq 1 ]; then
    echo "   ${PASS} Health endpoint working"
else
    echo "   ${FAIL} Health endpoint failed"
fi
echo ""

# Test 2: Models Status
echo "2️⃣  Testing models status..."
MODELS=$(curl -s "${BASE_URL}/api/models/status" | grep -c "age_detector")
if [ $MODELS -eq 1 ]; then
    echo "   ${PASS} Models loaded successfully"
else
    echo "   ${FAIL} Models status failed"
fi
echo ""

# Test 3: Wardrobe Items
echo "3️⃣  Testing wardrobe endpoint..."
WARDROBE=$(curl -s "${BASE_URL}/api/extended/wardrobe/items" | grep -c "success")
if [ $WARDROBE -eq 1 ]; then
    echo "   ${PASS} Wardrobe endpoint working"
else
    echo "   ${FAIL} Wardrobe endpoint failed"
fi
echo ""

# Test 4: Monk Scale Info
echo "4️⃣  Testing Monk Scale v2 endpoint..."
MONK=$(curl -s "${BASE_URL}/api/v2/monk-scale-info" | grep -c "MST-1")
if [ $MONK -eq 1 ]; then
    echo "   ${PASS} Monk Scale endpoint working"
else
    echo "   ${FAIL} Monk Scale endpoint failed"
fi
echo ""

# Test 5: Wardrobe Analyze (new endpoint)
echo "5️⃣  Testing wardrobe analyze endpoint..."
ANALYZE=$(curl -s "${BASE_URL}/api/extended/wardrobe/analyze" | grep -c "total_items")
if [ $ANALYZE -eq 1 ]; then
    echo "   ${PASS} Wardrobe analyze endpoint working"
else
    echo "   ${FAIL} Wardrobe analyze endpoint failed"
fi
echo ""

echo "======================================"
echo "✅ Verification Complete!"
echo ""
echo "🔗 Active Endpoints:"
echo "  • Main UI: ${BASE_URL}/api/"
echo "  • Health: ${BASE_URL}/api/health"
echo "  • Models: ${BASE_URL}/api/models/status"
echo "  • Analysis: ${BASE_URL}/api/analyze"
echo "  • Wardrobe: ${BASE_URL}/api/extended/wardrobe/*"
echo "  • AI v2: ${BASE_URL}/api/v2/*"
