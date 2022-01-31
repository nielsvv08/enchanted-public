import datetime
import random

import dbl
import aiohttp
import discord
from discord.ext import commands, tasks
import logging

import Config
import Utils


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.token = "!!!! TOPGG TOKEN !!!!"
        self.dblpy = dbl.DBLClient(self.bot, self.token, webhook_path=#PATH,
                                   webhook_auth="!!!! ENCHANTED SECRET !!!!", webhook_port=#PORT)
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "!!! USER AGENT !!!!",
        }
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count"""
        Config.LOGGING.info('Attempting to post server count')

        try:
            await self.dblpy.post_guild_count()
            Config.LOGGING.info('Posted server count ({})'.format(self.dblpy.guild_count()))
        except Exception as e:
            Config.LOGGING.exception('Failed to post server count\n{}: {}'.format(type(e).__name__, e))

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        weekend = False
        data['user'] = int(data['user'])
        account = Utils.get_account(data['user'])
        print(data)
        decide_reward = random.randint(1, 3)

        async with self.session.get("https://top.gg/api/weekend", headers=self.headers) as r:
            weekend = bool((await r.json())["is_weekend"])

        if decide_reward == 1:
            chest_amount = 1
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`1` Chest",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if weekend:
                chest_amount = 2
                embed = discord.Embed(title="Vote Redeemed",
                                      description="Thanks for voting. You have redeemed:\n\n`2` Chests",
                                      color=Config.MAINCOLOR,
                                      timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'chests': chest_amount}})
        elif decide_reward == 2:
            amount = random.randint(20, 50)
            if weekend:
                amount *= 2
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`"+str(amount)+"` Rubies",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if weekend:
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'rubies': amount}})
        elif decide_reward == 3:
            amount = random.randint(20, 70)
            if weekend:
                amount *= 2
            embed = discord.Embed(title="Vote Redeemed",
                                  description="Thanks for voting. You have redeemed:\n\n`"+str(amount)+"` Coins",
                                  color=Config.MAINCOLOR,
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=12))
            embed.set_footer(text="You can vote again at")
            if weekend:
                embed.set_footer(text="2x Vote | You can vote again at")
            Config.USERS.update_one({'user_id': data['user']}, {'$inc': {'coins': amount}})

        if Config.EVENT_ACTIVE == "tower":
            # Let user know they got tickets
            amount = 1
            if weekend:
                amount *= 2
            embed.description += "\n" + str(amount) + " Event Tickets"
            # Add Tickets
            try:
                event_data = account['event']
                event_data['tower']['tickets'] += amount
            except KeyError:
                event_data = {'tower': {'attempts': 0, 'high': 0, 'tickets': 3 + amount}}
            Config.USERS.update_one({'user_id': data['user']}, {'$set': {'event': event_data}})

        try:
            user = await self.bot.fetch_user(int(data['user']))
            await user.send(embed=embed)
        except Exception as e:
            await Config.LOGGING.error('Error occured in voting. Could not find user, or could not DM user. '
                                       'Ignore this as it is not a big deal. But kinda is idk. '
                                       'Its just not the best outcome.')
        Config.LOGGING.info('Received a (' + data['type'] + ') action from : ' + str(data['user']))

    @commands.Cog.listener()
    async def on_dbl_test(self, data):
        Config.LOGGING.info('Received a (' + data['type'] + ') action from : ' + str(data['user']))


def setup(bot):
    global logger
    logger = logging.getLogger('bot')
    bot.add_cog(TopGG(bot))
