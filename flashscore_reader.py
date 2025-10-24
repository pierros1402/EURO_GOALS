# ==============================================
# FLASHSCORE READER – Live Odds Scraper (Clean v2)
# ==============================================
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_flashscore_odds():
    """
    Παίρνει αποδόσεις (1X2) από Flashscore live feed.
    Προσοχή: χρησιμοποιεί scraping, όχι API.
    """
    try:
        url = "https://www.flashscore.com/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        matches = []
        live_blocks = soup.select(".event__match.event__match--live")

        for block in live_blocks:
            try:
                league_tag = block.find_previous("div", class_="event__titleBox")
                league = league_tag.text.strip() if league_tag else "Unknown League"

                home = block.select_one(".event__participant--home").text.strip()
                away = block.select_one(".event__participant--away").text.strip()
                score_home = block.select_one(".event__score--home").text.strip()
                score_away = block.select_one(".event__score--away").text.strip()

                matches.append({
                    "league": league,
                    "home": f"{home} ({score_home})",
                    "away": f"{away} ({score_away})",
                    "odds": "-",  # Placeholder, μπορεί να επεκταθεί
                    "source": "Flashscore",
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
            except Exception:
                continue

        print(f"[FLASHSCORE] ✅ Scraped {len(matches)} live matches.")
        return matches

    except Exception as e:
        print(f"[FLASHSCORE] ❌ Error scraping Flashscore: {e}")
        return []
