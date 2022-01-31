import asyncio
import Config
import discord
from discord.ext import commands
import Utils
import random

class Chests(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def restart_open_menu(self, ctx, msg):
        account = Utils.get_account(ctx.author.id)
        if account['chests'] < 1:
            embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
            embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
            embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
            await msg.edit(embed=embed)
            await msg.delete(delay=30)
            return
        else:
            mystring = str(account['chests']) + " Chests."

        embed = discord.Embed(colour=Config.MAINCOLOR, description=mystring+"\n\n**React below to open a chest**")
        embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
        embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
        await msg.edit(embed=embed)

        if not Config.testing:
            await msg.add_reaction(self.bot.get_emoji(671574326364995595))
        else:
            await msg.add_reaction(self.bot.get_emoji(730362456702189600))
        
        if account['chests'] > 9:
            await msg.add_reaction(self.bot.get_emoji(736531447854268496))

        ten = False
        def check(reaction, user):
            if user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and isinstance(reaction.emoji, discord.Emoji):
                if reaction.emoji.id == 736531447854268496:
                    return reaction.emoji.id == 736531447854268496
                if not Config.testing:
                    return reaction.emoji.id == 671574326364995595
                else:
                    return reaction.emoji.id == 730362456702189600
                return reaction.emoji.id == 736531447854268496
            else:
                return False
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout = 30.0, check=check)
            if reaction.emoji.id == 736531447854268496:
                ten = True
            await reaction.message.clear_reactions()
            await self.open_crate(account, ctx, msg, embed, ten)

        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
                embed.set_footer(text='Time-out, run the command again to continue')
                await msg.edit(embed=embed)
            except:
                Config.LOGGING.info("Error deleting message of user. Don't have the permission or message does not exist.")

    async def open_crate(self, account, ctx, msg, embed, ten):
        account = Utils.get_account(ctx.author.id)
        if ten is True:
            if account['chests'] < 10:
                embed = discord.Embed(colour=Config.MAINCOLOR, description="No 10 chests yet.\nCollect keys or vote to get chests.")
                embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
                embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
                if msg is None:
                    msg = await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                await msg.delete(delay=30)
                return
        else:
            if account['chests'] < 1:
                embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
                embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
                embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
                if msg is None:
                    msg = await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                await msg.delete(delay=30)
                return

        desc = "You opened a chest and got:\n"
        if ten is True:
            max_loop = 10
        else: 
            max_loop = 1
        loop = 0
        while loop < max_loop:
            # Get account again to avoid duplicates
            account = Utils.get_account(ctx.author.id)
            spell = Utils.win_spell(account)
            _class = Utils.win_class(account)
            ability = Utils.win_ability(account)
            all_titles = Config.TITLES.copy()
            new_title = random.choice(all_titles)
            i = len(all_titles) + 5
            titles = []
            for cosmetic in account["cosmetics"]:
                if cosmetic["type"] == "title":
                    titles.append(cosmetic["value"])
            while new_title in titles:
                i -= 1
                new_title = random.choice(all_titles)
                if i < 0:
                    new_title = None
                    break
            account['chests'] -= 1
            if account['chests'] < 1:
                account['chests'] = 0

            if _class is not None and random.randint(0, 100) == 0:
                account["spells"].append({"class": _class["name"], "spells": [0, 1]})
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'spells': account["spells"], 'chests': account['chests']}})
                desc += "\n> "+_class['emote']+" **"+ _class['name'] + "** - "+_class['desc']
            elif ability is not None and random.randint(0, 150) == 0 and account["power"] >= 25:
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$push': {'abilities': ability['id']}, '$set': {'chests': account['chests']}})
                desc += "\n> "+ability['emoji']+" **"+ ability['name'] + "** - "+ability['desc']
            elif spell is not None and random.randint(0, 8) == 0:
                number = 0
                while number < len(account["spells"]):
                    if account["spells"][number]["class"] == spell["class"]:
                        break
                    number += 1
                account["spells"][number]["spells"].append(spell["id"])
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'spells': account["spells"], 'chests': account['chests']}})
                desc += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" Effect] [ "+str(spell['cost'])+" Cost] [ "+str(spell['scaling'])+" Scaling] | __"+spell['class']+"__"
            # elif :
            #     seed = Utils.win_seed()
            #     account_ = Utils.get_account(ctx.author.id)
            #     did_add = False
            #     for user_seed in account_['seeds']:
            #         if user_seed['id'] == seed['id']:
            #             did_add = True
            #             user_seed['amount'] += 1
            #     if not did_add:
            #         account_['seeds'].append({'id': seed['id'], 'amount': 1})
            #     Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'seeds': account_['seeds'], 'chests': account['chests']}})
            #     desc += "\n> 1 "+seed['emoji']+" "+seed['name']+" Seed."
            elif random.randint(0, 6) == 0 and new_title is not None:
                Config.USERS.update_one({'user_id': ctx.author.id},
                                        {'$push': {'cosmetics': {'type': 'title', 'value': new_title}}, '$set': {'chests': account['chests']}})
                desc += "\n> `" + new_title + "` Title"
            elif random.randint(0, 1) == 0:
                coins = random.randint(10, 20)
                Config.USERS.update_one({'user_id': ctx.author.id},
                                        {'$set': {'chests': account['chests']}, '$inc': {'coins': coins}})
                desc += "\n> " + str(coins) + " " + Config.EMOJI['coin']
            else:
                rubies = random.randint(8, 27)
                Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': {'chests': account['chests']}, '$inc': {'rubies': rubies}})
                desc += "\n> " + str(rubies) + " "+ Config.EMOJI['ruby']
            loop += 1
        end_embed=discord.Embed(title='Chest', color = Config.MAINCOLOR, description = desc)
        end_embed.set_footer(text='Click ✔ to continue')
        slot_embed = discord.Embed(title='Chest', color=Config.MAINCOLOR)
        slot_embed.set_image(url="https://i.pinimg.com/originals/20/c0/27/20c0271883ddbbeda8aaa106b9c57066.gif")
        await msg.edit(embed=slot_embed)
        await asyncio.sleep(2)

        await msg.edit(embed=end_embed)
        await msg.add_reaction("✅")
        def check(reaction, user):
            return reaction.message.id == msg.id and user.id == ctx.author.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
            if str(reaction) == "✅":
                await reaction.message.clear_reactions()
                await self.restart_open_menu(ctx, msg)

        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
                end_embed.set_footer(text='Time-out, run the command again to continue')
                await msg.edit(embed=end_embed)
            except:
                Config.LOGGING.info("Error editing message of user. Don't have permission or message does not exist.")

        

    @commands.command(aliases=['crates', 'c', 'o', 'chests', 'chest'])
    async def open(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
            
        if account["keys"] > 9:
            while account['keys'] > 9:
                account['keys'] -= 10
                account['chests'] += 1
            Config.USERS.update_one({'user_id': account['user_id']}, {'$set': {'chests': account['chests'], 'keys': account['keys']}})

        if account['chests'] < 1:
            embed = discord.Embed(colour=Config.MAINCOLOR, description="No chests yet.\nCollect keys or vote to get chests.")
            embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
            embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=30)
            return
        else:
            mystring = str(account['chests']) + " Chests."

        embed = discord.Embed(colour=Config.MAINCOLOR, description=mystring+"\n\n**React below to open a chest**")
        embed.set_author(name=str(ctx.author.name) + "'s Chests", icon_url=str(ctx.author.avatar_url))
        embed.set_footer(text=str(account['chests']) + " chests collected | message will be deleted in 30 seconds.")
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        
        ten = False
        if not Config.testing:
            await msg.add_reaction(self.bot.get_emoji(671574326364995595))
        else:
            await msg.add_reaction(self.bot.get_emoji(730362456702189600))
        
        if account['chests'] > 9:
            await msg.add_reaction(self.bot.get_emoji(736531447854268496))

        def check(reaction, user):
            if user.id == ctx.author.id and reaction.message.channel.id == ctx.channel.id and reaction.message.id == msg.id and isinstance(reaction.emoji, discord.Emoji):
                if reaction.emoji.id == 736531447854268496:
                    return reaction.emoji.id == 736531447854268496
                if not Config.testing:
                    return reaction.emoji.id == 671574326364995595
                else:
                    return reaction.emoji.id == 730362456702189600
                return reaction.emoji.id == 736531447854268496
            else:
                return False
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout = 30.0, check=check)
            if reaction.emoji.id == 736531447854268496:
                ten = True
            await reaction.message.clear_reactions()
            await self.open_crate(account, ctx, msg, embed, ten)

        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
                embed.set_footer(text='Time-out, run the command again to continue')
                await msg.edit(embed=embed)
            except:
                Config.LOGGING.info("Error editing message of user. Don't have permission or message does not exist.")

def setup(bot):
    bot.add_cog(Chests(bot))
