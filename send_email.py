import json
import os
import sys
import smtplib
import getpass
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT_EMAIL = "DadiShekar@gmail.com"
DATA_FILE = "data.js"

def load_stock_data():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: Technical analysis data file '{DATA_FILE}' not found. Please run 'python analyze.py' first.")
        sys.exit(1)
        
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            print("ERROR: Could not parse stock database format inside data.js.")
            sys.exit(1)
            
        json_str = content[start_idx:end_idx+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"ERROR parsing stock data: {e}")
        sys.exit(1)

def build_html_report(data):
    last_updated = data.get('lastUpdated', 'Unknown')
    stocks = data.get('stocks', {})
    sorted_stocks = sorted(stocks.values(), key=lambda x: x.get('compositeScore', 0), reverse=True)
    
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
                background: linear-gradient(135deg, #7c4dff, #00f5ff);
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
                background-color: #eef2f7;
                border-left: 4px solid #7c4dff;
                padding: 15px;
                border-radius: 4px;
                font-size: 13.5px;
                color: #475569;
                margin-bottom: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 13px;
            }}
            th {{
                background-color: #f8f9fa;
                border-bottom: 2px solid #dee2e6;
                color: #495057;
                text-align: left;
                padding: 12px 10px;
                font-weight: 600;
            }}
            td {{
                padding: 12px 10px;
                border-bottom: 1px solid #e9ecef;
            }}
            .ticker {{
                font-weight: 700;
                color: #1a1c23;
            }}
            .company-name {{
                color: #6c757d;
                font-size: 11px;
                display: block;
                margin-top: 2px;
            }}
            .signal-badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
                text-align: center;
                min-width: 50px;
            }}
            .signal-badge.buy {{
                background-color: #d4edda;
                color: #155724;
            }}
            .signal-badge.sell {{
                background-color: #f8d7da;
                color: #721c24;
            }}
            .signal-badge.hold {{
                background-color: #e2e3e5;
                color: #383d41;
            }}
            .price-change {{
                font-weight: 600;
            }}
            .price-change.positive {{
                color: #28a745;
            }}
            .price-change.negative {{
                color: #dc3545;
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
                color: #7c4dff;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Orbital Alpha Intelligence</h1>
                <p>Space & Aerospace Technical Stock Analysis Report</p>
            </div>
            
            <div class="content">
                <div class="summary-badge">
                    Trading Session Date: <strong>{last_updated}</strong> &nbsp;|&nbsp; Companies Analyzed: <strong>{len(sorted_stocks)}</strong>
                </div>
                
                <div class="analysis-note">
                    <strong>Technical Summary Alert:</strong> The Space sector saw **unprecedented momentum** on the last trading day (e.g. SPCE +17.82%, LUNR +11.74%, ASTS +10.01%). While trend indicators triggered buy signals, momentum oscillators (RSI, Stochastic) surged into near-overbought territories. The consensus model wisely marks these as <strong>HOLD</strong>, advising caution before entering at the top of a vertical spike.
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th style="text-align: right;">Price</th>
                            <th style="text-align: right;">Change</th>
                            <th style="text-align: center;">Consensus</th>
                            <th style="text-align: center;">Targets (ST / MT / LT)</th>
                            <th style="text-align: right;">Stop Loss</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for s in sorted_stocks:
        sig = s.get('signal', 'HOLD')
        sig_class = sig.lower()
        change = s.get('changePercent', 0.0)
        is_pos = change >= 0
        change_class = "positive" if is_pos else "negative"
        change_sign = "+" if is_pos else ""
        
        targets = s.get('targets')
        if targets:
            st = targets.get('shortTerm', 0.0)
            mt = targets.get('mediumTerm', 0.0)
            lt = targets.get('longTerm', 0.0)
            sl = targets.get('stopLoss', 0.0)
            targets_html = f"""
                <span style="color:#28a745;font-weight:600;font-size:11.5px;">${st:.2f}</span>&nbsp;|&nbsp;
                <span style="color:#00b8d4;font-weight:600;font-size:11.5px;">${mt:.2f}</span>&nbsp;|&nbsp;
                <span style="color:#7c4dff;font-weight:600;font-size:11.5px;">${lt:.2f}</span>
            """
            sl_html = f"<span style='color:#dc3545;font-weight:600;'>${sl:.2f}</span>"
        else:
            targets_html = "<span style='color:#868e96;'>N/A</span>"
            sl_html = "<span style='color:#868e96;'>N/A</span>"
            
        html += f"""
                        <tr>
                            <td>
                                <span class="ticker">{s.get('ticker')}</span>
                                <span class="company-name">{s.get('name')}</span>
                            </td>
                            <td style="text-align: right; font-weight: 600;">${s.get('price', 0.0):.2f}</td>
                            <td style="text-align: right;" class="price-change {change_class}">
                                {change_sign}{change:.2f}%
                            </td>
                            <td style="text-align: center;">
                                <span class="signal-badge {sig_class}">{sig}</span>
                            </td>
                            <td style="text-align: center;">
                                {targets_html}
                            </td>
                            <td style="text-align: right; font-weight: 600;">
                                {sl_html}
                            </td>
                        </tr>
        """
        
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                This analysis is powered by the <strong>Orbital Alpha Consensus Engine</strong>.<br>
                To view interactive technical charts and indicators, open your local <a href="#">dashboard.html</a>.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def main():
    parser = argparse.ArgumentParser(description="Orbital Alpha Email Dispatcher")
    parser.add_argument('--sender', type=str, help="Gmail Address of Sender")
    parser.add_argument('--password', type=str, help="Gmail 16-character App Password")
    args = parser.parse_args()
    
    print(f"==================================================")
    print(f"      ORBITAL ALPHA EMAIL DISPATCH SERVICE        ")
    print(f"==================================================")
    print(f"Recipient: {RECIPIENT_EMAIL}\n")
    
    # 1. Load technical analysis results
    data = load_stock_data()
    
    # 2. Build email body
    html_content = build_html_report(data)
    
    # 3. Retrieve Credentials (Env -> Arguments -> Prompts)
    sender_email = os.environ.get('GMAIL_SENDER') or args.sender
    password = os.environ.get('GMAIL_PASSWORD') or args.password
    
    if not sender_email:
        sender_email = input("Enter your Gmail address: ").strip()
        
    if not password:
        password = getpass.getpass("Enter your 16-character Gmail App Password (hidden): ").strip()
        
    sender_email = sender_email.strip()
    password = password.strip().replace(" ", "")
    
    if not sender_email or not password:
        print("ERROR: Gmail address and password cannot be blank.")
        sys.exit(1)
        
    # 4. Construct email structures
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Orbital Alpha Space Stock Report - {data.get('lastUpdated', '')}"
    msg['From'] = f"Orbital Alpha <{sender_email}>"
    msg['To'] = RECIPIENT_EMAIL
    
    part1 = MIMEText("Please enable HTML viewing to see the Space Stock technical analysis report.", 'plain')
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
        print("\nSUCCESS! The stock analysis report has been sent to DadiShekar@gmail.com.")
    except Exception as e:
        print(f"\nERROR: Failed to send email: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
