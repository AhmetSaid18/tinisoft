-- PostgreSQL Schema Initialization Script
-- Bu script PostgreSQL başlatıldığında otomatik çalışır ve tüm schema'ları oluşturur

-- Products Schema
CREATE SCHEMA IF NOT EXISTS products;

-- Inventory Schema
CREATE SCHEMA IF NOT EXISTS inventory;

-- Payments Schema
CREATE SCHEMA IF NOT EXISTS payments;

-- Orders Schema
CREATE SCHEMA IF NOT EXISTS orders;

-- Shipping Schema
CREATE SCHEMA IF NOT EXISTS shipping;

-- Notifications Schema
CREATE SCHEMA IF NOT EXISTS notifications;

-- Public Schema (Main API için)
-- Public schema zaten var, ekstra bir şey yapmaya gerek yok

-- Schema'lar için gerekli izinleri ver
GRANT ALL ON SCHEMA products TO postgres;
GRANT ALL ON SCHEMA inventory TO postgres;
GRANT ALL ON SCHEMA payments TO postgres;
GRANT ALL ON SCHEMA orders TO postgres;
GRANT ALL ON SCHEMA shipping TO postgres;
GRANT ALL ON SCHEMA notifications TO postgres;

-- Default search path'i ayarla (opsiyonel)
ALTER DATABASE tinisoft SET search_path TO public, products, inventory, payments, orders, shipping, notifications;

