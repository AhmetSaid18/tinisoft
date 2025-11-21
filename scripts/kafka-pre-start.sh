#!/bin/sh

# Kafka Pre-Start Script
# Cluster ID uyumsuzluğunu önlemek için meta.properties'i kontrol eder ve gerekirse siler

KAFKA_DATA_DIR="/var/lib/kafka/data"
META_PROPERTIES_FILE="${KAFKA_DATA_DIR}/meta.properties"

echo "🔍 Kafka Pre-Start: Checking meta.properties..."

# Eğer meta.properties varsa, Cluster ID uyumsuzluğunu önlemek için sil
if [ -f "$META_PROPERTIES_FILE" ]; then
    echo "⚠️  meta.properties found. Removing to prevent Cluster ID mismatch..."
    rm -f "$META_PROPERTIES_FILE"
    echo "✅ meta.properties removed. Kafka will create new one with matching Cluster ID."
else
    echo "✅ No meta.properties found. Kafka will create new one."
fi

# Orijinal Confluent entrypoint'i çalıştır
exec /etc/confluent/docker/run

