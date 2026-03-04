#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MzIzMzg4OX0.BwMKOD2bYqcl5ilIu1oP4V2rbv0T6NmEVNTPC3rFATI"

timeout 5 python test_web_server.py 2>&1 &
sleep 2

echo "=== Testing GET /api/sessions ==="
curl -s http://localhost:8765/api/sessions \
  -H "Authorization: Bearer $TOKEN"

echo ""
echo "=== Testing POST /api/sessions ==="
curl -s -X POST http://localhost:8765/api/sessions \
  -H "Authorization: Bearer $TOKEN"

echo ""
pkill -f test_web_server
