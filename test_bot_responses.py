import sys
sys.path.insert(0, 'AI-CHATBOT')

from whatsapp.message_handler import process_message

print("=" * 60)
print("  TESTING BOT RESPONSES")
print("=" * 60)

test_phone = "+923001234567"

tests = [
    ("hi", "Main menu"),
    ("1", "Stock check"),
    ("order Product A 50", "Order creation"),
    ("3", "Price finder"),
    ("product a", "Price lookup"),
    ("4", "Transactions"),
]

for msg, desc in tests:
    print(f"\n[TEST] {desc}")
    print(f"Input: '{msg}'")
    response = process_message(test_phone, msg)
    print(f"Output: {response[:100]}...")
    print("[OK]" if len(response) > 0 else "[FAIL]")

print("\n" + "=" * 60)
print("  ALL TESTS COMPLETED")
print("=" * 60)
