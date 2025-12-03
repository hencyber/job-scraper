import csv
import datetime
import random
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from dotenv import load_dotenv
from jobspy import scrape_jobs
from remote_boards import fetch_all_remote_boards

# Load environment variables
load_dotenv()

# --- Configuration ---
SEARCH_TERMS = [
    "Junior Data Scientist",
    "Entry Level Data Scientist",
    "Junior Software Testing Engineer",
    "Entry Level Test Automation Engineer",
    "Junior Back-End Engineer",
    "Entry Level DevOps",
    "Junior DevOps",
    "Entry Level MLOps",
    "Graduate Data Scientist",
    "Graduate Software Engineer"
]

# Note: "Remote" is often handled by the location field in jobspy or specific site parameters.
# We will search for "Remote" as the location.
LOCATION = "Remote" 
RESULTS_WANTED = 20  # Adjust as needed, keep low for testing
HOURS_OLD = 720 # 30 days * 24 hours

# EU Filtering Keywords (Heuristic)
EU_LOCATIONS = [
    "Europe", "EMEA", "EU", "Germany", "Sweden", "France", "UK", "United Kingdom",
    "Netherlands", "Spain", "Italy", "Poland", "Switzerland", "Austria", "Belgium",
    "Denmark", "Finland", "Norway", "Ireland", "Portugal", "Czech Republic", "Romania"
]

EU_KEYWORDS = [
    "EU based", "European time zone", "CET", "GMT", "CEST", "BST"
]

US_LOCATIONS_TO_EXCLUDE = [
    "USA", "United States", "North America", "APAC", "US Only", "Canada", "Mexico"
]

US_KEYWORDS_TO_EXCLUDE = [
    "US authorization required", "Must reside in US", "US Citizens only", "Green Card",
    "Canada only", "Must reside in Canada", "North America only", "Must reside in North America"
]

# Entry-level indicators (positive)
ENTRY_LEVEL_POSITIVE = [
    "junior", "entry level", "entry-level", "graduate", "internship", "intern",
    "0-1 years", "0-2 years", "no experience", "recent graduate", "new grad",
    "trainee", "associate"
]

# Senior/experienced indicators (negative - to exclude)
EXPERIENCE_KEYWORDS_TO_EXCLUDE = [
    "senior", "lead", "principal", "staff", "architect", "director", "manager",
    "5+ years", "5-7 years", "7+ years", "10+ years", "expert", "experienced"
]

def is_eu_friendly(job):
    """
    Analyzes job location and description to determine if it's remote-friendly for EU citizens.
    Now permissive: includes all remote jobs UNLESS they explicitly exclude non-US workers.
    """
    location = str(job.get('location', '')).lower()
    description = str(job.get('description', '')).lower()
    
    # 1. Check for explicit exclusions (US-only jobs)
    for loc in US_LOCATIONS_TO_EXCLUDE:
        if loc.lower() in location:
            return False
    
    for kw in US_KEYWORDS_TO_EXCLUDE:
        if kw.lower() in description:
            return False
    
    # 2. If no exclusions found, include the job
    # This allows global remote jobs that don't restrict location
    return True

def is_entry_level(job):
    """
    Checks if a job is entry-level or suitable for candidates without experience.
    """
    title = str(job.get('title', '')).lower()
    description = str(job.get('description', '')).lower()
    
    # 1. Exclude senior/experienced positions
    for kw in EXPERIENCE_KEYWORDS_TO_EXCLUDE:
        if kw.lower() in title or kw.lower() in description:
            return False
    
    # 2. Look for positive entry-level indicators
    for kw in ENTRY_LEVEL_POSITIVE:
        if kw.lower() in title or kw.lower() in description:
            return True
    
    # 3. If no clear indicators, we'll be permissive and include it
    # (since we're already searching for entry-level terms)
    return True

def scrape_and_filter_jobs():
    """
    Main function to scrape job listings and filter them.
    Returns a pandas DataFrame with filtered jobs.
    """
    print(f"Starting job scrape for {len(SEARCH_TERMS)} roles...")
    all_jobs = []

    for term in SEARCH_TERMS:
        print(f"Scraping for: {term}")
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"],
                search_term=term,
                location=LOCATION,
                results_wanted=RESULTS_WANTED,
                hours_old=HOURS_OLD,
                country_indeed='Germany',  # Focus on an EU country for Indeed
                linkedin_fetch_description=True # Needed for filtering
            )
            
            print(f"Found {len(jobs)} jobs for {term}")
            
            # Add source term for reference
            jobs['search_term'] = term
            all_jobs.append(jobs)
            
            # Sleep to be polite
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error scraping {term}: {e}")

    # --- 2. Sweden On-site/Hybrid Jobs ---
    print(f"Starting Sweden job scrape...")
    SWEDEN_TERMS = SEARCH_TERMS + ["Internship", "Trainee", "Summer Job"]
    
    for term in SWEDEN_TERMS:
        print(f"Scraping Sweden for: {term}")
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"],
                search_term=term,
                location="Sweden",  # Specific location
                results_wanted=RESULTS_WANTED,
                hours_old=HOURS_OLD,
                country_indeed='Sweden',
                linkedin_fetch_description=True
            )
            
            print(f"Found {len(jobs)} jobs in Sweden for {term}")
            jobs['search_term'] = term
            jobs['is_sweden_local'] = True # Flag to identify these jobs
            all_jobs.append(jobs)
            time.sleep(random.uniform(2, 5))
            
        except Exception as e:
            print(f"Error scraping Sweden {term}: {e}")

    if not all_jobs:
        print("No jobs found.")
        return pd.DataFrame()

    # --- 3. Remote-Only Job Boards ---
    print("Starting remote-only job boards scraping...")
    try:
        remote_jobs = fetch_all_remote_boards()
        if not remote_jobs.empty:
            # Rename columns to match our standard format
            remote_jobs_renamed = remote_jobs.rename(columns={
                'Job Title': 'title',
                'Company': 'company',
                'Job URL': 'job_url',
                'Date Posted': 'date_posted',
                'Location': 'location',
                'Source': 'site'
            })
            remote_jobs_renamed['search_term'] = 'Remote Board'
            remote_jobs_renamed['is_remote_board'] = True
            all_jobs.append(remote_jobs_renamed)
            print(f"Found {len(remote_jobs)} jobs from remote-only boards")
    except Exception as e:
        print(f"Error fetching remote boards: {e}")

    # Combine all dataframes
    full_df = pd.concat(all_jobs, ignore_index=True)
    
    # Deduplicate based on ID or URL
    full_df.drop_duplicates(subset=['job_url'], inplace=True)
    
    print(f"Total unique jobs found before filtering: {len(full_df)}")

    # --- Filtering ---
    filtered_jobs = []
    
    for index, row in full_df.iterrows():
        # Check flags
        is_sweden = row.get('is_sweden_local', False)
        is_remote_board = row.get('is_remote_board', False)
        
        # Apply filters
        # 1. Entry Level check (applies to all)
        if not is_entry_level(row):
            continue
            
        # 2. Location check
        # Skip location checks for:
        # - Sweden local jobs (already local)
        # - Remote-only board jobs (already verified remote)
        if not is_sweden and not is_remote_board and not is_eu_friendly(row):
            continue
            
        filtered_jobs.append(row)

    if not filtered_jobs:
        print("No jobs remained after EU and entry-level filtering.")
        final_df = pd.DataFrame(columns=["title", "company", "job_url", "date_posted", "location", "site", "search_term"])
    else:
        final_df = pd.DataFrame(filtered_jobs)
        print(f"Jobs after EU and entry-level filtering: {len(final_df)}")

    # Select and Rename Columns
    cols_to_keep = ['title', 'company', 'job_url', 'date_posted', 'location', 'site']
    
    # Ensure columns exist
    existing_cols = [c for c in cols_to_keep if c in final_df.columns]
    final_df = final_df[existing_cols]
    
    final_df.rename(columns={
        'title': 'Job Title',
        'company': 'Company',
        'job_url': 'Job URL',
        'date_posted': 'Date Posted',
        'location': 'Location',
        'site': 'Source'
    }, inplace=True)

    return final_df

def main():
    """Main entry point when running the scraper directly."""
    final_df = scrape_and_filter_jobs()
    
    # Save to CSV
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"remote_eu_jobs_{timestamp}.csv"
    final_df.to_csv(filename, index=False)
    print(f"Saved results to {filename}")

    # --- Email Notification ---
    if not final_df.empty:
        send_email(final_df)

def send_email(df):
    """
    Sends an email with the new jobs found.
    """
    sender_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not sender_email or not password or not receiver_email:
        print("Email credentials not found in .env file. Skipping email.")
        print("Please create a .env file with EMAIL_ADDRESS, EMAIL_PASSWORD, and RECEIVER_EMAIL.")
        return

    subject = f"New Remote EU Jobs Found - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    dashboard_url = os.getenv("DASHBOARD_URL", "https://job-scraper-mg37.onrender.com/")
    
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <div style="background-color: #f3f4f6; padding: 20px; text-align: center;">
            <h2 style="color: #2563eb;">Found {len(df)} new jobs matching your criteria</h2>
            <p>The full list of jobs is available on your dashboard.</p>
            <br>
            <a href="{dashboard_url}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">Go to Dashboard</a>
            <br><br>
            <p style="color: #666; font-size: 12px;">{dashboard_url}</p>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    try:
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        server.login(sender_email, password)
        # Use as_bytes() to properly handle UTF-8 encoding
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    main()
