"""
Remote Job Board Scrapers
Fetches jobs from remote-only job boards via RSS feeds and APIs
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
from functools import wraps

# Rate limiting decorator
def rate_limit(seconds=5):
    """Rate limit function calls to avoid being blocked"""
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < seconds:
                time.sleep(seconds - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

def safe_scrape(func):
    """Wrapper to catch and log errors without crashing"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    return wrapper

@safe_scrape
@rate_limit(5)
def fetch_remotive_jobs():
    """
    Fetch jobs from Remotive via RSS feed
    https://remotive.com/api/remote-jobs
    """
    print("Fetching from Remotive...")
    jobs = []
    
    # Try RSS feed first (real-time)
    try:
        feed = feedparser.parse('https://remotive.com/remote-jobs?feed=rss')
        
        for entry in feed.entries[:20]:  # Limit to 20 most recent
            jobs.append({
                'Job Title': entry.get('title', ''),
                'Company': entry.get('author', 'Remotive'),
                'Job URL': entry.get('link', ''),
                'Date Posted': entry.get('published', ''),
                'Location': 'Remote',
                'Source': 'Remotive'
            })
    except Exception as e:
        print(f"Remotive RSS failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_weworkremotely_jobs():
    """
    Fetch jobs from We Work Remotely via RSS feed
    """
    print("Fetching from We Work Remotely...")
    jobs = []
    
    # We Work Remotely has category-based RSS feeds
    categories = [
        'https://weworkremotely.com/categories/remote-programming-jobs.rss',
        'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss',
        'https://weworkremotely.com/categories/remote-product-jobs.rss',
    ]
    
    for cat_url in categories:
        try:
            feed = feedparser.parse(cat_url)
            for entry in feed.entries[:10]:  # 10 per category
                jobs.append({
                    'Job Title': entry.get('title', ''),
                    'Company': entry.get('author', 'WWR'),
                    'Job URL': entry.get('link', ''),
                    'Date Posted': entry.get('published', ''),
                    'Location': 'Remote',
                    'Source': 'We Work Remotely'
                })
        except Exception as e:
            print(f"WWR category {cat_url} failed: {e}")
            continue
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_remoteok_jobs():
    """
    Fetch jobs from Remote OK via HTML scraping
    """
    print("Fetching from Remote OK...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://remoteok.com/remote-dev-jobs', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_listings = soup.find_all('tr', class_='job')[:20]  # Limit to 20
            
            for job in job_listings:
                try:
                    title_elem = job.find('h2', itemprop='title')
                    company_elem = job.find('h3', itemprop='name')
                    link_elem = job.find('a', class_='preventLink')
                    
                    if title_elem and link_elem:
                        jobs.append({
                            'Job Title': title_elem.text.strip(),
                            'Company': company_elem.text.strip() if company_elem else 'Remote OK',
                            'Job URL': 'https://remoteok.com' + link_elem['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Remote',
                            'Source': 'Remote OK'
                        })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Remote OK scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_himalayas_jobs():
    """
    Fetch jobs from Himalayas (remote job board)
    """
    print("Fetching from Himalayas...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://himalayas.app/jobs/remote', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # This is a simplified scraper - actual structure may vary
            job_cards = soup.find_all('div', class_='job-card')[:20]
            
            for card in job_cards:
                try:
                    title = card.find('h3')
                    company = card.find('div', class_='company-name')
                    link = card.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Himalayas',
                            'Job URL': 'https://himalayas.app' + link['href'] if not link['href'].startswith('http') else link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Remote',
                            'Source': 'Himalayas'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Himalayas scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_jobicy_jobs():
    """
    Fetch jobs from Jobicy via API
    https://jobicy.com/api
    """
    print("Fetching from Jobicy...")
    jobs = []
    
    try:
        response = requests.get('https://jobicy.com/api/v2/remote-jobs?count=20', timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data.get('jobs', []):
                jobs.append({
                    'Job Title': job.get('jobTitle', ''),
                    'Company': job.get('companyName', 'Jobicy'),
                    'Job URL': job.get('url', ''),
                    'Date Posted': job.get('pubDate', ''),
                    'Location': 'Remote',
                    'Source': 'Jobicy'
                })
    except Exception as e:
        print(f"Jobicy API failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_euremote_jobs():
    """
    Fetch jobs from EU Remote Jobs via RSS
    """
    print("Fetching from EU Remote Jobs...")
    jobs = []
    
    try:
        feed = feedparser.parse('https://euremotejobs.com/jobs.xml')
        for entry in feed.entries[:20]:
            jobs.append({
                'Job Title': entry.get('title', ''),
                'Company': entry.get('author', 'EU Remote'),
                'Job URL': entry.get('link', ''),
                'Date Posted': entry.get('published', ''),
                'Location': 'Remote (EU)',
                'Source': 'EU Remote Jobs'
            })
    except Exception as e:
        print(f"EU Remote Jobs RSS failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_workingnomads_jobs():
    """
    Fetch jobs from Working Nomads via RSS
    """
    print("Fetching from Working Nomads...") 
    jobs = []
    
    try:
        feed = feedparser.parse('https://www.workingnomads.com/jobs/feed')
        for entry in feed.entries[:15]:
            jobs.append({
                'Job Title': entry.get('title', ''),
                'Company': 'Working Nomads',
                'Job URL': entry.get('link', ''),
                'Date Posted': entry.get('published', ''),
                'Location': 'Remote',
                'Source': 'Working Nomads'
            })
    except Exception as e:
        print(f"Working Nomads RSS failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_remoterocketship_jobs():
    """
    Fetch jobs from Remote Rocketship via RSS
    """
    print("Fetching from Remote Rocketship...")
    jobs = []
    
    try:
        feed = feedparser.parse('https://remoterocketship.com/jobs/feed')
        for entry in feed.entries[:15]:
            jobs.append({
                'Job Title': entry.get('title', ''),
                'Company': entry.get('author', 'Remote Rocketship'),
                'Job URL': entry.get('link', ''),
                'Date Posted': entry.get('published', ''),
                'Location': 'Remote',
                'Source': 'Remote Rocketship'
            })
    except Exception as e:
        print(f"Remote Rocketship RSS failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_justremote_jobs():
    """
    Fetch jobs from JustRemote via HTML
    """
    print("Fetching from JustRemote...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://justremote.co/remote-developer-jobs', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='job-listing')[:15]
            
            for card in job_cards:
                try:
                    title = card.find('h3')
                    company = card.find('span', class_='company')
                    link = card.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'JustRemote',
                            'Job URL': 'https://justremote.co' + link['href'] if not link['href'].startswith('http') else link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Remote',
                            'Source': 'JustRemote'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"JustRemote scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_wellfound_jobs():
    """
    Fetch jobs from Wellfound (AngelList) - simplified scraper
    """
    print("Fetching from Wellfound...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Wellfound has complex JS rendering, this might not work perfectly
        response = requests.get('https://wellfound.com/remote', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Simplified - actual structure needs inspection
            job_divs = soup.find_all('div', class_='job')[:10]
            
            for div in job_divs:
                try:
                    title = div.find('h2')
                    if title:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': 'Wellfound',
                            'Job URL': 'https://wellfound.com/remote',
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Remote',
                            'Source': 'Wellfound'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Wellfound scraping failed: {e}")
    
    return pd.DataFrame(jobs)

def fetch_all_remote_boards():
    """
    Fetch jobs from all remote-only job boards
    Returns combined DataFrame
    """
    all_jobs = []
    
    # Tier 1: RSS/API (most reliable)
    all_jobs.append(fetch_remotive_jobs())
    all_jobs.append(fetch_weworkremotely_jobs())
    all_jobs.append(fetch_jobicy_jobs())
    all_jobs.append(fetch_euremote_jobs())
    all_jobs.append(fetch_workingnomads_jobs())
    all_jobs.append(fetch_remoterocketship_jobs())
    
    # Tier 2: HTML scraping (less reliable but valuable)
    all_jobs.append(fetch_remoteok_jobs())
    all_jobs.append(fetch_himalayas_jobs())
    all_jobs.append(fetch_justremote_jobs())
    all_jobs.append(fetch_wellfound_jobs())
    
    # Combine all
    if all_jobs:
        combined = pd.concat([df for df in all_jobs if not df.empty], ignore_index=True)
        return combined
    
    return pd.DataFrame()

