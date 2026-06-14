import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings

def send_reset_email(recipient_email, otp_code):
    """
    Send password reset OTP to user's email
    """
    subject = "VIBGYOR HRM - Password Reset OTP"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e3e6f0; border-radius: 10px;">
            <h2 style="color: #4e73df;">VIBGYOR HRM System</h2>
            <h3>Password Reset Request</h3>
            <p>You requested to reset your password. Use the following OTP to complete the process:</p>
            <div style="background-color: #f8f9fc; padding: 15px; text-align: center; font-size: 24px; letter-spacing: 5px; font-weight: bold;">
                {otp_code}
            </div>
            <p>This OTP is valid for <strong>10 minutes</strong>.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <hr>
            <small>VIBGYOR HRM System - Secure Authentication</small>
        </div>
    </body>
    </html>
    """
    
    # Always print to console for debugging
    print(f"\n{'='*50}")
    print(f"📧 Password Reset OTP for {recipient_email}")
    print(f"🔑 OTP Code: {otp_code}")
    print(f"⏰ Valid for 10 minutes")
    print(f"{'='*50}\n")
    
    # Check if SMTP is configured (not console backend)
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"✅ Email successfully sent to {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False
    else:
        print(f"ℹ️ Console backend active. Check terminal for OTP.")
    
    return True