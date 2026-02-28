import pyotp
import qrcode
import os

# In-memory user store (replace with DB in production)
_users = {}

def get_or_create_user(from_number):
    if from_number not in _users:
        _users[from_number] = {
            "mfa_secret": None,
            "mfa_verified": False,
            "authenticated": False
        }
    return type("User", (), _users[from_number])()

def generate_totp_secret():
    return pyotp.random_base32()

def save_user_secret(from_number, secret):
    _users.setdefault(from_number, {})
    _users[from_number]["mfa_secret"] = secret
    _users[from_number]["mfa_verified"] = False
    _users[from_number]["authenticated"] = False

def generate_qr_code(secret, from_number):
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=from_number, issuer_name="AI Business Bot")
    qr = qrcode.make(uri)
    path = f"qr_{from_number.replace('+', '')}.png"
    qr.save(path)
    return path

def verify_totp(secret, code):
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def mark_authenticated(from_number):
    _users.setdefault(from_number, {})
    _users[from_number]["mfa_verified"] = True
    _users[from_number]["authenticated"] = True

def is_user_authenticated(from_number):
    user = _users.get(from_number, {})
    return user.get("authenticated", False)

def handle_mfa_flow(from_number, message):
    try:
        user = get_or_create_user(from_number)

        if not user.mfa_secret:
            secret = generate_totp_secret()
            save_user_secret(from_number, secret)
            generate_qr_code(secret, from_number)
            return (
                "🔐 *Welcome to AI Business Bot!*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Your account is being secured.\n\n"
                "📱 Please scan the QR code with:\n"
                "• Microsoft Authenticator\n"
                "• Oracle Authenticator\n\n"
                "Then reply with the *6-digit code* shown in your app."
            )

        elif not user.mfa_verified:
            if message.isdigit() and len(message) == 6:
                if verify_totp(user.mfa_secret, message):
                    mark_authenticated(from_number)
                    from whatsapp.menu import get_main_menu
                    return (
                        "✅ *Authentication Successful!*\n"
                        "━━━━━━━━━━━━━━━━━━\n"
                        "Welcome aboard! 🎉\n\n"
                        + get_main_menu()
                    )
                else:
                    return (
                        "❌ Invalid code. Please try again.\n"
                        "Open your authenticator app and enter the current 6-digit code."
                    )
            else:
                return "Please reply with the *6-digit code* from your authenticator app."

    except Exception as e:
        print(f"❌ MFA error: {e}")
        return "Authentication error. Please try again by sending *hi*."
