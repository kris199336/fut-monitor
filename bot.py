import json
import requests

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_player_price(player_url):
    try:
        # Wyciągamy ID gracza z linku futbin (np. /27/player/23168/...)
        parts = player_url.strip("/").split("/")
        if "player" in parts:
            player_id_index = parts.index("player") + 1
            if player_id_index < len(parts):
                player_id = parts[player_id_index]
                
                # Oficjalny endpoint API Futbin dla cen PS
                api_url = f"https://www.futbin.com/27/playerPrices?player={player_id}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": player_url
                }
                
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Sprawdzamy dane dla konkretnego ID
                    if player_id in data:
                        prices = data[player_id].get("prices", {})
                        # Pobieramy cenę z PS (lub alternatywnych platform)
                        ps_price = prices.get("PS", {}).get("S")
                        if ps_price:
                            return int(str(ps_price).replace(",", ""))
    except Exception as e:
        print(f"Błąd podczas pobierania ceny dla {player_url}: {e}")
        
    return None

def main():
    config = load_config()
    webhook_url = config.get("webhook_url")
    
    print("Rozpoczynam sprawdzanie cen zawodników via API Futbin...")
    
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
    # Zapisz zaktualizowany stan flag do config.json
    save_config(config)

if __name__ == "__main__":
    main()
