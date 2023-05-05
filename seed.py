from models import db, connect_db, Medication, Order
from app import app

db.drop_all()
db.create_all()

# Add seed data for Medication and Order models
