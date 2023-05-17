CREATE TABLE medication_to_be_ordered (
id SERIAL PRIMARY KEY,
name VARCHAR(100) NOT NULL,
date_requested DATE NOT NULL,
backordered BOOLEAN NOT NULL DEFAULT false,
quantity INTEGER NOT NULL,
user_id INTEGER REFERENCES users(id) NOT NULL
);

CREATE TABLE medication_on_order (
id SERIAL PRIMARY KEY,
name VARCHAR(100) NOT NULL,
date_order_placed DATE NOT NULL,
quantity INTEGER NOT NULL,
user_id INTEGER REFERENCES users(id) NOT NULL
);

CREATE TABLE order_received (
id SERIAL PRIMARY KEY,
name VARCHAR(100) NOT NULL,
date_received DATE NOT NULL,
quantity INTEGER NOT NULL,
received_by VARCHAR(30) NOT NULL
);

CREATE TABLE user (
id SERIAL PRIMARY KEY,
username VARCHAR(20) UNIQUE NOT NULL,
password VARCHAR NOT NULL,
email VARCHAR(50) UNIQUE NOT NULL,
first_name VARCHAR(30) NOT NULL,
last_name VARCHAR(30) NOT NULL,
is_manager BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE time_off_request (
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id) NOT NULL,
shift_time VARCHAR(120) NOT NULL,
shift_coverage_date DATE NOT NULL,
covering_user_id INTEGER REFERENCES users(id),
timestamp TIMESTAMP NOT NULL DEFAULT now(),
reason VARCHAR NOT NULL,
request_acknowledged BOOLEAN NOT NULL DEFAULT false,
manager_approval BOOLEAN
);

CREATE TABLE client (
id SERIAL PRIMARY KEY,
name VARCHAR(128) NOT NULL,
is_blacklisted BOOLEAN NOT NULL DEFAULT false,
reason VARCHAR(256),
blacklisting_person VARCHAR(128)
);


CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users (id),
    post_id INTEGER NOT NULL REFERENCES posts (id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
);
