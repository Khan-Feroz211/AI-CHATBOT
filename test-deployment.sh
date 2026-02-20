#!/bin/bash

# AI Project Assistant - Deployment Test Script
# Tests all critical functionality before client handover

set -e

echo "🚀 AI Project Assistant - Deployment Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
WEB_URL="${WEB_URL:-http://localhost:8080}"

# Test counter
PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected, got $response)"
        ((FAILED++))
    fi
}

# Test API endpoint with JSON
test_api_json() {
    local name=$1
    local url=$2
    local data=$3
    
    echo -n "Testing $name... "
    
    response=$(curl -s -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data" \
        -w "\n%{http_code}" || echo "000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "Response: $body"
        ((FAILED++))
    fi
}

echo "1. Testing Docker Containers"
echo "----------------------------"
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Docker containers running${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Docker containers not running${NC}"
    ((FAILED++))
fi
echo ""

echo "2. Testing API Endpoints"
echo "------------------------"
test_endpoint "API Health Check" "$API_URL/health" "200"
test_endpoint "API Root" "$API_URL/" "200"
echo ""

echo "3. Testing Payment API"
echo "----------------------"
test_api_json "Payment Creation (JazzCash)" \
    "$API_URL/api/v1/payments/create" \
    '{"order_id":"TEST-001","amount_pkr":1000,"payment_provider":"jazzcash"}'

test_api_json "Payment Creation (EasyPaisa)" \
    "$API_URL/api/v1/payments/create" \
    '{"order_id":"TEST-002","amount_pkr":2000,"payment_provider":"easypaisa"}'

test_api_json "Payment Creation (Bank Transfer)" \
    "$API_URL/api/v1/payments/create" \
    '{"order_id":"TEST-003","amount_pkr":3000,"payment_provider":"bank_transfer"}'

test_api_json "Payment Creation (COD)" \
    "$API_URL/api/v1/payments/create" \
    '{"order_id":"TEST-004","amount_pkr":500,"payment_provider":"cod"}'
echo ""

echo "4. Testing Web Interface"
echo "------------------------"
test_endpoint "Web Home Page" "$WEB_URL/" "200"
test_endpoint "Web CSS" "$WEB_URL/css/style.css" "200"
test_endpoint "Web JS" "$WEB_URL/js/script.js" "200"
echo ""

echo "5. Testing Security"
echo "-------------------"
echo -n "Checking .env file permissions... "
if [ -f ".env" ]; then
    perms=$(stat -c "%a" .env 2>/dev/null || stat -f "%A" .env 2>/dev/null)
    if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (Permissions: $perms)"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠ WARNING${NC} (Permissions: $perms, should be 600)"
    fi
else
    echo -e "${YELLOW}⚠ WARNING${NC} (.env file not found)"
fi

echo -n "Checking for hardcoded secrets... "
if grep -r "admin123\|password123\|secret123" . --exclude-dir={node_modules,.git,venv,env} --exclude="*.md" >/dev/null 2>&1; then
    echo -e "${RED}✗ FAILED${NC} (Found hardcoded secrets)"
    ((FAILED++))
else
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
fi
echo ""

echo "6. Testing Database"
echo "-------------------"
echo -n "Checking database file... "
if docker exec project-assistant-api test -f /app/chatbot_data/chatbot.db 2>/dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (Database will be created on first use)"
fi
echo ""

echo "7. Testing Backups"
echo "------------------"
echo -n "Creating test backup... "
if docker exec project-assistant-api tar czf /tmp/test_backup.tar.gz /app/chatbot_data 2>/dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
    docker exec project-assistant-api rm /tmp/test_backup.tar.gz
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

echo "8. Testing Resource Usage"
echo "-------------------------"
echo "Container resource usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 3
echo ""

echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! System is production-ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review before deployment.${NC}"
    exit 1
fi
