import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import smtplib
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)

# Configuration File for storing recipient email dynamically
CONFIG_FILE = 'config.json'

def get_recipient_email():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                if data.get('RECIPIENT_EMAIL'):
                    return data.get('RECIPIENT_EMAIL')
        except Exception:
            pass
    return os.environ.get('RECIPIENT_EMAIL', 'your-email@example.com')

def set_recipient_email(email):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'RECIPIENT_EMAIL': email}, f)

def get_market_context():
    tickers = {
        "Wipro": "WIPRO.NS", "MRF": "MRF.NS", "Infosys": "INFY.NS", 
        "Reliance": "RELIANCE.NS", "Bajaj Finance": "BAJFINANCE.NS", 
        "Titan": "TITAN.NS", "Eicher Motors": "EICHERMOT.NS", 
        "Trent": "TRENT.NS", "Asian Paints": "ASIANPAINT.NS", "PI Industries": "PIIND.NS"
    }
    context = ""
    for name, ticker in tickers.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5).json()
            close_prices = r['chart']['result'][0]['indicators']['quote'][0]['close']
            valid_closes = [px for px in close_prices if px is not None]
            if len(valid_closes) >= 2:
                start_px = valid_closes[0]
                end_px = valid_closes[-1]
                pct_change = ((end_px - start_px) / start_px) * 100
                context += f"- {name} ({ticker}): {pct_change:+.2f}%\\n"
            else:
                context += f"- {name} ({ticker}): Data unavailable\\n"
        except Exception:
            context += f"- {name} ({ticker}): Error fetching\\n"
    return context

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_email = request.form.get('recipient_email')
        if new_email:
            set_recipient_email(new_email)
            message = "Recipient email updated successfully!"
        else:
            message = "Invalid email."
        return render_template('index.html', current_email=get_recipient_email(), message=message)
    return render_template('index.html', current_email=get_recipient_email())

@app.route('/trigger-weekly', methods=['GET', 'POST'])
def trigger_weekly():
    try:
        # 1. Initialize Groq
        api_key = os.environ.get('GROQ_API_KEY')
        if not api_key:
            return jsonify({'status': 'error', 'message': 'GROQ_API_KEY not configured.'}), 500
        
        from groq import Groq
        client = Groq(api_key=api_key)
        
        market_context = get_market_context()
        
        system_prompt = f"""You are an elite, world-class stock analyst and investment strategist specializing in identifying early-stage multi-baggers in the Indian Stock Market.

Your absolute highest priority is rigorous, data-driven financial analysis. Your mission is to find EXACTLY ONE current Indian stock trading under ₹100 (or a penny stock) that exhibits early signs of becoming a massive compounder.

# The Baseline: 10 Historical Indian Compounders (The "Massive Boom" Reference)
These are historical stocks that created massive wealth booms. Here is their current real-time performance over the past week to gauge current sector momentum:
{market_context}

# THE CORE ANALYTICAL FRAMEWORK (CRITICAL INSTRUCTIONS)
This section is your primary focus. You must execute deep, flawless analysis before writing anything:
1. DATA-DRIVEN SECTOR MOMENTUM: Analyze the real-time weekly performance of the legendary compounders above. Determine exactly which sectors are gaining momentum right now and which are bleeding capital. You must align your recommendation with where the money is flowing this week.
2. HISTORICAL BEHAVIOR COMPARISON: Deeply analyze the early-stage behavior, market conditions, and business fundamentals of the historical compounders during their initial "boom" phases (when they were small). Compare those exact early-day characteristics directly with your newly recommended stock to prove fundamentally why it is poised for the exact same trajectory.
3. FINANCIAL RIGOR: Your analysis must check for High Scalability, Business Turnaround potential, Monopoly/Duopoly nature, High ROE/ROCE, Low Debt, and Increasing Promoter Holding. Avoid fundamentally weak pump-and-dump penny stocks. Look for actual hidden gems.
4. NO HALLUCINATIONS: Do not invent or estimate financial metrics. Base your logic strictly on the real-world momentum provided and factual historical comparisons.
5. THE EXACT MATCH: You MUST explicitly state which of the 10 compounders above your recommended stock is currently mirroring, and justify this match.

# Output Formatting
Based strictly on the rigorous analysis above, output ONLY a beautifully designed, premium HTML email body (do NOT use markdown formatting like ```html, just output raw HTML).
Use inline CSS, a dark-mode scheme, and include: Stock Name & Ticker, Price (under ₹100), Sector, a 3-bullet-point analytical thesis based on the framework, and an AI disclaimer."""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": system_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.2
        )
        email_html_content = response.choices[0].message.content
        email_html_content = email_html_content.replace('```html', '').replace('```', '')
        
        # 2. Send Email
        sender_email = os.environ.get('SENDER_EMAIL')
        app_password = os.environ.get('APP_PASSWORD')
        recipient_email = get_recipient_email()
        
        if not sender_email or not app_password:
            return jsonify({'status': 'error', 'message': 'SENDER_EMAIL or APP_PASSWORD not configured.'}), 500

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Weekly DiamondDigger Stock Pick'
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        part = MIMEText(email_html_content, 'html')
        msg.attach(part)
        
        # Assuming Gmail for sending
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
            
        return jsonify({'status': 'success', 'message': 'Analysis complete and email sent successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Initialize Scheduler (placed here so Gunicorn picks it up on Render)
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
# Run every Monday at 8:30 AM
scheduler.add_job(func=trigger_weekly, trigger="cron", day_of_week='mon', hour=8, minute=30)
scheduler.start()

if __name__ == '__main__':
    # Run Flask app locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
