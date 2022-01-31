import asyncio
import datetime
import random
import sys
import time

import discord
from discord.ext import commands, tasks

import Battle_Utils
import Config
import Utils


class Matchmaking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.battles = 0
        self.battling_users = []
        self.friendly_matchmaking = []
        self.chats = []
        self.matchmaking.start()
        self.ticket_garbage.start()

    def cog_unload(self):
        Config.LOGGING.info("Shutting down matchmaking system")
        self.matchmaking.cancel()
        Config.LOGGING.info("Shutting down queue cleaning system")
        self.ticket_garbage.cancel()

    async def setup_field(self, match):
        field_description = "╔ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        found = False
        for chat in self.chats:
            if match[0]['account']['user_id'] in chat[0]["ids"]:
                for c in chat[1:]:
                    field_description += f"│ **{c['user']}**: {c['msg']}\n"
                    found = True
        if not found:
            field_description += f"│ *No chat logs, use the chat command to chat*\n"
        field_description += "╚ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"

        return field_description

    async def construct_embeds(self, match, turn):
        for _ in range(2):
            embed = Battle_Utils.construct_pvp_embed(match, turn, _, await self.setup_field(match))
            await match[_]['message'].edit(embed=embed)

    async def construct_embeds_with_message(self, turn, match, message):
        for _ in range(2):
            embed = Battle_Utils.construct_pvp_embed_with_message(match, turn, _, await self.setup_field(match), message)
            await match[_]['message'].edit(embed=embed)

    async def battle_thread(self, match):
        try:
            Config.LOGGING.info("Battle thread started: Current threads: " + str(self.battles))
            self.battling_users.append({"id": match[0]['ctx'].author.id, "time": time.time()})
            self.battling_users.append({"id": match[1]['ctx'].author.id, "time": time.time()})
            turn = random.randint(0, 1)
            total_turns = 1

            draw = False
            match[0]['health'] = match[0]['account']['stats']['health']
            embed = discord.Embed(title="Match Started", color=Config.MAINCOLOR,
                                  description="[jump](" + match[0]['message'].jump_url + ")")
            one_message = await match[0]['ctx'].send(match[0]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)
            embed = discord.Embed(title="Match Started", color=Config.MAINCOLOR,
                                  description="[jump](" + match[1]['message'].jump_url + ")")
            one_message = await match[1]['ctx'].send(match[1]['ctx'].author.mention, embed=embed)
            await one_message.delete(delay=10)
            match[1]['health'] = match[1]['account']['stats']['health']
            match[0]['mana'] = match[0]['account']['stats']['endurance']
            match[1]['mana'] = match[1]['account']['stats']['endurance']
            match[0]['effects'] = []
            match[1]['effects'] = []
            match[0]['afk'] = 0
            match[1]['afk'] = 0
            a_turn = False

            for _ in range(2):
                if match[_]['armor'] is not None:
                    if match[_]['account']['armor'] is not None:
                        match[_]['account']['stats']['defense'] += Utils.calc_item_effect(match[_]["account"]["armor"],
                                                                                          match[_]['armor'])
                if match[_]['weapon'] is not None:
                    if match[_]['account']['weapon'] is not None:
                        match[_]['account']['stats']['strength'] += Utils.calc_item_effect(
                            match[_]["account"]["weapon"], match[_]['weapon'])

                if match[_]['account']['slots'][0] is not None:
                    await match[_]['message'].add_reaction("1️⃣")
                if match[_]['account']['slots'][1] is not None:
                    await match[_]['message'].add_reaction("2️⃣")
                if match[_]['account']['slots'][2] is not None:
                    await match[_]['message'].add_reaction("3️⃣")
                if match[_]['account']['slots'][3] is not None:
                    await match[_]['message'].add_reaction("4️⃣")
                if len(match[_]['account']['slots']) >= 5:
                    if match[_]['account']['slots'][4] is not None:
                        await match[_]['message'].add_reaction("🔆")
                await match[_]['message'].add_reaction("💤")
            while match[0]['health'] > 0 and match[1]['health'] > 0 and match[0]['mana'] > 0 and \
                    match[1]['mana'] > 0 and total_turns < 100:
                if match[turn]['afk'] > 2:
                    match[turn]['health'] = 0
                    match[turn]['mana'] = 0
                    continue

                # calculate effects for beginning of round
                for _ in range(2):
                    effects_remove = []
                    for effect in match[_]['effects']:
                        if effect["name"] in ["Regenerating", "Restoring"]:
                            match[_][effect['type']] += effect['amount']
                        else:
                            match[_][effect['type']] -= effect['amount']
                        match[_][effect['type']] = round(match[_][effect['type']], 1)
                        effect['turns'] -= 1
                        if effect['turns'] < 1:
                            effects_remove.append(effect)
                    for effect in effects_remove:
                        match[_]['effects'].remove(effect)

                # add mana to player
                resource = 'mana'
                resource_number = 3
                if match[turn]['ability'] is not None:
                    if match[turn]['ability'] == "Healing Blood":
                        resource = 'health'
                        resource_number = 5
                    elif match[turn]['ability'] == "Inner Light":
                        resource_number = 6
                if match[int(not bool(turn))]['ability'] is not None:
                    if match[int(not bool(turn))]["ability"] == "Stagnation":
                        if match[turn]['ability'] == "Healing Blood":
                            resource = 'health'
                            resource_number = 2.5
                        elif match[turn]['ability'] == "Inner Light":
                            resource_number = 3
                        else:
                            resource_number = 1.5

                if not (match[0]['health'] > 0 and match[1]['health'] > 0 and match[0]['mana'] > 0 and
                        match[1]['mana'] > 0):
                    break

                if a_turn is True:
                    resource_number = 0
                    a_turn = False
                elif match[turn]['stunned']:
                    resource_number = 0

                match[turn][resource] += resource_number

                match = Battle_Utils.match_check(match)

                for _ in range(2):
                    if match[_]['health'] <= 0 or match[_]['mana'] <= 0:
                        break

                total_turns += 1

                await self.construct_embeds(match, turn)
                try:
                    # Check if the user is stunned
                    if match[turn]['stunned']:
                        match[turn]['stunned'] = False
                        await asyncio.sleep(3)
                        turn = turn = int(not bool(turn))
                        continue

                    reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '🔆': 4, '💤': 5}

                    def check(payload):
                        if payload.user_id == match[turn]['ctx'].author.id and \
                                payload.message_id == match[turn]['message'].id:
                            if str(payload.emoji) in reaction_dict.keys():
                                if reaction_dict[str(payload.emoji)] < 5:
                                    return match[turn]['account']['slots'][
                                               reaction_dict[str(payload.emoji)]] is not None
                                else:
                                    return True
                        return False

                    temp_msg = await match[turn]['ctx'].channel.fetch_message(match[turn]['message'].id)
                    reaction = None
                    for temp_reaction in temp_msg.reactions:
                        users = await temp_reaction.users().flatten()
                        if match[turn]['ctx'].author.id in [x.id for x in users] and temp_reaction.me:
                            can_continue = True
                            reaction = temp_reaction
                            try:
                                await temp_reaction.remove(match[turn]['ctx'].author)
                            except:
                                await Config.LOGGING.error("Cannot remove emoji (not a big deal)")
                    if reaction is None:
                        payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                        reaction = payload.emoji
                        try:
                            await match[turn]['message'].remove_reaction(payload.emoji, match[turn]['ctx'].author)
                        except:
                            await Config.LOGGING.error("Cannot remove emoji (not big deal)")
                    if str(reaction) == "💤":
                        turn = int(not bool(turn))
                        continue
                    elif str(reaction) == "🔆" and match[turn]["ability"] is not None:
                        a_turn = True
                    elif str(reaction) == "🔆" and match[turn]["ability"] is None:
                        ability = Utils.get_ability(match[turn]['account']['slots'][4])

                        match, text = Battle_Utils.ability_effect(ability, match, turn)

                        await self.construct_embeds_with_message(turn, match, text)

                        # Only change turn if it's supposed to
                        if ability["name"] not in ["Amplify"]:
                            turn = int(not bool(turn))

                        await asyncio.sleep(5)
                        continue
                    elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                        spell = Utils.get_spell(match[turn]['account']['class'],
                                                match[turn]['account']['slots'][reaction_dict[str(reaction)]])

                        match[turn], match[int(not bool(turn))], text = Battle_Utils.spell_effect(
                            spell, match[turn], match[int(not bool(turn))], True)

                        await self.construct_embeds_with_message(turn, match, text)

                        turn = int(not bool(turn))

                        if match[int(not bool(turn))]['ability'] is not None:
                            if match[int(not bool(turn))]["ability"] == "Amplify":
                                ability = Utils.get_ability(match[int(not bool(turn))]['account']['slots'][4])
                                match[int(not bool(turn))]["ability"] = "Amplify Done"
                                match[int(not bool(turn))]['account']['stats']['strength'] -= ability['effect']
                                match = Battle_Utils.match_check(match)
                        if match[turn]['ability'] is not None:
                            if match[turn]["ability"] == "Glass Armor":
                                ability = Utils.get_ability(match[turn]['account']['slots'][4])
                                match[turn]["ability"] = "Glass Armor Done"
                                match[turn]['account']['stats']['defense'] -= ability['effect']
                                match = Battle_Utils.match_check(match)

                        await asyncio.sleep(5)
                        continue

                except Exception as e:
                    if isinstance(e, asyncio.TimeoutError):
                        embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                              description="Your battle is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" +
                                                          match[turn]['message'].jump_url + ")")
                        timeout_msg = await match[turn]['ctx'].send(match[turn]['ctx'].author.mention, embed=embed)
                        await timeout_msg.delete(delay=20)
                        match[turn]['afk'] += 1
                        turn = int(not bool(turn))
                        continue
                    elif isinstance(e, discord.errors.NotFound):
                        Config.LOGGING("Someone deleted a message\n```\n"+str(match)+"```")
                        draw = True
                        break

            for i in range(2):
                if 'friendly' not in match[i].keys():
                    if match[i]['account']['power'] < 0:
                        match[i]['account']['power'] *= -1

            # Calculate the loser:
            # Draw
            if draw or total_turns >= 100:
                draw = True
            # Suicide
            elif (match[0]['mana'] <= 0 or match[0]['health'] <= 0) and \
                    (match[1]['mana'] <= 0 or match[1]['health'] <= 0):
                loser = match[turn]
            # Player 1 killed the opponent
            elif match[0]['mana'] <= 0 or match[0]['health'] <= 0:
                loser = match[0]
            # Player 0 killed the opponent
            elif match[1]['mana'] <= 0 or match[1]['health'] <= 0:
                loser = match[1]
            # Somehow nobody lost....
            else:
                await Config.LOGGING.error("Nobody lost....")
            for _ in range(2):
                try:
                    await match[_]['message'].clear_reactions()
                except:
                    await Config.LOGGING.error("Cannot remove emoji (not a big deal)")

                if draw or total_turns >= 100:
                    embed = discord.Embed(color=Config.MAINCOLOR, description="**DRAW**")
                elif loser == match[_]:
                    if 'friendly' not in match[_].keys():
                        power = random.randint(5, 7)
                        upgrade_emoji = Config.EMOJI['down1']
                        if power == 6:
                            upgrade_emoji = Config.EMOJI['down2']
                        elif power == 7:
                            upgrade_emoji = Config.EMOJI['down3']
                        money = random.randint(3, 9)
                        coins = random.randint(4, 10)
                        # xp = round(round(total_turns / 2, 1) * 100)
                        if match[_]['account']['power'] < 0:
                            match[_]['account']['power'] *= -1
                            Config.USERS.update_one({'user_id': match[_]['ctx'].author.id},
                                                    {'$set': {'power': match[_]['account']['power']}})
                        match[_]['account']['power'] -= power
                        if match[_]['account']['power'] < 2:
                            match[_]['account']['power'] = 1
                            power = 0
                        rankstring = Utils.get_rank_emoji(match[_]['account']['power']) + " " + upgrade_emoji + "\n\n"
                        # if 'xp' not in match[_]['account']:
                        #     match[_]['account']['xp'] = 0
                        Config.USERS.update_one({'user_id': match[_]['ctx'].author.id},
                                                {'$inc': {'rubies': money, "coins": coins},
                                                 '$set': {'power': match[_]['account']['power']}})
                        embed = discord.Embed(color=Config.MAINCOLOR,
                                              description="**You lost...**\n\n" + rankstring + "+`" + str(
                                                  money) + "` " + Config.EMOJI['ruby'] + "\n+`" + str(coins) + "` " +
                                                          Config.EMOJI['coin'])
                    else:
                        embed = discord.Embed(color=Config.MAINCOLOR,
                                              description="**You lost...**\n\n" + "Friendly battle, no rewards!")
                else:
                    if 'friendly' not in match[_].keys():
                        amount = random.randint(1, 3)
                        money = random.randint(15, 35)
                        coins = random.randint(12, 20)
                        power = random.randint(7, 9)
                        upgrade_emoji = Config.EMOJI['up1']
                        if power == 8:
                            upgrade_emoji = Config.EMOJI['up2']
                        elif power == 9:
                            upgrade_emoji = Config.EMOJI['up3']

                        # xp = round(round(total_turns / 2, 1) * 100)
                        if match[_]['account']['power'] < 0:
                            match[_]['account']['power'] *= -1
                            Config.USERS.update_one({'user_id': match[_]['ctx'].author.id},
                                                    {'$set': {'power': match[_]['account']['power']}})
                        rankstring = Utils.get_rank_emoji(
                            match[_]['account']['power'] + power) + " " + upgrade_emoji + "\n\n"
                        mystring = rankstring + "+`" + str(amount) + "` <:key:670880439199596545>\n+`" + str(
                            money) + "` " + Config.EMOJI['ruby'] + "\n+`" + str(coins) + "` " + Config.EMOJI['coin']
                        match[_]['account']['keys'] += amount
                        if match[_]['account']['keys'] > 9:
                            match[_]['account']['keys'] -= 10
                            match[_]['account']['chests'] += 1
                            mystring += "\n+`1` " + Config.EMOJI['chest']
                        # if 'xp' not in match[_]['account']:
                        #     match[_]['account']['xp'] = 0
                        Config.USERS.update_one({'user_id': match[_]['ctx'].author.id},
                                                {'$inc': {'rubies': money, 'power': power, "coins": coins},
                                                 '$set': {'chests': match[_]['account']['chests'],
                                                          'keys': match[_]['account']['keys']}})
                    else:
                        mystring = "Friendly battle, no rewards!"
                    embed = discord.Embed(color=Config.MAINCOLOR,
                                          description="**Congratulations! You have won!**\n\n" + mystring)
                for __ in range(2):
                    embed.add_field(
                        name=Utils.get_rank_emoji(match[__]['account']['power']) + match[__]['ctx'].author.name +
                             match[__]['account']['selected_title'],
                        value="Health: " + str(match[__]['health']) + Config.EMOJI['hp'] + "\nMana: " + str(
                            match[__]['mana']) + Config.EMOJI['flame'])
                embed.title = "Battle against " + match[int(not bool(_))]['ctx'].author.name + \
                              match[int(not bool(_))]['account']['selected_title']
                try:
                    await match[_]['message'].edit(embed=embed)
                except:
                    await Config.LOGGING.error("While cleaning up match message is not found. ignorning.")
                Config.LOGGING.info("Cleaning up a battle")
                Config.USERS.update_many({'user_id': {'$in': [match[0]['ctx'].author.id, match[1]['ctx'].author.id]}},
                                         {'$inc': {'battles.pvp': 1}})
                i = 0
                while i != len(self.battling_users):
                    if self.battling_users[i]["id"] == match[0]['ctx'].author.id or match[1]['ctx'].author.id:
                        self.battling_users.pop(i)
                    else:
                        i += 1
                broken_items = Utils.decrease_durability(match[_]['account']['user_id'])
                if len(broken_items) > 0:
                    embed = discord.Embed(title="Broken Tools",
                                          description=match[_]['ctx'].author.mention + "! Your " + " and ".join(
                                              [x['name'] for x in broken_items]) + " broke!",
                                          color=Config.MAINCOLOR)
                    await match[_]['ctx'].send(content=match[_]['ctx'].author.mention, embed=embed)
        except:
            frames = ""
            tb_next = sys.exc_info()[2]
            while tb_next != None:
                frames += "\n" + str(tb_next.tb_frame)
                tb_next = tb_next.tb_next
            await Config.LOGGING.error("Battle has errored! It has been disbanded and players were unqueued. "
                                       "\nError: `" + str(sys.exc_info()[1]) + "`"
                                       "\nLine #: `" + str(sys.exc_info()[2].tb_lineno) + "`"
                                       "\nFrames: ```Python" + frames + "```")
            embed = discord.Embed(color=Config.MAINCOLOR, title="Battle has ended", description="The battle has ended.")
            for _ in match:
                try:
                    await _['message'].edit(embed=embed)
                except:
                    pass

        finally:
            self.battles -= 1
            i = 0
            while i != len(self.battling_users):
                if self.battling_users[i]["id"] == match[0]['ctx'].author.id or \
                        self.battling_users[i]["id"] == match[1]['ctx'].author.id:
                    self.battling_users.pop(i)
                else:
                    i += 1

    @commands.command()
    async def clear_q(self, ctx):
        if ctx.author.id not in Config.OWNERIDS:
            await ctx.send("You do not have permission to do this")
        else:
            Utils.matchmaking = []
            await ctx.send("All tickets in matchmaking Queue have been cleared.")

    async def user_can_battle(self, ctx):
        """
        Gets the user's data and checks that the bot isn't in maintenance
        """
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.ERRORCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under maintenance.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return -1, -1, True

        return msg, account, False

    async def is_user_battling(self, msg, ctx, target):
        """
        Checks if the user is currently battling
        """
        i = 0
        while i != len(self.battling_users):
            b_user = self.battling_users[i]
            if b_user["id"] == ctx.author.id:
                if (b_user["time"] + 600) > time.time():
                    if target == ctx.author:
                        embed = discord.Embed(color=Config.MAINCOLOR, title="Error entering Queue",
                                              description="You are already battling someone. Please finish that battle "
                                                          "first.")
                    else:
                        embed = discord.Embed(color=Config.MAINCOLOR, title="Error",
                                              description="This person is battling already.")
                    if msg is None:
                        await ctx.send(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    return True
                else:
                    self.battling_users.pop(self.battling_users.index(b_user))
                    continue
            else:
                i += 1

        return False

    @commands.command(aliases=['b'])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def battle(self, ctx, member: discord.Member = None, weapons: bool = True):
        # Get the user's data
        msg, account, error = await self.user_can_battle(ctx)
        if error:
            return

        # Check they're not already battling
        error = await self.is_user_battling(msg, ctx, ctx.author)
        if error:
            return

        prefix = Utils.fetch_prefix(ctx)
        if member is None:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Looking for match... <a:lg:670720658166251559>",
                                  description=f"You are in queue. Once you find a match you will begin battling.\n\n*\"{Battle_Utils.quotes()}\"*",
                                  timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=10))
            embed.set_footer(text=f'type {prefix}cancel to stop searching | timeout at ')
            embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/736320366116470815/779302691326525440/crossed-swords_2694.png")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

            for ticket in Battle_Utils.matchmaking:
                if ticket['account']['user_id'] == ctx.author.id:
                    await ticket['message'].edit(embed=discord.Embed(title="Entered Queue somewhere else",
                                                                     description="You have started looking for a match in a different location.",
                                                                     color=Config.MAINCOLOR))
                    ticket['ctx'] = ctx
                    ticket['message'] = msg
                    return
            weapon = None
            armor = None
            if account["weapon"] is not None:
                weapon = Utils.get_item(account['weapon']["name"])
            if account["armor"] is not None:
                armor = Utils.get_item(account['armor']["name"])
            Battle_Utils.send_ticket({'ability': None, 'armor': armor, 'weapon': weapon, 'power': account['power'],
                                      'ctx': ctx, 'account': account, 'message': msg,
                                      'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
                                      'user': ctx.author, 'stunned': False})
        else:
            for ticket in Battle_Utils.matchmaking:
                if ticket['account']['user_id'] == ctx.author.id:
                    embed = discord.Embed(color=Config.MAINCOLOR, title="Error entering Queue",
                                          description="You are already in the queue. Please finish that battle first.")
                    if msg is None:
                        msg = await ctx.send(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    return

            error = await self.is_user_battling(msg, ctx, member)
            if error:
                return

            for invite in self.friendly_matchmaking:
                if invite["inviter"] == ctx.author.id:
                    embed = discord.Embed(color=Config.MAINCOLOR, title="Error",
                                          description=f"You already sent a pending invitation, delete that first with `{prefix}cancel` before sending a new invite.")
                    if msg is None:
                        msg = await ctx.send(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    return
            armor = None
            weapon = None
            if weapons is False:
                embed = discord.Embed(color=Config.MAINCOLOR, title=f"Battle invitation | No items!!",
                                      description=f"Invitation sent to `{member.name}`\nDo {prefix}accept {ctx.author.mention} to accept.",
                                      timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=2))
                embed.set_footer(text=f'type {prefix}cancel to stop searching | timeout at ')
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/736320366116470815/779302691326525440/crossed-swords_2694.png")
                msg = await ctx.send(embed=embed)
            else:
                if account["weapon"] is not None:
                    weapon = Utils.get_item(account['weapon']["name"])
                if account["armor"] is not None:
                    armor = Utils.get_item(account['armor']["name"])
                embed = discord.Embed(color=Config.MAINCOLOR, title=f"Battle invitation",
                                      description=f"Invitation sent to `{member.name}`\nDo {prefix}accept {ctx.author.mention} to accept.",
                                      timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=2))
                embed.set_footer(text=f'type {prefix}cancel to stop searching | timeout at ')
                msg = await ctx.send(embed=embed)
            self.friendly_matchmaking.append(({'ability': None, 'friendly': True, 'inviter': ctx.author.id,
                                               'invited': member.id, 'weapons': weapons, 'weapon': weapon,
                                               'armor': armor, 'power': account['power'], 'ctx': ctx,
                                               'account': account, 'message': msg,
                                               'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=2),
                                               'stunned': False}))

    @commands.command()
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def accept(self, ctx, member: discord.Member = None):
        msg, account, error = await self.user_can_battle(ctx)
        if error:
            return

        error = await self.is_user_battling(msg, ctx, ctx.author)
        if error:
            return

        battle = []

        invited = False
        for invite in self.friendly_matchmaking:
            if invite["invited"] == ctx.author.id:
                if invite["inviter"] == member.id:
                    invited = True
                    armor = None
                    weapon = None
                    if invite["weapons"] is True:
                        if account["weapon"] is not None:
                            weapon = Utils.get_item(account['weapon']["name"])
                        if account["armor"] is not None:
                            armor = Utils.get_item(account['armor']["name"])
                    msg = await ctx.send(embed=discord.Embed(color=Config.MAINCOLOR, title=f"invitation Accept",
                                                             description="Starting battle against"
                                                                         f"`{invite['ctx'].author.name}`",
                                                             timestamp=datetime.datetime.utcnow() + datetime.timedelta(
                                                                 minutes=1)))
                    ticket = {'friendly': True, 'ability': None, 'weapon': weapon, 'armor': armor,
                              'power': account['power'], 'ctx': ctx, 'account': account, 'message': msg,
                              'expire': datetime.datetime.utcnow() + datetime.timedelta(minutes=2),
                              'user': ctx.author, 'stunned': False}
                    if invite["weapons"] is False:
                        ticket["account"]["armor"] = None
                        ticket["account"]["weapon"] = None
                    battle.append([invite, ticket])
                    self.friendly_matchmaking.remove(invite)
                    for match in battle:
                        await match[0]['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Match found!",
                                                                           description="Battling " + match[1][
                                                                               'ctx'].author.name))
                        await match[1]['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Match found!",
                                                                           description="Battling " + match[0][
                                                                               'ctx'].author.name))
                        self.battles += 1
                        # match[0]['message']
                        id1 = match[0]['ctx'].author.id
                        id2 = match[1]['ctx'].author.id
                        match[0]['user'] = match[0]['ctx'].author
                        self.chats = [[{"ids": [id1, id2]}]]
                        battle = self.bot.loop.create_task(self.battle_thread(match))
        if invited is False:
            embed = discord.Embed(color=Config.MAINCOLOR, title="No invitation found",
                                  description="This person has not invited you to a battle.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @commands.command()
    async def cancel(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        remove_ticket = None
        for ticket in Battle_Utils.matchmaking:
            if ticket['account']['user_id'] == ctx.author.id:
                await ticket['message'].edit(
                    embed=discord.Embed(title="Canceled Matchmaking", description="Matchmaking has been canceled.",
                                        color=Config.MAINCOLOR))
                await ticket['message'].delete(delay=10)
                await ticket['ctx'].message.delete(delay=10)
                remove_ticket = ticket
        invited = None
        for invite in self.friendly_matchmaking:
            if invite["inviter"] == ctx.author.id:
                invited = invite
        if remove_ticket is not None:
            Battle_Utils.matchmaking.remove(remove_ticket)

            embed = discord.Embed(color=Config.MAINCOLOR, title="Matchmaking Canceled",
                                  description="You have exited the battle queue.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=10)
            await ctx.message.delete(delay=10)
        elif invited is not None:
            self.friendly_matchmaking.remove(invited)
            embed = discord.Embed(color=Config.MAINCOLOR, title="Invitation Canceled",
                                  description="You have removed the battle invitation.")
            await invited['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Invitation Cancelled!",
                                                              description="This battle invitation to has been cancelled"))

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
                await msg.delete(delay=10)
                await ctx.message.delete(delay=10)
        else:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(color=Config.MAINCOLOR, title=f"You look confused.",
                                  description="You are not actively looking for a battle. Use {prefix}battle to start looking for one.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.delete(delay=10)
            await ctx.message.delete(delay=10)

    @battle.error
    async def battle_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..",
                                               description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"),
                           color=Config.ERRORCOLOR)

    async def after_battle(self, task, match):
        Config.LOGGING.info("Callback for after match has been called.")
        try:
            task.result()
        except:
            frames = ""
            tb_next = sys.exc_info()[2]
            while tb_next != None:
                frames += "\n" + str(tb_next.tb_frame)
                tb_next = tb_next.tb_next
            await Config.LOGGING.error("Battle has errored! It has been disbanded and players were unqueued. "
                                       "\nError: `" + str(sys.exc_info()[1]) + "`"
                                                                               "\nLine #: `" + str(
                sys.exc_info()[2].tb_lineno) + "`"
                                               "\nFrames: ```Python" + frames + "```")
            embed = discord.Embed(color=Config.MAINCOLOR, title="Battle has ended", description="The battle has ended.")
            print(match)
            print(task)
            for _ in match:
                await _['message'].edit(embed=embed)
        finally:
            self.battles -= 1
            i = 0
            while i != len(self.battling_users):
                if self.battling_users[i]["id"] == match[0]['ctx'].author.id or match[1]['ctx'].author.id:
                    self.battling_users.pop(i)
                else:
                    i += 1
            loop = 0
            for chat in self.chats:
                if match[0]['ctx'].author.id in chat[0]["ids"]:
                    self.chats.remove(self.chats[loop])
                loop += 1

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def chat(self, ctx, *, choice: str = None):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if choice is None:
            prefix = Utils.fetch_prefix(ctx)
            embed = discord.Embed(title="Emotes", description="", color=Config.MAINCOLOR)
            i = 0
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    i += 1
                    embed.description += "> " + str(i) + " | **" + cosmetic["value"] + "**\n"
            embed.set_footer(text=f"Get more emotes from the shop | use {prefix}chat <index> to chat in battle")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        emotes = []
        try:
            for cosmetic in account['cosmetics']:
                if cosmetic["type"] == "emote":
                    emotes.append(cosmetic)
            choice = int(choice)
            if choice > len(emotes) or choice < 1:
                embed = discord.Embed(title="Hmmmm...", description="You only have " + str(
                    len(emotes)) + " Emotes. Try using a number 1-" + str(len(emotes)),
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
            else:
                choice = choice - 1
                loop = 0
                for chat in self.chats:
                    if ctx.author.id in chat[0]["ids"]:
                        if len(chat) > 5:
                            self.chats[loop].remove(self.chats[loop][1])
                        self.chats[loop].append({'user': str(ctx.author.name), 'msg': emotes[choice]['value']})
                        embed = discord.Embed(
                            description=f"Chat sent!\n**{str(ctx.author.name)}**: {emotes[choice]['value']}",
                            color=Config.MAINCOLOR)
                        if msg is None:
                            message = await ctx.send(embed=embed)
                            await asyncio.sleep(5)
                            await message.delete()
                            await ctx.message.delete()
                        else:
                            await msg.edit(embed=embed)
                        return
                    loop += 1
                embed = discord.Embed(title="Whoops..",
                                      description=f"You can only use this command when you're battling!",
                                      color=Config.MAINCOLOR)
                if msg is None:
                    await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
                return
        except ValueError:
            embed = discord.Embed(title="Hmmmm...",
                                  description="Thats not a emote index. Try using a number 1-" + str(len(emotes)),
                                  color=Config.MAINCOLOR)
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

    @tasks.loop(seconds=10)
    async def matchmaking(self):
        if len(Battle_Utils.matchmaking) > 1:
            Config.LOGGING.info("Starting matching")
            matched = Battle_Utils.match_tickets()
            for match in matched:
                Config.LOGGING.info("Found match")
                await match[0]['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Match found!",
                                                                   description="Battling " + match[1][
                                                                       'ctx'].author.name))
                await match[1]['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Match found!",
                                                                   description="Battling " + match[0][
                                                                       'ctx'].author.name))
                self.battles += 1
                # match[0]['message']
                Config.USERS.update_one({'user_id': match[0]['ctx'].author.id}, {'$inc': {'battles.pvp': 1}})
                Config.USERS.update_one({'user_id': match[1]['ctx'].author.id}, {'$inc': {'battles.pvp': 1}})
                id1 = match[0]['ctx'].author.id
                id2 = match[1]['ctx'].author.id
                self.chats = [[{"ids": [id1, id2]}]]
                battle = self.bot.loop.create_task(self.battle_thread(match))
                # battle.add_done_callback(functools.partial(self.after_battle, match=match))

            Config.LOGGING.info("Matching completed.")

    @tasks.loop(seconds=30)
    async def ticket_garbage(self):
        if len(Battle_Utils.matchmaking) > 0:
            Config.LOGGING.info("Started queue cleaning")
            to_delete = []
            for ticket in Battle_Utils.matchmaking:
                if ticket['expire'] < datetime.datetime.utcnow():
                    to_delete.append(ticket)
            for ticket in to_delete:
                prefix = Utils.fetch_prefix(ticket["ctx"])
                await ticket['message'].edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Matchmaking Canceled",
                                                                 description=f"Unfortunately, we could not find you a battle at this time. You may type `{prefix}battle` to join the queue again."))
                Battle_Utils.matchmaking.remove(ticket)
                Config.LOGGING.info("Cleaned ticket from queue.")
            Config.LOGGING.info("Queue cleaning completed.")
        if len(self.friendly_matchmaking) > 0:
            for invite in self.friendly_matchmaking:
                if invite['expire'] < datetime.datetime.utcnow():
                    await invite['message'].edit(
                        embed=discord.Embed(color=Config.MAINCOLOR, title="Invitation Cancelled!",
                                            description="This battle invitation to has been cancelled"))
                    self.friendly_matchmaking.remove(invite)

    @commands.group()
    async def season(self, ctx):
        if ctx.invoked_subcommand is not None:
            return

        # Get time left until next season
        timer = Battle_Utils.get_season_timer()
        the_time = time.time()
        hours, remainder = divmod(timer - the_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        time_left = ""
        if (timer - the_time) < 0:
            time_left += "SOON!"
        elif days:
            time_left += f"{round(days)} days, {round(hours)} hours, {round(minutes)} minutes and {round(seconds)} seconds"
        elif hours:
            time_left += f"{round(hours)} hours, {round(minutes)} minutes and {round(seconds)} seconds"
        elif minutes:
            time_left += f"{round(minutes)} minutes and {round(seconds)} seconds"
        else:
            time_left += f"{round(seconds)} seconds"

        # Get the user's rewards
        account = Utils.get_account(ctx.author.id)
        user_rank = Utils.get_rank_object(account['power'])

        # Generate the rewards for each rank
        rewards = ""
        for power, rank in Config.RANK_LINKS.items():
            reward = rank['rewards'].split(';')
            if len(reward) == 2:
                rewards += f"\n{rank['emoji']} {reward[0]} {Config.EMOJI[reward[1].lower()]}"
            else:
                rewards += f"\n{rank['emoji']} `{reward[0]}`"
            if rank == user_rank:
                rewards += "  **<===**"

        rewards += f"\n\nUse `{ctx.prefix}season claim` to get your rewards from last season."

        # Create the embed
        embed = discord.Embed(title="Enchanted PVP Seasons",
                              description="**Season Reset in **" + time_left + "\n\n**Season Rewards:**" + rewards,
                              color=Config.MAINCOLOR)

        embed.set_footer(text="⚠️ Each season, you must battle at least once to join the season and "
                         "claim rewards for that season ⚠️")

        await ctx.send(embed=embed)

    @season.command()
    async def claim(self, ctx):
        account = Utils.get_account(ctx.author.id)

        if account is None:
            return

        rewards = {'coin': 0, 'ruby': 0, 'crown': 0, 'artifact': 0, 'chest': 0}
        for power, rank in Config.RANK_LINKS.items():
            # Check they deserve the reward
            if power > account['old_power']:
                break

            # Add the reward
            reward = rank['rewards'].split(';')
            if len(reward) == 2:
                try:
                    rewards[reward[1].lower()] += int(reward[0])
                except KeyError:
                    await Config.LOGGING.error("Invalid reward specified: " + str(reward))

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is not None:
            str_rewards = f"+`{rewards['coin']}` {Config.EMOJI['coin']}" \
                          f"\n+`{rewards['ruby']}` {Config.EMOJI['ruby']}" \
                          f"\n+`{rewards['chest']}` {Config.EMOJI['chest']}" \
                          f"\n+`{rewards['crown']}` {Config.EMOJI['crown']}" \
                          f"\n+`{rewards['artifact']}` {Config.EMOJI['artifact']}"
        else:
            str_rewards = f"+`{rewards['coin']}` {Config.EMOJI['coin']}" \
                          f"\n+`{rewards['ruby']}` {Config.EMOJI['ruby']}" \
                          f"\n+`{rewards['chest']}` {Config.EMOJI['chest']}" \
                          f"\n+`{rewards['crown']}` {Config.EMOJI['crown']}" \
                          f"\n~~+`{rewards['artifact']}`~~ {Config.EMOJI['artifact']} :warning: You're not in a clan."
        color = int(account['selected_embed_color']['value'], 16)
        embed = discord.Embed(title="Season Rewards Claimed!", color=color, description=str_rewards)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        if account['selected_embed_image'] is not None:
            embed.set_thumbnail(url=account['selected_embed_image']['value'])

        Config.USERS.update_one({'user_id': account['user_id']},
                                {'$inc': {'coins': rewards['coin'], 'rubies': rewards['ruby'],
                                          'chests': rewards['chest'], 'crowns': rewards['crown']},
                                 '$set': {'old_power': -1}})
        if rewards['artifact'] > 0:
            if clan is not None:
                Config.CLANS.update_one({'name': clan['name']}, {"$inc": {'artifacts': rewards['artifact']}})

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Matchmaking(bot))
