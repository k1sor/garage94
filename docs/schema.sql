
PRAGMA foreign_keys = ON;

CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(256) NOT NULL, 
	is_staff BOOLEAN NOT NULL, 
	display_name VARCHAR(120), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE products (
	id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	artist VARCHAR(200) NOT NULL, 
	artist_slug VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	genre VARCHAR(32) NOT NULL, 
	year INTEGER NOT NULL, 
	price NUMERIC(10, 2) NOT NULL, 
	condition VARCHAR(8) NOT NULL, 
	stock INTEGER NOT NULL, 
	description TEXT NOT NULL, 
	cover VARCHAR(255), 
	cover_url VARCHAR(512), 
	deezer_id VARCHAR(32), 
	tracklist TEXT, 
	is_featured BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_products_artist_slug ON products (artist_slug);

CREATE UNIQUE INDEX ix_products_deezer_id ON products (deezer_id);

CREATE INDEX ix_products_genre ON products (genre);

CREATE UNIQUE INDEX ix_products_slug ON products (slug);

CREATE TABLE orders (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	email VARCHAR(120) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE order_items (
	id INTEGER NOT NULL, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	price_at_purchase NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
);
