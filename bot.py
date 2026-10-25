import json
import requests
from bs4 import BeautifulSoup
import cloudscraper

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_player_price(url):
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"Błąd pobierania strony {url}, status: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Próba znalezienia ceny na stronie Futbin (np. w elementach identyfikujących cenę PS/Xbox/PC)
        # Futbin często trzyma cenę w określonych tagi ID lub klasach
        price_element = soup.find(id="ps-price") or soup.find(id="xbox-price") or soup.find(id="pc-price")
        if price_element:
            price_text = price_element.text.replace(',', '').replace('.', '').strip()
            return int(price_text)
            
        # Alternatywne szukanie po klasach lub tekście w razie zmian układu strony
        # (można rozwinąć w razie potrzeby)
        
    except Exception as e:
        print(f"Wyjątek podczas pobierania ceny dla {url}: {e}")
    
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
            print(f"Nie udało się pobrać ceny dla {name}.")
            continue
            
        print(f"Aktualna cena {name}: {current_price}")
        
        # Warunek: cena jest niższa lub równa limitowi
        if current_price <= max_price:
            if not alert_active:
                # Wyślij powiadomienie na Discord
                message = {
                    "content": f"🚨 **OKAZJA CENOWA!** 🚨\nZawodnik: **{name}**\nAktualna cena: **{current_price:,}** (Twój limit: **{max_price:,}**)\nLink: {url}"
                }
                requests.post(webhook_url, json=message)
                player["alert_active"] = True
                print(f"Wysłano powiadomienie dla {name}!")
        else:
            # Jeśli cena wzrosła powyżej limitu, resetujemy flagę, żeby bot znów powiadomił, gdy spadnie
            if alert_active:
                player["alert_active"] = False
                print(f"Cena {name} wzrosła ponad limit. Resetuję flagę alertu.")

    # Zapisz zaktualizowany stan flag do config.json
    save_config(config)

if __name__ == "__main__":
    main()
