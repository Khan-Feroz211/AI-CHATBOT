# WhatsApp Quick Connect

## Twilio (5 steps)
1. Create a Twilio account and enable WhatsApp Sandbox or approved WhatsApp sender.
2. Fill `.env` with `WHATSAPP_PROVIDER=twilio`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`.
3. Deploy the app and copy your public URL.
4. In Twilio WhatsApp configuration, set webhook URL to `https://YOUR-DEPLOYED-URL/webhook`.
5. Send a test WhatsApp message to your Twilio number and confirm your app logs the webhook.

## Meta Cloud API (5 steps)
1. Create a Meta app and add WhatsApp product in Meta Developer Console.
2. Fill `.env` with `WHATSAPP_PROVIDER=meta`, `META_ACCESS_TOKEN`, `META_PHONE_NUMBER_ID`, `META_WEBHOOK_VERIFY_TOKEN`.
3. Deploy the app and copy your public URL.
4. In Meta webhook configuration, set callback URL to `https://YOUR-DEPLOYED-URL/webhook` and verify token.
5. Send a test WhatsApp message from an allowed number and confirm webhook event is received.

## Webhook URL Format
`https://YOUR-DEPLOYED-URL/webhook`

## Verify Webhook Works
1. Send a test message from WhatsApp.
2. Check app logs for inbound payload.
3. Confirm HTTP 200 response returned by webhook handler.

## Common Errors
- `403 webhook verify failed`: verify token mismatch between `.env` and provider console.
- `401 unauthorized`: invalid/expired access token.
- `404 webhook`: wrong callback path; use `/webhook` exactly.
- No incoming events: provider app is not subscribed to message events.
