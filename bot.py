import json
import re
import cloudscraper
import requests

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_player_price(player_url):
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.futbin.com/"
    }
    
    try:
        response = scraper.get(player_url, headers=headers, timeout=15)
        print(f"Status HTTP dla {player_url}: {response.status_code}")
        if response.status_code == 200:
            match = re.search(r'id="(?:ps-price|xbox-price|pc-price)"[^>]*>\s*([\d,.]+)\s*<', response.text)
            if match:
                raw_price = match.group(1).replace(',', '').replace('.', '').strip()
                print(f"Znaleziono cenę (regex): {raw_price}")
                if raw_price.isdigit():
                    return int(raw_price)
            
            match_json = re.search(r'"LCPrice":\s*(\d+)', response.text)
            if match_json:
                print(f"Znaleziono cenę (JSON): {match_json.group(1)}")
                return int(match_json.group(1))
                
            print("Ostrzeżenie: Strona się załadowała, ale nie dopasowano wzorca ceny w HTML.")
    except Exception as e:
        print(f"Błąd wyjątku dla {player_url}: {e}")
        
    return None

def main():
    config = load_config()
    webhook_url = config.get("webhook_url")
    
    print("Rozpoczynam sprawdzanie cen zawodników...")
    
    for player in config.get("players", []):
        name = player.get("name")
        url = player.get("url")
        max_price = player.get("max_price")
        alert_active = player.get("alert_active", False)
        
        print(f"Sprawdzam: {name} (Limit: {max_price})")
        current_price = get_player_price(url)
        
        if current_price is None:
            print(f"Nie udało się odczytać ceny dla {name}.")
            continue
            
        print(f"Aktualna cena {name}: {current_price}")
        
        if current_price <= max_price:
            if not alert_active:
                message = {
                    "content": f"🚨 **OKAZJA CENOWA!** 🚨\nZawodnik: **{name}**\nAktualna cena: **{current_price:,}** (Twój limit: **{max_price:,}**)\nLink: {url}"
                }
                requests.post(webhook_url, json=message)
                player["alert_active"] = True
                print(f"Wysłano powiadomienie dla {name}!")
        else:
            if alert_active:
                player["alert_active"] = False
                print(f"Cena {name} wzrosła ponad limit. Resetuję flagę alertu.")

    save_config(config)

if __name__ == "__main__":
    main()
