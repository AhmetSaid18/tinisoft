#!/bin/bash

# Kafka Cluster ID Uyumsuzluğu Düzeltme Scripti
# Bu script Kafka container'ı başlamadan önce meta.properties'i kontrol eder ve düzeltir

echo "🔧 Kafka Cluster ID uyumsuzluğu düzeltme scripti"
echo "================================================"

# Kafka container'ını durdur
echo "1. Kafka container'ını durduruyorum..."
docker compose stop kafka 2>/dev/null || true

# Kafka volume'unu kontrol et
echo "2. Kafka volume'unu kontrol ediyorum..."
if docker volume inspect tinisoft_kafka_data >/dev/null 2>&1; then
    echo "   Kafka volume bulundu."
    
    # Volume içindeki meta.properties'i kontrol et
    echo "3. meta.properties dosyasını kontrol ediyorum..."
    
    # Geçici container ile volume'u mount et ve meta.properties'i kontrol et
    docker run --rm \
        -v tinisoft_kafka_data:/data \
        alpine sh -c "
            if [ -f /data/meta.properties ]; then
                echo '   meta.properties bulundu.'
                echo '   Dosyayı siliyorum (Cluster ID uyumsuzluğu nedeniyle)...'
                rm -f /data/meta.properties
                echo '   ✅ meta.properties silindi.'
            else
                echo '   meta.properties bulunamadı (normal).'
            fi
        "
else
    echo "   Kafka volume bulunamadı (normal, ilk kurulum)."
fi

# Kafka'yı yeniden başlat
echo "4. Kafka'yı yeniden başlatıyorum..."
docker compose up -d kafka

# Kafka'nın başlamasını bekle
echo "5. Kafka'nın başlamasını bekliyorum..."
sleep 10

# Durumu kontrol et
echo "6. Kafka durumunu kontrol ediyorum..."
if docker compose ps kafka | grep -q "Up"; then
    echo "   ✅ Kafka başarıyla başladı!"
else
    echo "   ❌ Kafka başlatılamadı. Logları kontrol edin:"
    echo "   docker compose logs kafka"
fi

echo ""
echo "✨ İşlem tamamlandı!"

