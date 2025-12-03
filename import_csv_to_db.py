
import sqlite3
import pandas as pd
import os
import glob

DB_FILE = 'jobs.db'

def import_csv():
    # Find the latest CSV file
    list_of_files = glob.glob('remote_eu_jobs_*.csv') 
    if not list_of_files:
        print("No CSV files found.")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Importing {latest_file} into database...")

    try:
        df = pd.read_csv(latest_file)
        
        conn = sqlite3.connect(DB_FILE)
        
        # Ensure table exists (schema from app.py)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                job_url TEXT UNIQUE,
                date_posted TEXT,
                location TEXT,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert data
        for _, row in df.iterrows():
            conn.execute('''
                INSERT OR REPLACE INTO jobs (title, company, job_url, date_posted, location, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Job Title', ''),
                row.get('Company', ''),
                row.get('Job URL', ''),
                row.get('Date Posted', ''),
                row.get('Location', ''),
                row.get('Source', '')
            ))
        
        conn.commit()
        conn.close()
        print(f"Successfully imported {len(df)} jobs.")
        
    except Exception as e:
        print(f"Error importing CSV: {e}")

if __name__ == "__main__":
    import_csv()
