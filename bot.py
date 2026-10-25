import requests
import json

def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    webhook_url = config.get("webhook_url")
    print(f"Testuję wysyłanie na webhook: {webhook_url}")
    
    payload = {
        "content": "🚨 **TESTOWY ALARM DISCORD** - Bot działa poprawnie!"
    }
    
    response = requests.post(webhook_url, json=payload)
    print, f"Status HTTP z Discorda: {response.status_code}"
    print(f"Odpowiedź Discorda: {response.text}")

if __name__ == "__main__":
    main()
