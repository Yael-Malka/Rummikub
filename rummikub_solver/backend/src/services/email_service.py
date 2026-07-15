"""Send verification emails."""

import logging
import smtplib
from email.message import EmailMessage
from src.core.config import settings

logger = logging.getLogger(__name__)

async def send_verification_email(to_email: str, token: str) -> None:
    """Send an email verification link to the user.

    Args:
        to_email (str): The recipient's email address.
        token (str): The verification token.
    """
    if not hasattr(settings, 'SMTP_HOST') or not settings.SMTP_HOST:
        logger.info(f"Skipping email send for {to_email} because SMTP is not configured. Token: {token}")
        return

    msg = EmailMessage()
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FBF7EC; margin: 0; padding: 40px; }}
      .container {{ max-width: 480px; margin: 0 auto; background: #FFFFFF; border-radius: 28px; padding: 40px 32px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }}
      .eyebrow {{ font-weight: 700; font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: #1E6B4E; margin-bottom: 8px; }}
      h1 {{ font-size: 28px; color: #1C1B16; margin-top: 0; font-weight: 800; }}
      p {{ font-size: 16px; line-height: 1.5; color: #1C1B16; margin-bottom: 24px; }}
      .token-box {{ background: #F6EFDE; border-radius: 16px; padding: 20px; font-size: 36px; font-weight: 800; letter-spacing: 6px; color: #1E6B4E; margin: 32px 0; }}
      .btn {{ display: inline-block; background-color: #1E6B4E; color: #FFFFFF !important; text-decoration: none; padding: 16px 32px; border-radius: 9999px; font-weight: 700; font-size: 16px; }}
      .footer {{ margin-top: 32px; font-size: 13px; color: #6b6375; opacity: 0.8; }}
    </style>
    </head>
    <body>
      <div class="container">
        <div class="eyebrow">Rummikub Assistant</div>
        <h1>Verify your email</h1>
        <p>Welcome! We're thrilled to help you find your best moves. Enter the code below in the app or click the button to verify your account.</p>
        <div class="token-box">{token}</div>
        <div>
          <a href="{settings.FRONTEND_URL}/verify?token={token}" class="btn">Verify Account</a>
        </div>
        <p class="footer">If you didn't create an account, you can safely ignore this email.</p>
      </div>
    </body>
    </html>
    """
    
    msg.set_content(f"Your verification token is: {token}\n\nVisit {settings.FRONTEND_URL}/verify?token={token} to verify your account.")
    msg.add_alternative(html_content, subtype='html')
    msg["Subject"] = "Verify Your Rummikub Assistant Account"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, getattr(settings, 'SMTP_PORT', 465)) as server:
            if hasattr(settings, 'GMAIL_RUMMIKUB_EMAIL_ADDRESS') and settings.GMAIL_RUMMIKUB_EMAIL_ADDRESS:
                server.login(settings.GMAIL_RUMMIKUB_EMAIL_ADDRESS, settings.GMAIL_RUMMIKUB_APP_PASSWORD)
            server.send_message(msg)
        logger.info(f"Sent verification email to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
