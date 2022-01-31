import asyncio
import datetime
import math
import random
import statistics
import sys

import discord
import pymongo
from discord.ext import commands

import Battle_Utils
import Config
import Utils


async def calculate_artifacts(floor, player_count, is_titan):
    arts = 0
    floor -= 1
    if is_titan:
        for i in range(1, floor + 1):
            arts += 2 + round((i - 1) * 0.5) + round(player_count / 5)
    else:
        for i in range(1, floor + 1):
            arts += 1 + round((i - 1) * 0.2) + round(player_count / 5)

    return arts


def change_turn(turn, max_turn):
    turn += 1
    if turn > max_turn:
        turn = 0
    return turn


async def construct_embeds(match, turn, floor, message, monster):

    if monster["titan"]:
        title = "⛓️ | TITAN DUNGEON fight against " + monster['name'] + " | Floor " + str(floor)
    else:
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        title = boss_class["emote"] + " | Dungeon fight against " + monster['name'] + " | Floor " + str(floor)

    embed = Battle_Utils.construct_boss_embed(match, turn, monster, title)

    await message.edit(embed=embed)


async def construct_embeds_with_message(message, monster, turn, floor, match, text):
    if monster["titan"]:
        title = "⛓️ | TITAN DUNGEON fight against " + monster['name'] + " | Floor " + str(floor)
    else:
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        title = boss_class["emote"] + " | Dungeon fight against " + monster['name'] + " | Floor " + str(floor)

    embed = Battle_Utils.construct_boss_embed_with_message(match, turn, monster, title, text)

    await message.edit(embed=embed)


class Dungeons(commands.Cog):

    def __init__(self, bot):
        self.waiting_users = []
        self.dungeons = 0
        self.active_channels = []
        self.battling_users = []
        self.bot = bot

    async def dungeon_thread(self, match, message, monster, floor, clan):
        match_cache = match.copy()
        if len(match) < 1:
            if monster["titan"]:
                emoji = "⛓️"
                embed = discord.Embed(color=Config.MAINCOLOR,
                                      description=emoji + " | **" + monster['name'] +
                                                  " Has bested the group...**\n\nYou made it past " + str(floor - 1) +
                                                  " floors and collected " + Config.EMOJI['artifact'] + " `" +
                                                  str(await calculate_artifacts(floor, len(match_cache), True)) +
                                                  "` Artifacts.")
            else:
                emoji = Utils.get_class(monster['spells'][0]["class"])["emote"]
                embed = discord.Embed(color=Config.MAINCOLOR,
                                      description=emoji + " | **" + monster['name'] +
                                                  " Has bested the group...**\n\nYou made it past " + str(floor - 1) +
                                                  " floors and collected " + Config.EMOJI['artifact'] + " `" +
                                                  str(await calculate_artifacts(floor, len(match_cache), False)) +
                                                  "` Artifacts.")
            await message.edit(embed=embed)
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.dungeons -= 1
            return match, floor - 1, False, message
        Config.LOGGING.info("Dungeon thread started: Current threads: " + str(self.dungeons))
        await message.clear_reactions()
        monster['health'] = monster['stats']['health']
        monster['mana'] = monster['stats']['endurance']
        await message.delete()
        embed = discord.Embed(title="You enter floor " + str(floor) + "...", color=Config.MAINCOLOR,
                              description="[jump](" + message.jump_url + ")")
        message = await message.channel.send(", ".join(x['user'].mention for x in match), embed=embed)
        # await one_message.delete(delay=10)
        monster['effects'] = []
        for user in match:
            user['health'] = user['account']['stats']['health']
            user['mana'] = user['account']['stats']['endurance']
            user['effects'] = []
            user['afk'] = 0
            user['stunned'] = False
        turn = random.randint(0, len(match) - 1)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("🔆")
        await message.add_reaction("💤")
        await message.add_reaction("🏳️")
        a_turn = False
        for player in match:
            broken_items = Utils.decrease_durability(player['account']['user_id'])
            if len(broken_items) > 0:
                embed = discord.Embed(title="Broken Tools",
                                      description=player['user'].mention + "! Your " + " and ".join(
                                          [x['name'] for x in broken_items]) + " broke!", color=Config.MAINCOLOR)
                await message.channel.send(content=player['user'].mention, embed=embed)

        while len(match) > 0 and monster['health'] > 0 and monster['mana'] > 0:
            restart = False
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    match.remove(user)
                    turn -= 1
                    restart = True
            if turn < 0:
                turn = 0
            if restart:
                continue

            # calculate effects for beginning of round
            for _ in match:
                effects_remove = []
                for effect in _['effects']:
                    _[effect['type']] -= effect['amount']
                    _[effect['type']] = round(_[effect['type']], 1)
                    effect['turns'] -= 1
                    if effect['turns'] < 1:
                        effects_remove.append(effect)
                for effect in effects_remove:
                    _['effects'].remove(effect)

            # restart if needed after effects applied
            restart = False
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    if turn >= match.index(user):
                        turn -= 1
                    match.remove(user)
                    restart = True
            if restart:
                continue

            # effects for monster
            effects_remove = []
            for effect in monster['effects']:
                monster[effect['type']] -= effect['amount']
                monster[effect['type']] = round(monster[effect['type']], 1)
                effect['turns'] -= 1
                if effect['turns'] < 1:
                    effects_remove.append(effect)
            for effect in effects_remove:
                monster['effects'].remove(effect)

            if turn != len(match):
                resource = 'mana'
                resource_number = 3
                if match[turn]['ability'] is not None:
                    if match[turn]['ability'] == "Healing Blood":
                        resource = 'health'
                        resource_number = 5
                    elif match[turn]['ability'] == "Inner Light":
                        resource_number = 6

                if a_turn is True:
                    resource_number = 0
                    a_turn = False
                # Check if the user is stunned
                elif match[turn]['stunned']:
                    resource_number = 0

                match[turn][resource] += resource_number
            else:
                abilities = []
                for user in match:
                    abilities.append(user["ability"])
                if "Stagnation" not in abilities and not monster['stunned']:
                    monster['mana'] += 8
                elif "Stagnation" in abilities and not monster['stunned']:
                    monster['mana'] += 4

            Battle_Utils.match_check(match, monster)

            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    if match.index(user) < turn:
                        turn -= 1
                    match.remove(user)
            if turn < 0:
                turn = 0

            if monster['health'] <= 0 or monster['mana'] <= 0:
                break

            await construct_embeds(match, turn, floor, message, monster)

            if monster['stunned']:
                monster['stunned'] = False
                await asyncio.sleep(3)
                turn = change_turn(turn, len(match_cache))
                continue

            # check if monster's turn
            if turn == len(match):

                # simulate monster thinking lol
                await asyncio.sleep(3)

                spell = Battle_Utils.pick_spell(monster)
                if spell is not None:
                    victim = random.randint(0, len(match) - 1)

                    monster, match[victim], text = Battle_Utils.spell_effect(spell, monster, match[victim], True)

                    await construct_embeds_with_message(message, monster, turn, floor, match, text)

                    if match[victim]['ability'] is not None:
                        if match[victim]["ability"] == "Glass Armor":
                            ability = Utils.get_ability(match[victim]['account']['slots'][4])
                            match[victim]["ability"] = "Glass Armor Done"
                            match[victim]['account']['stats']['defense'] -= ability['effect']
                            match, monster = Battle_Utils.match_check(match, monster)
                    await asyncio.sleep(3)

                turn = change_turn(turn, len(match))
                for user in match:
                    if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                        match.remove(user)
                        turn -= 1
                continue

            try:
                # Check if the user is stunned
                if match[turn]['stunned']:
                    match[turn]['stunned'] = False
                    await asyncio.sleep(3)
                    turn = change_turn(turn, len(match_cache))
                    continue

                reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '🔆': 4, '💤': 5, '🏳️': 6}

                def check(payload):
                    if payload.user_id == match[turn]['user'].id and payload.message_id == message.id:
                        if str(payload.emoji) in reaction_dict.keys():
                            if str(payload.emoji) in reaction_dict.keys():
                                if reaction_dict[str(payload.emoji)] < 5:
                                    return match[turn]['account']['slots'][
                                               reaction_dict[str(payload.emoji)]] is not None
                                else:
                                    return True
                    else:
                        return False

                temp_msg = await message.channel.fetch_message(message.id)
                reaction = None
                for temp_reaction in temp_msg.reactions:
                    users = await temp_reaction.users().flatten()
                    if match[turn]['user'].id in [x.id for x in users] and temp_reaction.me:
                        reaction = temp_reaction
                        try:
                            await temp_reaction.remove(match[turn]['user'])
                        except:
                            await Config.LOGGING.error("Cannot remove emoji (not big deal)")
                if reaction is None:
                    payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                    reaction = payload.emoji

                    try:
                        await message.remove_reaction(payload.emoji, match[turn]['user'])
                    except:
                        await Config.LOGGING.error("Cannot remove emoji (not big deal)")

                if str(reaction) == "💤":
                    turn = change_turn(turn, len(match))
                    continue
                elif str(reaction) == "🏳️":
                    match[turn]['health'] = 0
                    match[turn]['mana'] = 0
                    turn = change_turn(turn, len(match))
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue
                elif str(reaction) == "🔆" and match[turn]["ability"] is not None:
                    a_turn = True
                elif str(reaction) == "🔆" and match[turn]["ability"] is None:
                    ability = Utils.get_ability(match[turn]['account']['slots'][4])

                    if ability is None:
                        pass

                    match, text, monster = Battle_Utils.ability_effect(ability, match, turn, monster)

                    await construct_embeds_with_message(message, monster, turn, floor, match, text)

                    # Only change turn if it's supposed to
                    if ability["name"] not in ["Amplify"]:
                        turn = change_turn(turn, len(match))

                    await asyncio.sleep(3)
                    continue
                elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                    spell = Utils.get_spell(match[turn]['account']['class'],
                                            match[turn]['account']['slots'][reaction_dict[str(reaction)]])

                    if spell is None:
                        pass

                    match[turn], monster, text = Battle_Utils.spell_effect(spell, match[turn], monster, False)

                    await construct_embeds_with_message(message, monster, turn, floor, match, text)

                    # Remove amplify effect
                    if match[turn]["ability"] == "Amplify":
                        ability = Utils.get_ability(match[turn]['account']['slots'][4])
                        match[turn]["ability"] = "Amplify Done"
                        match[turn]['account']['stats']['strength'] -= ability['effect']
                        match = Battle_Utils.match_check(match)

                    turn = change_turn(turn, len(match))

                    await asyncio.sleep(3)
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and turn != len(match):
                    embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                          description="Your quest is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + message.jump_url + ")")
                    timeout_msg = await message.channel.send(match[turn]['user'].mention, embed=embed)
                    await timeout_msg.delete(delay=20)
                    match[turn]['afk'] += 1
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    turn = change_turn(turn, len(match))
                    continue
                elif isinstance(e, discord.errors.NotFound):
                    return
                else:
                    frames = ""
                    tb_next = sys.exc_info()[2]
                    while tb_next != None:
                        frames += "\n" + str(tb_next.tb_frame)
                        tb_next = tb_next.tb_next
                    await Config.LOGGING.error("Something went wrong in a dungeon! "
                                               "\nError: `" + str(sys.exc_info()[1]) + "`"
                                                                                       "\nLine #: `" + str(
                        sys.exc_info()[2].tb_lineno) + "`"
                                                       "\nFrames: ```Python" + frames + "```")
                    match[turn]['mana'] -= 3
                    await message.channel.send(
                        embed=discord.Embed(title="Uh oh..", description="Something went wrong\n```\n" + str(e) + "```",
                                            color=Config.ERRORCOLOR))
        try:
            await message.clear_reactions()
        except:
            await Config.LOGGING.error("Cannot remove emoji (not big deal)")

        if monster['health'] > 0 and monster['mana'] > 0:
            temp_clan = Config.CLANS.find_one({'name': clan['name']})
            if temp_clan is not None:
                if 'member_artifacts' not in temp_clan.keys():
                    temp_clan['member_artifacts'] = {}
                for guy in match_cache:
                    if str(guy['user'].id) not in temp_clan['member_artifacts'].keys():
                        temp_clan['member_artifacts'][str(guy['user'].id)] = 1
                    else:
                        temp_clan['member_artifacts'][str(guy['user'].id)] += 1
            # Only add if they actually cleared at least one floor
            if floor > 1:
                Config.CLANS.update_one({'name': clan['name']},
                                        {'$set': {'member_artifacts': temp_clan['member_artifacts']}})

            if monster["titan"]:
                embed = discord.Embed(color=Config.MAINCOLOR,
                                      description="**" + monster['name'] +
                                                  " Has bested the group...**\n\nYou made it past " +
                                                  str(floor - 1) + " floors and collected " + Config.EMOJI['artifact'] +
                                                  " `" + str(await calculate_artifacts(floor, len(match_cache), True)) +
                                                  "` Artifacts.")
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**" + monster[
                    'name'] + " Has bested the group...**\n\nYou made it past " + str(
                    floor - 1) + " floors and collected " + Config.EMOJI['artifact'] + " `" +
                    str(await calculate_artifacts(floor, len(match_cache), False)) + "` Artifacts.")
            await message.edit(embed=embed)
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.dungeons -= 1
            return match, floor - 1, False, message
        else:
            if not monster['titan']:
                coins_amount = random.randint(5, (len(match_cache) * 2) + 5) + floor
            else:
                coins_amount = random.randint(5, (len(match_cache) * 3) + 5) + floor * 2
            mystring = "+`" + str(coins_amount) + "` " + Config.EMOJI['coin']
            for user in match_cache:
                user['account'] = Utils.get_account(user['user'].id)
                if user['account']["weapon"] is not None:
                    user['weapon'] = Utils.get_item(user['account']['weapon']["name"])
                if user['account']["armor"] is not None:
                    user['armor'] = Utils.get_item(user['account']['armor']["name"])
                Config.USERS.update_one({'user_id': user['user'].id}, {'$inc': {'coins': coins_amount}})
            if monster["titan"]:
                artifacts = 2 + round((floor - 1) * 0.5) + round(len(match_cache) / 5)
            else:
                artifacts = 1 + round((floor - 1) * 0.2) + round(len(match_cache) / 5)
            Config.CLANS.update_one({'name': clan['name']}, {'$inc': {'artifacts': artifacts}})
            if monster['health'] <= 0:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster[
                    'name'] + " has been killed!**\n\nEveryone gets:\n\n" + mystring + "\nArtifacts Collected this floor: " + str(
                    artifacts) + " " + Config.EMOJI['artifact'] +
                    "\nTotal Artifacts Collected this dungeon: " +
                    str(await calculate_artifacts(floor + 1, len(match), monster['titan'])) + " " + Config.EMOJI['artifact'] +
                    "\nNext Floor: " + str(floor + 1) + "\n\n*Starting in 10s*")
            elif monster['mana'] <= 0:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster[
                    'name'] + " has fainted!**\n\nEveryone gets:\n\n" + mystring + "\nArtifacts Collected this floor: " + str(
                    artifacts) + " " + Config.EMOJI['artifact'] +
                    "\nTotal Artifacts Collected this dungeon: " +
                    str(await calculate_artifacts(floor + 1, len(match), monster['titan'])) + " "
                    + Config.EMOJI['artifact'] + "\nNext Floor: " + str(floor + 1) + "\n\n*Starting in 10s*")
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster[
                    'name'] + " has been destroyed completely!**\n\nEveryone gets:\n\n" + mystring + "\nArtifacts Collected this floor: " + str(
                    artifacts) + " " + Config.EMOJI['artifact'] +
                    "\nTotal Artifacts Collected this dungeon: " +
                    str(await calculate_artifacts(floor + 1, len(match), monster['titan'])) + " " + Config.EMOJI['artifact']
                    + "\nNext Floor: " + str(floor + 1) + "\n\n*Starting in 10s*")
            await message.edit(embed=embed)
            await asyncio.sleep(10)
            return match, floor + 1, True, message

    @commands.command(aliases=["dungeons", "floors", "floor", "clanfight"])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def dungeon(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.ERRORCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under Maintenance.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.battling_users:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon",
                                  description="You are already in a dungeon. Please finish that quest first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in self.waiting_users:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon",
                                  description="You are already entering a dungeon. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.channel.id in self.active_channels:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon",
                                  description="This channel is already exploring a dungeon. Please finish that quest first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        clan = Utils.get_user_clan(ctx.author.id)
        if clan is None:
            embed = discord.Embed(color=Config.MAINCOLOR, title="Error Entering Dungeon",
                                  description="You are not part of a clan. Dungeons are meant to get Artifacts for clans. Go create or join a clan to be able to explore dungeons!")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        user_names = []
        user_ids = []
        quote = "*\"" + Battle_Utils.quotes() + "\"*"
        self.waiting_users.append(ctx.author.id)
        self.active_channels.append(ctx.channel.id)

        user_ids.append(ctx.author.id)
        user_names.append(ctx.author.name)
        users_names = ""
        for user_n in user_names:
            users_names += user_n + "\n"

        embed = discord.Embed(color=Config.MAINCOLOR,
                              title=ctx.author.name + " Is entering a Dungeon for the **`" + str(
                                  clan['name']) + "`** clan<a:dots:715134569355018284>",
                              description=f"The quest will begin in 1 minute. React to join.\n⚔️ **Players ({str(len(user_ids))}/10):**\n{users_names}\n{quote}",
                              timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
        embed.set_footer(text='React with the ✔️ to join | starting at ')
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/736320366116470815/779302506147610624/chains_26d3.png")
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✔️")
        await msg.add_reaction("❌")
        await msg.add_reaction("⏩")

        countdown = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)

        def check(reaction, user):
            return user.id != self.bot.user.id and reaction.message.id == msg.id

        while datetime.datetime.utcnow() < countdown:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
                if str(reaction) == "⏩" and user.id == ctx.author.id:
                    break
                elif str(reaction) == "❌" and user.id == ctx.author.id:
                    await msg.clear_reactions()
                    await msg.edit(embed=discord.Embed(title="Dungeon Quest canceled", color=Config.MAINCOLOR,
                                                       description=ctx.author.name + " has disbanded the quest..."))

                    if ctx.channel.id in self.active_channels:
                        self.active_channels.remove(ctx.channel.id)
                    for u in user_ids:
                        if u in self.waiting_users:
                            self.waiting_users.remove(u)
                    return
                elif Utils.get_account(user.id) is None:
                    await reaction.remove(user)
                    error_msg = await ctx.send(
                        embed=discord.Embed(title="You don't have an account", color=Config.MAINCOLOR,
                                            description="Type `]profile` to choose a class and react again to join the party!"))
                    await error_msg.delete(delay=20)
                    continue
                elif user.id in self.waiting_users and user.id != ctx.author.id:
                    if user.id not in user_ids:
                        error_msg = await ctx.send(content=user.mention,
                                                   embed=discord.Embed(title="Already entering", color=Config.MAINCOLOR,
                                                                       description="You are already entering a dungeon!"))
                        await error_msg.delete(delay=20)
                        await reaction.remove(user)
                        continue
                elif user.id in self.battling_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention,
                                               embed=discord.Embed(title="Already exploring", color=Config.MAINCOLOR,
                                                                   description="You are already exploring a dungeon!"))
                    await error_msg.delete(delay=20)
                    await reaction.remove(user)
                    continue
                elif reaction.message.id != msg.id or not reaction.me:
                    continue

                if str(reaction) != "✔️":
                    await reaction.remove(user)
                    continue
                await reaction.remove(user)
                if user.id in user_ids:
                    user_ids.remove(user.id)
                    user_names.remove(user.name)
                    self.waiting_users.remove(user.id)
                else:
                    if len(user_ids) > 9:
                        error_msg = await ctx.send(content=user.mention,
                                                   embed=discord.Embed(title="Already full", color=Config.MAINCOLOR,
                                                                       description="The party is full. Only 10 people can fight a single boss."))
                        continue
                    user_ids.append(user.id)
                    user_names.append(user.name)
                    self.waiting_users.append(user.id)
                users_names = ""
                for user in user_names:
                    users_names += user + "\n"
                embed = discord.Embed(color=Config.MAINCOLOR,
                                      title=ctx.author.name + " Is entering a Dungeon for the **`" + str(
                                          clan['name']) + "`** clan<a:dots:715134569355018284>",
                                      description=f"The quest will begin in 1 minute. React to join.\n⚔️ **Players ({str(len(user_ids))}/10):**\n{users_names}\n{quote}",
                                      timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
                embed.set_footer(text='React with the ✔️ to join | starting at ')
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/736320366116470815/779302506147610624/chains_26d3.png")
                if msg is None:
                    msg = await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)
            except asyncio.TimeoutError:
                continue

        # temp_msg = await ctx.channel.fetch_message(msg.id)
        # users = []
        # for temp_reaction in temp_msg.reactions:
        #     if str(temp_reaction) == "✔️":
        #         users = await temp_reaction.users().flatten()
        # if ctx.author.id not in [x.id for x in users]:
        #     users.append(ctx.author)

        if len(user_ids) == 0:
            await msg.clear_reactions()
            await msg.edit(embed=discord.Embed(title="Boss Search canceled", color=Config.MAINCOLOR,
                                               description="No one was brave enough to challenge a boss..."))
            if ctx.channel.id in self.active_channels:
                self.active_channels.remove(ctx.channel.id)
            for u in user_ids:
                if u in self.waiting_users:
                    self.waiting_users.remove(u)
            return

        match = []
        for user in user_ids:
            Config.USERS.update_one({'user_id': user}, {'$inc': {'battles.dungeons': 1}})
            user = await self.bot.fetch_user(user)
            if user.id != self.bot.user.id:
                account = Utils.get_account(user.id)
                armor = None
                weapon = None
                if account["weapon"] is not None:
                    weapon = Utils.get_item(account['weapon']["name"])
                if account["armor"] is not None:
                    armor = Utils.get_item(account['armor']["name"])
                match.append({'ability': None, 'weapon': weapon, 'armor': armor, 'user': user, 'account': account,
                              'stunned': False})
        self.dungeons += 1
        do_continue = True
        floors = 1

        if random.randint(1, 10) == 10:
            titan = True
        else:
            titan = False
        monster_class = random.choice(list(Config.CLASSES.find({})))

        match_copy = match.copy()

        for i in range(len(match)):
            self.battling_users.append(match[i]['user'].id)

        while do_continue:
            # Randomly selects 6 spells
            spells = list(Config.SPELLS.find({'class': monster_class['name']}))
            random.shuffle(spells)
            spells = spells[:6]

            if titan:
                strength = round(
                    3 + statistics.mean(x['account']['stats']['defense'] for x in match_copy) * (2.8 + floors))
                defense = round(
                    2 * statistics.mean(x['account']['stats']['strength'] for x in match_copy) * (2 + (floors * 0.5)))
                health = round(90 + (math.sqrt(len(match_copy)) * 16) + (1.5 * floors))
                endurance = random.randint(120, 150) + len(match_copy) * 13 + floors * 2.2
                monster = {'name': Battle_Utils.make_monster_name(True), 'titan': True, 'spells': spells,
                           'armor': {'name': "Titan's Breastplate", 'effect': random.randint(2, 8),
                                     'emoji': "<:helmet:675820506284556306>"},
                           'weapon': {'name': "Aged Sword", 'effect': random.randint(2, int((floors * 0.3)) + 4),
                                      'emoji': "<:battle:670882198450339855>"},
                           'stats': {'health': health, 'strength': strength, 'defense': defense,
                                     'endurance': endurance},
                           'stunned': False}
            else:
                strength = round(
                    3 + statistics.mean(x['account']['stats']['defense'] for x in match_copy) * (2 + (floors * 0.5)))
                defense = round(
                    1 * statistics.mean(x['account']['stats']['strength'] for x in match_copy) * (2 + (floors * 0.2)))
                health = round(60 + (math.sqrt(len(match_copy)) * 13) + (1.3 * floors))
                endurance = random.randint(90, 120) + len(match_copy) * 10 + floors * 2
                monster = {'name': Battle_Utils.make_monster_name(), 'titan': False, 'spells': spells,
                           'stats': {'health': health, 'strength': strength,
                                     'defense': defense, 'endurance': endurance},
                           'stunned': False}
            for user in match:
                if user["account"]["user_id"] in self.waiting_users:
                    self.waiting_users.remove(user["account"]["user_id"])

                user['stunned'] = False

            if 'weapon' in monster.keys():
                monster['stats']['strength'] += monster['weapon']['effect']
            if 'armor' in monster.keys():
                monster['stats']['defense'] += monster['armor']['effect']

            for i in range(len(match)):
                if match[i]['armor'] is not None:
                    if match[i]["account"]["armor"] is not None:
                        match[i]['account']['stats']['defense'] += Utils.calc_item_effect(match[i]["account"]["armor"],
                                                                                          match[i]['armor'])
                if match[i]['weapon'] is not None:
                    if match[i]["account"]["weapon"] is not None:
                        match[i]['account']['stats']['strength'] += Utils.calc_item_effect(
                            match[i]["account"]["weapon"], match[i]['weapon'])

            monster['stats']['strength'] = round(monster['stats']['strength'])
            monster['stats']['defense'] = round(monster['stats']['defense'])
            monster['stats']['health'] = round(monster['stats']['health'])
            try:
                match, floors, do_continue, msg = await self.dungeon_thread(match, msg, monster, floors, clan)
            except Exception as e:
                for user in match_copy:
                    if user['user'].id in self.battling_users:
                        self.battling_users.remove(user['user'].id)
                if msg.channel.id in self.active_channels:
                    self.active_channels.remove(msg.channel.id)
                self.dungeons -= 1
                raise e

        for user in match_copy:
            if user['user'].id in self.battling_users:
                self.battling_users.remove(user['user'].id)
        if msg.channel.id in self.active_channels:
            self.active_channels.remove(msg.channel.id)

    @dungeon.error
    async def dungeon_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..",
                                               description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"),
                           color=Config.ERRORCOLOR)


def setup(bot):
    bot.add_cog(Dungeons(bot))
