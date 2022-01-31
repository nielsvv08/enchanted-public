import asyncio

import Config
import discord
from discord.ext import commands
import Utils


async def generate_embed(account, member, ctx):
    rank = Utils.get_rank_object(account['power'])
    prefix = Utils.fetch_prefix(ctx)

    # Calculate chest count
    if account["keys"] > 9:
        while account['keys'] > 9:
            account['keys'] -= 10
            account['chests'] += 1
        Config.USERS.update_one({'user_id': account['user_id']}, {
            '$set': {'chests': account['chests'], 'keys': account['keys']}})

    # Class count
    class_number = 0
    while class_number < len(account["spells"]):
        class_number += 1

    # Embed colour
    if account["selected_embed_color"] is None:
        color = Config.MAINCOLOR
    else:
        color = int(account["selected_embed_color"]["value"], 0)

    # Base embed
    embed = discord.Embed(title="Welcome back to the world...", color=color,
                          description="Health: " + str(account['stats']['health']) +
                                      "\nStrength: " + str(account['stats']['strength']) +
                                      "\nDefense: " + str(account['stats']['defense']) +
                                      "\nEndurance: " + str(account['stats']['endurance']))
    embed.set_author(name=str(member.name), icon_url=str(member.avatar_url))

    if account["selected_embed_image"] is not None:
        embed.set_thumbnail(url=account["selected_embed_image"]["value"])

    embed.set_footer(
        text=f"use {prefix}s to look at spells, {prefix}b to battle, {prefix}c to open chests,"
             f" {prefix}items to see items, and {prefix}switch to switch class")

    # Profile details
    embed.add_field(name=Config.EMOJI['book'] + " Class:",
                    value=account['class'] + " (" + str(class_number) + "/" + str(len(Config.ALL_CLASSES)) + ")")

    # Make power appear positive
    power = account['power']
    if account['power'] < 0:
        power = account['power'] * -1

    embed.add_field(name=rank['emoji'] + " " + rank['name'],
                    value=str(power) + Config.EMOJI['power'])
    embed.add_field(name=Config.EMOJI['scroll'] + " Title:",
                    value=str(account['selected_title']))
    embed.add_field(name=Config.EMOJI['coin'] + " Coins: ",
                    value=str("{:,}".format(account['coins'])))
    embed.add_field(name=Config.EMOJI['ruby'] + " Rubies:",
                    value=str("{:,}".format(account['rubies'])))
    embed.add_field(name=Config.EMOJI['crown'] + " Crowns:",
                    value=str("{:,}".format(account['crowns'])))
    embed.add_field(name=Config.EMOJI['chest'] + " Chests:", value=str(account['chests']))
    embed.add_field(name=Config.EMOJI['key'] + " Keys: ",
                    value="(" + str(account['keys']) + "/10)")
    desc = str(account["battles"]['pvp']) + " 🏹 / " + str(account["battles"]['bosses']) + " 🔥 / " + \
        str(account["battles"]['dungeons']) + " ⛓️"  # + "  (⚔️ / 🔥 / ⛓️)"
    embed.add_field(name="⚔️ Battles:", value=desc)  # +Config.EMOJI['battle']

    return embed


class Profile(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['player', 'p'])
    async def profile(self, ctx, *, member: discord.Member = None):
        if member is not None and Utils.get_account(member.id) is None:
            await ctx.send(
                embed=discord.Embed(title="User has no profile", description=member.name + " does not have a profile.",
                                    color=Config.MAINCOLOR))
            return
        if member is None:
            member = ctx.author
        msg, account = await Utils.get_account_lazy(self.bot, ctx, member.id)
        if account is None:
            return

        embed = await generate_embed(account, member, ctx)

        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)
        # if needsTutorial == True:
        #    Tutorial.tutorial(self, ctx, member)

    @commands.command(aliases=["rebirth"])
    async def switch(self, ctx):
        account = Utils.get_account(ctx.author.id)
        if account is None:
            await ctx.send(embed=discord.Embed(title="Oh no.", description="You don't appear to have played before... "
                                                                           "you cannot use this command yet.",
                                               color=Config.MAINCOLOR))
            return
        else:
            embed = discord.Embed(title="Please select the class you want to switch to, or do nothing to cancel",
                                  description="use the emojis to choose",
                                  color=Config.MAINCOLOR)
            embed.set_footer(text="Message will be timeout in 30 seconds")
            emotes = []
            classes = []
            loop = 0
            while loop < len(account["spells"]):
                classes.append(account["spells"][loop]["class"])
                loop += 1
            for cl in classes:
                _class = Utils.get_class(cl)
                embed.add_field(name=_class['name'] + " " + _class['emote'], value=_class['desc'])
                emotes.append(_class['emote'])
            msg = await ctx.send(embed=embed)
            for emote in emotes:
                await msg.add_reaction(emote)

            all_classes = Utils.get_all_classes()

            def check(check_reaction, check_user):
                return check_user.id == ctx.author.id and check_reaction.message.channel.id == ctx.channel.id and \
                       check_reaction.message.id == msg.id and check_reaction.me and check_reaction.emoji \
                       in [x['emote'] for x in all_classes]

            try:
                reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
                for _class in all_classes:
                    if _class['emote'] == str(reaction):
                        if _class['name'] in classes:
                            account['slots'] = [0, 1, None, None, None]
                            account['class'] = _class['name']
                            account['stats'] = _class['stats']
                            double = False

                            for cosmetic in account['cosmetics']:
                                if cosmetic['type'] == 'title':
                                    if cosmetic['value'] == " the " + _class['name']:
                                        double = True
                            if not double:
                                account['cosmetics'].append({'type': 'title', 'value': " the " + _class['name']})
                            account['selected_title'] = " the " + _class['name']
                            Config.USERS.update_one({'user_id': ctx.author.id}, {'$set': account})

                            embed = await generate_embed(account, ctx.author, ctx)

                            await msg.clear_reactions()
                            await msg.edit(embed=embed)
                            return
                        else:
                            Config.LOGGING.info("Player selected class they didn't have")

            except asyncio.TimeoutError:
                await ctx.message.delete()
                await msg.delete()
                return None, None


def setup(bot):
    bot.add_cog(Profile(bot))
