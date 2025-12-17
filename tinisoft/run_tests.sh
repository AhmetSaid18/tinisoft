#!/bin/bash

# API Test Script Runner
# Docker container'da testleri çalıştırır

echo "=========================================="
echo "Tinisoft API Test Script"
echo "=========================================="
echo ""

# Docker container'ın çalışıp çalışmadığını kontrol et
if ! docker ps | grep -q tinisoft-backend; then
    echo "❌ Backend container çalışmıyor!"
    echo "Önce 'docker-compose up -d' ile container'ları başlatın."
    exit 1
fi

echo "✅ Backend container çalışıyor"
echo ""

# Test scriptini container içinde çalıştır
echo "Test scripti çalıştırılıyor..."
echo ""

docker exec -it tinisoft-backend python test_all_endpoints.py

echo ""
echo "=========================================="
echo "Test tamamlandı!"
echo "=========================================="

