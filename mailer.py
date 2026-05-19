# mailer.py
import smtplib
import random
from email.mime.text import MIMEText

def send_verification_otp(receiver_email):
    """
    Generates a random 6-digit OTP, sends it to the user's email via Gmail SMTP,
    and returns a dictionary containing the success status and the generated OTP.
    """
    # 1. ── CREDENTIALS CONFIGURATION ─────────────────────────────────────────
    # Using your dedicated team email and the verified working App Password
    SENDER_EMAIL = "ematch888@gmail.com"
    SENDER_APP_PASSWORD = "cepipfdxyiyleeno"  
    
    # 2. ── GENERATE SECURITY TOKEN ───────────────────────────────────────────
    # This generates a string token (e.g., "482915") for your verification form
    otp = str(random.randint(100000, 999999))
    
    # 3. ── CRAFT THE EMAIL CONTENT ───────────────────────────────────────────
    email_body = (
        f"Welcome to E-match!\n\n"
        f"Your account verification code is: {otp}\n\n"
        f"This code will expire in 15 minutes. If you did not request this account setup, "
        f"please safely ignore this email.\n\n"
        f"Best regards,\n"
        f"The E-match Team"
    )
    
    msg = MIMEText(email_body)
    msg['Subject'] = "🌿 Verify Your E-match Account"
    msg['From'] = f"E-match Team <{SENDER_EMAIL}>"
    msg['To'] = receiver_email

    # 4. ── EXECUTE SECURE SMTP DISPATCH ──────────────────────────────────────
    try:
        # Establish secure SSL handshake on Port 465
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        
        # Return success tracking dict back to your Streamlit logic
        return {"success": True, "otp": otp, "error": None}
        
    except Exception as e:
        # Capture failure details safely without breaking the app flow
        return {"success": False, "otp": None, "error": str(e)}