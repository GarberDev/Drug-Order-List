CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    email VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(30) NOT NULL,
    last_name VARCHAR(30) NOT NULL
);

CREATE TABLE medication_to_be_ordered (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_requested DATE NOT NULL,
    backordered BOOLEAN DEFAULT FALSE NOT NULL,
    quantity INTEGER NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL
);

CREATE TABLE medication_on_order (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_order_placed DATE NOT NULL,
    quantity INTEGER NOT NULL
);

CREATE TABLE order_received (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_received DATE NOT NULL,
    quantity INTEGER NOT NULL,
    received_by VARCHAR(30) NOT NULL
);


CREATE TABLE master_list_for_reports (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_received DATE NOT NULL,
    quantity INTEGER NOT NULL
);
