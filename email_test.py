# email_test.py
import smtplib
import random
from email.mime.text import MIMEText

def test_send():
    # 1. ── CONFIGURATION ──────────────────────────────────────────────────────
    SENDER_EMAIL = "ematch888@gmail.com"
    SENDER_APP_PASSWORD = "cepipfdxyiyleeno"  # Spaces completely removed
    RECEIVER_EMAIL = "ematch888@gmail.com"
    
    # Generate a dummy 6-digit verification code
    mock_otp = str(random.randint(100000, 999999))
    
    # 2. ── BUILD THE EMAIL ────────────────────────────────────────────────────
    msg = MIMEText(f"Hello from E-match!\n\nYour test verification code is: {mock_otp}\n\nIf you see this, your script works!")
    msg['Subject'] = "🌿 E-match Account Verification Test"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # 3. ── CONNECT TO GMAIL & SEND ───────────────────────────────────────────
    print("Connecting to Gmail secure server (SSL Port 465)...")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(f"\n✅ SUCCESS! Email sent to {RECEIVER_EMAIL}.")
        print(f"Generated test OTP was: {mock_otp}")
        print("Go check your inbox (and your spam folder just in case)!")
    except Exception as e:
        print(f"\n❌ FAILED to send email.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    test_send()