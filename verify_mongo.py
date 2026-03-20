import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database_manager import init_database, fetch_all_candidates

def test_db():
    print("Testing MongoDB Connection...")
    success = init_database()
    if success:
        print("SUCCESS: MongoDB Initialized Successfully!")
        candidates = fetch_all_candidates()
        print(f"Current Candidate Count: {len(candidates)}")
    else:
        print("FAILED: MongoDB Initialization Failed. Ensure MongoDB is running on localhost:27017")

if __name__ == "__main__":
    test_db()
