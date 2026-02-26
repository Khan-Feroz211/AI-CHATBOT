.PHONY: run-whatsapp-bot tunnel

run-whatsapp-bot:
	FLASK_APP=whatsapp_bot.app flask run --host=0.0.0.0 --port=5000

tunnel:
	ngrok http 5000
