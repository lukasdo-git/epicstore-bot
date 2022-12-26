from epicstore_api import EpicGamesStoreAPI
import json
import discord
from discord.ext import tasks, commands

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
    for game in gamelist:
        message += game[0]['title'] + f" | https://store.epicgames.com/en/p/{game[0]['productSlug']}" +"\n"
    return ''.join(message)

if __name__ == "__main__":
    config = loadConfig()
    #client = discord.Client(intents=discord.Intents.all())
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
        await client.change_presence(status=discord.Status.online, activity=discord.Game(name="!help"))
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
            embed.add_field(name="Set a channel!", value="If you want to change the channel which recieves automatic updates, please type !setch <channelID>", inline=True)
            embed.add_field(name="Channel ID", value="To obtain a channel's ID right click on it, and select \"Copy ID\"", inline=True)
            embed.add_field(name="Default", value="If no channel ID is set, then the system channel set in server settings will be used!", inline=False)
            supported_commands = '''e!helpme - shows this message
            e!list - shows current free-to-take games
            e!setch <channelId> - explained above'''
            embed.add_field(name="Supported commands", value=supported_commands)
            await guild.system_channel.send(embed=embed)
            subscribed_channels.update({str(guild.id): int(guild.system_channel.id)})
            with open("channels.json", "w+") as f:
                jsona = json.dumps(subscribed_channels, indent=4)
                f.write(jsona)

    @client.command()
    async def list(ctx):
        gamelist = loadGamesList("free_games.json")
        message = createMessage(gamelist)
        await ctx.send(message)

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
                        value="If you want to change the channel which recieves automatic updates, please type !setch <channelID>",
                        inline=True)
        embed.add_field(name="Channel ID", value="To obtain a channel's ID right click on it, and select \"Copy ID\"",
                        inline=True)
        embed.add_field(name="Default",
                        value="If no channel ID is set, then the system channel set in server settings will be used!",
                        inline=False)
        supported_commands = '''e!helpme - shows this message
                    e!list - shows current free-to-take games
                    e!setch <channelId> - explained above'''
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


    client.run(bot_token)