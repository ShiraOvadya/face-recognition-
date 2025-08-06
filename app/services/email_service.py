

import os
import smtplib
import logging
import yagmail
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
   # שירות שליחת מיילים - מתוקן לשליחה אמיתית

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.app_name = os.getenv("APP_NAME", "Face Recognition App")
        self.website_url = os.getenv("WEBSITE_URL", "https://your-website.com")
        self.yag = None  # יאותחל רק כשצריך

    def _get_yagmail_client(self):
       # יצירת Yagmail client (lazy loading)
        if self.yag is None and self.email_address and self.email_password:
            try:
                self.yag = yagmail.SMTP(self.email_address, self.email_password)
                logging.info("Yagmail client created successfully")
            except Exception as e:
                logging.error(f"Failed to create Yagmail client: {e}")
                return None
        return self.yag

    def send_photo_notification(self, user_email: str, user_name: str,
                                event_name: str, photo_count: int, event_code: str) -> bool:
       # שליחת מייל HTML מעוצב - הפונקציה הראשית
        try:
            # נסה קודם עם Yagmail
            yag_client = self._get_yagmail_client()
            if yag_client:
                try:
                    subject = f"🎉 {photo_count} תמונות חדשות מ{event_name}!"
                    html_content = self._create_beautiful_html(user_name, event_name, photo_count, event_code)

                    # שליחה עם Yagmail - מציין שזה HTML
                    yag_client.send(
                        to=user_email,
                        subject=subject,
                        contents=[html_content],
                        attachments=None,
                        cc=None,
                        bcc=None,
                        preview_only=False,
                        headers={'Content-Type': 'text/html; charset=utf-8'}
                    )

                    logging.info(f"HTML email sent successfully via Yagmail to {user_email}")
                    return True
                except Exception as e:
                    logging.warning(f"Yagmail failed, trying fallback: {e}")

            # Fallback - שליחה עם SMTP רגיל
            return self._send_html_fallback(user_email, user_name, event_name, photo_count, event_code)

        except Exception as e:
            logging.error(f"Failed to send photo notification: {e}")
            return False

    def _send_html_fallback(self, user_email: str, user_name: str,
                            event_name: str, photo_count: int, event_code: str) -> bool:
        #שליחת HTML עם SMTP רגיל
        try:
            if not self.email_address or not self.email_password:
                logging.error("Missing email credentials")
                return False

            subject = f"🎉 {photo_count} תמונות חדשות מ{event_name}!"
            html_content = self._create_beautiful_html(user_name, event_name, photo_count, event_code)

            # יצירת הודעה עם HTML בלבד
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = user_email
            msg['Subject'] = subject
            msg['Content-Type'] = 'text/html; charset=utf-8'

            # הוספת תוכן HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # שליחת המייל
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            logging.info(f"HTML email sent successfully via SMTP to {user_email}")
            return True

        except Exception as e:
            logging.error(f"HTML fallback failed: {e}")
            return False

    def _create_beautiful_html(self, user_name: str, event_name: str,
                               photo_count: int, event_code: str) -> str:

        return f"""
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>התמונות שלך מוכנות!</title>
    </head>
    <body style="font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #8e44ad, #e91e63); margin: 0; padding: 0;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:600px; margin:auto; background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.2);">
            <tr>
                <td style="background: linear-gradient(to right, #e91e63, #9b59b6); color:white; text-align:center; padding:40px 20px;">
                    <h1 style="margin:0; font-size:28px;">MyEventMemory</h1>
                    <p style="margin:10px 0 0; font-size:16px;">התמונות שלך מוכנות! 🎉</p>
                </td>
            </tr>
            <tr>
                <td style="padding:30px 20px; text-align:center;">
                    <p style="font-size:18px; margin-bottom:10px;">שלום {user_name},</p>
                    <p style="font-size:16px; color:#333;">יש לך <strong>{photo_count}</strong> תמונות חדשות מהאירוע <strong>{event_name}</strong>.</p>
                    <p style="margin:20px 0; font-size:16px;">קוד האירוע שלך:</p>
                    <div style="display:inline-block; padding:12px 25px; background-color:#fce4ec; color:#d81b60; font-weight:bold; border-radius:30px; font-size:18px;">
                        {event_code}
                    </div>
                    <p style="margin:30px 0 0;">
                        <a href="{self.website_url}" style="display:inline-block; background: linear-gradient(to right, #8e44ad, #e91e63); color:white; text-decoration:none; padding:14px 30px; border-radius:50px; font-size:16px; box-shadow:0 4px 12px rgba(233, 30, 99, 0.4);">
                             לצפייה בתמונות
                        </a>
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background-color:#f9f9f9; text-align:center; padding:20px; font-size:14px; color:#777;">
                    <div style="margin-bottom:8px;">תודה שבחרת ב־MyEventMemory!</div>
                    <a href="{self.website_url}" style="color:#d81b60; text-decoration:none; font-weight:bold;">{self.website_url}</a>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    def send_html_email(self, to_email: str, subject: str, html_content: str) -> bool:
        try:
            if not self.email_address or not self.email_password:
                logging.error(f"Cannot send email to {to_email} - missing EMAIL_ADDRESS or EMAIL_PASSWORD")
                return False

            # יצירת הודעה מעורבת (HTML + Plain Text)
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject

            # הוספת תוכן HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # שליחת המייל
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            logging.info(f"HTML email sent successfully to {to_email}")
            return True

        except Exception as e:
            logging.error(f"HTML email sending failed: {e}")
            return False

    def send_simple_email(self, to_email: str, subject: str, message: str) -> bool:
      #  שליחת מייל פשוט - מתוקן לשליחה אמיתית
        try:
            # בדיקה אם יש credentials
            if not self.email_address or not self.email_password:
                logging.error(f"Cannot send email to {to_email} - missing EMAIL_ADDRESS or EMAIL_PASSWORD")
                return False

            # יצירת ההודעה
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject

            # שליחת המייל
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            logging.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logging.error(f"SMTP Auth failed: {e}")
            return False

        except smtplib.SMTPRecipientsRefused as e:
            logging.error(f"Recipient refused: {e}")
            return False

        except smtplib.SMTPServerDisconnected as e:
            logging.error(f"SMTP disconnected: {e}")
            return False

        except Exception as e:
            logging.error(f"Email failed: {e}")
            return False

    def test_email_connection(self) -> bool:
       # בדיקת חיבור למייל
        try:
            if not self.email_address or not self.email_password:
                return False

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                return True

        except Exception as e:
            logging.error(f"Email connection test failed: {e}")
            return False

    def send_test_email(self, to_email: str) -> bool:
      #  שליחת מייל בדיקה HTML מעוצב
        try:
            subject = " בדיקת מערכת MyEventMemory"

            # שליחת מייל בדיקה עם העיצוב החדש
            return self.send_photo_notification(
                user_email=to_email,
                user_name="בודק מערכת",
                event_name="בדיקת מערכת",
                photo_count=1,
                event_code="TEST2024"
            )

        except Exception as e:
            logging.error(f"Failed to send test email: {e}")
            return False

    def create_photo_notification_message(self, user_name: str, event_name: str,
                                          photo_count: int, event_code: str) -> str:
        """יצירת הודעת מייל מעוצבת (טקסט רגיל - Fallback)"""

        message = f"""

🎉            תמונות חדשות מהאירוע!            🎉


👋 שלום {user_name}!

🔥 יש לך {photo_count} תמונות חדשות מ{event_name}!
        📸 פרטי האירוע     

│ 🎪 שם האירוע: {event_name}
│ 🎯 קוד האירוע: {event_code}
│ 📅 תאריך עיבוד: {datetime.now().strftime("%d/%m/%Y בשעה %H:%M")}
│ 🖼️  מספר תמונות: {photo_count}


 איך זה עובד?
המערכת שלנו זיהתה אותך אוטומטית בתמונות באמצעות 
טכנולוגיית זיהוי פנים מתקדמת! כל התמונות שלך מוכנות 
להורדה באפליקציה.

 כדי לראות ולהוריד את התמונות שלך:
 כנס לאתר: {self.website_url}
 הכנס את קוד האירוע: {event_code}
 הורד את התמונות שלך


 תודה שאתה משתמש במערכת זיהוי הפנים שלנו!
 אנחנו כאן כדי להפוך את האירועים שלך לבלתי נשכחים


 מערכת זיהוי פנים לאירועים | {self.website_url}
"""

        return message

    def __del__(self):
       #סגירת Yagmail client כשמסיימים
        if hasattr(self, 'yag') and self.yag:
            try:
                self.yag.close()
            except:
                pass


# יצירת instance גלובלי
email_service = EmailService()