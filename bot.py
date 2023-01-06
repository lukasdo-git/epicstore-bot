from epicstore_api import EpicGamesStoreAPI
import json
import discord
import dictdiffer
from operator import length_hint
from discord.ext import tasks, commands
from datetime import datetime

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

        #Debugging - todo!

        print("\nFound new games! Updating free_games.json")
        return True
    else:
        print("No new games found :(")
        return False

def loadConfig():
    f = open("bot_conf.json", "r")
    config = json.loads(f.read())
    f.close()
    return config

def loadChannels():
    f = open("channels.json", "r")
    channels = json.loads(f.read())
    f.close()
    return channels

def loadGamesList(file):
    f = open(file, "r")
    gamelist = json.loads(f.read())
    f.close()
    return gamelist

def createMessage(*gamelist):
    message = [">>> Current free-to-take games on Epic Games Store: \n\n"]
    game_no = 0
    try:
        while game_no <= len(gamelist)+10:
            for game in gamelist:
                if game[game_no]['title'] != "Mystery Game":
                    if game and game[game_no]['price']['totalPrice']['discountPrice'] == 0 and game[game_no]['promotions'] is not None:
                        if game[game_no]['productSlug'] is not None:
                            message += game[game_no]['title'] + f" | https://store.epicgames.com/en/p/{game[game_no]['productSlug']}" + "\n"
                        else:
                            message += game[game_no]['title'] + " | Unfortunately the API link is broken. Please go to the EGStore to claim the game. \n"
                game_no += 1
            print(''.join(message))
        return ''.join(message)
    except:
        return ''.join(message)

if __name__ == "__main__":
    config = loadConfig()
    client = commands.Bot(command_prefix="e!", intents=discord.Intents.all())
    bot_token = config[0]["BOT_TOKEN"]
    subscribed_channels = dict(loadChannels())


    @tasks.loop(seconds=10)  # repeat after every 10 seconds
    async def myLoop():
        if onChange():
            for channels in subscribed_channels:
                gamelist = loadGamesList("free_games.json")
                message = createMessage(gamelist)

                channel = client.get_channel(int(subscribed_channels[channels]))
                await channel.send(message)

    @client.event
    async def on_ready():
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name="e!helpme"))
        print(f'We have logged in as {client.user}')
        await myLoop.start()

    @client.event
    async def on_guild_join(guild):
        if guild.system_channel:
            embed = discord.Embed(
                title="Welcome!",
                description=f"Thank you for letting me be a part of {guild.name}!",
                color=0x67e6ca
            )
            embed.add_field(name="My purpose", value="I'm a simple bot, thats supposed to tell you, when new games become free-to-take on Epic Games Store", inline=False)
            embed.add_field(name="Set a channel!", value="If you want to change the channel which recieves automatic updates, please type e!setch <channelID>", inline=True)
            embed.add_field(name="Channel ID", value="To obtain a channel's ID you need to enable Developer View in Discord settings. Then right click on a channel, and select \"Copy ID\"", inline=True)
            embed.add_field(name="Default", value="If no channel ID is set, then the system channel set in server settings will be used!", inline=False)
            supported_commands = '''e!helpme - shows this message
            e!list - sends current free-to-take games [Administrator]
            e!list me - dm's the current list to you
            e!setch <channelId> - explained above [Administrator]'''
            embed.add_field(name="Supported commands", value=supported_commands)
            await guild.system_channel.send(embed=embed)
            subscribed_channels.update({str(guild.id): int(guild.system_channel.id)})
            with open("channels.json", "w+") as f:
                jsona = json.dumps(subscribed_channels, indent=4)
                f.write(jsona)

    @client.group()
    async def lista(ctx):
        if ctx.invoked_subcommand is None:
            if ctx.message.author.guild_permissions.administrator or ctx.message.author.id == client.owner_id:
                gamelist = loadGamesList("free_games.json")
                message = createMessage(gamelist)
                await ctx.send(message)

    @lista.command()
    async def me(ctx):
        gamelist = loadGamesList("free_games.json")
        message = createMessage(gamelist)
        await ctx.message.author.send(message)

    @client.command()
    async def helpme(ctx):
        embed = discord.Embed(
            title="Welcome!",
            description=f"Thank you for letting me be a part of {ctx.guild.name}!",
            color=0x67e6ca
        )
        embed.add_field(name="My purpose",
                        value="I'm a simple bot, thats supposed to tell you, when new games become free-to-take on Epic Games Store",
                        inline=False)
        embed.add_field(name="Set a channel!",
                        value="If you want to change the channel which recieves automatic updates, please type e!setch <channelID>",
                        inline=True)
        embed.add_field(name="Channel ID",
                        value="To obtain a channel's ID you need to enable Developer View in Discord settings. Then right click on a channel, and select \"Copy ID\"",
                        inline=True)
        embed.add_field(name="Default",
                        value="If no channel ID is set, then the system channel set in server settings will be used!",
                        inline=False)
        supported_commands = '''e!helpme - shows this message
                    e!list - sends current free-to-take games [Administrator]
                    e!list me - dm's the current list to you
                    e!setch <channelId> - explained above [Administrator]'''
        embed.add_field(name="Supported commands", value=supported_commands)
        await ctx.send(embed=embed)

    @client.command()
    async def setch(ctx, *, channel_id):
        if ctx.message.author.guild_permissions.administrator:
            guild_id = ctx.guild.id
            subscribed_channels.update({str(guild_id): int(channel_id)})
            print(subscribed_channels)
            try:
                with open("channels.json", "w+") as f:
                    jsonb = json.dumps(subscribed_channels, indent=4)
                    f.write(jsonb)
                embed = discord.Embed(
                    title="Channel ID set!",
                    description=f"Correctly set channel ID to {channel_id}",
                    color=0x12cc12
                )
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(
                    title="Oops!",
                    description="Something went wrong when setting Channel ID :(",
                    color=0xcc1212
                )
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No permissions!",
                description=f"You cannot set the channel id! You're not an administrator!",
                color=0xcc1212
            )
            await ctx.send(embed=embed)


    client.run(bot_token, reconnect=True)