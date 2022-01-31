import pymongo
import asyncio
import Config
import discord
from discord.ext import commands, tasks
import logging
import Utils

from Paginator import EmbedPaginatorSession


class Clans(commands.Cog):

    def __init__(self, bot):
        self.upgrading_users = []
        self.bot = bot
        # self.clan_minter.start()
        # self.clan_grinder.start()
        # self.clan_miner.start()
        self.clan_power_update.start()
        self.clan_loop.start()

    def cog_unload(self):
        self.clan_loop.cancel()
        Config.LOGGING.info("Shutdown clan rewards system")

    @tasks.loop(hours=1)
    async def clan_power_update(self):
        Config.LOGGING.info("Starting Clan Power Update loop")
        async for clan in Config.motor_CLANS.find({}):
            all_members = await Config.motor_USERS.find({'user_id': {'$in': clan['members']}}).to_list(None)
            clan['power'] = 0
            for member in all_members:
                if member['power'] > 0:
                    clan['power'] += member['power']
            await Config.motor_CLANS.update_one({'name': clan["name"]}, {
                '$set': {'power': clan['power'], "member_count": len(clan['members'])}})
        Config.LOGGING.info("Completed clan Power Update loop.")

    @tasks.loop(hours=1)
    async def clan_loop(self):
        Config.LOGGING.info("Starting Clan loop")
        async for clan in Config.motor_CLANS.find({}):
            clan['key_storage'] += clan['key_factory']
            if clan['key_storage'] > clan['key_storage_max']:
                clan['key_storage'] = clan['key_storage_max']

            clan['coin_storage'] += clan['coin_mint']
            if clan['coin_storage'] > clan['coin_storage_max']:
                clan['coin_storage'] = clan['coin_storage_max']

            clan['ruby_storage'] += clan['ruby_miner']
            if clan['ruby_storage'] > clan['ruby_storage_max']:
                clan['ruby_storage'] = clan['ruby_storage_max']

            await Config.motor_CLANS.update_one({'name': clan['name']}, {'$set': clan})
        Config.LOGGING.info("Completed clan loop.")

    async def make_clan_embed(self, ctx, clan):
        clan_members = ""
        prefix = Utils.fetch_prefix(ctx)
        owner_name = "Nobody?"
        if clan['member_count'] > 20:
            # Check for paginator
            all_clan_members = list(
                Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
            all_clan_members2 = all_clan_members[15:]
            all_clan_members = all_clan_members[:15]
        else:
            all_clan_members = list(
                Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        i = 0

        # Front page
        for member in all_clan_members:
            i += 1
            try:
                discord_member = await self.bot.fetch_user(member['user_id'])
            except:
                continue
            if 'member_artifacts' not in clan.keys():
                clan['member_artifacts'] = {}
            if str(member['user_id']) not in clan['member_artifacts'].keys():
                artifact = ""
            else:
                artifact = "| **%s**%s" % (
                str(clan['member_artifacts'][str(member['user_id'])]), Config.EMOJI['artifact'])

            if member['user_id'] == clan['owner']:
                clan_members += "\n%s | %s %s %s | 🌟" % (
                i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
                owner_name = discord_member.name
            elif member['user_id'] in clan['admins']:
                clan_members += "\n%s | %s %s %s | ⭐" % (
                i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
            else:
                clan_members += "\n%s | %s %s %s" % (
                    i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
        clan_info = "Name: " + clan['name'] + "\nPower: " + str(clan['power']) + "\nOwner: " + owner_name + "\nIcon: " + \
                    clan['emoji'] + "\nArtifacts: " + str(clan['artifacts']) + " " + Config.EMOJI[
                        'artifact'] + "\n\n**Members (" + str(clan['member_count']) + "/" + str(
            clan['max_members']) + "):**\n" + clan_members
        embed = discord.Embed(title=clan['name'],
                              description=clan_info, color=Config.MAINCOLOR)
        if self.bot.get_emoji(clan['emoji_id']) is not None:
            embed.set_author(name="Clan", icon_url=str(self.bot.get_emoji(clan['emoji_id']).url))
            embed.set_thumbnail(url=str(self.bot.get_emoji(clan['emoji_id']).url))
        embed.add_field(name="Base", value="Ruby Miner: +`" + str(clan['ruby_miner']) + "` " + Config.EMOJI[
            'ruby'] + "/hour\nCoin Mint: +`" + str(clan['coin_mint']) + "` " + Config.EMOJI[
                                               'coin'] + "/hour\nKey Factory: +`" + str(clan['key_factory']) + "` " +
                                           Config.EMOJI['key'] + "/hour")
        embed.add_field(name="Storage", value="Ruby Storage: `" + str(clan['ruby_storage']) + "/" + str(
            clan['ruby_storage_max']) + "` " + Config.EMOJI['ruby'] + "\nCoin Storage: `" + str(
            clan['coin_storage']) + "/" + str(clan['coin_storage_max']) + "` " + Config.EMOJI[
                                                  'coin'] + "\nKey Factory: `" + str(clan['key_storage']) + "/" + str(
            clan['key_storage_max']) + "` " + Config.EMOJI['key'])
        if 'motd' in clan.keys():
            if clan['motd']:
                embed.add_field(name="Clan Message", value=clan['motd'], inline=False)
        embed.set_footer(text=f"{prefix}clan claim, {prefix}clan leave, {prefix}clan upgrade, {prefix}clan help")

        # Check for paginator
        if clan['member_count'] > 20:
            clan_members = ""
            for member in all_clan_members2:
                i += 1
                try:
                    discord_member = await self.bot.fetch_user(member['user_id'])
                except:
                    continue
                if 'member_artifacts' not in clan.keys():
                    clan['member_artifacts'] = {}
                if str(member['user_id']) not in clan['member_artifacts'].keys():
                    artifact = ""
                else:
                    artifact = "| **%s**%s" % (
                    str(clan['member_artifacts'][str(member['user_id'])]), Config.EMOJI['artifact'])

                if member['user_id'] == clan['owner']:
                    clan_members += "\n%s | %s %s %s | 🌟" % (
                    i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
                    owner_name = discord_member.name
                elif member['user_id'] in clan['admins']:
                    clan_members += "\n%s | %s %s %s | ⭐" % (
                    i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
                else:
                    clan_members += "\n%s | %s %s %s" % (
                        i, Utils.get_rank_emoji(member['power']), discord_member.name, artifact)
            clan_info = "Name: " + clan['name'] + "\nPower: " + str(
                clan['power']) + "\nOwner: " + owner_name + "\nIcon: " + \
                        clan['emoji'] + "\nArtifacts: " + str(clan['artifacts']) + " " + Config.EMOJI[
                            'artifact'] + "\n\n**Members (" + str(clan['member_count']) + "/" + str(
                clan['max_members']) + "):**\n" + clan_members
            embed2 = discord.Embed(title=clan['name'],
                                   description=clan_info, color=Config.MAINCOLOR)
            if self.bot.get_emoji(clan['emoji_id']) is not None:
                embed2.set_author(name="Clan", icon_url=str(self.bot.get_emoji(clan['emoji_id']).url))
                embed2.set_thumbnail(url=str(self.bot.get_emoji(clan['emoji_id']).url))
            embed2.add_field(name="Base", value="Ruby Miner: +`" + str(clan['ruby_miner']) + "` " + Config.EMOJI[
                'ruby'] + "/hour\nCoin Mint: +`" + str(clan['coin_mint']) + "` " + Config.EMOJI[
                                                    'coin'] + "/hour\nKey Factory: +`" + str(
                clan['key_factory']) + "` " + Config.EMOJI['key'] + "/hour")
            embed2.add_field(name="Storage", value="Ruby Storage: `" + str(clan['ruby_storage']) + "/" + str(
                clan['ruby_storage_max']) + "` " + Config.EMOJI['ruby'] + "\nCoin Storage: `" + str(
                clan['coin_storage']) + "/" + str(clan['coin_storage_max']) + "` " + Config.EMOJI[
                                                       'coin'] + "\nKey Factory: `" + str(
                clan['key_storage']) + "/" + str(clan['key_storage_max']) + "` " + Config.EMOJI['key'])
            # embed.add_field(name="Members (" + str(clan['member_count']) + "/20):", value=clan_members, inline=False)
            if 'motd' in clan.keys():
                if clan['motd']:
                    embed2.add_field(name="Clan Message", value=clan['motd'], inline=False)
            embed2.set_footer(text=f"{prefix}clan claim, {prefix}clan leave, {prefix}clan upgrade, {prefix}clan help")
            paginator = EmbedPaginatorSession(ctx, embed, embed2)
            await paginator.run()
        else:
            await ctx.send(embed=embed)

    @commands.group(aliases=['clans', 'group', 'groups'])
    async def clan(self, ctx):
        if ctx.invoked_subcommand is None:
            msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
            if account is None:
                return

            clan = Utils.get_user_clan(ctx.author.id)
            prefix = Utils.fetch_prefix(ctx)
            if clan is None:
                recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}}).limit(5))
                clan_string = ""
                for rec_clan in recommended:
                    clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']), prefix, rec_clan['name'])
                embed = discord.Embed(title="Clan", color=Config.MAINCOLOR,
                                      description="Clans are groups of players that band together in order to fight dungeons, get larger rewards, and share resources.\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
                await ctx.send(embed=embed)
            else:
                await self.make_clan_embed(ctx, clan)

    @clan.command()
    async def info(self, ctx, *, name: str = None):
        if name is not None:
            clan = Config.CLANS.find_one({'name': name})
            if clan is None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="That clan does not exist. Sorry about that.")
                await ctx.send(embed=embed)
                return
            else:
                await self.make_clan_embed(ctx, clan)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You need to specify a clan name in order to see info!")
            await ctx.send(embed=embed)

    @clan.command()
    async def top(self, ctx):
        prefix = Utils.fetch_prefix(ctx)
        top = list(Config.CLANS.find({'power': {'$gt': 0}}).sort("power", pymongo.DESCENDING).limit(5))
        clan_string = ""
        for rec_clan in top:
            if len(rec_clan['members']) < rec_clan["max_members"] and rec_clan['open']:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']), prefix, rec_clan['name'])
            else:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']))
        embed = discord.Embed(title="Top Clans", color=Config.MAINCOLOR,
                              description="**Top 5 Clans based on Power:**\n\n" + clan_string)
        await ctx.send(embed=embed)

    @clan.command()
    async def promote(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return

        if ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are not a clan admin!")
            await ctx.send(embed=embed)
        elif member["user_id"] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't promote yourself, nice try though")
            await ctx.send(embed=embed)
        elif member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="That's the owner, silly")
            await ctx.send(embed=embed)
        else:
            discord_member = await self.bot.fetch_user(member["user_id"])
            p = Utils.fetch_prefix(ctx)
            if member["user_id"] in clan['admins']:
                if ctx.author.id != clan['owner']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="That user is already an admin. You cannot promote them any futher.")
                    await ctx.send(embed=embed)
                    return
                embed = discord.Embed(title="Change Clan Ownership?", color=Config.MAINCOLOR,
                                      description=discord_member.name + f" is already a clan admin. React with `✔` to this message to transfer ownership, or `✖` to cancel.")
                msg = await ctx.send(embed=embed)
                await msg.add_reaction("✔")
                await msg.add_reaction("✖")

                def check(reaction, user):
                    return reaction.message.id == msg.id and user.id == ctx.author.id

                try:
                    reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
                    if str(reaction) == "✖":
                        embed = discord.Embed(title="Canceled", color=Config.MAINCOLOR,
                                              description=discord_member.name + f" is still a clan admin. Ownership has not changed")
                        await msg.edit(embed=embed)
                        return
                    Config.CLANS.update_one({'name': clan['name']}, {'$set': {'owner': member["user_id"]}})
                    if member["user_id"] not in clan['admins']:
                        Config.CLANS.update_one({'name': clan['name']}, {'$push': {'admins': member["user_id"]}})

                    embed = discord.Embed(title="Ownership changed", color=Config.MAINCOLOR,
                                          description=discord_member.name + f" is now the owner of **{clan['name']}** {clan['emoji']}")
                    await msg.edit(embed=embed)
                except asyncio.TimeoutError:
                    embed = discord.Embed(title="Canceled", color=Config.MAINCOLOR,
                                          description=discord_member.name + f" is still a clan admin. Ownership has not changed")
                    await msg.edit(embed=embed)
                    return
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$push': {'admins': member["user_id"]}})
                embed = discord.Embed(title="Welcome aboard!", color=Config.MAINCOLOR,
                                      description=discord_member.name + " is now a clan admin. They can edit the clan, and manage members.")
                await ctx.send(embed=embed)

    @clan.command()
    async def demote(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return

        if ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are not a clan admin!")
            await ctx.send(embed=embed)
        elif member["user_id"] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You cannot demote yourself!")
            await ctx.send(embed=embed)
        elif member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You cannot demote the clan owner!")
            await ctx.send(embed=embed)
        else:
            discord_member = await self.bot.fetch_user(member["user_id"])
            p = Utils.fetch_prefix(ctx)
            if member["user_id"] not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description=member.name + f" is not a clan admin. Use `{p}clan promote {discord_member.name}` to promote them.")
                await ctx.send(embed=embed)
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$pull': {'admins': member["user_id"]}})
                embed = discord.Embed(title="C ya later!", color=Config.MAINCOLOR,
                                      description=discord_member.name + " is no longer a clan admin. They cannot edit the clan or manage members anymore.")
                await ctx.send(embed=embed)

    @clan.command()
    async def create(self, ctx, *, name):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            if Config.CLANS.find_one({'name': name}) is not None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="A clan already exists with that name! try using something else.")
                await ctx.send(embed=embed)
            elif len(name) > 30:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="That's too long! A clan name must be 30 characters or less.")
                await ctx.send(embed=embed)
            else:
                power = account['power']
                if account['power'] < 0:
                    power = 0
                Config.CLANS.insert_one(
                    {'name': name, 'emoji': "<:C:731873623840784434>", 'emoji_id': 731873623840784434,
                     'members': [ctx.author.id], 'member_artifacts': {}, 'member_count': 1, 'max_members': 20,
                     'artifacts': 0, 'owner': ctx.author.id, 'admins': [ctx.author.id],
                     'power': power, 'open': True, 'color': str(Config.MAINCOLOR), 'bans': [],
                     'ruby_miner': 10, 'coin_mint': 30, 'key_factory': 5,
                     'ruby_storage': 0, 'ruby_storage_max': 30, 'coin_storage': 0, 'coin_storage_max': 120,
                     'key_storage': 0, 'key_storage_max': 15})

                embed = discord.Embed(title="Clan created", color=Config.MAINCOLOR,
                                      description=f"You can view your clan with the `{prefix}clan` command. Edit your clan with the `{prefix}clan edit` command. Good luck!")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You are already in a clan!")
            await ctx.send(embed=embed)

    async def do_upgrade_loop(self, ctx, clan, msg, part, add):
        if part in ["max_members", "key_factory", "key_storage_max"]:
            cost = Utils.calc_clan_upgrade_cost(round(clan[part.lower()] * 4.5))
        elif part in ["coin_storage_max"]:
            cost = Utils.calc_clan_upgrade_cost(round(clan[part.lower()] / 2.5))
        elif part in ["ruby_storage_max"]:
            cost = Utils.calc_clan_upgrade_cost(round(clan[part.lower()] / 1.5))
        else:
            cost = Utils.calc_clan_upgrade_cost(round(clan[part.lower()] / 1.2))
        more_output = 1
        if part in ["key_factory", "ruby_miner", "coin_mint"]:
            embed = discord.Embed(
                title="Upgrade `" + part.title().replace("_", " ") + "` to `" + str((clan[part] + add)) + "`/hour?",
                description=
                "Clan Artifacts: `" + str(clan['artifacts']) + "`\n" +
                "Cost: `" + str(cost) + "` " + Config.EMOJI['artifact']
                + f"\nUpgrades: `{clan[part]}` → `{clan[part] + add}` per hour"
                + "\n\n*Click the reaction to upgrade\nwait to cancel*", color=Config.MAINCOLOR)
        else:
            embed = discord.Embed(
                title="Upgrade `" + part.title().replace("_", " ") + "` to `" + str((clan[part] + add)) + "`?",
                description=
                "Clan Artifacts: `" + str(clan['artifacts']) + "`\n" +
                "Cost: `" + str(cost) + "` " + Config.EMOJI['artifact']
                + f"\nUpgrades: `{clan[part]}` → `{clan[part] + add}`"
                + "\n\n*Click the reaction to upgrade\nwait to cancel*", color=Config.MAINCOLOR)
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✅")

        def check(reaction, user):
            return reaction.message.id == msg.id and user.id == ctx.author.id and reaction.me

        try:
            if clan['artifacts'] < cost:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have enough artifacts to upgrade this item...",
                                      color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, clan, msg

            maxed = False
            if part == "ruby_storage_max":
                if clan["ruby_storage_max"] >= 120:
                    maxed = True
            elif part == "ruby_miner":
                if clan["ruby_miner"] >= 40:
                    maxed = True
            elif part == "coin_storage_max":
                if clan["coin_storage_max"] >= 240:
                    maxed = True
            elif part == "coin_mint":
                if clan["coin_mint"] >= 80:
                    maxed = True
            elif part == "key_storage_max":
                if clan["key_storage_max"] >= 45:
                    maxed = True
            elif part == "key_factory":
                if clan["key_factory"] >= 15:
                    maxed = True
            elif part == "max_members":
                if clan["max_members"] >= 30:
                    maxed = True

            if maxed:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="The thing you are trying to upgrade has been maxed out already!")
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    msg = await ctx.send(embed=embed)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, clan, msg

            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=60)
            await reaction.remove(user)
            clan = Utils.get_user_clan(ctx.author.id)
            if clan['artifacts'] < cost:
                embed = discord.Embed(title="Wait a second",
                                      description="You don't have enough artifacts to upgrade this...",
                                      color=Config.MAINCOLOR)
                await msg.edit(embed=embed)
                await msg.clear_reactions()
                await asyncio.sleep(3)
                return False, 0, 0, 0, clan, msg

            clan[part] += add
            clan['artifacts'] -= cost

            Config.CLANS.update_one({'name': clan['name']}, {'$inc': {'artifacts': -cost, part: add}})
            clan = Utils.get_user_clan(ctx.author.id)
            return True, cost, more_output, 1, clan, msg
        except asyncio.TimeoutError:
            return False, 0, 0, 0, clan, msg

    @clan.command()
    async def message(self, ctx, *, content: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan admin!")
            elif content is None:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You must provide a message!")
            elif len(content) > 100:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="Your message must be under 100 characters in length.")
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'motd': content}})
                embed = discord.Embed(title="Message Set!", color=Config.MAINCOLOR,
                                      description="Your message has been set!\n```\n" + content + "\n```")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

    @clan.command()
    async def upgrade(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan leader!")
                await ctx.send(embed=embed)
            else:
                if True:
                    part = None
                    embed = discord.Embed(
                        title="Clan Upgrade Menu",
                        description="Select the category you want to upgrade:\n"
                                    + "🔧: Generators\n"
                                    + "🧺: Storage\n"
                                    + "⬆️: Max Members\n",
                        color=Config.MAINCOLOR
                    )

                    msg = await ctx.send(embed=embed)
                    await msg.add_reaction("🔧")
                    await msg.add_reaction("🧺")
                    await msg.add_reaction("⬆️")
                    menu = None

                    def check(reaction, user):
                        return reaction.message.id == msg.id and user.id == ctx.author.id

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
                        if str(reaction) == "🔧":
                            menu = "Generator"
                            await msg.clear_reactions()
                        elif str(reaction) == "🧺":
                            menu = "Storage"
                            await msg.clear_reactions()
                        elif str(reaction) == "⬆️":
                            if clan["max_members"] < 30:
                                menu = "Max Members"
                                part = "max_members"
                                add = 1
                            else:
                                menu = "maxed"
                            await msg.clear_reactions()
                        else:
                            embed.set_footer(text="Time-out!")
                            await msg.clear_reactions()
                            await msg.edit(embed=embed)
                            return
                    except asyncio.TimeoutError:
                        embed.set_footer(text="Time-out!")
                        await msg.clear_reactions()
                        await msg.edit(embed=embed)
                        return

                    if menu == "Generator" or menu == "Storage":
                        embed = discord.Embed(
                            title="Clan Upgrade Menu",
                            description="Select the resource you want to upgrade:\n"
                                        + Config.EMOJI["ruby"] + ": Rubies\n"
                                        + Config.EMOJI["coin"] + ": Coins\n"
                                        + Config.EMOJI["key"] + ": Keys\n",
                            color=Config.MAINCOLOR
                        )
                        if msg is not None:
                            await msg.edit(embed=embed)
                        else:
                            msg = await ctx.send(embed=embed)

                        await msg.add_reaction(Config.EMOJI["ruby"])
                        await msg.add_reaction(Config.EMOJI["coin"])
                        await msg.add_reaction(Config.EMOJI["key"])

                        def check(reaction, user):
                            return reaction.message.id == msg.id and user.id == ctx.author.id

                        try:
                            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
                            if str(reaction) == Config.EMOJI["ruby"]:
                                if menu == "Storage":
                                    if clan["ruby_storage_max"] < 120:
                                        part = "ruby_storage_max"
                                        add = 9
                                    else:
                                        menu = "maxed"
                                else:
                                    if clan["ruby_miner"] < 40:
                                        part = "ruby_miner"
                                        add = 3
                                    else:
                                        menu = "maxed"
                                await msg.clear_reactions()
                            elif str(reaction) == Config.EMOJI["coin"]:
                                if menu == "Storage":
                                    if clan["coin_storage_max"] < 240:
                                        part = "coin_storage_max"
                                        add = 15
                                    else:
                                        menu = "maxed"
                                else:
                                    if clan["coin_mint"] < 80:
                                        part = "coin_mint"
                                        add = 5
                                    else:
                                        menu = "maxed"
                                await msg.clear_reactions()
                            elif str(reaction) == Config.EMOJI["key"]:
                                if menu == "Storage":
                                    if clan["key_storage_max"] < 45:
                                        part = "key_storage_max"
                                        add = 3
                                    else:
                                        menu = "maxed"
                                else:
                                    if clan["key_factory"] < 15:
                                        part = "key_factory"
                                        add = 1
                                    else:
                                        menu = "maxed"
                                await msg.clear_reactions()
                            else:
                                embed.set_footer(text="Time-out!")
                                await msg.clear_reactions()
                                await msg.edit(embed=embed)
                                return
                        except asyncio.TimeoutError:
                            embed.set_footer(text="Time-out!")
                            await msg.clear_reactions()
                            await msg.edit(embed=embed)
                            return
                    elif menu is None:
                        return await ctx.send("Huts")

                    if menu == "maxed":
                        embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                              description="The thing you are trying to upgrade has been maxed out already!")
                        if msg is not None:
                            await msg.edit(embed=embed)
                        else:
                            msg = await ctx.send(embed=embed)
                        return

                    if ctx.author.id not in self.upgrading_users:
                        self.upgrading_users.append(ctx.author.id)
                    archived_clan = clan.copy()
                    do_continue = True
                    total_cost = 0
                    total_output = 0
                    total_upgrades = 0
                    while do_continue:
                        do_continue, more_cost, more_upgrades, more_output, clan, msg = await self.do_upgrade_loop(
                            ctx, clan, msg, part, add)
                        total_cost += more_cost
                        total_output += more_output
                        total_upgrades += more_upgrades
                    try:
                        if archived_clan[part] == clan[part]:
                            return
                        await msg.clear_reactions()
                        if part in ["key_factory", "ruby_miner", "coin_mint"]:
                            embed = discord.Embed(
                                title="Upgraded `" + part.title().replace("_", " ") + "` from `" + str(
                                    archived_clan[part]) + "`/hour to `" + str(clan[part]) + "`/hour",
                                description=
                                "Total Cost: `" + str(total_cost) + "` " + Config.EMOJI['artifact']
                                + f"\nUpgrades: `{archived_clan[part]}` → `{clan[part]}`",
                                color=Config.MAINCOLOR)
                        else:
                            embed = discord.Embed(
                                title="Upgraded `" + part.title().replace("_", " ") + "` from `" + str(
                                    archived_clan[part]) + "` to `" + str(clan[part]) + "`",
                                description=
                                "Total Cost: `" + str(total_cost) + "` " + Config.EMOJI['artifact']
                                + f"\nUpgrades: `{archived_clan[part]}` → `{clan[part]}`",
                                color=Config.MAINCOLOR)
                        await msg.edit(embed=embed)
                    except:
                        await Config.LOGGING.error("Issue with upgrading. Error editing message.")
                    finally:
                        if ctx.author.id in self.upgrading_users:
                            self.upgrading_users.remove(ctx.author.id)

    @clan.command(name="help")
    async def _help(self, ctx):
        prefix = Utils.fetch_prefix(ctx)
        embed = discord.Embed(title="Clan Command Help", color=Config.MAINCOLOR,
                              description=f"`{prefix}clan` - Show info about your clan"
                                          f"\n`{prefix}clan help` - Shows this embed"
                                          f"\n`{prefix}clan info <name>` - Shows info about a clan"
                                          f"\n`{prefix}clan join <name>` - Join a clan"
                                          f"\n`{prefix}clan leave` - Leave your current clan"
                                          f"\n`{prefix}clan create <name>` - Create a clan"
                                          f"\n`{prefix}clan claim` - Collect the resources in the clan's storage for everyone"
                                          f"\n⭐`{prefix}clan edit <attribute> <value>` - Edit a clan that you own"
                                          f"\n⭐`{prefix}clan message <message>` - Set your description"
                                          f"\n⭐`{prefix}clan upgrade` - Upgrade a part of your clan base"
                                          f"\n⭐`{prefix}clan kick <member>` - Kick a member from your clan"
                                          f"\n⭐`{prefix}clan promote <member>` - Promote a member to admin status"
                                          f"\n🌟`{prefix}clan demote <member>` - Demote a member from admin status"
                                          f"\n🌟`{prefix}clan disband` - Disband a clan that you own"
                                          f"\n\n*⭐ specifies an admin only command\n🌟 specifies an owner only command.*")
        await ctx.send(embed=embed)

    @clan.command()
    async def join(self, ctx, *, name: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            if name is None:
                prefix = Utils.fetch_prefix(ctx)
                recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
                clan_string = ""
                for rec_clan in recommended:
                    clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                        rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                        str(rec_clan['max_members']), prefix, rec_clan['name'])
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You must specify a clan to join!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
                await ctx.send(embed=embed)
            else:
                joining_clan = Config.CLANS.find_one({'name': name})
                if joining_clan is None:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="That clan does not exist. Sorry about that.")
                    await ctx.send(embed=embed)
                elif ctx.author.id in joining_clan['bans']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="You have been banned from this club!")
                    await ctx.send(embed=embed)
                elif not joining_clan['open']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="This clan is not accepting new members.")
                    await ctx.send(embed=embed)
                elif len(joining_clan['members']) >= joining_clan['max_members']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="This clan is full!")
                    await ctx.send(embed=embed)
                else:
                    if account['power'] > 0:
                        Config.CLANS.update_one({'name': name}, {'$set': {'member_count': len(joining_clan['members']) + 1,
                                                                          'power': joining_clan['power'] + account[
                                                                              'power']},
                                                                 '$push': {'members': ctx.author.id}})
                    else:
                        Config.CLANS.update_one({'name': name},
                                                {'$set': {'member_count': len(joining_clan['members']) + 1,
                                                          'power': joining_clan['power']},
                                                 '$push': {'members': ctx.author.id}})
                    embed = discord.Embed(title="Welcome to the clan!", color=Config.MAINCOLOR,
                                          description="You have successfully joined **%s** %s" % (
                                          joining_clan['name'], joining_clan['emoji']))
                    await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"You are already in a clan. If you would like to join a new one, please use `{prefix}clan leave` first.")
            await ctx.send(embed=embed)

    @clan.command()
    async def claim(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" %\
                               (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']),
                                str(rec_clan['member_count']), str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        else:
            result = Config.USERS.update_many({'user_id': {'$in': clan['members']}}, {
                '$inc': {'coins': clan['coin_storage'], 'rubies': clan['ruby_storage'], 'keys': clan['key_storage']}})
            Config.LOGGING.info("Claimed for " + str(result.modified_count) + " users.")
            Config.CLANS.update_one({'name': clan['name']},
                                    {'$set': {'coin_storage': 0, 'ruby_storage': 0, 'key_storage': 0}})
            embed = discord.Embed(title="Resources Claimed", color=Config.MAINCOLOR,
                                  description="You have claimed resources from your clan base for everyone:\n\n+`" + str(
                                      clan['ruby_storage']) + "` " + Config.EMOJI['ruby'] + "\n+`" + str(
                                      clan['key_storage']) + "` " + Config.EMOJI['key'] + "\n+`" + str(
                                      clan['coin_storage']) + "` " + Config.EMOJI['coin'])
            await ctx.send(embed=embed)

    @clan.command()
    async def leave(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" % (
                    rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']), str(rec_clan['member_count']),
                    str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        elif clan['owner'] == ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"You can't leave your own clan! If you would like to disband it, use `{prefix}clan disband`")
            await ctx.send(embed=embed)
        else:
            if account['power'] > 0:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power'] - account['power']},
                                                                 '$pull': {'members': ctx.author.id,
                                                                           'admins': ctx.author.id}})
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power']},
                                                                 '$pull': {'members': ctx.author.id,
                                                                           'admins': ctx.author.id}})
            embed = discord.Embed(title="Sad to see you go!", color=Config.MAINCOLOR,
                                  description="You have successfully left **%s** %s" % (clan['name'], clan['emoji']))
            await ctx.send(embed=embed)

    @clan.command()
    async def kick(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" %\
                               (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']),
                                str(rec_clan['member_count']), str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return
        if clan['owner'] != ctx.author.id and ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You don't have the permissions to kick somebody from the clan!")
            return await ctx.send(embed=embed)
        choice -= 1
        if member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't kick the owner of a clan!")
            await ctx.send(embed=embed)
        elif member["user_id"] in clan['admins'] and ctx.author.id != clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't kick a fellow clan admin!")
            await ctx.send(embed=embed)
        else:
            if member['power'] > 0:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power'] - member['power']},
                                                                 '$pull': {'members': member["user_id"],
                                                                           'admins': member['user_id']}})
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power']},
                                                                 '$pull': {'members': member["user_id"],
                                                                           'admins': member['user_id']}})
            discord_member = await self.bot.fetch_user(member["user_id"])
            embed = discord.Embed(title="There must be a reason...", color=Config.MAINCOLOR,
                                  description="You have successfully kicked %s from **%s** %s" % (
                                  discord_member.name, clan['name'], clan['emoji']))
            await ctx.send(embed=embed)

    @clan.command()
    async def disband(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        prefix = Utils.fetch_prefix(ctx)
        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            prefix = Utils.fetch_prefix(ctx)
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" %\
                               (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']),
                                str(rec_clan['member_count']), str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        elif clan['owner'] != ctx.author.id:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description=f"Yopu cannot disband a clan you don't own. use `{prefix}clan leave` to leave it instead.")
            await ctx.send(embed=embed)
        else:
            Config.CLANS.delete_one({'name': clan['name']})
            embed = discord.Embed(title="There were many adventures!", color=Config.MAINCOLOR,
                                  description="You have successfully disbanded **%s** %s" % (
                                      clan['name'], clan['emoji']))
            await ctx.send(embed=embed)
            if clan['emoji_id'] != 675820506284556306:
                old_emoji = self.bot.get_emoji(clan['emoji_id'])
                if old_emoji is not None:
                    await old_emoji.delete()

    @clan.command()
    async def edit(self, ctx, attribute: str = None, *, value=None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must create a clan before you can do that!")
            await ctx.send(embed=embed)
        else:
            if ctx.author.id not in clan['admins']:
                embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                      description="You are not a clan admin!")
                await ctx.send(embed=embed)
            else:
                if attribute is None:
                    attribute = "None"
                if attribute.lower() not in ['name', 'icon', 'invite']:
                    embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                          description="That's not a valid clan attribute you can change, sorry about that. Here are the things you can edit:\n`name`, `icon`, `invite`")
                    await ctx.send(embed=embed)
                else:
                    if attribute.lower() == "name":
                        if value is None:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="You can't change your clan name to nothing! Please specify a name.")
                            await ctx.send(embed=embed)
                        elif Config.CLANS.find_one({'name': value}) is not None:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="A clan already exists with that name! try using something else.")
                            await ctx.send(embed=embed)
                        elif len(value) > 30:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="That's too long! A clan name must be 30 characters or less.")
                            await ctx.send(embed=embed)
                        else:
                            Config.CLANS.update_one({'name': clan['name']}, {'$set': {'name': value}})
                            embed = discord.Embed(title="Nice name!", color=Config.MAINCOLOR,
                                                  description="You clan is now called: **%s** %s" % (
                                                  value, clan['emoji']))
                            await ctx.send(embed=embed)
                    elif attribute.lower() == "icon":
                        if len(ctx.message.attachments) < 1:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="Please upload an image or gif with the message to change the icon. (put the command in the caption)")
                            await ctx.send(embed=embed)
                        else:
                            for host in Config.CLAN_EMOTE_HOSTS:
                                guild_obj = self.bot.get_guild(host)
                                if guild_obj is None:
                                    continue
                                elif len(guild_obj.emojis) >= guild_obj.emoji_limit:
                                    continue
                                else:
                                    with open(f"temp/{ctx.message.attachments[0].filename}", 'wb+') as fp:
                                        await ctx.message.attachments[0].save(fp)
                                    with open(f"temp/{ctx.message.attachments[0].filename}", 'rb') as new_image:
                                        try:
                                            emoji = await guild_obj.create_custom_emoji(
                                                name="Clan_Icon_" + str(len(guild_obj.emojis)), image=new_image.read(),
                                                reason=ctx.author.name + " updating icon for clan " + clan['name'])
                                        except Exception as e:
                                            await Config.LOGGING.error(str(e))
                                            continue
                                    emoji_string = ""
                                    if emoji.animated:
                                        emoji_string = "<a:" + str(emoji.name) + ":" + str(emoji.id) + ">"
                                    else:
                                        emoji_string = "<:" + str(emoji.name) + ":" + str(emoji.id) + ">"
                                    Config.CLANS.update_one({'name': clan['name']},
                                                            {'$set': {'emoji': emoji_string, 'emoji_id': emoji.id}})
                                    if clan['emoji_id'] != 675820506284556306:
                                        old_emoji = self.bot.get_emoji(clan['emoji_id'])
                                        if old_emoji is not None:
                                            await old_emoji.delete()
                                    embed = discord.Embed(title="Icon Changed", color=Config.MAINCOLOR,
                                                          description="Your clan's icon has changed to " + emoji_string)
                                    await ctx.send(embed=embed)
                                    return
                            embed = discord.Embed(title="Uh oh..", color=Config.MAINCOLOR,
                                                  description="We could not change your clan icon at this time. We are sorry about this.")
                            await ctx.send(embed=embed)
                    elif attribute.lower() == "invite":
                        if value is None:
                            value = ""
                        if value.lower() not in ['open', 'closed']:
                            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                                  description="Please specify whether you want your clan to be `open` or `closed`.")
                            await ctx.send(embed=embed)
                        else:
                            if value.lower() == "open":
                                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'open': True}})
                                embed = discord.Embed(title="Clan invite status updated", color=Config.MAINCOLOR,
                                                      description="Your clan is now open and people can join!")
                                await ctx.send(embed=embed)
                            elif value.lower() == "closed":
                                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'open': False}})
                                embed = discord.Embed(title="Clan invite status updated", color=Config.MAINCOLOR,
                                                      description="Your clan is closed. Nobody can join.")
                                await ctx.send(embed=embed)
                            else:
                                embed = discord.Embed(title="oh dear", color=Config.MAINCOLOR,
                                                      description="something has gone very, very wrong.")
                                await ctx.send(embed=embed)

    @clan.command()
    async def ban(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        prefix = Utils.fetch_prefix(ctx)
        if clan is None:
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" %\
                               (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']),
                                str(rec_clan['member_count']), str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        if choice == 0:
            i = 0
            clan_info = ""
            if len(clan["bans"]) > 0:
                clan_base = ""
            else:
                clan_base = "There aren't any bans yet\n"
            for ban in clan["bans"]:
                i += 1
                try:
                    discord_member = await self.bot.fetch_user(ban)
                except:
                    continue
                clan_info += discord_member.name + " (" + str(discord_member.id) + ")\n"
            if clan_base == "":
                clan_base = f"**Bans:** {str(i)}\n\n"
            embed = discord.Embed(title=clan['name'] + " | Ban List",
                                  description=clan_base + clan_info + f"\n*To unban do* `{prefix}clan unban <id>`",
                                  color=Config.MAINCOLOR)
            if self.bot.get_emoji(clan['emoji_id']) is not None:
                embed.set_author(name="Clan", icon_url=str(self.bot.get_emoji(clan['emoji_id']).url))
                embed.set_thumbnail(url=str(self.bot.get_emoji(clan['emoji_id']).url))
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        if choice > clan["member_count"] or choice < 1:
            embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                clan["member_count"]) + " members in your clan. Try using a number 1-" + str(clan["member_count"]),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        all_clan_members = list(
            Config.USERS.find({'user_id': {'$in': clan['members']}}).sort("power", pymongo.DESCENDING))
        m_int = 0
        member = None
        for members in all_clan_members:
            m_int += 1
            if m_int == choice:
                member = members
        if not member:
            return
        if clan['owner'] != ctx.author.id and ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You don't have the permissions to ban somebody from the clan!")
            return await ctx.send(embed=embed)
        choice -= 1
        if member["user_id"] == clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't ban the owner of a clan!")
            await ctx.send(embed=embed)
        elif member["user_id"] in clan['admins'] and ctx.author.id != clan['owner']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You can't ban a fellow clan admin!")
            await ctx.send(embed=embed)
        else:
            if member['power'] > 0:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power'] - member['power']},
                                                                 '$pull': {'members': member["user_id"]},
                                                                 '$push': {'bans': member["user_id"]}})
            else:
                Config.CLANS.update_one({'name': clan['name']}, {'$set': {'member_count': len(clan['members']) - 1,
                                                                          'power': clan['power']},
                                                                 '$pull': {'members': member["user_id"],
                                                                           'admins': member['user_id']}})
            discord_member = await self.bot.fetch_user(member["user_id"])
            embed = discord.Embed(title="There must be a reason...", color=Config.MAINCOLOR,
                                  description="You have successfully banned %s from **%s** %s" % (
                                  discord_member.name, clan['name'], clan['emoji']))
            await ctx.send(embed=embed)

    @clan.command()
    async def unban(self, ctx, choice: int = 0):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        clan = Utils.get_user_clan(ctx.author.id)
        prefix = Utils.fetch_prefix(ctx)
        if clan is None:
            recommended = list(Config.CLANS.find({'member_count': {'$lt': 20}, 'open': True}).limit(5))
            clan_string = ""
            for rec_clan in recommended:
                clan_string += "%s %s\n  ⌞ Power: `%s` | Members: `%s/%s`\n  ⌞ Join: **`%sclan join %s`**\n\n" %\
                               (rec_clan['emoji'], rec_clan['name'], str(rec_clan['power']),
                                str(rec_clan['member_count']), str(rec_clan['max_members']), prefix, rec_clan['name'])
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You must be in a clan to use this command!\n\n**Recommended clans:**\n\n" + clan_string + f"\n\n`{prefix}clan join <name>`\n`{prefix}clan leave`\n`{prefix}clan create <name>`")
            await ctx.send(embed=embed)
        if clan['owner'] != ctx.author.id and ctx.author.id not in clan['admins']:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="You don't have the permissions to ban somebody from the clan!")
            return await ctx.send(embed=embed)
        if choice == 0:
            embed = discord.Embed(title="Wait a second!", color=Config.MAINCOLOR,
                                  description="Please define an user id!")
            await ctx.send(embed=embed)
        if choice not in clan["bans"]:
            embed = discord.Embed(title="Hmmmm...",
                                  description="This person is not on the ban list. Please get the correct user ID from the ban list!",
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return
        else:
            Config.CLANS.update_one({'name': clan['name']}, {'$pull': {'bans': choice}})
            discord_member = await self.bot.fetch_user(choice)
            embed = discord.Embed(title="Sorry (not sorry?)", color=Config.MAINCOLOR,
                                  description="You have successfully unbanned %s from **%s** %s" % (
                                  discord_member.name, clan['name'], clan['emoji']))
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Clans(bot))
