import asyncio
import math

import discord
import pymongo
from discord.ext import commands

import Config
import Utils


def skip_limit(page_size, page_num, field):
    """returns a set of documents belonging to page number `page_num`
    where size of each page is `page_size`.
    """
    # Calculate number of documents to skip
    skips = page_size * (page_num - 1)
    if skips < 0:
        skips = 0

    # Skip and limit
    cursor = Config.USERS.aggregate([{"$sort": {field: pymongo.DESCENDING, "user_id": pymongo.DESCENDING}},
                                     {"$match": {'power': {"$gt": 0}}}, {"$skip": skips}, {"$limit": 10}])

    # Return documents
    return [x for x in cursor]


class Leaderboard(commands.Cog):

    async def add_reactions(self, page, msg, field, total):
        """
        Add reactions to the embed
        """
        dic = {'power': 852824647317454910, 'rubies': 676177832963211284,
               'battles.pvp': 670882198450339855, 'coins': 676181520062349322}
        del dic[field]
        if page > 1:
            await msg.add_reaction("⬅️")
        if total > page:
            await msg.add_reaction("➡️")
        for not_field in dic.values():
            emoji = self.bot.get_emoji(not_field)
            await msg.add_reaction(emoji)

    def __init__(self, bot):
        self.bot = bot

    async def generate_lb_embed(self, page, field, total):
        """
        Generate the leaderboard embed to display
        """
        if total < page:
            page = total
        docs = skip_limit(10, page, field)
        embed = discord.Embed(title="Leaderboard", description="", color=Config.MAINCOLOR)
        embed.set_footer(text="Page " + str(page) + " of " + str(total))
        index = (page - 1) * 10
        emoji = {'power': "<:power:852824647317454910>", 'rubies': "<:ruby:676177832963211284>",
                 'battles.pvp': "<:battle:670882198450339855>", 'coins': "<:Coin:676181520062349322>"}
        # Loop through the users and add them
        for doc in docs:
            index += 1
            # try:
            user = await self.bot.fetch_user(doc['user_id'])
            if field == 'battles.pvp':
                embed.description += str(index) + " | " + str(doc['battles']['pvp']) + emoji[field] + " **" +\
                                     user.name + "** \n"
            elif field == 'power':
                embed.description += str(index) + " | " + str(doc[field]) + " " + Utils.get_rank_emoji(doc[field]) + " **" + user.name + \
                                     "** \n"
            else:
                embed.description += str(index) + " | " + str(doc[field]) + emoji[field] + " **" + user.name + \
                                     "** \n"
            # except:
            #     print("Error at line 68 of Leaderboard.py with index " + str(index))

        return embed, page

    async def get_next_reaction(self, ctx, page, msg, field, total):
        """
        Adds the reactions to the embed.
        Starts a wait_for() to see if the user want's to change the lb type
        """
        # Add reactions
        routine = self.bot.loop.create_task(self.add_reactions(page, msg, field, total))

        def check(check_reaction, check_user):
            return check_reaction.me and check_reaction.message.id == msg.id and check_user.id != self.bot.user.id

        # Wait for the user to react
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            dic = {'power': 852824647317454910, 'rubies': 676177832963211284,
                   'battles.pvp': 670882198450339855, 'coins': 676181520062349322}
            # Complete the action the user selected
            if str(reaction) == "➡️":
                page += 1
            elif str(reaction) == "⬅️":
                page -= 1
            else:
                for key, value in dic.items():
                    if reaction.emoji.id == value:
                        field = key

            # Setup next leaderboard
            routine.cancel()
            await msg.clear_reactions()
            await self.restart_leaderboard(page, field, msg, total, ctx)

        # The user didn't react
        except asyncio.TimeoutError:
            routine.cancel()
            await msg.delete()
            await ctx.message.delete()

    async def restart_leaderboard(self, page, field, msg, total, ctx):
        """
        Called if the user reacted on the leaderboard to generate and display the next one
        """
        embed, page = await self.generate_lb_embed(page, field, total)
        await msg.edit(embed=embed)

        await self.get_next_reaction(ctx, page, msg, field, total)

    @commands.command(aliases=['top'])
    async def leaderboard(self, ctx, page: int = 1):
        """
        Command to show the top players in power with reactions to choose other stat type leaderboards
        """
        total = math.ceil(Config.USERS.count_documents({'power': {'$gt': 0}}) / 10)
        field = "power"

        embed, page = await self.generate_lb_embed(page, field, total)
        msg = await ctx.send(embed=embed)

        await self.get_next_reaction(ctx, page, msg, field, total)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
