# DiamondDigger

DiamondDigger is an autonomous Full-Stack AI application that analyzes the Indian stock market daily. It identifies high-potential stocks (under ₹100 or penny stocks) by looking for early traits matching 10 historical compounders. 

The application utilizes the Gemini API for analysis and emails a 3-bullet-point thesis directly to your inbox.

## Hosting Platform
Designed to be hosted on **Render** (Web Service).

## Setup Instructions

### 1. Deployment to Render
1. Push this repository to your GitHub account.
2. Go to [Render](https://render.com/) and create a new **Web Service**.
3. Connect your GitHub repository.
4. Render will automatically detect the `Procfile` and use `gunicorn` to serve the Flask app. 
5. Under the Environment Variables section in Render, set the following keys:

### 2. Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key.
- `SENDER_EMAIL`: The email address you want to send from (e.g., your Gmail).
- `APP_PASSWORD`: The App Password for your sender email account (if using Gmail, go to Google Account Security -> App Passwords and generate one).
- `RECIPIENT_EMAIL`: The email address where you want to receive the daily recommendations.

### 3. Setting Up the Daily Loop (Preventing Sleep)
Render's free tier goes to sleep after 15 minutes of inactivity. To ensure the application runs daily:
1. Sign up for a free account at [cron-job.org](https://cron-job.org/).
2. Create a new "Cronjob".
3. **URL**: Set this to your Render app's trigger endpoint: `https://your-app-name.onrender.com/trigger-daily`
4. **Execution Schedule**: Choose a time (e.g., Every day at 09:00 AM) when you want the AI to analyze the market and send the email.
5. Save the cron job.

cron-job.org will hit this endpoint daily, waking up your Render instance, triggering the Gemini AI analysis, and sending the formatted HTML email.

## Usage
- **Web UI**: Visit your Render URL to see the status dashboard. Here you can also dynamically update the `RECIPIENT_EMAIL` or manually trigger a run.
- **Daily Loop**: Everything else is autonomous! Wait for your email every day based on the cron schedule.
