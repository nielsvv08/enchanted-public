import logging
import math
import time
import pymongo
import asyncio

import Battle_Utils
import Config
import discord
import datetime
from discord.ext import commands, tasks
import Utils

from Paginator import EmbedPaginatorSession
from discord.ext.commands import Context
from discord.ext.commands.view import StringView

class Essentials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.refreshes = {}
        # self.season_reset.start()

    @commands.command(name='discord')
    async def discord_link(self, ctx):
        embed = discord.Embed(description="[**Click here to join the community!**](https://google.com/)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command(name='vote', aliases=['daily', 'weekly'])
    async def vote_link(self, ctx):
        # embed=discord.Embed(description="[**Click here to vote for the bot**](https://google.com/", color = Config.MAINCOLOR)
        embed=discord.Embed(description="**[Click here to vote for the bot!](https://google.com/)**\n**[Click here to vote for the server!](https://google.com/)**\nYou can vote every 12 hours.", color = Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command(aliases=['h', 'commands'])
    async def help(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        prefix = Utils.fetch_prefix(ctx)
        embed = discord.Embed(title="Here to help you my friend", description="", color = Config.MAINCOLOR)
        embed.add_field(name="Base Commands", value=f"`{prefix}profile` - view and open your chests\n`{prefix}boss` - start a battle against a boss\n`{prefix}battle` - start a battle with another player\n`{prefix}chests` - view and open your chests\n ")
        embed.add_field(name="Socials & stats", value=f"`{prefix}discord` - join the community!\n`{prefix}twitter` - follow our twitter for updates!\n`{prefix}invite` - invite the bot!\n`{prefix}stats` - show the bot statistics\n ")
        embed.add_field(name="Progression", value=f"`{prefix}vote` - gain some neat rewards!\n`{prefix}shop` - view today's NPC shop.\n`{prefix}items`- view and equip weapons and armor.\n`{prefix}upgrade` - upgrade your items\n`{prefix}season` - View info on the current season\n ")
        embed.add_field(name="Clans", value=f"`{prefix}clan` - view and join clans\n`{prefix}dungeon` - start a dungeon battle")
        embed.add_field(name="Class commands", value=f"`{prefix}spells` - view and equip your spells for battle\n`{prefix}switch` - switch to a different class")
        embed.add_field(name="Cosmetics!", value=f"`{prefix}cosmetics` - view and equip your cosmetics\n`{prefix}crowns` -  more info on crowns!")
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def twitter(self, ctx):
        embed = discord.Embed(description="[**Here's our twitter page!**](https://twitter.com/EnchantedGG)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        embed = discord.Embed(description="[**Add the bot to your server!**](https://discordapp.com/api/oauth2/authorize?client_id=697879596040716455&permissions=67464272&scope=bot)",
                              color=Config.MAINCOLOR)
        embed.set_image(url="https://i.imgur.com/82uVAPe.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def wiki(self, ctx, topic : str = None, *, extra : str = None):
        prefix = Utils.fetch_prefix(ctx)
        if topic is None:
            embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki", description=f"Welcome to the enchanted wiki command. Here might be some useful things to check out.\n\n`{prefix}tutorial`\n`{prefix}help`\n`{prefix}wiki <topic>`\n\nHere are the current topics in the wiki:\n\n`" + "`, `".join(x['name'] for x in Config.WIKI) + "`.")# + "\n\n**\> > > [WIKI WEB-VERSION](" + Config.WIKILINK + ") < < <**")
            await ctx.send(embed=embed)
        elif topic.lower() in (x['name'].lower() for x in Config.WIKI):
            if topic.lower() == "classes":
                if extra is None:
                    classes = ""
                    for x in Config.ALL_CLASSES:
                        classes += f", **{x}**"
                    classes = classes[2:]
                    embed = discord.Embed(color=Config.MAINCOLOR, title="Enchanted Wiki", description=f"Please define a class like `{prefix}wiki classes <class>`\nClasses: " + classes)
                    return await ctx.send(embed=embed)
                try:
                    _class = Utils.get_class(extra.title())
                except KeyError:
                    _class = None
                if _class is None:
                    classes = ""
                    for x in Config.ALL_CLASSES:
                        classes += f", **{x}**"
                    classes = classes[2:]
                    embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki", description=f"Please define a class like `{prefix}wiki classes <class>`\nClasses: " + classes)
                    return await ctx.send(embed=embed)
                stats = "> Health: " + str(_class['stats']['health']) + "\n> Strength: " + str(_class['stats']['strength']) + "\n> Defense: " + str(_class['stats']['defense']) + "\n> Endurance: " + str(_class['stats']['endurance'])
                spells = list(Config.SPELLS.find({'class': _class["name"]}).sort("id", pymongo.ASCENDING))
                spell_string = ""
                for spell in spells:
                    spell_string += "\n"+spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
                embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki | " + _class["name"] + " " + _class["emote"], description=stats + "\n\n**Spells:**\n"+spell_string)
                # if Config.WIKI[2]["link"] != "":
                #     embed.add_field(name="Wiki", value="**\> > > [WIKI WEB-VERSION](" + Config.WIKILINK + Config.WIKI[2]["link"] + _class["name"].lower().replace(" ", "-") + ") < < <**")
                return await ctx.send(embed=embed)
            elif topic.lower() == "abilities":
                ab_string = f"Everyone in silver and higher can now unlock abilities from chests. These unique stones can be activated once per match to help you defeat your opponent. Commands: `{prefix}ability` & `{prefix}ability equip`\n\n"
                abilities = list(Config.ABILITIES.find({'id': {'$nin': [7, 8, 11]}}))
                for ab in abilities:
                    ab_string += "\n> "+ab['emoji']+" **"+ ab['name'] + "** - "+ab['desc']
                embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki | Abilities", description=ab_string)
                # if Config.WIKI[1]["link"] != "":
                #     embed.add_field(name="Wiki", value="**\> > > [WIKI WEB-VERSION](" + Config.WIKILINK + Config.WIKI[1]["link"] + ") < < <**")
                return await ctx.send(embed=embed)
            else:
                loop = 0
                while loop < len(Config.WIKI):
                    if Config.WIKI[loop]["name"].lower() == topic.lower():
                        break
                    loop += 1
                embeds = []
                for page in Config.WIKI[loop]["pages"]:
                    embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki | " + page["title"], description=page["content"])
                    # if Config.WIKI[loop]["link"] != "":
                    #     embed.add_field(name="Wiki", value="**\> > > [WIKI WEB-VERSION](" + Config.WIKILINK + Config.WIKI[loop]["link"] + ") < < <**")
                    embeds.append(embed)
                paginator = EmbedPaginatorSession(ctx, *embeds)
                await paginator.run()


    @commands.command()
    async def toggle_q(self, ctx):
        if ctx.author.id in Config.OWNERIDS:
            Config.OPEN_QUEUES = not Config.OPEN_QUEUES
            await ctx.send("Queuing is now set to: " + str(Config.OPEN_QUEUES))

    @commands.command()
    async def toggle_m(self, ctx):
        if ctx.author.id in Config.OWNERIDS:
            Config.MAINTENANCE = not Config.MAINTENANCE
            if Config.MAINTENANCE is True:
                await self.bot.change_presence(status=discord.Status.dnd)
            else:
                await self.bot.change_presence(status=discord.Status.online)
            await ctx.send("Maintenance is now set to: " + str(Config.MAINTENANCE))

    @commands.command()
    async def toggle_s(self, ctx):
        if ctx.author.id in Config.OWNERIDS:
            Config.PERM_SEASON = not Config.PERM_SEASON
            await ctx.send("Permission to reset season is now set to: " + str(Config.PERM_SEASON))

    @commands.command()
    async def disable(self, ctx, *, command:str=None):
        if ctx.author.id in Config.OWNERIDS:
            if command is None:
                return
            if command in Config.DISABLED:
                Config.DISABLED.remove(command)
                await ctx.send("Re-enabled the " + str(command) + " command")
            else:
                Config.DISABLED.append(command)
                await ctx.send("Disabled the " + str(command) + " command")

    @commands.command(aliases=["statistics"])
    async def stats(self, ctx):
        """Returns an embed containing some basic statistics."""
        
        prefix = Utils.fetch_prefix(ctx)

        embed = discord.Embed(
            title="Stats for Enchanted",
            color=Config.MAINCOLOR,
            description=f"**Name**: Enchanted\n"
            + f"**Prefix**: {prefix}\n"
            + f"**Ping**: {round(self.bot.latency * 1000)} ms\n"
            + f"**Uptime**: {self.get_uptime()}\n"
            + f"**Server Count**: {len(self.bot.guilds)} ({self.bot.shard_count} shards)\n"
            + f"**Saved Accounts**: {Config.USERS.count_documents({})}\n"
            + f"**Discord**: <https://google.com/>",
        )

        await ctx.send(embed=embed)

    def get_uptime(self):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime

        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if days:
            fmt = f"{days} days, {hours} hours, {minutes} minutes and {seconds} seconds"
        elif hours:
            fmt = f"{hours} hours, {minutes} minutes and {seconds} seconds"
        elif minutes:
            fmt = f"{minutes} minutes and {seconds} seconds"
        else:
            fmt = f"{seconds} seconds"

        return fmt

    @commands.command()
    async def change_user(self, ctx, user: discord.Member = None, mongo_string : str = None):
        if ctx.author.id in Config.OWNERIDS:
            eval("Config.USERS.update_one({'user_id': user.id}, %s)" % mongo_string)

    @commands.command()
    async def change_clan(self, ctx, name: str = None, mongo_string: str = None):
        if ctx.author.id in Config.OWNERIDS:
            eval("Config.CLANS.update_one({'name': name}, %s)" % mongo_string)

    @commands.command()
    async def unlock(self, ctx):
        if not Config.testing:
            return
        account = Config.USERS.find_one({'user_id': ctx.author.id})
        if account is None:
            return
        classes = []
        loop = 0
        while loop < len(account["spells"]):
            classes.append(account["spells"][loop]["class"])
            loop += 1
        cl = list(Config.CLASSES.find({'name': {'$nin': classes}}))
        if len(cl) < 1:
            return await ctx.send("Error, all classes unlocked already")
        else:
            embed = discord.Embed(title="Please select the class you want to unlock!", description = "Use the emojis to choose", color = Config.MAINCOLOR)
            embed.set_footer(text="Message will be deleted in 30 seconds")
            for _class in cl:
                embed.add_field(name=_class['name'] + " " + _class['emote'], value=_class['desc'])
            msg = await ctx.send(embed=embed)
            for _class in cl:
                await msg.add_reaction(_class['emote'])

            def check(reaction, user):
                return user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and reaction.me and reaction.emoji in [x['emote'] for x in cl]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
                for _class in cl:
                    if _class['emote'] == str(reaction):
                        account["spells"].append({'class': _class["name"], 'spells': [0, 1]}) 
                        Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'spells': account["spells"]}})
                        await msg.clear_reactions()
                        embed = discord.Embed(
                            title="New class added!",
                            description = "You selected **"+ _class['name'] + "** "+_class["emote"]+"\n"
                            + "__Your stats are:__\n"
                            + "> Health: " + str(account['stats']['health']) + "\n> Strength: " + str(account['stats']['strength']) + "\n> Defense: " + str(account['stats']['defense']) + "\n> Endurance: " + str(account['stats']['endurance']) + "\n\n"
                            + "**Health**, if you fall below 0 health in battle you lose.\n"
                            + "**Strenght**, will boost your spells.\n"
                            + "**Defense**, protects you from incoming damage.\n"
                            + "**Endurance/Mana**, the resources used in battle to cast your spells. If it falls below 0 you lose.\n",
                            color = Config.MAINCOLOR
                        )
                        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320244649295894/736899297848852530/en_shield.png")
                        await msg.edit(embed=embed)
            except asyncio.TimeoutError:
                await msg.clear_reactions()

    async def _update_embed(self, config):
        id_ = str(config["channel"])
        last_refreshed = self.refreshes.get(id_)

        self.refreshes[id_] = time.time()

        try:
            channel = self.bot.get_channel(config["channel"])
            message = await channel.fetch_message(config["message"])
        except BaseException:
            message = None

        if message is None:
            return

        if last_refreshed and time.time() - last_refreshed < 120:
            await self.remove_reactions(message)
            return

        if config["class"] == "season":
            timer = Battle_Utils.get_season_timer()
            the_time = time.time()
            hours, remainder = divmod(timer - the_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            season = ""
            if (timer - the_time) < 0:
                season += "SOON!"
            elif days:
                season += f"{round(days)} days, {round(hours)} hours, {round(minutes)} minutes and {round(seconds)} seconds"
            elif hours:
                season += f"{round(hours)} hours, {round(minutes)} minutes and {round(seconds)} seconds"
            elif minutes:
                season += f"{round(minutes)} minutes and {round(seconds)} seconds"
            else:
                season += f"{round(seconds)} seconds"
            embed = discord.Embed(color=Config.MAINCOLOR, title="Enchanted Wiki | Seasons", description=f"*Each 2 weeks there is a season reset. Everyone has their power lowered to that of the previous rank. Rewards can then be claimed using `]season claim` if the user joined the season.\n\n*:clock1: **Season reset is in "+season+"**")
            embed.timestamp = datetime.datetime.utcnow()
            embed.set_footer(
                text="Enchanted | Wiki | Last update",
            )

            await message.edit(content=None, embed=embed)

            await self.remove_reactions(message)
            return 

        _class = Utils.get_class(config["class"])
        if _class is None:
            return

        stats = "> Health: " + str(_class['stats']['health']) + "\n> Strength: " + str(_class['stats']['strength']) + "\n> Defense: " + str(_class['stats']['defense']) + "\n> Endurance: " + str(_class['stats']['endurance'])
        spells = list(Config.SPELLS.find({'class': _class["name"]}).sort("id", pymongo.ASCENDING))
        spell_string = ""
        for spell in spells:
            spell_string += "\n"+spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
        embed = discord.Embed(color = Config.MAINCOLOR, title="Enchanted Wiki | " + _class["name"] + " " + _class["emote"], description=stats + "\n\n**Spells:**\n"+spell_string)
        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(
            text="Enchanted | Wiki | Last update",
        )

        await message.edit(content=None, embed=embed)

        await self.remove_reactions(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        if payload.guild_id not in [615841347944841226, 736315344854974535]:
            return
        
        if payload.emoji.name != "🔄":
            return

        user = self.bot.get_user(payload.user_id)
        if user.bot:
            return

        config = Config.WIKIS.find_one({"message": payload.message_id})

        if config is None:
            return

        await self._update_embed(config)

    async def remove_reactions(self, message):
        refresh_emoji = "🔄"

        try:
            if message.reactions is not None:
                await message.clear_reactions()

            await message.add_reaction(refresh_emoji)
        except (discord.Forbidden, discord.HTTPException):
            pass
    
    @commands.command()
    async def wikiembed(self, ctx, *, content: str=None):
        if ctx.author.id not in Config.OWNERIDS:
            return
        
        if content != "season":
            if content not in Config.ALL_CLASSES:
                return await ctx.send("Can't find that class")
        
        msg = await ctx.send("Wiki")

        account = {"class": content, "message": msg.id, "channel": ctx.channel.id}
        Config.WIKIS.insert_one(account)

        await asyncio.sleep(1)

        config = Config.WIKIS.find_one({"message": msg.id})

        await self._update_embed(config)

    @tasks.loop(minutes=60)
    async def reset_timer(self, ctx):
        if Battle_Utils.get_season_timer() < time.time():
            channel = await self.bot.get_channel(710352120880169010)
            await channel.send("It's time for a season reset!")

    @commands.command()
    async def season_reset(self, ctx):
        if ctx.author.id not in Config.OWNERIDS:
            return

        Config.LOGGING.info("! Season reset - Started")

        # Loop through users
        for user in Config.USERS.find({}):
            try:
                # Save their previous power so they can claim rewards
                user['old_power'] = user['power']
                # Set their current power to that of the rank one lower than their current
                user['power'] = Utils.get_reset_power(user['power'])
                # Make it negative to show they haven't battled yet
                # But only if they battles last season
                if user['power'] > 0:
                    user['power'] *= -1
                # Save the user's powers
                Config.USERS.find_one_and_update({"user_id": user["user_id"]}, {"$set": user})

            except KeyError:
                Config.LOGGING.info(f"! Season reset - Error with user: {str(user['user_id'])}")
        Config.MAIN.find_one_and_update({"name": "Season Reset"}, {"$set": {"timer": (time.time() + 120600)}})
        Config.LOGGING.info("! Season reset - Finished")

    @commands.command()
    async def claim(self, ctx):
        return
        
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        
        for cosmetic in account['cosmetics']:
            if cosmetic['type'] == "color":
                if cosmetic["name"] == "OG Embed Color":
                    return await ctx.send("You already claimed your reward!")
        
        Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'cosmetics': {'type': 'color', 'name': "OG Embed Color", 'value': "0x6A00FF"}}, '$inc': {'crowns': 500}})
        embed = discord.Embed(
            title="Full Release - Rewards claimed!",
            description = "To celebrate our full release we just added **500** "+Config.EMOJI["crown"]+" and the **OG Embed Color** to your profile!\n"
            + "Thank you for supporting our lil' project, it means a lot. - Enchanted Staff :heart:",
            color = 0xF6CB48
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320366116470815/761593245183901706/ABILITY_Wish.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def tutorial(self, ctx):
        account = Config.USERS.find_one({'user_id': ctx.author.id})
        if account is not None: 
            await Utils.tutorial(self.bot, ctx, ctx.author.id, False)
        else:
            await Utils.tutorial(self.bot, ctx, ctx.author.id, True)

    @commands.command(hidden=True)
    async def sudo(self, ctx: Context, user: discord.User = None, *, text: str = None):
        """Uses the bot as a user"""

        
        if ctx.author.id not in Config.OWNERIDS:
            return

        if user is None:
            return await ctx.send("missing user")
        if text is None or text.strip() == "":
            return await ctx.send("missing command")

        amsg = ctx.message
        amsg.author = user
        amsg.content = text

        view = StringView(text)
        invoker = view.get_word()
        actx = Context(
            prefix=ctx.prefix,
            view=view,
            bot=ctx.bot,
            message=amsg,
            invoked_with=invoker,
            command=ctx.bot.all_commands.get(invoker))

        await actx.command.invoke(actx)

def setup(bot):
    bot.add_cog(Essentials(bot))    
