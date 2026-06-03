import json
import os
import sys
import smtplib
import getpass
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

RECIPIENT_EMAIL = "DadiShekar@gmail.com"
DATA_FILE = "data_ipos.js"

def load_stock_data():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: Technical analysis data file '{DATA_FILE}' not found. Please run 'python analyze_ipos.py' first.")
        sys.exit(1)
        
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read()
            
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            print("ERROR: Could not parse stock database format inside data_ipos.js.")
            sys.exit(1)
            
        json_str = content[start_idx:end_idx+1]
        return json.loads(json_str)
    except Exception as e:
        print(f"ERROR parsing stock data: {e}")
        sys.exit(1)

def build_html_report(data):
    last_updated = data.get('lastUpdated', 'Unknown')
    ipos = data.get('ipos', {})
    sorted_ipos = sorted(ipos.values(), key=lambda x: x.get('compositeScore', 0), reverse=True)
    
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
                background: linear-gradient(135deg, #7c4dff, #ff1744);
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
                <h1>Recent IPOs Intelligence</h1>
                <p>Advanced Quantitative Technical Performance for New Listings (Last 60 Days)</p>
            </div>
            
            <div class="content">
                <div class="summary-badge">
                    Trading Session Date: <strong>{last_updated}</strong> &nbsp;|&nbsp; IPOs Scanned: <strong>{len(sorted_ipos)}</strong>
                </div>
                
                <div class="analysis-note">
                    <strong>Recent IPO Alert:</strong> This technical scan evaluates newly debuted companies (past 60 days) to identify emerging trends, support structures, and consolidation targets. Because new listings lack long-term moving averages, our models utilize adaptive periods to generate mathematically supported technical recommendations.
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Asset</th>
                            <th>Sector</th>
                            <th style="text-align: right;">IPO Price</th>
                            <th style="text-align: right;">Current</th>
                            <th style="text-align: right;">Change</th>
                            <th style="text-align: right;">Low/High Range</th>
                            <th style="text-align: center;">Consensus</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    for s in sorted_ipos:
        sig = s.get('signal', 'HOLD')
        sig_class = sig.lower()
        change = s.get('changePercent', 0.0)
        is_pos = change >= 0
        change_class = "positive" if is_pos else "negative"
        change_sign = "+" if is_pos else ""
        
        low_52 = s.get('low_52w', s.get('price', 0.0))
        high_52 = s.get('high_52w', s.get('price', 0.0))
        
        famous_news = s.get('famous_news', 'No recent news.')
        
        html += f"""
                        <tr style="border-bottom: 1px solid #e9ecef;">
                            <td style="padding: 12px 10px;">
                                <span class="ticker">{s.get('ticker')}</span>
                                <span class="company-name">{s.get('name')}</span>
                            </td>
                            <td style="padding: 12px 10px; color:#495057;">{s.get('sector')}</td>
                            <td style="padding: 12px 10px; text-align: right; font-weight: 500;">${s.get('ipo_price', 0.0):.2f}</td>
                            <td style="padding: 12px 10px; text-align: right; font-weight: 600; color:#1a1c23;">${s.get('price', 0.0):.2f}</td>
                            <td style="padding: 12px 10px; text-align: right;" class="price-change {change_class}">
                                {change_sign}{change:.2f}%
                            </td>
                            <td style="padding: 12px 10px; text-align: right; font-family: monospace; font-size:11.5px; color:#0b7285;">
                                ${low_52:.2f} - ${high_52:.2f}
                            </td>
                            <td style="padding: 12px 10px; text-align: center;">
                                <span class="signal-badge {sig_class}">{sig}</span>
                            </td>
                        </tr>
                        <tr style="background-color: #f8f9fa;">
                            <td colspan="7" style="padding: 6px 12px; font-size: 11px; border-bottom: 1px solid #dee2e6; color: #495057;">
                                <strong style="color: #7c4dff;">News Catalyst:</strong> {famous_news}
                            </td>
                        </tr>
        """
        
    html += """
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                This analysis is powered by the <strong>Recent IPOs Consensus Engine</strong>.<br>
                To view interactive technical charts and indicators, open your local <a href="#">dashboard.html</a>.
            </div>
        </div>
    </body>
    </html>
    """
    return html

def main():
    parser = argparse.ArgumentParser(description="IPO Mechanics Email Dispatcher")
    parser.add_argument('--sender', type=str, help="Gmail Address of Sender")
    parser.add_argument('--password', type=str, help="Gmail 16-character App Password")
    args = parser.parse_args()
    
    print(f"==================================================")
    print(f"       RECENT IPOs EMAIL DISPATCH SERVICE         ")
    print(f"==================================================")
    print(f"Recipient: {RECIPIENT_EMAIL}\n")
    
    data = load_stock_data()
    html_content = build_html_report(data)
    
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
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Recent IPOs Debut Stock Report - {data.get('lastUpdated', '')}"
    msg['From'] = f"Recent IPOs <{sender_email}>"
    msg['To'] = RECIPIENT_EMAIL
    
    part1 = MIMEText("Please enable HTML viewing to see the Recent IPOs technical analysis report.", 'plain')
    part2 = MIMEText(html_content, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    print("Connecting to Gmail SMTP servers (smtp.gmail.com:587)...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("TLS handshake complete. Logging in...")
        server.login(sender_email, password)
        print("Authentication successful! Dispatching report...")
        server.sendmail(sender_email, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print("\nSUCCESS! The Recent IPOs stock analysis report has been sent to DadiShekar@gmail.com.")
    except Exception as e:
        print(f"\nERROR: Failed to send email: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
