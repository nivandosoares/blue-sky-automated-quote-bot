import os
import requests
from atproto import Client, client_utils
from serpapi import GoogleSearch
import schedule
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")
USERNAME = os.getenv("BLUESKY_USERNAME")
PASSWORD = os.getenv("BLUESKY_PASSWORD")

# Parâmetros da SerpAPI para buscar as informações do time e notícias
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

def get_team_and_news_info():
    search = GoogleSearch(API_PARAMS)
    results = search.get_dict()

    print("Dados recebidos da API:", results)

    sports_results = results.get("sports_results", {})
    title = sports_results.get("title", "No team info available")
    ranking = sports_results.get("rankings", "No ranking available")
    games = sports_results.get("games", [])

    web_results = results.get("web_results", [])
    news = web_results[0] if web_results else None

    previous_games, next_games = [], []

    for game in games:
        teams = game.get("teams", [])
        if len(teams) >= 2:
            game_info = {
                "tournament": game.get("tournament", "Unknown Tournament"),
                "teams": f'{teams[0].get("name", "Unknown")} {teams[0].get("score", "--")} x {teams[1].get("score", "--")} {teams[1].get("name", "Unknown")}',
                "date": game.get("date", "Unknown Date"),
                "status": game.get("status", "Unknown Status"),
            }

            if game_info["status"].lower() == "fim":
                previous_games.append(game_info)
            else:
                next_games.append(game_info)

    return title, ranking, previous_games, next_games, news

def post_team_info_to_bluesky(client: Client):
    title, ranking, previous_games, next_games, news = get_team_and_news_info()

    posts = []

    post_text = f'⚽ {title}\n📈 Classificação: {ranking}'
    posts.append(post_text)

    if previous_games:
        post_text = "📅 Últimos jogos:\n"
        for game in previous_games[:3]:
            post_text += f'{game["tournament"]}: {game["teams"]} - {game["date"]}\n'
        posts.append(post_text)

    if next_games:
        post_text = "📅 Próximos jogos:\n"
        for game in next_games[:3]:
            post_text += f'{game["tournament"]}: {game["teams"]} - {game["date"]}\n\n'
        posts.append(post_text)

    rich_text = client_utils.TextBuilder()
    if news:
        news_title = news.get("title")
        news_link = news.get("link")
        news_thumbnail = news.get("thumbnail")
        news_source_image = news.get("source_image")
        rich_text.text('📰\n').link(news_title, news_link)
        if news_thumbnail:
            rich_text.image(news_thumbnail)
        if news_source_image:
            rich_text.text(f'\nFonte: ').image(news_source_image)
    else:
        rich_text.text('📰 **Nenhuma notícia recente encontrada.**')

    for post_text in posts:
        if post_text.strip():
            post_text = post_text[:300]
            try:
                text_builder = client_utils.TextBuilder().text(post_text)
                client.send_post(text=text_builder)
                print(f"Postado com sucesso: {post_text}")
            except Exception as e:
                print(f"Erro ao postar: {e}")

    try:
        client.send_post(rich_text)
        print("Notícia postada com sucesso!")
    except Exception as e:
        print(f"Erro ao postar notícia: {e}")

def job_post_team_info():
    client = Client()
    try:
        client.login(USERNAME, PASSWORD)
        post_team_info_to_bluesky(client)
    except Exception as e:
        print(f"Erro ao fazer login ou postar no Bluesky: {e}")

def schedule_jobs():
    schedule.every().thursday.at("22:00").do(job_post_team_info)
    schedule.every().sunday.at("22:00").do(job_post_team_info)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    post_team_info_to_bluesky(Client())