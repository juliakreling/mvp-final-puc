CREATE DATABASE IF NOT EXISTS shopping_list;
USE shopping_list;

CREATE TABLE IF NOT EXISTS shopping_items (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    quantity INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES fake_store.products(id_product)
);
