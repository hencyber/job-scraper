from flask import Flask, render_template, jsonify
import pandas as pd
import sqlite3
import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Import the scraper function
from job_scraper import scrape_and_filter_jobs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database file
DB_FILE = 'jobs.db'

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
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
    conn.commit()
    conn.close()

def save_jobs_to_db(df):
    """Save jobs DataFrame to SQLite database."""
    if df.empty:
        return
    
    conn = sqlite3.connect(DB_FILE)
    
    # Use replace to update existing jobs or insert new ones
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
    print(f"Saved {len(df)} jobs to database")

def get_jobs_from_db():
    """Retrieve all jobs from SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT title, company, job_url, date_posted, location, source FROM jobs ORDER BY scraped_at DESC", conn)
    conn.close()
    
    # Rename columns to match expected format
    df.rename(columns={
        'title': 'Job Title',
        'company': 'Company',
        'job_url': 'Job URL',
        'date_posted': 'Date Posted',
        'location': 'Location',
        'source': 'Source'
    }, inplace=True)
    
    return df

def run_scraper():
    """Run the job scraper and save results to database."""
    from job_scraper import send_email
    
    logger.info(f"⏰ SCHEDULED SCRAPE STARTED at {datetime.now()}")
    try:
        df = scrape_and_filter_jobs()
        save_jobs_to_db(df)
        logger.info(f"✅ Scrape completed. Found {len(df)} jobs.")
        
        # Send email notification
        if not df.empty:
            logger.info("📧 Sending email notification...")
            send_email(df)
            logger.info("📧 Email sent successfully!")
        else:
            logger.info("📭 No jobs to email.")
    except Exception as e:
        logger.error(f"❌ Error during scheduled scrape: {e}")

# Initialize database
init_db()

# Run scraper on startup to ensure we have fresh data
# Run scraper on startup in background thread to avoid blocking server
def initial_scrape():
    logger.info("🚀 Running initial scrape on startup...")
    try:
        df = scrape_and_filter_jobs()
        save_jobs_to_db(df)
        logger.info(f"✅ Initial scrape complete. Found {len(df)} jobs.")
    except Exception as e:
        logger.error(f"❌ Error during initial scrape: {e}")

import threading
# threading.Thread(target=initial_scrape, daemon=True).start()

# Setup scheduler for daily scraping at 08:00 and 20:00 Stockholm time
logger.info("📅 Initializing APScheduler...")
scheduler = BackgroundScheduler()
stockholm_tz = pytz.timezone('Europe/Stockholm')
scheduler.add_job(
    run_scraper,
    trigger=CronTrigger(hour='8,20', minute=0, timezone=stockholm_tz),
    id='daily_scrape',
    name='Daily job scrape at 08:00 and 20:00 Stockholm time',
    replace_existing=True
)
scheduler.start()
logger.info("✅ Scheduler started! Jobs scheduled for 08:00 and 20:00 Stockholm time.")

@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')

@app.route('/api/jobs')
def get_jobs():
    """API endpoint to get job data as JSON."""
    df = get_jobs_from_db()
    
    if df.empty:
        return jsonify([])
    
    # Replace NaN values with empty strings
    df = df.fillna('')
    
    # Convert DataFrame to list of dictionaries
    jobs = df.to_dict('records')
    
    return jsonify(jobs)

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """Manually trigger a job scrape in the background."""
    def run_background_scrape():
        try:
            logger.info("🚀 Manual scrape started in background...")
            df = scrape_and_filter_jobs()
            save_jobs_to_db(df)
            
            # Send email notification
            from job_scraper import send_email
            if not df.empty:
                send_email(df)
                
            logger.info(f"✅ Manual scrape completed. Found {len(df)} jobs.")
        except Exception as e:
            logger.error(f"❌ Error during manual scrape: {e}")

    try:
        # Start scrape in a separate thread
        thread = threading.Thread(target=run_background_scrape)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Scrape started in background! Check back in 2-3 minutes.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Job Dashboard...")
    print("📊 Open your browser and go to: http://localhost:5000")
    print("⏰ Automatic scraping scheduled for 08:00 and 20:00 daily")
    print("Press CTRL+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)
