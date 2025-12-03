"""
Swedish Job Board Scrapers
Fetches jobs from Swedish job boards - mix of API and HTML scraping
"""

import feedparser
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
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
            return pd.DataFrame()
    return wrapper

@safe_scrape
@rate_limit(5)
def fetch_arbetsformedlingen_jobs():
    """
    Fetch jobs from Arbetsförmedlingen/Platsbanken via JobSearch API
    https://jobtechdev.se/docs/apis/jobsearch/
    """
    print("Fetching from Arbetsförmedlingen/Platsbanken...")
    jobs = []
    
    try:
        # Arbetsförmedlingen JobSearch API - public, no auth required!
        base_url = 'https://jobsearch.api.jobtechdev.se'
        endpoint = '/search'
        
        params = {
            'q': 'junior OR trainee OR graduate OR entry-level',
            'limit': 20,
            'offset': 0
        }
        
        response = requests.get(base_url + endpoint, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            
            for hit in hits:
                try:
                    jobs.append({
                        'Job Title': hit.get('headline', ''),
                        'Company': hit.get('employer', {}).get('name', 'AF'),
                        'Job URL': hit.get('webpage_url', ''),
                        'Date Posted': hit.get('publication_date', ''),
                        'Location': hit.get('workplace_address', {}).get('municipality', 'Sverige'),
                        'Source': 'Arbetsförmedlingen'
                    })
                except Exception:
                    continue
            
            print(f"Arbetsförmedlingen: Found {len(jobs)} jobs")
        else:
            print(f"Arbetsförmedlingen: API returned status {response.status_code}")
            
    except Exception as e:
        print(f"Arbetsförmedlingen API failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_jobbsafari_jobs():
    """
    Fetch jobs from Jobbsafari via HTML scraping
    """
    print("Fetching from Jobbsafari...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://jobbsafari.se/lediga-jobb', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Correct selector: a.MuiButtonBase-root.MuiCardActionArea-root
            job_links = soup.find_all('a', class_='MuiButtonBase-root')[:15]
            
            for link in job_links:
                try:
                    title_elem = link.find('h3')
                    # First p tag is company
                    paragraphs = link.find_all('p')
                    company_elem = paragraphs[0] if paragraphs else None
                    
                    if title_elem and link.get('href'):
                        jobs.append({
                            'Job Title': title_elem.text.strip(),
                            'Company': company_elem.text.strip() if company_elem else 'Jobbsafari',
                            'Job URL': 'https://jobbsafari.se' + link['href'] if link['href'].startswith('/') else link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Jobbsafari'
                        })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Jobbsafari scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_ledigajobb_jobs():
    """
    Fetch jobs from Ledigajobb.se via HTML scraping
    """
    print("Fetching from Ledigajobb.se...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Search for junior jobs
        response = requests.get('https://www.ledigajobb.se/sok?s=junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Correct selector: a.job-link
            job_links = soup.find_all('a', class_='job-link')[:15]
            
            for link in job_links:
                try:
                    title = link.text.strip()
                    # Company name is often in a sibling text node or adjacent element
                    # For now, extract from link href or use default
                    company = 'Ledigajobb.se'  # Placeholder - may need more inspection
                    
                    if title and link.get('href'):
                        jobs.append({
                            'Job Title': title,
                            'Company': company,
                            'Job URL': link['href'] if link['href'].startswith('http') else 'https://www.ledigajobb.se' + link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Ledigajobb.se'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Ledigajobb.se scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_blocket_jobb():
    """
    Fetch jobs from Blocket Jobb via HTML scraping
    """
    print("Fetching from Blocket Jobb...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://jobb.blocket.se/lediga-jobb-junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_items = soup.find_all('article')[:15]
            
            for item in job_items:
                try:
                    title = item.find('h2')
                    company = item.find('span', class_='company')
                    link = item.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Blocket',
                            'Job URL': link['href'] if link['href'].startswith('http') else 'https://jobb.blocket.se' + link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Blocket Jobb'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Blocket Jobb scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_karriarguiden_network():
    """
    Fetch jobs from Karriärguiden network sites (Teknikjobb, Itjobb, Ekonomijobb, etc.)
    """
    print("Fetching from Karriärguiden network...")
    jobs = []
    
    # Karriärguiden has multiple specialized sites
    sites = [
        ('https://www.teknikjobb.se/lediga-jobb/junior', 'Teknikjobb.se'),
        ('https://www.itjobb.se/lediga-jobb/junior', 'ITjobb.se'),
        ('https://www.ekonomijobb.se/lediga-jobb/junior', 'Ekonomijobb.se'),
    ]
    
    for url, source in sites:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                job_listings = soup.find_all('div', class_='job-listing')[:10]
                
                for listing in job_listings:
                    try:
                        title = listing.find('h2')
                        company = listing.find('span', class_='company')
                        link = listing.find('a')
                        
                        if title and link:
                            jobs.append({
                                'Job Title': title.text.strip(),
                                'Company': company.text.strip() if company else source,
                                'Job URL': link['href'] if link['href'].startswith('http') else 'https://www.' + source.lower() + link['href'],
                                'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                                'Location': 'Sverige',
                                'Source': source
                            })
                    except Exception:
                        continue
            time.sleep(2)  # Extra delay between sites
        except Exception as e:
            print(f"{source} scraping failed: {e}")
            continue
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_careerjet_sweden():
    """
    Fetch jobs from Careerjet.se
    """
    print("Fetching from Careerjet.se...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.careerjet.se/sokning/jobb?s=junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_items = soup.find_all('article', class_='job')[:15]
            
            for item in job_items:
                try:
                    title = item.find('h2')
                    company = item.find('p', class_='company')
                    link = item.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Careerjet',
                            'Job URL': link['href'] if link['href'].startswith('http') else 'https://www.careerjet.se' + link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Careerjet.se'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Careerjet.se scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_akademikernas_jobs():
    """
    Fetch jobs from Akademikernas (SACO member jobs)
    """
    print("Fetching from Akademikernas...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.saco.se/om-saco/jobba-hos-oss/', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_divs = soup.find_all('div', class_='job-post')[:10]
            
            for div in job_divs:
                try:
                    title = div.find('h3')
                    link = div.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': 'Akademikernas/SACO',
                            'Job URL': link['href'] if link['href'].startswith('http') else 'https://www.saco.se' + link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Akademikernas'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Akademikernas scraping failed: {e}")
    
    return pd.DataFrame(jobs)

def fetch_all_swedish_boards():
    """
    Fetch jobs from all Swedish job boards
    Returns combined DataFrame
    """
    all_jobs = []
    
    # API sources (most reliable)
    all_jobs.append(fetch_arbetsformedlingen_jobs())
    
    # HTML scraping sources  
    all_jobs.append(fetch_jobbsafari_jobs())
    all_jobs.append(fetch_ledigajobb_jobs())
    
    # Combine all - handle case where all are empty
    non_empty_jobs = [df for df in all_jobs if not df.empty]
    
    if non_empty_jobs:
        combined = pd.concat(non_empty_jobs, ignore_index=True)
        return combined
    
    return pd.DataFrame()
