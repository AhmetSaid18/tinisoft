#!/bin/bash

# 🚀 Tinisoft Migration Helper Script
# Django'daki `python manage.py migrate` gibi kullanım

set -e

SERVICE_NAME=$1

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Servis adı belirtilmedi!"
    echo ""
    echo "Kullanım:"
    echo "  ./scripts/migrate.sh <servis-adı>"
    echo ""
    echo "Örnek:"
    echo "  ./scripts/migrate.sh api"
    echo "  ./scripts/migrate.sh products-api"
    echo "  ./scripts/migrate.sh orders-api"
    echo ""
    echo "Mevcut servisler:"
    echo "  - api"
    echo "  - products-api"
    echo "  - orders-api"
    echo "  - inventory-api"
    echo "  - customers-api"
    echo "  - payments-api"
    echo "  - marketplace-api"
    echo "  - shipping-api"
    echo "  - notifications-api"
    echo "  - invoices-api"
    exit 1
fi

# Container adını oluştur
CONTAINER_NAME="tinisoft-${SERVICE_NAME}-1"

# Container'ın çalışıp çalışmadığını kontrol et
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '${CONTAINER_NAME}' çalışmıyor!"
    echo ""
    echo "Container'ı başlat:"
    echo "  docker compose up -d ${SERVICE_NAME}"
    exit 1
fi

echo "🚀 Migration çalıştırılıyor: ${SERVICE_NAME}"
echo "📦 Container: ${CONTAINER_NAME}"
echo ""

# Migration çalıştır
docker exec -it "${CONTAINER_NAME}" dotnet ef database update \
    --project /src/src/Tinisoft.Infrastructure \
    --context ApplicationDbContext

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration başarıyla tamamlandı!"
else
    echo ""
    echo "❌ Migration hatası!"
    exit 1
fi

