# Imports
import Config
import discord
from discord.ext import commands, tasks
import logging
import random
import datetime
import importlib
import Utils
from EnchantedLogging import EnchantedLogging

if Config.testing:
    intents = discord.Intents.default()
    intents.members = True
    intents.presences = True

logging.basicConfig(level=logging.INFO, format="Enchanted [%(levelname)s] | %(message)s")

running_commands = 0


class UserInBlacklist(Exception):
    """Raised when a user is in the blacklist"""
    pass


async def get_prefix(bot, message):
    return commands.when_mentioned_or(Utils.fetch_prefix(message))(bot, message)


bot = commands.AutoShardedBot(command_prefix=get_prefix, case_insensitive=True)

bot.remove_command("help")

# Create Logging Method
Config.LOGGING = EnchantedLogging(bot, logging.INFO, "Enchanted `[{level}]` | {message}")

# Cogs
cogs = ["Eval", "Settings", "Profile", "Spells", "Matchmaking", "Chests", "Bosses", "Essentials", "Cosmetics",
        "Leaderboard", "Shop", "Inventory", "Clans", "Blacklist", "TopGG", "Code", "Dungeons", "Tournament"]
if Config.testing:
    cogs.remove("TopGG")

# Starts all cogs
for cog in cogs:
    bot.load_extension("Cogs." + cog)


# Check to see if the user invoking the command is in the OWNERIDS Config
def owner(ctx):
    return int(ctx.author.id) in Config.OWNERIDS


# Restarts and reloads all cogs
@bot.command(aliases=["retard"])
@commands.check(owner)
async def restart(ctx):
    """
    Restart the bot.
    """
    restarting = discord.Embed(
        title="Restarting...",
        color=Config.MAINCOLOR
    )
    msg = await ctx.send(embed=restarting)
    the_cogs = cogs
    if "TopGG" in the_cogs:
        the_cogs.remove("TopGG")
    for cog in the_cogs:
        bot.reload_extension("Cogs." + cog)
        restarting.add_field(name=f"{cog}", value="✅ Restarted!")
        # await msg.edit(embed = restarting)
    importlib.reload(Utils)
    restarting.add_field(name="Utils module", value="Reloaded")
    importlib.reload(Config)
    restarting.add_field(name="Config", value="Reloaded")
    restarting.title = "Bot Restarted"
    await msg.edit(embed=restarting)
    Config.LOGGING.info(
        f"Bot has been restarted succesfully in {len(bot.guilds)} server(s) with {len(bot.users)} users by {ctx.author.name}#{ctx.author.discriminator} (ID - {ctx.author.id})!")
    await msg.delete(delay=3)
    if ctx.guild != None:
        await ctx.message.delete(delay=3)


@bot.command()
@commands.check(owner)
async def clean_q(ctx):
    """
    Restart queues.
    """
    restarting = discord.Embed(
        title="Cleaning queue",
        color=Config.MAINCOLOR
    )
    msg = await ctx.send(embed=restarting)
    for cog in ["Bosses", "Clans", "Matchmaking"]:
        bot.reload_extension("Cogs." + cog)
        restarting.add_field(name=f"{cog}", value="✅ Restarted!")
        # await msg.edit(embed = restarting)
    restarting.title = "Queue Cleaned!"
    await msg.edit(embed=restarting)
    await msg.delete(delay=5)
    if ctx.guild != None:
        await ctx.message.delete(delay=5)


@bot.command()
@commands.check(owner)
async def reload(ctx, *, command: str = None):
    """
    Restart queues.
    """
    if command is None:
        return
    restarting = discord.Embed(
        title="Reloading",
        color=Config.MAINCOLOR
    )
    msg = await ctx.send(embed=restarting)
    if command == "Utils":
        importlib.reload(Utils)
    elif command == "Config":
        importlib.reload(Config)
    else:
        bot.reload_extension("Cogs." + command)
    restarting.add_field(name=f"{command}", value="✅ Restarted!")
    await msg.edit(embed=restarting)
    restarting.title = "Reloading done!"
    await msg.edit(embed=restarting)
    await msg.delete(delay=5)
    if ctx.guild != None:
        await ctx.message.delete(delay=5)


@bot.before_invoke
async def before_commands(ctx):
    if Config.testing:
        if ctx.guild.id == 1:
            return
    global running_commands
    running_commands += 1
    Config.LOGGING.info("Command " + ctx.command.name + " Started by " + ctx.author.name + " | "
                        + str(running_commands) + " commands running")


@bot.after_invoke
async def after_commands(ctx):
    global running_commands
    running_commands -= 1
    Config.LOGGING.info(
        "Command " + ctx.command.name + " Started by " + ctx.author.name + " Was completed alright." + " | "
        + str(running_commands) + " commands running")


@bot.check
async def check(ctx):
    if Config.testing:
        if ctx.guild.id == 1:
            return False
    if ctx.author.id in Config.OWNERIDS:
        return True
    if Config.MAINTENANCE is True and ctx.author.id not in Config.OWNERIDS:
        return False
    elif ctx.command.name in Config.DISABLED and ctx.author.id not in Config.OWNERIDS:
        return False
    else:
        if ctx.command.name not in ["blacklist", "add", "remove"]:
            server = Config.SERVERS.find_one({'guild_id': ctx.guild.id})
            if server is not None:
                return not ctx.channel.id in server['channel_blacklist']
            else:
                return True
        else:
            return True


# Command error
@bot.event
async def on_command_error(ctx, error):
    if Config.testing:
        if ctx.guild.id == 1:
            pass
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.UserInputError):
        embed = discord.Embed(
            title="Oh no.",
            description=f"Looks like you used that command wrong:\n```{error}```",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, UserInBlacklist):
        embed = discord.Embed(
            title="Oh no.",
            description=f"It looks like you have been blacklisted from using Enchanted. You can join the [Support Server](https://google.com/) and appeal by opening a ticket.",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CheckFailure):
        if Config.MAINTENANCE is True:
            embed = discord.Embed(
                title="Uh oh..",
                description=f"Enchanted is currently in maintenance...",
                color=Config.ERRORCOLOR
            )
            await ctx.send(embed=embed)
        elif ctx.command.name in Config.DISABLED:
            embed = discord.Embed(
                title="Uh oh..",
                description=f"This command has been disabled (temporarily)...",
                color=Config.ERRORCOLOR
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Uh oh..",
                description=f"You can't use this command here...",
                color=Config.ERRORCOLOR
            )
            await ctx.send(embed=embed)
    elif isinstance(error, discord.errors.Forbidden):
        try:
            await Config.LOGGING.error("Missing permissions to post.")
        except discord.errors.Forbidden:
            print("Missing permission to post missing permission error in logging channel")
    else:
        try:
            embed = discord.Embed(
                title="Error",
                description=f"An error has occurred while executing this command:\n```{error}```",
                color=Config.ERRORCOLOR
            )
            await ctx.send(embed=embed)
        except discord.errors.Forbidden:
            try:
                await Config.LOGGING.error("\n```" + str(error) + "```")
            except discord.errors.Forbidden:
                print("Missing permission to post missing permission error in logging channel")
        raise error


@tasks.loop(seconds=30)
async def status_set():
    # Main # 
    statuses = ["heavenly beings smile", "flutters of the night", "the sky twinkle", "trees bend", "the fairies dance",
                "leaves fall", "every star", "grass wave", "bees buzz", "stardust sprinkle", "tadpoles play",
                "waterfalls"]
    spooktober_statuses = ["the ghosts", "the graveyard", "the devil laugh", "the vampires screeching",
                           "the wolfs growl", "the demonic creatures", "the dead", "the dead souls", "the nightmares",
                           "the creatures growl", "the orks", "the people panic", "burning houses", "souls rise"]
    snow_statuses = ["the snow fall", "the Ice Golem", "the reindeer", "the snowball fights", "santa fly by",
                     "the bells jingle", "the snowflakes tumble", "the children laughing"]
    easter_statuses = ["chicks hatching", "the Easter Bunny", "grass sway", "daffodils bloom", "Easter Island",
                       "bunnies hop", "eggs being eaten", "eggs being hidden", "lambs jump hedges", "chicks cheep"]
    if Config.MAINTENANCE is True:
        status = discord.Status.dnd
    else:
        status = discord.Status.online
    await bot.change_presence(status=status, activity=discord.Activity(type=discord.ActivityType.watching,
                                                                       name=random.choice(statuses) + " | ]help"))


# Starts info log sending
@tasks.loop(seconds=300)
async def send_info_logs():
    await Config.LOGGING.send_logs()


@bot.check
async def check_blacklist(ctx):
    if Config.BLACKLIST.find_one({'user_id': ctx.author.id}) is not None:
        embed = discord.Embed(
            title="Oh no.",
            description=f"It looks like you have been blacklisted from using Enchanted. You can join the [Support Server](https://google.com/) and appeal by opening a ticket.",
            color=Config.ERRORCOLOR
        )
        await ctx.send(embed=embed)
        raise UserInBlacklist
    else:
        return True


# On ready
@bot.event
async def on_ready():
    Config.LOGGING.info(f"__Bot has started successfully in {len(bot.guilds)} server(s)__")  # with {len(bot.users)} users")
    status_set.start()
    send_info_logs.start()
    if not hasattr(bot, "uptime"):
        bot.uptime = datetime.datetime.utcnow()


# shard on_ready
@bot.event
async def on_shard_ready(shard_id):
    Config.LOGGING.info(f"Shard ID {shard_id} is online and connected to discord gateway")


# cache all classes
classes = []
for _class in Utils.get_all_classes():
    classes.append(_class["name"])
Config.ALL_CLASSES = classes

# Starts bot
bot.run(Config.TOKEN)
