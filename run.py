from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from whatsapp.message_handler import process_message
import os
import traceback

app = Flask(__name__)

# Environment-based validation (disabled by default for demo)
VALIDATE_TWILIO = os.environ.get("VALIDATE_TWILIO", "false").lower() == "true"

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    """Twilio WhatsApp webhook - MUST return TwiML format."""
    if request.method == "GET":
        return "OK", 200
    
    try:
        # Get incoming message details
        incoming_msg = request.form.get("Body", "").strip()
        from_number = request.form.get("From", "").replace("whatsapp:", "")
        
        # Sanitize input
        if len(incoming_msg) > 1000:
            incoming_msg = incoming_msg[:1000]
        
        print(f"📨 Received: '{incoming_msg}' from {from_number}")
        
        # Process message
        response_text = process_message(from_number, incoming_msg.lower())
        
        print(f"📤 Sending: '{response_text[:50]}...'")
        
        # CRITICAL: Must return TwiML format with correct Content-Type
        resp = MessagingResponse()
        msg = resp.message()
        msg.body(response_text)
        
        return str(resp), 200, {"Content-Type": "text/xml"}
    
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message("Sorry, technical issue. Type *menu* to continue.")
        return str(resp), 200, {"Content-Type": "text/xml"}

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return {"status": "ok", "bot": "ready", "version": "1.0.0"}, 200

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting WhatsApp Bot on port {PORT}...")
    print(f"📍 Webhook URL: http://localhost:{PORT}/webhook")
    print(f"💚 Health check: http://localhost:{PORT}/health")
    app.run(host="0.0.0.0", port=PORT, debug=True)
