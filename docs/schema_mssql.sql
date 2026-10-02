
IF DB_ID('GarageVinylDB') IS NULL
    CREATE DATABASE GarageVinylDB;
GO

USE GarageVinylDB;
GO

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;
GO

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(64) NOT NULL UNIQUE,
    email NVARCHAR(120) NOT NULL UNIQUE,
    password_hash NVARCHAR(256) NOT NULL,
    is_staff BIT NOT NULL DEFAULT 0,
    display_name NVARCHAR(120) NULL,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    artist NVARCHAR(200) NOT NULL,
    artist_slug NVARCHAR(255) NOT NULL,
    slug NVARCHAR(255) NOT NULL UNIQUE,
    genre NVARCHAR(32) NOT NULL,
    year INT NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    condition NVARCHAR(8) NOT NULL DEFAULT 'VG+',
    stock INT NOT NULL DEFAULT 0 CHECK (stock >= 0),
    description NVARCHAR(MAX) NOT NULL DEFAULT '',
    cover NVARCHAR(255) NULL,
    cover_url NVARCHAR(512) NULL,
    deezer_id NVARCHAR(32) NULL,
    tracklist NVARCHAR(MAX) NULL,
    is_featured BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    updated_at DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);

CREATE INDEX ix_products_genre ON products (genre);
CREATE INDEX ix_products_artist_slug ON products (artist_slug);

CREATE TABLE orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NULL,
    email NVARCHAR(120) NOT NULL,
    status NVARCHAR(16) NOT NULL DEFAULT 'PENDING',
    total DECIMAL(12,2) NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT fk_orders_users FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE order_items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
    price_at_purchase DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_items_orders FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    CONSTRAINT fk_items_products FOREIGN KEY (product_id) REFERENCES products (id)
);
GO
