# Job Scraper Deployment Guide

## Prerequisites
- GitHub account (free)
- Render.com account (free)

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and log in
2. Click the **"+" icon** → "New repository"
3. Name it: `job-scraper` (or anything you like)
4. Choose **Public** (required for free Render)
5. **DO NOT** initialize with README
6. Click "Create repository"

## Step 2: Push Code to GitHub

Run these commands in your project directory:

```bash
cd /path/to/job-scraper

# Initialize git (if not already done)
git init

# Add all files
git add .

# Make first commit
git commit -m "Initial commit - Job scraper with dashboard"

# Link to your GitHub repo (replace USERNAME with your GitHub username)
git remote add origin https://github.com/USERNAME/job-scraper.git

# Push to GitHub
git push -u origin main
```

> **Note**: You may need to run `git branch -M main` if you get an error about branches.

## Step 3: Deploy to Render

1. Go to [Render.com](https://render.com) and sign up (use GitHub to sign in)

2. Click **"New +"** → **"Web Service"**

3. Connect your GitHub repository:
   - Grant Render access to your repositories
   - Select `job-scraper` repository

4. Configure the service:
   - **Name**: `job-scraper-dashboard` (or your choice)
   - **Environment**: `Python3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Select **Free**

5. **Set Environment Variables** (click "Advanced"):
   - `EMAIL_ADDRESS` = `your.email@gmail.com`
   - `EMAIL_PASSWORD` = `[your Gmail App Password]`
   - `RECEIVER_EMAIL` = `your.email@gmail.com`

6. Click **"Create Web Service"**

## Step 4: Wait for Deployment

- First deploy takes ~5-10 minutes
- Watch the logs for "Build successful"
- Your app will be live at: `https://job-scraper-dashboard.onrender.com` (or similar)

## Step 5: Access Your Dashboard

- Click the URL provided by Render
- First load may take 30 seconds (free tier sleeps after inactivity)
- Bookmark the URL for easy access!

## Features

✅ **Automatic Daily Scraping**: Runs at 08:00 Swedish time every day
✅ **Email Notifications**: Sends results to your email
✅ **Persistent Storage**: SQLite database keeps job history
✅ **Mobile Friendly**: Access from any device

## Troubleshooting

### App not loading?
- Check Render logs for errors
- Verify environment variables are set correctly

### Jobs not showing?
- Wait for first scrape (08:00 next day) OR
- Trigger manual scrape by sending POST to `/api/scrape`

### Scraper not running?
- Check Render logs at 08:00
- Verify scheduler is active

## Updating the App

When you make changes locally:

```bash
git add .
git commit -m "Description of changes"
git push
```

Render will automatically redeploy!

## Pro Tip: Keep Your App Awake 24/7 (Free)

Render's free tier sleeps after 15 minutes of inactivity. This means your scheduled scraper (08:00/20:00) might **NOT** run if the app is sleeping.

**Solution:** Use a free uptime monitor to "ping" your site every 10 minutes.

1. Go to [UptimeRobot.com](https://uptimerobot.com/) (Free)
2. Create an account
3. Click **"Add New Monitor"**
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Job Scraper
   - **URL**: `https://your-app-name.onrender.com`
   - **Monitoring Interval**: 10 minutes (important!)
4. Click **"Create Monitor"**

**Why this works:**
- By pinging every 10 minutes, the app never goes to sleep.
- Render allows 750 free hours/month, which covers one app running 24/7 (31 days × 24 hours = 744 hours).
- This ensures your 08:00 and 20:00 schedules always fire on time!

## Cost

**100% FREE** on Render's free tier:
- Unlimited deploys
- Automatic HTTPS
- Free domain (`.onrender.com`)

**Limitations**:
- App sleeps after 15 min inactivity (wakes in ~30s)
- 750 hours/month free (enough for always-on)
