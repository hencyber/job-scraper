
import sys
import os
sys.path.append('.')

from job_scraper import is_relevant_job

test_jobs = [
    {"title": "Junior Data Scientist", "expected": True},
    {"title": "Software Testing Engineer", "expected": True},
    {"title": "Test Automation Engineer", "expected": True},
    {"title": "Back-End Engineer", "expected": True},
    {"title": "Data Software Engineer", "expected": True},
    {"title": "DevOps Engineer", "expected": True},
    {"title": "MLOps Engineer", "expected": True},
    # Negative tests
    {"title": "Frontend Developer", "expected": False},
    {"title": "Full Stack Developer", "expected": False},
    {"title": "Project Manager", "expected": False},
    {"title": "Data Analyst", "expected": False}, 
    {"title": "General Software Engineer", "expected": False},
    {"title": "Sales Development Rep", "expected": False},
    {"title": "Senior DevOps Engineer", "expected": False}, # Should be excluded by 'senior'
    {"title": "Product Manager", "expected": False},
    {"title": "HR Manager", "expected": False},
]

print("--- Testing Job Filtering Logic ---")
passed = 0
for job in test_jobs:
    result = is_relevant_job(job)
    status = "✅" if result == job["expected"] else "❌"
    if result == job["expected"]:
        passed += 1
    print(f"{status} Title: '{job['title']}' -> Result: {result} (Expected: {job['expected']})")

print(f"\nPassed {passed}/{len(test_jobs)} tests.")
