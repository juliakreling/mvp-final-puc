CREATE DATABASE IF NOT EXISTS fake_store;
USE fake_store;

CREATE TABLE IF NOT EXISTS products (
    id_product INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    category VARCHAR(100) NOT NULL
);
