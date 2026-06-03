import json
import os
import sys
import smtplib
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT_EMAIL = "DadiShekar@gmail.com"
DATA_SPACE_FILE = "data.js"
DATA_QUANTUM_FILE = "data_quantum.js"
DATA_IPOS_FILE = "data_ipos.js"

def load_dataset(filepath):
    if not os.path.exists(filepath):
        print(f"WARNING: Data file '{filepath}' not found.")
        return {}
        
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            print(f"WARNING: Could not parse database format inside '{filepath}'.")
            return {}
            
        json_str = content[start_idx:end_idx+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"WARNING parsing data file '{filepath}': {e}")
        return {}

def merge_stocks():
    space_data = load_dataset(DATA_SPACE_FILE)
    quantum_data = load_dataset(DATA_QUANTUM_FILE)
    ipos_data = load_dataset(DATA_IPOS_FILE)
    
    merged = {}
    last_updated = "Unknown"
    
    if space_data:
        last_updated = space_data.get('lastUpdated', 'Unknown')
        for t, s in space_data.get('stocks', {}).items():
            merged[t] = s
            
    if quantum_data:
        if last_updated == "Unknown":
            last_updated = quantum_data.get('lastUpdated', 'Unknown')
        for t, s in quantum_data.get('stocks', {}).items():
            merged[t] = s

    if ipos_data:
        if last_updated == "Unknown":
            last_updated = ipos_data.get('lastUpdated', 'Unknown')
        for t, s in ipos_data.get('ipos', {}).items():
            merged[t] = s
            
    return list(merged.values()), last_updated

def build_html_table(stocks, title, accent_color):
    if not stocks:
        return f"""
        <div style="text-align: center; padding: 25px; background-color: #fcfcfd; border: 1px dashed #dee2e6; border-radius: 8px; color: #868e96; font-size: 13px; margin-bottom: 25px;">
            No overextended candidates detected in the {title} range.
        </div>
        """
        
    table_html = f"""
    <h3 style="color: {accent_color}; border-bottom: 2px solid {accent_color}; padding-bottom: 8px; font-size: 15px; margin-top: 15px; margin-bottom: 12px; font-family: Arial, sans-serif;">
        {title} Price Bracket Candidates
    </h3>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 12.5px; font-family: Arial, sans-serif;">
        <thead>
            <tr style="background-color: #fafafa; border-bottom: 2px solid #e9ecef; color: #495057;">
                <th style="padding: 10px; text-align: left; font-weight: 600;">Asset Details</th>
                <th style="padding: 10px; text-align: right; font-weight: 600;">Last Price</th>
                <th style="padding: 10px; text-align: center; font-weight: 600;">BB Dev</th>
                <th style="padding: 10px; text-align: center; font-weight: 600;">Squeeze Risk</th>
                <th style="padding: 10px; text-align: center; font-weight: 600;">Exit (Cover Target)</th>
                <th style="padding: 10px; text-align: right; font-weight: 600;">Stop Loss</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for s in stocks:
        change = s.get('changePercent', 0.0)
        is_pos = change >= 0
        change_color = "#28a745" if is_pos else "#dc3545"
        change_sign = "+" if is_pos else ""
        
        sa = s.get('shortAnalysis', {})
        percent_above = sa.get('percentAboveBB', -99)
        is_above = percent_above >= 0
        dev_badge = f"""
            <span style="display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 10.5px; 
                         background-color: {'#fff0f3' if is_above else '#e3fafc'}; color: {'#ff1744' if is_above else '#0b7285'}; 
                         border: 1px solid {'#ffd3e0' if is_above else '#c5f6fa'};">
                {'+' if is_above else ''}{percent_above:.1f}%
            </span>
        """
        
        sq_risk = sa.get('squeezeRisk', 'LOW')
        sq_color = "#28a745"
        if sq_risk == 'HIGH':
            sq_color = "#ff1744"
        elif sq_risk == 'MODERATE':
            sq_color = "#fd7e14"
            
        sq_badge = f"<span style='color: {sq_color}; font-weight: bold;'>{sq_risk}</span>"
        
        cover = sa.get('recommendedCover', s.get('price', 0.0) * 0.9)
        stop = sa.get('shortStopLoss', s.get('price', 0.0) * 1.1)
        
        news_html = ""
        if sa.get('hasBigNews', 'NO').startswith('YES'):
            news_html = f"""
            <tr style="background-color: #fff9db;">
                <td colspan="6" style="padding: 6px 12px; font-size: 11px; border-bottom: 1px solid #e9ecef;">
                    <span style="color:#ff922b; font-weight:bold; text-transform:uppercase; font-size:9.5px; display:inline-block; margin-right:6px; border:1px solid #ffe3e3; padding:1px 4px; background:#fff5f5; border-radius:3px;">Active Catalyst</span>
                    <strong style="color: #495057;">{sa.get('latestHeadline')}</strong>
                </td>
            </tr>
            """
            
        table_html += f"""
            <tr style="border-bottom: 1px solid #e9ecef;">
                <td style="padding: 10px; vertical-align: middle;">
                    <strong style="font-size: 13.5px; color: #1a1c23;">{s.get('ticker')}</strong>
                    <span style="color: #6c757d; font-size: 10px; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;">{s.get('name')}</span>
                </td>
                <td style="padding: 10px; text-align: right; vertical-align: middle;">
                    <strong style="color: #1a1c23;">${s.get('price', 0.0):.2f}</strong>
                    <span style="color: {change_color}; font-size: 10.5px; display: block; font-weight: 600;">{change_sign}{change:.2f}%</span>
                </td>
                <td style="padding: 10px; text-align: center; vertical-align: middle;">{dev_badge}</td>
                <td style="padding: 10px; text-align: center; vertical-align: middle;">{sq_badge}</td>
                <td style="padding: 10px; text-align: center; vertical-align: middle; color: #28a745; font-weight: bold;">${cover:.2f}</td>
                <td style="padding: 10px; text-align: right; vertical-align: middle; color: #dc3545; font-weight: bold;">${stop:.2f}</td>
            </tr>
            {news_html}
        """
        
    table_html += "</tbody></table>"
    return table_html

def build_html_report(speculative, midtier, highbeta, last_updated):
    total = len(speculative) + len(midtier) + len(highbeta)
    
    spec_table = build_html_table(speculative, "Speculative ($1 - $10)", "#d9480f")
    midtier_table = build_html_table(midtier, "Mid-Tier ($11 - $20)", "#862e9c")
    highbeta_table = build_html_table(highbeta, "High-Beta ($21 - $50)", "#1c7ed6")
    
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                color: #2c3e50;
                line-height: 1.6;
                background-color: #f8f9fa;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 680px;
                margin: 20px auto;
                background: #ffffff;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            }}
            .header {{
                background: linear-gradient(135deg, #ff1744, #ff8f00);
                color: #ffffff;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}
            .header p {{
                margin: 5px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .summary-badge {{
                display: inline-block;
                background-color: #f1f3f5;
                border: 1px solid #dee2e6;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 12px;
                color: #495057;
                margin-bottom: 20px;
            }}
            .analysis-note {{
                background-color: #fff5f5;
                border-left: 4px solid #ff1744;
                padding: 15px;
                border-radius: 4px;
                font-size: 13.5px;
                color: #c92a2a;
                margin-bottom: 25px;
            }}
            .footer {{
                background: #f1f3f5;
                padding: 20px;
                text-align: center;
                font-size: 11px;
                color: #868e96;
                border-top: 1px solid #e9ecef;
            }}
            .footer a {{
                color: #ff1744;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Apex Shorts Technical Intelligence</h1>
                <p>Consensus Engine Short-Selling & Extreme Overextension Report</p>
            </div>
            
            <div class="content">
                <div class="summary-badge">
                    Trading Session Date: <strong>{last_updated}</strong> &nbsp;|&nbsp; Candidates Loaded: <strong>{total}</strong>
                </div>
                
                <div class="analysis-note">
                    <strong>Bearish Reversion Summary:</strong> This scan identifies stocks trading near or above their upper Bollinger Band (reversion limits). High volatility names are sorted by overextension scale to isolate high-leverage entry points. Squeeze risk markers gauge potential risk bounds, while institutional insider support monitors backing strength. Recommended cover prices represent the SMA 20 target bounds.
                </div>
                
                {spec_table}
                {midtier_table}
                {highbeta_table}
            </div>
            
            <div class="footer">
                This analysis is powered by the <strong>Apex Shorts Consensus Engine</strong>.<br>
                To view interactive technical charts and indicators, open your local <a href="https://601b2d70603553a2-70-178-250-148.serveousercontent.com/dashboard.html?tab=shorts">Live Dashboard</a>.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def main():
    parser = argparse.ArgumentParser(description="Apex Shorts Email Dispatcher")
    parser.add_argument('--sender', type=str, default="DadiShekar@gmail.com", help="Gmail Address of Sender")
    parser.add_argument('--password', type=str, default="tfhuczdxuuumcdec", help="Gmail 16-character App Password")
    args = parser.parse_args()
    
    print(f"==================================================")
    print(f"        APEX SHORTS EMAIL DISPATCH SERVICE         ")
    print(f"==================================================")
    print(f"Recipient: {RECIPIENT_EMAIL}\n")
    
    # 1. Load merged datasets
    stocks, last_updated = merge_stocks()
    
    speculative = [s for s in stocks if s.get('price', 0.0) >= 1.0 and s.get('price', 0.0) <= 10.0]
    midtier = [s for s in stocks if s.get('price', 0.0) >= 11.0 and s.get('price', 0.0) <= 20.0]
    highbeta = [s for s in stocks if s.get('price', 0.0) >= 21.0 and s.get('price', 0.0) <= 50.0]
    
    # Sort by overextension descending
    speculative.sort(key=lambda s: s.get('shortAnalysis', {}).get('percentAboveBB', -999), reverse=True)
    midtier.sort(key=lambda s: s.get('shortAnalysis', {}).get('percentAboveBB', -999), reverse=True)
    highbeta.sort(key=lambda s: s.get('shortAnalysis', {}).get('percentAboveBB', -999), reverse=True)
    
    # 2. Build email body
    html_content = build_html_report(speculative, midtier, highbeta, last_updated)
    
    # 3. Retrieve Credentials
    sender_email = args.sender
    password = args.password
    
    if not sender_email or not password:
        print("ERROR: Gmail address and password cannot be blank.")
        sys.exit(1)
        
    # 4. Construct email structures
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Apex Shorts Stock Opportunity Alert - {last_updated}"
    msg['From'] = f"Apex Shorts <{sender_email}>"
    msg['To'] = RECIPIENT_EMAIL
    
    part1 = MIMEText("Please enable HTML viewing to see the Apex Shorts technical analysis report.", 'plain')
    part2 = MIMEText(html_content, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # 5. Connect and send
    print("Connecting to Gmail SMTP servers (smtp.gmail.com:587)...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("TLS handshake complete. Logging in...")
        server.login(sender_email, password)
        print("Authentication successful! Dispatching report...")
        server.sendmail(sender_email, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"\nSUCCESS! The Apex Shorts stock report has been sent to {RECIPIENT_EMAIL}.")
    except Exception as e:
        print(f"\nERROR: Failed to send email: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
