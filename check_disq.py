from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["hireai_pro"]
col = db["Disqualified_Candidate"]

print("Disqualified Records:")
for doc in col.find():
    print(f"Candidate: {doc.get('full_name')}, Round: {doc.get('round')}, HR: {doc.get('hr_username')}")
