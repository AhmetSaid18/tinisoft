# Migration Guide

## İlk Migration

```bash
# 1. Virtual environment aktif et (eğer yoksa)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# 2. Dependencies yükle
pip install -r requirements.txt

# 3. Environment variables ayarla
# .env dosyasını düzenle

# 4. İlk migration'ları oluştur
python manage.py makemigrations

# 5. Migration'ları uygula
python manage.py migrate

# 6. Superuser oluştur (opsiyonel)
python manage.py createsuperuser
```

## Yeni Model Eklendiğinde

```bash
# 1. Migration oluştur
python manage.py makemigrations

# 2. Migration'ı uygula
python manage.py migrate
```

## Docker ile Migration

```bash
# Container içinde migration
docker exec -it tinisoft-backend python manage.py migrate
```

## Schema Yönetimi

Tenant schema'ları otomatik oluşturulur. Manuel oluşturmak için:

```python
from core.db_utils import create_tenant_schema

create_tenant_schema('tenant_abc123')
```

