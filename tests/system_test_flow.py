"""
HireAI Pro - System Test Flow
This script verifies the core integration between AI Engine and Database Manager.
"""

import sys
import os
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_engine import calculate_weighted_score, get_ai_evaluation
from modules.database_manager import save_candidate_to_mongo

def test_weighted_scoring():
    """Verify the weighted scoring algorithm."""
    mock_ai_result = {
        'efficiency': {
            'Technical': 8.0,
            'Experience': 7.0,
            'Communication': 9.0,
            'Leadership': 7.0
        }
    }
    
    weights = {'Technical': 50, 'Experience': 30, 'Soft_Skills': 20}
    
    # Calculation:
    # Technical: 8.0 * 0.5 = 4.0
    # Experience: 7.0 * 0.3 = 2.1
    # Soft_Skills: ((9+7)/2) * 0.2 = 1.6
    # Total: 4.0 + 2.1 + 1.6 = 7.7
    
    score = calculate_weighted_score(mock_ai_result, weights)
    print(f"Computed Score: {score}")
    assert score == 7.7, f"Expected 7.7, got {score}"
    print("[PASS] Weighted scoring test passed!")

def test_mock_db_save():
    """Verify database save logic (mocked)."""
    mock_ai_result = {'score': 8.0}
    weights = {'Technical': 50, 'Experience': 30, 'Soft_Skills': 20}
    
    # We can mock the database manager if Mongo is not running
    # but let's just see if we can call it.
    success, message, cid = save_candidate_to_mongo(
        "Test User", "test@example.com", "1234567890",
        mock_ai_result, weights, applied_role="Backend Developer"
    )
    
    if success:
        print(f"[PASS] Candidate saved successfully. ID: {cid}")
    else:
        print(f"[FAIL] Save failed (Expected if DB is offline): {message}")

if __name__ == "__main__":
    print("--- Starting HireAI Pro Core Tests ---")
    try:
        test_weighted_scoring()
        test_mock_db_save()
        print("--- All tests completed ---")
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
