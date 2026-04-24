# backend/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load the variables from your .env file into Python
load_dotenv()

class EmailService:
    def __init__(self):
        # ⚠️ We use environment variables so you don't leak your password on GitHub!
        # For Gmail, you MUST use an "App Password", not your normal login password.
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL", "your_system_email@gmail.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "your_app_password")

    def send_report(self, recipient_email: str, authority: str, urgency: int, data: dict):
        """
        Constructs and sends an HTML email report to the designated authority.
        """
        if not self.sender_password or self.sender_password == "your_app_password":
            print("⚠️ [EMAIL] Setup incomplete: Missing SMTP credentials in environment variables.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = f"Jalan-Ready AI System <{self.sender_email}>"
            msg['To'] = recipient_email
            
            # Add an urgent tag to the subject if score is high
            urgency_tag = "🚨 [URGENT P1]" if urgency >= 80 else "📋 [Standard]"
            msg['Subject'] = f"{urgency_tag} Automated Road Defect Report: {data.get('road_name', 'Unknown Location')}"

            # Safely extract user info if available
            user_info = data.get('citizen_description', 'Auto-detected via Dashcam/System')
            issue_type = data.get('yolo_label', 'Unknown Anomaly').replace('_', ' ').title()

            # HTML Email Template
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #2c3e50;">Jalan-Ready Actionable Work Order</h2>
                    <p>Hello <strong>{authority}</strong>,</p>
                    <p>The Z.AI Governance Engine has detected a new infrastructure defect within your jurisdiction.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 5px solid {'#e74c3c' if urgency >= 80 else '#f1c40f'}; margin-bottom: 20px;">
                        <h3 style="margin-top: 0;">Report Details</h3>
                        <ul>
                            <li><strong>Issue Detected:</strong> {issue_type}</li>
                            <li><strong>AI Confidence:</strong> {data.get('confidence', 0.0) * 100:.1f}%</li>
                            <li><strong>Urgency Score:</strong> {urgency}/100</li>
                            <li><strong>Weather Context:</strong> {data.get('weather', 'Clear')}</li>
                        </ul>
                    </div>

                    <div style="background-color: #e9ecef; padding: 15px; margin-bottom: 20px;">
                        <h3 style="margin-top: 0;">Location & User Data</h3>
                        <ul>
                            <li><strong>Road Name:</strong> {data.get('road_name', 'N/A')}</li>
                            <li><strong>GPS Coordinates:</strong> {data.get('lat')}, {data.get('lon')}</li>
                            <li><strong>Google Maps Link:</strong> <a href="https://www.google.com/maps/search/?api=1&query={data.get('lat')},{data.get('lon')}">View on Map</a></li>
                            <li><strong>Reporter Notes:</strong> {user_info}</li>
                        </ul>
                    </div>
                    
                    <p><em>Please review this ticket in the Jalan-Ready Contractor Dashboard to update its status.</em></p>
                </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html'))

            # Connect to SMTP and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 [EMAIL] Successfully sent report to {authority} ({recipient_email})")
            return True

        except Exception as e:
            print(f"❌ [EMAIL ERROR] Failed to send email: {e}")
            return False