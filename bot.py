import json
import re
import cloudscraper
import requests

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_futbin_price(url):
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"Błąd HTTP {response.status_code} dla {url}")
            return None
        
        html = response.text
        
        # Uproszczone wyszukiwanie ceny w kodzie strony
        match = re.search(r'"ps_price"\s*:\s*"([0-9,]+)"', html, re.IGNORECASE)
        if not match:
            match = re.search(r'"ps"\s*:\s*"?([0-9]+)"?', html, re.IGNORECASE)
                
        if match:
            clean_price = match.group(1).replace(',', '').replace('.', '')
            return int(clean_price)
    except Exception as e:
        print(f"Błąd pobierania {url}: {e}")
    return None

def send_discord_alert(webhook_url, player_name, price, max_price):
    payload = {
        "content": f"🚨 **OKAZJA! KUP: {player_name}** za **{price:,}** (Twój limit: {max_price:,})\n🔥 **Cena spadła poniżej limitu – wskakuj do gry!**"
    }
    try:
        requests.post(webhook_url, json=payload)
    except Exception as e:
        print(f"Błąd wysyłania Discord webhook: {e}")

def main():
    config = load_config()
    requests.post(config.get("webhook_url"), json={"content": "🚨 TESTOWA WIADOMOŚĆ Z BOTA!"})
    webhook_url = config.get("webhook_url")
    
    for player in config.get("players", []):
        name = player["name"]
        url = player["url"]
        max_price = player["max_price"]
        
        print(f"Sprawdzam cenę: {name}...")
        current_price = get_futbin_price(url)
        
        if current_price:
            print(f"Aktualna cena {name}: {current_price:,} (Limit: {max_price:,})")
            if current_price <= max_price:
                if not player.get("alert_active", False):
                    send_discord_alert(webhook_url, name, current_price, max_price)
                    player["alert_active"] = True
            else:
                player["alert_active"] = False
        else:
            print(f"Nie udało się odczytać ceny dla {name}")
            
    save_config(config)

if __name__ == "__main__":
    main()
