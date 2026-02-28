from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from whatsapp.message_handler import process_message

app = Flask(__name__)

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return "OK", 200
    try:
        incoming_msg = request.form.get("Body", "").strip().lower()
        from_number = request.form.get("From", "").replace("whatsapp:", "")

        print(f"📨 Message from {from_number}: {incoming_msg}")

        response = process_message(from_number, incoming_msg)

        resp = MessagingResponse()
        resp.message(response)
        return str(resp), 200
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, technical issue. Type *menu* to continue.")
        return str(resp), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
