import requests
import schedule
import time
from atproto import Client

# URL da API de quotes
QUOTE_API_URL = "https://dummyjson.com/quotes/random"

def get_random_quote():
    # Fazendo a requisição à API para obter uma citação aleatória
    response = requests.get(QUOTE_API_URL)
    if response.status_code == 200:
        data = response.json()
        return f'"{data["quote"]}" - {data["author"]}'
    else:
        print("Erro ao obter a citação.")
        return None

def post_quote_to_bluesky(client: Client):
    quote = get_random_quote()
    if quote:
        # Postando a citação como um novo post
        client.send_post(text=quote)
        print(f"Postado com sucesso: {quote}")
    else:
        print("Não foi possível postar a citação.")

def job():
    client = Client()
    client.login('quote-of-the-day.bsky.social', 'jW28RdPB4dndKHa')
    post_quote_to_bluesky(client)

if __name__ == '__main__':
    # Agendar o post para todos os dias às 7 da manhã
    schedule.every().day.at("10:00").do(job)

    # Loop para manter o agendador rodando
    while True:
        schedule.run_pending()  # Executa as tarefas agendadas quando necessário
        time.sleep(60)  # Verifica a cada minuto

