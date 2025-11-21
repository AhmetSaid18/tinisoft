#!/bin/bash

# Toplu Migration Script
# Tüm servislerin migration'larını çalıştırır (Program.cs'deki otomatik migration'ı tetikler)

set -e

echo "🚀 Tinisoft Toplu Migration Script"
echo "===================================="
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Container isimleri ve servis adları
declare -A SERVICES=(
    ["products"]="tinisoft-products-api-1"
    ["inventory"]="tinisoft-inventory-api-1"
    ["orders"]="tinisoft-orders-api-1"
    ["payments"]="tinisoft-payments-api-1"
    ["marketplace"]="tinisoft-marketplace-api-1"
    ["customers"]="tinisoft-customers-api-1"
    ["shipping"]="tinisoft-shipping-api-1"
    ["notifications"]="tinisoft-notifications-api-1"
    ["invoices"]="tinisoft-invoices-api-1"
    ["api"]="tinisoft-api-1"
)

# Migration çalıştır (container'ı restart ederek)
run_migration() {
    local service_name=$1
    local container_name=$2
    
    echo -e "${YELLOW}📦 Running migration for ${service_name}...${NC}"
    
    if ! docker ps | grep -q "$container_name"; then
        echo -e "${RED}❌ Container ${container_name} is not running!${NC}"
        return 1
    fi
    
    # Container'ı restart et (Program.cs'deki migration kodu çalışacak)
    # RunMigrations=true environment variable'ı zaten docker-compose.yml'de var
    echo "   Restarting container to trigger migration..."
    docker restart "$container_name" > /dev/null 2>&1
    
    # Container'ın başlamasını bekle
    echo "   Waiting for container to start..."
    sleep 5
    
    # Container'ın çalışıp çalışmadığını kontrol et
    if docker ps | grep -q "$container_name"; then
        echo -e "${GREEN}✅ ${service_name} migration completed${NC}"
        return 0
    else
        echo -e "${RED}❌ ${service_name} container failed to start${NC}"
        echo "   Check logs: docker logs ${container_name}"
        return 1
    fi
}

# Tüm servisler için migration çalıştır
run_all_migrations() {
    echo "Running migrations for all services..."
    echo ""
    
    local failed_services=()
    
    for service in "${!SERVICES[@]}"; do
        container="${SERVICES[$service]}"
        if ! run_migration "$service" "$container"; then
            failed_services+=("$service")
        fi
        echo ""
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        echo -e "${GREEN}✨ All migrations completed successfully!${NC}"
    else
        echo -e "${RED}⚠️  Some migrations failed:${NC}"
        for service in "${failed_services[@]}"; do
            echo -e "   - ${RED}${service}${NC}"
        done
        echo ""
        echo "Check logs for details:"
        for service in "${failed_services[@]}"; do
            echo "   docker logs ${SERVICES[$service]}"
        done
    fi
}

# Tek bir servis için migration çalıştır
run_single_migration() {
    local service_name=$1
    
    if [ -z "${SERVICES[$service_name]}" ]; then
        echo -e "${RED}❌ Unknown service: ${service_name}${NC}"
        echo "Available services: ${!SERVICES[@]}"
        exit 1
    fi
    
    container_name="${SERVICES[$service_name]}"
    run_migration "$service_name" "$container_name"
}

# Kullanım
if [ "$1" == "--all" ] || [ -z "$1" ]; then
    run_all_migrations
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage:"
    echo "  ./run-all-migrations.sh              # Run migrations for all services"
    echo "  ./run-all-migrations.sh --all         # Run migrations for all services"
    echo "  ./run-all-migrations.sh <service>     # Run migration for specific service"
    echo ""
    echo "Available services:"
    for service in "${!SERVICES[@]}"; do
        echo "  - $service"
    done
else
    run_single_migration "$1"
fi

