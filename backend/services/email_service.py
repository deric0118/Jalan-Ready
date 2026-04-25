import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_USERNAME")
        self.sender_password = os.getenv("SMTP_PASSWORD")

    def send_report(self, recipient_email: str, authority: str, urgency: int, data: dict, image_path: str = None):
        if not self.sender_email or not self.sender_password:
            print("⚠️ [EMAIL] Setup incomplete.")
            return False

        # Determine theme color based on urgency
        # Critical (Red) vs Warning (Gold)
        theme_color = "#e74c3c" if urgency >= 80 else "#f39c12"
        urgency_label = "CRITICAL" if urgency >= 80 else "STANDARD"

        try:
            msg = MIMEMultipart()
            msg['From'] = f"Jalan-Ready AI System <{self.sender_email}>"
            msg['To'] = recipient_email
            
            urgency_tag = "🚨 [URGENT]" if urgency >= 80 else "📋 [Report]"
            msg['Subject'] = f"{urgency_tag} {data.get('yolo_label', 'Defect').upper()} at {data.get('road_name', 'Unknown')}"

            issue_type = data.get('yolo_label', 'Unknown Anomaly').replace('_', ' ').title()

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 0; background-color: #f4f7f6; font-family: 'Segoe UI', Helvetica, Arial, sans-serif;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f7f6; padding: 20px;">
                    <tr>
                        <td align="center">
                            <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                                
                                <tr>
                                    <td style="background-color: {theme_color}; padding: 30px 40px; text-align: center;">
                                        <h1 style="color: #ffffff; margin: 0; font-size: 24px; letter-spacing: 1px;">JALAN-READY</h1>
                                        <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-weight: bold; font-size: 12px;">GOVERNANCE ENGINE | {urgency_label} REPORT</p>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding: 40px;">
                                        <p style="font-size: 16px; color: #2c3e50; margin-top: 0;">Hello <strong>{authority}</strong>,</p>
                                        <p style="font-size: 14px; color: #7f8c8d; line-height: 1.6;">Our AI vision system has identified a road defect that requires attention. Below are the actionable details:</p>
                                        
                                        <table width="100%" border="0" cellspacing="0" cellpadding="10" style="margin: 20px 0; background-color: #fcfcfc; border: 1px solid #eee; border-radius: 6px;">
                                            <tr>
                                                <td width="50%">
                                                    <span style="font-size: 11px; color: #95a5a6; text-transform: uppercase;">Defect Type</span><br>
                                                    <strong style="color: #2c3e50; font-size: 15px;">{issue_type}</strong>
                                                </td>
                                                <td width="50%">
                                                    <span style="font-size: 11px; color: #95a5a6; text-transform: uppercase;">Urgency Score</span><br>
                                                    <strong style="color: {theme_color}; font-size: 15px;">{urgency}/100</strong>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <span style="font-size: 11px; color: #95a5a6; text-transform: uppercase;">AI Confidence</span><br>
                                                    <strong style="color: #2c3e50; font-size: 15px;">{data.get('confidence', 0.0) * 100:.1f}%</strong>
                                                </td>
                                                <td>
                                                    <span style="font-size: 11px; color: #95a5a6; text-transform: uppercase;">Weather</span><br>
                                                    <strong style="color: #2c3e50; font-size: 15px;">{data.get('weather', 'Clear')}</strong>
                                                </td>
                                            </tr>
                                        </table>

                                        <div style="border-left: 4px solid #3498db; padding-left: 15px; margin: 25px 0;">
                                            <h4 style="margin: 0 0 5px 0; color: #2c3e50;">Location Details</h4>
                                            <p style="margin: 0; font-size: 14px; color: #34495e;">{data.get('road_name', 'N/A')}</p>
                                            <p style="margin: 5px 0; font-size: 12px; color: #95a5a6;">GPS: {data.get('lat')}, {data.get('lon')}</p>
                                            <a href="https://www.google.com/maps/search/?api=1&query={data.get('lat')},{data.get('lon')}" 
                                               style="color: #3498db; text-decoration: none; font-size: 13px; font-weight: bold;">📍 Open in Google Maps &rarr;</a>
                                        </div>

                                        <div style="text-align: center; margin-top: 35px;">
                                            <a href="http://127.0.0.1:8080/frontend/contractor.html" 
                                               style="background-color: #2c3e50; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px; display: inline-block;">
                                                Review in Contractor Dashboard
                                            </a>
                                        </div>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="background-color: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eeeeee;">
                                        <p style="margin: 0; font-size: 11px; color: #bdc3c7;">
                                            This is an automated report generated by the Jalan-Ready AI Engine.<br>
                                            © 2024 Smart City Governance.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html'))

            # (Optional) Logic to attach an actual photo of the pothole/defect
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img_data = f.read()
                image = MIMEImage(img_data, name=os.path.basename(image_path))
                msg.attach(image)

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 [EMAIL] Premium report sent to {authority}")
            return True

        except Exception as e:
            print(f"❌ [EMAIL ERROR] {e}")
            return False