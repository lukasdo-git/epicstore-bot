from epicstore_api import EpicGamesStoreAPI
import json
import discord
from discord.ext import tasks

def onChange():
    f = open("free_games.json", "r")
    free_games_old = json.loads(f.read())
    f.close()

    api = EpicGamesStoreAPI()
    free_games_new = api.get_free_games()['data']['Catalog']['searchStore']['elements']

    if free_games_new != free_games_old:
        with open("free_games.json", "w") as f:
            json_obj = json.dumps(free_games_new, indent=4)
            f.write(json_obj)
        print("Found new games! Updating free_games.json")
        return True
    else:
        print("No new games found :(")
        return False

def loadConfig():
    f = open("bot_conf.json", "r")
    config = json.loads(f.read())
    f.close()
    return config

def loadGamesList(file):
    f = open(file, "r")
    gamelist = json.loads(f.read())
    f.close()
    return gamelist

def createMessage(*gamelist):
    message = [">>> Aktualna lista darmowych gier na Epic Games Store: \n\n"]
    for game in gamelist:
        message += game[0]['title'] + f" | https://store.epicgames.com/pl/p/{game[0]['productSlug']}" +"\n"
    return ''.join(message)

if __name__ == "__main__":
    config = loadConfig()
    client = discord.Client(intents=discord.Intents.all())
    bot_token = config[0]["BOT_TOKEN"]


    @tasks.loop(seconds=10)  # repeat after every 10 seconds
    async def myLoop():
        if onChange():
            gamelist = loadGamesList("free_games.json")
            message = createMessage(gamelist)

            channel = client.get_channel(1032760359766986834)
            await channel.send(message)

    @client.event
    async def on_ready():
        await client.change_presence(status=discord.Status.online)
        print(f'We have logged in as {client.user}')
        await myLoop.start()


    client.run(bot_token)