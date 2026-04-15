"""WhatsApp menu strings for BazaarBot."""


def get_main_menu(business_name: str = "BazaarBot") -> str:
    return (
        f"🛒 *{business_name}*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Aapka swagat hai! 🇵🇰\n\n"
        "1️⃣  Mera Stock (Inventory)\n"
        "2️⃣  Naya Order Lein\n"
        "3️⃣  Market Finder / Supplier\n"
        "4️⃣  Payment Info (EasyPaisa/JazzCash)\n"
        "5️⃣  Appointment Book Karein\n"
        "6️⃣  Meri History (Orders)\n"
        "7️⃣  Madad (Help)\n\n"
        "Number likhein ya apna sawaal karein!"
    )


def get_payment_menu(tenant: dict) -> str:
    ep = (tenant or {}).get("easypaisa_number", "")
    jc = (tenant or {}).get("jazzcash_number", "")
    iban = (tenant or {}).get("bank_iban", "")
    bank = (tenant or {}).get("bank_title", "")
    lines = [
        "💰 *Payment Methods*",
        "━━━━━━━━━━━━━━━━━━",
    ]
    if ep:
        lines.append(f"📱 *EasyPaisa:* {ep}")
    if jc:
        lines.append(f"📱 *JazzCash:* {jc}")
    if iban:
        lines.append(f"🏦 *Bank Transfer ({bank}):*\nIBAN: {iban}")
    if not ep and not jc and not iban:
        lines += [
            "⚠️ Payment info abhi configure nahi hui.",
            "Admin se rabita karein ya web dashboard pe update karein.",
        ]
    lines += [
        "━━━━━━━━━━━━━━━━━━",
        "Payment ke baad screenshot bhejein aur order ref mention karein.",
    ]
    return "\n".join(lines)
