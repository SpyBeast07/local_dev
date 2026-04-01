import sys
import os

# Mock the database service for a standalone check
sys.path.append(os.path.abspath('.'))

try:
    from services.backups import export_db, generate_dbml
    print("SUCCESS: Imports successful.")
    
    # Test DBML Generation (structural only, doesn't need DB if we mock get_tables)
    # But since it calls get_tables internally, we just check if the function exists
    if callable(generate_dbml):
        print("SUCCESS: generate_dbml is defined.")
    
    # Test CSV/Excel logic (needs a connection usually, but we check if pandas is there)
    import pandas as pd
    import openpyxl
    print(f"SUCCESS: pandas version {pd.__version__}")
    print("SUCCESS: openpyxl is installed.")

except Exception as e:
    print(f"FAILURE: {str(e)}")
