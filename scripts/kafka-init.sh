#!/bin/bash

# Kafka Init Script - Cluster ID uyumsuzluğunu otomatik düzeltir

KAFKA_DATA_DIR="/var/lib/kafka/data"
META_PROPERTIES_FILE="${KAFKA_DATA_DIR}/meta.properties"

echo "Checking Kafka meta.properties..."

# Eğer meta.properties varsa ve Cluster ID uyumsuzluğu olabilirse, dosyayı sil
if [ -f "$META_PROPERTIES_FILE" ]; then
    echo "meta.properties found, checking Cluster ID..."
    
    # Zookeeper'dan Cluster ID'yi al (eğer bağlanabiliyorsa)
    # Eğer bağlanamazsa, meta.properties'i sil (yeni bir cluster başlatılacak)
    if ! timeout 5 zookeeper-shell zookeeper:2181 get /cluster/id 2>/dev/null | grep -q "cluster.id"; then
        echo "Warning: Cannot connect to Zookeeper or Cluster ID mismatch detected."
        echo "Removing meta.properties to allow fresh cluster start..."
        rm -f "$META_PROPERTIES_FILE"
        echo "meta.properties removed. Kafka will start with new Cluster ID."
    else
        echo "Cluster ID check passed."
    fi
else
    echo "No meta.properties found. Kafka will create new one."
fi

# Kafka'yı başlat
exec /etc/confluent/docker/run

