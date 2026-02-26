"""QR code generation for MFA setup."""

import base64
import io
import logging
import os
from datetime import datetime

import qrcode
from PIL import Image, ImageDraw, ImageFont

from src.auth.mfa import TOTPEncryption, TOTPManager

logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Generate QR codes for authenticator setup."""

    # QR Code configuration
    QR_VERSION = 1  # Auto-determine size
    ERROR_CORRECTION = qrcode.constants.ERROR_CORRECT_H  # High error correction
    BOX_SIZE = 10  # pixels per box
    BORDER = 2  # white boxes

    @staticmethod
    def generate_totp_qr(
        secret: str, account_name: str, issuer: str = "WhatsApp Inventory Bot"
    ) -> Image.Image:
        """Generate QR code for TOTP setup.

        Creates a QR code with otpauth:// URI compatible with:
        - Microsoft Authenticator
        - Google Authenticator
        - Authy
        - Oracle Mobile Authenticator

        Args:
            secret: TOTP secret key
            account_name: Account identifier (email or phone)
            issuer: Issuer name (app/company name)

        Returns:
            PIL Image object
        """
        totp_manager = TOTPManager()
        uri = totp_manager.get_totp_uri(secret, account_name, issuer)

        # Create QR code
        qr = qrcode.QRCode(
            version=QRCodeGenerator.QR_VERSION,
            error_correction=QRCodeGenerator.ERROR_CORRECTION,
            box_size=QRCodeGenerator.BOX_SIZE,
            border=QRCodeGenerator.BORDER,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        logger.info(f"Generated TOTP QR code for {account_name}")
        return img

    @staticmethod
    def generate_microsoft_authenticator_qr(
        secret: str, phone_number: str
    ) -> Image.Image:
        """Generate QR code optimized for Microsoft Authenticator.

        Microsoft Authenticator displays:
        - Issuer name
        - Account name/email
        - 6-digit code with timer

        Args:
            secret: TOTP secret
            phone_number: User's phone number

        Returns:
            PIL Image object
        """
        # Use company name as it appears in Microsoft Authenticator
        issuer = os.getenv("COMPANY_NAME", "WhatsApp Inventory Bot")

        return QRCodeGenerator.generate_totp_qr(secret, phone_number, issuer)

    @staticmethod
    def generate_oracle_authenticator_qr(secret: str, phone_number: str) -> Image.Image:
        """Generate QR code optimized for Oracle Mobile Authenticator.

        Oracle Authenticator also uses TOTP (RFC 6238).

        Args:
            secret: TOTP secret
            phone_number: User's phone number

        Returns:
            PIL Image object
        """
        # Oracle Authenticator displays issuer name
        issuer = "Oracle Mobile Authenticator"

        return QRCodeGenerator.generate_totp_qr(secret, phone_number, issuer)

    @staticmethod
    def add_label_to_qr(
        qr_image: Image.Image, label: str, font_size: int = 20
    ) -> Image.Image:
        """Add text label below QR code.

        Useful for indicating which authenticator the QR is for.

        Args:
            qr_image: PIL Image of QR code
            label: Text to add below QR code
            font_size: Font size in pixels

        Returns:
            PIL Image with label
        """
        # Create new image with space for label
        label_height = font_size + 20
        new_image = Image.new(
            "RGB", (qr_image.width, qr_image.height + label_height), color="white"
        )

        # Paste QR code
        new_image.paste(qr_image, (0, 0))

        # Add label text
        draw = ImageDraw.Draw(new_image)
        try:
            # Try to use a nice font, fallback to default
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Draw text centered
        text_bbox = draw.textbbox((0, 0), label)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (new_image.width - text_width) // 2
        text_y = qr_image.height + 10

        draw.text((text_x, text_y), label, fill="black", font=font)

        logger.info(f"Added label to QR code: {label}")
        return new_image

    @staticmethod
    def generate_branded_qr(
        secret: str, phone_number: str, authenticator_type: str
    ) -> Image.Image:
        """Generate branded QR code with labels.

        Args:
            secret: TOTP secret
            phone_number: User's phone
            authenticator_type: 'microsoft' or 'oracle'

        Returns:
            PIL Image with branding
        """
        if authenticator_type.lower() == "microsoft":
            qr_img = QRCodeGenerator.generate_microsoft_authenticator_qr(
                secret, phone_number
            )
            label = "Scan with Microsoft Authenticator"
        elif authenticator_type.lower() == "oracle":
            qr_img = QRCodeGenerator.generate_oracle_authenticator_qr(
                secret, phone_number
            )
            label = "Scan with Oracle Mobile Authenticator"
        else:
            qr_img = QRCodeGenerator.generate_totp_qr(secret, phone_number)
            label = f"Scan with {authenticator_type}"

        return QRCodeGenerator.add_label_to_qr(qr_img, label)

    @staticmethod
    def image_to_base64(image: Image.Image) -> str:
        """Convert PIL Image to base64-encoded string.

        Useful for sending via WhatsApp or storing in database.

        Args:
            image: PIL Image object

        Returns:
            Base64-encoded string
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        b64_string = base64.b64encode(buffer.getvalue()).decode()
        return b64_string

    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
        """Convert PIL Image to bytes.

        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Image as bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    @staticmethod
    def save_qr_to_file(
        image: Image.Image, filename: str, directory: str = "data/qr_codes"
    ) -> str:
        """Save QR code image to file.

        Args:
            image: PIL Image object
            filename: Filename (without extension)
            directory: Directory to save in

        Returns:
            Full path to saved file
        """
        os.makedirs(directory, exist_ok=True)

        filepath = os.path.join(directory, f"{filename}.png")
        image.save(filepath, format="PNG")

        logger.info(f"Saved QR code to {filepath}")
        return filepath

    @staticmethod
    def generate_setup_instructions(authenticator_type: str) -> str:
        """Generate setup instructions for user.

        Args:
            authenticator_type: 'microsoft' or 'oracle'

        Returns:
            Instruction text for WhatsApp
        """
        if authenticator_type.lower() == "microsoft":
            return """
📱 *Microsoft Authenticator Setup*

1️⃣ Download Microsoft Authenticator from your app store
2️⃣ Open the app
3️⃣ Tap the *Plus (+)* icon
4️⃣ Select *Add a work or school account*
5️⃣ Tap *Scan a QR code*
6️⃣ Point your camera at the QR code
7️⃣ Confirm the account details
8️⃣ Your 6-digit code will appear! ✓

📝 Save your backup codes in a safe place!
"""
        elif authenticator_type.lower() == "oracle":
            return """
📱 *Oracle Mobile Authenticator Setup*

1️⃣ Download Oracle Mobile Authenticator from your app store
2️⃣ Open the app
3️⃣ Tap the *Plus (+)* icon
4️⃣ Select *Scan QR Code*
5️⃣ Point your camera at the QR code
6️⃣ Accept to add the account
7️⃣ Your 6-digit code will appear! ✓

📝 Save your backup codes in a safe place!
"""
        else:
            return "Please scan this QR code with your authenticator app."


class WhatsAppQRSender:
    """Helper to send QR codes via WhatsApp."""

    @staticmethod
    def prepare_qr_for_whatsapp(image: Image.Image, max_size_kb: int = 100) -> bytes:
        """Prepare QR image for WhatsApp.

        WhatsApp supports PNG, JPEG up to 16 MB.
        This method optimizes the image.

        Args:
            image: PIL Image
            max_size_kb: Target max file size in KB

        Returns:
            Bytes ready to send
        """
        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)

        image_bytes = buffer.getvalue()

        # If too large, compress
        if len(image_bytes) > max_size_kb * 1024:
            buffer = io.BytesIO()
            # Reduce quality
            image_rgb = image.convert("RGB")
            image_rgb.save(buffer, format="JPEG", quality=85, optimize=True)
            image_bytes = buffer.getvalue()

        logger.info(f"Prepared QR for WhatsApp: {len(image_bytes)} bytes")
        return image_bytes

    @staticmethod
    def get_whatsapp_instructions(authenticator_type: str) -> str:
        """Get formatted WhatsApp instruction message.

        Args:
            authenticator_type: 'microsoft' or 'oracle'

        Returns:
            Formatted WhatsApp message
        """
        return QRCodeGenerator.generate_setup_instructions(authenticator_type)
