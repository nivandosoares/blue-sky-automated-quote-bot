import os
import json
from datetime import datetime
from atproto import Client, client_utils, models
from dotenv import load_dotenv
import time
import re
from serpapi import GoogleSearch
import schedule
load_dotenv()

API_KEY = os.getenv("SERPAPI_KEY")
USERNAME = os.getenv("BLUESKY_USERNAME")
PASSWORD = os.getenv("BLUESKY_PASSWORD")

API_PARAMS = {
    "api_key": API_KEY,
    "engine": "google",
     "q": "CR vasco da gama",
     "location": "Brazil",
     "google_domain": "google.com.br",
     "gl": "br",
     "hl": "pt",
     "no_cache": "true",
     "device": "mobile"
}
STANDINGS_PARAMS = {
    "api_key": API_KEY,
    "engine": "google",
     "q": "BRASILEIRÃO STANDINGS",
     "google_domain": "google.com.br",
     "no_cache": "true",
     "device": "mobile"
}
NEWS_PARAMS = {
    "api_key": API_KEY,
    "engine": "google",
     "q": "VASCO ÚLTIMAS NOTÍCIAS",
     "location_requested": "Brazil",
     "google_domain": "google.com.br",
     "no_cache": "true",
     "device": "desktop"
}
def fetch_teamdata_from_serpapi():
    search = GoogleSearch(API_PARAMS)
    results = search.get_dict()

    sports_results = results.get("sports_results", {})
    return {
        "sports_results": sports_results
    }

def fetch_standings_from_serpapi():
    search = GoogleSearch(API_PARAMS)
    results = search.get_dict()

    web_results = results.get("web_results", [])
    return {
        "web_results": web_results
    }
def fetch_news_from_serpapi():
    search = GoogleSearch(NEWS_PARAMS)
    results = search.get_dict()

    top_stories = results.get("top_stories", [])
    return {
        "top_stories": top_stories
    }

def fetch_standings_from_local_files():
    try:
        standings_file = 'standings.json'
        vasco_file = 'test.json'
        top_stories_file = 'news.json'
       
        if not os.path.exists(standings_file):
            print(f"Arquivo {standings_file} não encontrado.")
            return None
        
        if not os.path.exists(vasco_file):
            print(f"Arquivo {vasco_file} não encontrado.")
            return None
        
        if not os.path.exists(top_stories_file):
            print(f"Arquivo {top_stories_file} não encontrado.")
            return None
        

        with open(standings_file, 'r') as file:
            standings_data = json.load(file)
           
        with open(vasco_file, 'r') as file:
            vasco_data = json.load(file)

        with open(top_stories_file, 'r') as file:
            top_stories_data = json.load(file)
    
        league_standings = standings_data.get("sports_results", {}).get("league", {}).get("standings", [])

        return {
            "sports_results": vasco_data.get("sports_results", {}),
            "web_results": league_standings,
            "top_stories": top_stories_data.get("top_stories", [])
        }

    except Exception as e:
        print(f"Erro ao ler os arquivos JSON: {e}")
        return None

def get_team_and_news_info():
    results = fetch_teamdata_from_serpapi()
    standings_data = fetch_standings_from_local_files()
    if not results:
        print("Nenhum resultado encontrado.")
        return None, None, None, None, None, None, None, None
    
    sports_results = results.get("sports_results", {})
    title = sports_results.get("title", "No team info available")
    ranking = sports_results.get("rankings", "No ranking available")
    games = sports_results.get("games", [])
    league = {"standings": standings_data.get("web_results", [])}
    news = games[0] if games else None
    previous_games, next_games = [], []
    now = datetime.now()

    for game in games:
        teams = game.get("teams", [])
        if len(teams) >= 2:
            try:
                game_date = datetime.strptime(game.get("date", "Wed, Sep 11"), '%a, %b %d')
                game_date = game_date.replace(year=now.year)
            except ValueError:
                game_date = datetime(1900, 1, 1)  # Data inválida

            game_info = {
                "tournament": game.get("tournament", "Unknown Tournament"),
                "teams": f'{teams[0].get("name", "Unknown")} {teams[0].get("score", "--")} x {teams[1].get("score", "--")} {teams[1].get("name", "Unknown")}',
                "date": game.get("date", "Unknown Date"),
                "status": game.get("status", "Unknown Status"),
            }

            if game.get("status", "").lower() == "ft" or game_date < now:
                previous_games.append(game_info)
            else:
                next_games.append(game_info)

    standings = league.get("standings", [])
    table_info = []
    vasco_position = None

    for entry in standings:
        team = entry.get("team", {})
        team_name = team.get("name", "Unknown Team").lower().strip()
    
        if "vasco da gama" in team_name:
            vasco_position = entry.get("pos", "Unknown Position")
    
        table_info.append({
            "name": team.get("name", "Unknown Team"),
            "pos": entry.get("pos", "N/A"),
            "points": entry.get("pts", "0"),
            "form": " ".join(entry.get("last_5", [])),
            "matches": entry.get("mp", "0"),
            "wins": entry.get("w", "0"),
            "draws": entry.get("d", "0"),
            "losses": entry.get("l", "0"),
            "goals_for": entry.get("gf", "0"),
            "goals_against": entry.get("ga", "0"),
            "goal_difference": entry.get("gd", "0")
        })

    return title, ranking, previous_games, next_games, news, table_info, vasco_position

def split_text(text, max_length):
    """Divide o texto em partes menores, cada uma com até max_length caracteres."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def generate_table_summary(standings_data, next_games, previous_games):
    if not standings_data:
        print("Dados da tabela não disponíveis.")
        return []

    posts = []

    table_info = standings_data.get("standings", [])
    vasco_info = next((team for team in table_info if team["name"].lower() == "vasco da gama"), None)
    vasco_position = vasco_info["pos"] if vasco_info else "Desconhecido"

    if vasco_info:
        vasco_stats = {
            "games_played": vasco_info.get("matches", "--"),
            "wins": vasco_info.get("wins", "--"),
            "draws": vasco_info.get("draws", "--"),
            "losses": vasco_info.get("losses", "--"),
            "goals_for": vasco_info.get("goals_for", "--"),
            "goals_against": vasco_info.get("goals_against", "--"),
            "goal_difference": vasco_info.get("goal_difference", "--"),
            "points": vasco_info.get("points", "--"),
        }

        # Primeiro post - Atualização da Tabela
        post_1 = (
            f"📝 Atualização da Tabela (1/4)📊\n"
            f"Vasco está em {vasco_position}º lugar\n\n"
            f"Jogos: {vasco_stats['games_played']}\n"
            f"Vitórias: {vasco_stats['wins']}\n"
            f"Empates: {vasco_stats['draws']}\n"
            f"Derrotas: {vasco_stats['losses']}\n"
            f"Gols Feitos: {vasco_stats['goals_for']}\n"
            f"Gols Sofridos: {vasco_stats['goals_against']}\n"
            f"Saldo de Gols: {vasco_stats['goal_difference']}\n"
            f"Pontos: {vasco_stats['points']}\n"
        )
        posts.append(post_1)

        # Segundo post - Posição dos Times
        post_2 = "🔝 Posição dos principais times na tabela: (2/4)\n"
        for entry in table_info[:8]:
            team_name = entry['name']
            if "botafogo" in team_name.lower():
                team_name = "Bairro Futebol Clube"
            elif "flamengo" in team_name.lower():
                team_name = "Flacadela"
            elif "fluminense" in team_name.lower():
                team_name = "Tapetense FC"
            post_2 += f"{team_name} - {entry['points']} pts\n"
        posts.append(post_2)

        # Terceiro post - Próximos Jogos
        post_3 = "🔜 Próximos jogos do Colossal da colina (3/4):\n"
        for game in next_games:
            if "botafogo" in game['teams'].lower():
                game['teams'] = "Bairro Futebol Clube x Vasco da Gama"
            elif "flamengo" in game['teams'].lower():
                game['teams'] = "Flacadela x Vasco da Gama"
            elif "fluminense" in game['teams'].lower():
                game['teams'] = "Tapetense FC x Vasco da Gama"
            post_3 += f"{game['tournament']}: {game['teams']} - {game['date']}\n"
        posts.append(post_3)

        # Quarto post - Jogos Anteriores
        post_4 = "🔙 Jogos anteriores do Gigante:\n"
        for game in previous_games[:3]:
            if "botafogo" in game['teams'].lower():
                game['teams'] = "Bairro Futebol Clube x Vasco da Gama"
            elif "flamengo" in game['teams'].lower():
                game['teams'] = "Flacadela x Vasco da Gama"
            elif "fluminense" in game['teams'].lower():
                game['teams'] = "Tapetense FC x Vasco da Gama"
            post_4 += f"{game['tournament']}: {game['teams']} - {game['date']} \n"
        posts.append(post_4)

    return posts

def post_to_bluesky():
    client = Client()
    title, ranking, previous_games, next_games, news, table_info, vasco_position = get_team_and_news_info()
    client.login(USERNAME, PASSWORD)
    if title:
        print(f"Team: {title}, Ranking: {ranking}")
    
    posts = generate_table_summary({
        "standings": table_info
    }, next_games, previous_games)
    
    for post_text in reversed(posts):
        if post_text.strip():
            # Split the post into chunks of 300 characters
            chunks = [post_text[i:i+280] for i in range(0, len(post_text), 280)]
            for chunk in chunks:
                try:
                    text_builder = client_utils.TextBuilder().text(chunk)
                    client.send_post(text=text_builder)
                    print(f"Postado com sucesso: {chunk}")
                except Exception as e:
                    print(f"Erro ao postar: {e}")

def is_valid_url(url):
    """Check if the URL is valid."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def post_news_to_bluesky():
    client = Client()
    client.login(USERNAME, PASSWORD)
    top_stories = fetch_news_from_serpapi().get("top_stories", [])
    print(top_stories)

    for story in top_stories:
        title = story.get("title", "No title available")
        link = story.get("link", "No link available")
        image = story.get("image", "No image available")
        date = story.get("date", "No date available")
        source = story.get("source", "No source available")
        thumbnail = story.get("thumbnail", "No thumbnail available")
    
        try:
            text_builder = client_utils.TextBuilder()
            text_builder.tag(f"📰 {title}\n", 'atproto')
            text_builder.text(f"📅 {date}\n")
            if is_valid_url(link):
                text_builder.link(f"🔗 {link}\n", link)
            text_builder.text(f"📰 Fonte: {source}\n")
            if is_valid_url(thumbnail):
                text_builder.image(thumbnail)
            if is_valid_url(image):
                text_builder.link(f"📷 {image}\n", image)
    
            client.send_post(text=text_builder)
            print(f"Postado com sucesso: {text_builder}")
        except Exception as e:
            print(f"Erro ao postar: {e}")

def schedule_jobs():
    schedule.every().thursday.at("22:00").do(post_news_to_bluesky)
    schedule.every().sunday.at("22:00").do(post_to_bluesky)

    while True:
        schedule.run_pending()
        time.sleep(60)

   
if __name__ == "__main__":
    schedule_jobs()   
