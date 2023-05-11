import random
import string
import psycopg2
from psycopg2.extras import RealDictCursor

# Connect to the database
conn = psycopg2.connect(
    host="localhost",
    database="mydatabase",
    user="myuser",
    password="mypassword"
)

# Open a cursor to perform database operations
cur = conn.cursor(cursor_factory=RealDictCursor)

# List of medications
medications = [
    'Aspirin', 'Ibuprofen', 'Acetaminophen', 'Lisinopril', 'Atorvastatin',
    'Metformin', 'Levothyroxine', 'Omeprazole', 'Metoprolol', 'Amlodipine',
    'Simvastatin', 'Losartan', 'Gabapentin', 'Hydrochlorothiazide', 'Azithromycin',
    'Escitalopram', 'Prednisone', 'Amoxicillin', 'Sertraline', 'Citalopram',
    'Montelukast', 'Fluticasone', 'Trazodone', 'Venlafaxine', 'Ciprofloxacin',
    'Cephalexin', 'Duloxetine', 'Albuterol', 'Clonazepam', 'Clopidogrel'
]

# Generate random usernames
usernames = []
for i in range(100):
    username = ''.join(random.choices(string.ascii_letters, k=10))
    usernames.append(username)

# Insert users
for i in range(100):
    username = usernames[i]
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    email = f'{username}@example.com'
    first_name = ''.join(random.choices(string.ascii_letters, k=10))
    last_name = ''.join(random.choices(string.ascii_letters, k=10))
    is_manager = random.choice([True, False])
    cur.execute(
        "INSERT INTO users (username, password, email, first_name, last_name, is_manager) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (username, password, email, first_name, last_name, is_manager)
    )

# Insert medications to be ordered
for i in range(1000):
    name = random.choice(medications)
    date_requested = f'2022-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}'
    backordered = random.choice([True, False])
    quantity = random.randint(1, 1000)
    user_id = random.randint(1, 100)
    cur.execute(
        "INSERT INTO medication_to_be_ordered (name, date_requested, backordered, quantity, user_id) "
        "VALUES (%s, %s, %s, %s, %s)",
        (name, date_requested, backordered, quantity, user_id)
    )

# Insert medications on order
for i in range(1000):
    name = random.choice(medications)
    date_order_placed = f'2022-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}'
    quantity = random.randint(1, 1000)
    user_id = random.randint(1, 100)
    cur.execute(
        "INSERT INTO medication_on_order (name, date_order_placed, quantity, user_id) "
        "VALUES (%s, %s, %s, %s)",
        (name, date_order_placed, quantity, user_id)
   
