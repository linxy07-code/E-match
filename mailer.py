import smtplib
import random
from email.mime.text import MIMEText
import streamlit as st

def send_verification_otp(receiver_email):
    """Sends a 6-digit OTP to the user's email using project app credentials."""
    # Your Gmail account used for sending emails
    SENDER_EMAIL = "berniss2007@gmail.com"
    SENDER_APP_PASSWORD = "myzsqxcmtmhvbhzc" 
    
    # Generate a random 6-digit OTP string
    otp = str(random.randint(100000, 999999))
    
    # Craft the email body
    msg = MIMEText(
        f"Welcome to E-match!\n\n"
        f"Your account verification code is: {otp}\n\n"
        f"This code will expire in 15 minutes. If you did not request this, please ignore this email."
    )
    msg['Subject'] = "🌿 Verify Your E-match Account"
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email

    try:
        # Connect to Gmail's secure SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        return {"success": True, "otp": otp}
    except Exception as e:
        return {"success": False, "error": str(e)}