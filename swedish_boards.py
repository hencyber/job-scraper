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
    Fetch jobs from Arbetsf\u00f6rmedlingen/Platsbanken via API
    https://arbetsformedlingen.se/om-oss/oppna-data-och-api
    """
    print("Fetching from Arbetsförmedlingen/Platsbanken...")
    jobs = []
    
    try:
        # Arbetsförmedlingen JobSearch API
        # This is a simplified version - actual API requires more complex authentication
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json'
        }
        
        # Public job search endpoint (simplified)
        url = 'https://arbetsformedlingen.se/platsannonser/matchning'
        params = {
            'nyckelord': 'junior OR trainee OR graduate',
            'antalrader': 20
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # NOTE: Actual API structure may differ - this is a placeholder
            # Real implementation needs proper API documentation
            print(f"Arbetsförmedlingen: API response received (status {response.status_code})")
    except Exception as e:
        print(f"Arbetsförmedlingen scraping failed: {e}")
    
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
        response = requests.get('https://www.jobbsafari.se/jobb/junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='job-item')[:15]
            
            for card in job_cards:
                try:
                    title = card.find('h2')
                    company = card.find('span', class_='company')
                    link = card.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Jobbsafari',
                            'Job URL': 'https://www.jobbsafari.se' + link['href'] if not link['href'].startswith('http') else link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Jobbsafari'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Jobbsafari scraping failed: {e}")
    
    return pd.DataFrame(jobs)

@safe_scrape
@rate_limit(5)
def fetch_monsterse_jobs():
    """
    Fetch jobs from Monster.se via HTML scraping
    """
    print("Fetching from Monster.se...")
    jobs = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get('https://www.monster.se/jobb/q-junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_listings = soup.find_all('div', class_='job-listing')[:15]
            
            for listing in job_listings:
                try:
                    title = listing.find('h2')
                    company = listing.find('div', class_='company')
                    link = listing.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Monster.se',
                            'Job URL': link['href'] if link['href'].startswith('http') else 'https://www.monster.se' + link['href'],
                            'Date Posted': datetime.now().strftime('%Y-%m-%d'),
                            'Location': 'Sverige',
                            'Source': 'Monster.se'
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Monster.se scraping failed: {e}")
    
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
        response = requests.get('https://www.ledigajobb.se/junior', headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_divs = soup.find_all('div', class_='job')[:15]
            
            for div in job_divs:
                try:
                    title = div.find('h3')
                    company = div.find('span', class_='company-name')
                    link = div.find('a')
                    
                    if title and link:
                        jobs.append({
                            'Job Title': title.text.strip(),
                            'Company': company.text.strip() if company else 'Ledigajobb.se',
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
    all_jobs.append(fetch_monsterse_jobs())
    all_jobs.append(fetch_ledigajobb_jobs())
    all_jobs.append(fetch_blocket_jobb())
    all_jobs.append(fetch_karriarguiden_network())
    all_jobs.append(fetch_careerjet_sweden())
    all_jobs.append(fetch_akademikernas_jobs())
    
    # Combine all
    if all_jobs:
        combined = pd.concat([df for df in all_jobs if not df.empty], ignore_index=True)
        return combined
    
    return pd.DataFrame()
