import asyncio
import statistics

import Battle_Utils
import Config
import math
import discord
import datetime
from discord.ext import commands
import Utils
import random
import time


def get_numbers(number_string):
    final_string = ""
    for character in number_string:
        try:
            int(character)
            final_string += character
        except:
            continue
    return int(final_string)


class Bosses(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.battling_users = []
        self.waiting_users = []
        self.active_channels = []
        self.bosses = 0

    async def drops(self, message):
        type = random.choice(['ruby', 'coin', 'chest'])
        if type == 'ruby':
            amount = random.randint(1, 3)
            embed = discord.Embed(color=Config.MAINCOLOR, title="Rubies",
                                  description="There are " + str(amount) + " " + Config.EMOJI[
                                      'ruby'] + " on the ground. React first to pick them up!")
            ruby = self.bot.get_emoji(676177832963211284)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(ruby)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'rubies': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Rubies picked up by " + user.name,
                                               description=user.name + " has picked up the " + str(amount) + " " +
                                                           Config.EMOJI['ruby'] + " rubies"))
        elif type == 'coin':
            amount = random.randint(5, 10)
            embed = discord.Embed(color=Config.MAINCOLOR, title="Coins",
                                  description="There are " + str(amount) + " " + Config.EMOJI[
                                      'coin'] + " on the ground. React first to pick them up!")
            emoji = self.bot.get_emoji(676181520062349322)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'coins': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Coins picked up by " + user.name,
                                               description=user.name + " has picked up the " + str(amount) + " " +
                                                           Config.EMOJI['coin'] + " coins"))
        elif type == 'xp':
            amount = random.randint(20, 50)
            embed = discord.Embed(color=Config.MAINCOLOR, title="XP",
                                  description="There is " + str(amount) + " " + Config.EMOJI[
                                      'xp'] + " on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(730357877310488636)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'xp': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="XP picked up by " + user.name,
                                               description=user.name + " has picked up " + str(amount) + " " +
                                                           Config.EMOJI['xp'] + " XP"))
        elif type == 'chest':
            amount = 1
            embed = discord.Embed(color=Config.MAINCOLOR, title="Chest", description="There is a " + Config.EMOJI[
                'chest'] + " on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(671574326364995595)
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            await msg.add_reaction(emoji)
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
            except asyncio.TimeoutError:
                await msg.delete()
                return

            Config.USERS.update_one({'user_id': user.id}, {'$inc': {'chests': amount}})

            await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR, title="Chest picked up by " + user.name,
                                               description=user.name + " has picked up the " + Config.EMOJI[
                                                   'chest'] + " Chest"))
        elif type == 'item':
            item = random.choice(list(Config.ITEMS.find({'cost': {'$lt': 6000}})))
            item['level'] = 1
            embed = discord.Embed(color=Config.MAINCOLOR, title="Item",
                                  description="There is a " + item['emoji'] + " **" + item[
                                      'name'] + "** on the ground. React first to pick it up!")
            emoji = self.bot.get_emoji(get_numbers(item['emoji']))
            msg = await message.channel.send(embed=embed)

            def check(reaction, user):
                return reaction.message.id == msg.id and reaction.me and Utils.get_account(user.id) is not None

            did_pickup = False
            await msg.add_reaction(emoji)

            while not did_pickup:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return

                user_account = Utils.get_account(user.id)
                if user_account is not None:
                    for i in user_account['inventory']:
                        if i['name'] == item['name']:
                            await reaction.remove(user)
                            a_msg = await message.channel.send(user.mention + " You cannot collect an item you already have!")
                            await a_msg.delete(delay=20)
                            continue

                Config.USERS.update_one({'user_id': user.id}, {'$push': {'inventory': item}})

                await msg.edit(embed=discord.Embed(color=Config.MAINCOLOR,
                                                   title=item['emoji'] + " " + item['name'] + " picked up by " + user.name,
                                                   description=user.name + " has picked up the " + item['emoji'] + " **" +
                                                               item['name'] + "**"))
                return

    @commands.command()
    async def force_drop(self, ctx):
        if ctx.author.id not in Config.OWNERIDS:
            return
        await self.drops(ctx.message)

    def change_turn(self, turn, max, monster):
        if monster["turn"]:
            turn += 1
            if turn >= max:
                turn = 0
            monster["turn"] = False
        else:
            monster["turn"] = True  
        return turn

    async def construct_embeds(self, match, turn, message, monster):
        title = "Boss fight against " + monster['name']

        embed = Battle_Utils.construct_boss_embed(match, turn, monster, title)

        await message.edit(embed=embed)

    async def construct_embeds_with_message(self, message, monster, turn, match, text):
        title = "Boss fight against " + monster['name']

        embed = Battle_Utils.construct_boss_embed_with_message(match, turn, monster, title, text)

        await message.edit(embed=embed)

    async def boss_thread(self, match, message, monster):
        Config.LOGGING.info("Boss thread started: Current threads: " + str(self.bosses))
        match_cache = match.copy()
        await message.clear_reactions()
        monster['health'] = monster['stats']['health']
        monster['mana'] = monster['stats']['endurance']
        embed = discord.Embed(title="Boss found", color=Config.MAINCOLOR,
                              description="[jump](" + message.jump_url + ")")
        one_message = await message.channel.send(", ".join(x['user'].mention for x in match), embed=embed)
        await one_message.delete(delay=10)
        monster['effects'] = []
        monster["turn"] = False
        for user in match:
            self.battling_users.append({"id": user['user'].id, "time": time.time()})
            user['health'] = user['account']['stats']['health']
            user['mana'] = user['account']['stats']['endurance']
            user['effects'] = []
            user['afk'] = 0
        turn = random.randint(0, len(match) - 1)
        if len(match) == 1: 
            if match[0]['account']['slots'][0] is not None:
                await message.add_reaction("1️⃣")
            if match[0]['account']['slots'][1] is not None:
                await message.add_reaction("2️⃣")
            if match[0]['account']['slots'][2] is not None:
                await message.add_reaction("3️⃣")
            if match[0]['account']['slots'][3] is not None:
                await message.add_reaction("4️⃣")
            if len(match[0]['account']['slots']) >= 5:
                if match[0]['account']['slots'][4] is not None:
                    await message.add_reaction("🔆")
        else:
            await message.add_reaction("1️⃣")
            await message.add_reaction("2️⃣")
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
            await message.add_reaction("🔆")
        await message.add_reaction("💤")
        await message.add_reaction("🏳️")
        a_turn = False
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

            if not monster["turn"]:
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

            if monster['health'] <= 0 or monster['mana'] <= 0:
                break

            # Make sure player/boss stats are all fine
            Battle_Utils.match_check(match, monster)

            await self.construct_embeds(match, turn, message, monster)

            if monster['stunned']:
                monster['stunned'] = False
                await asyncio.sleep(3)
                turn = self.change_turn(turn, len(match_cache), monster)
                continue

            # check if monster's turn
            if monster["turn"]:  # turn == len(match):

                # simulate monster thinking lol
                if len(match_cache) == 1:
                    if match_cache[0]["account"]["battles"]["bosses"] < 3:
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(3)
                else:
                    await asyncio.sleep(3)

                spell = Battle_Utils.pick_spell(monster)

                if spell is not None:
                    victim = random.randint(0, len(match) - 1)

                    monster, match[victim], text = Battle_Utils.spell_effect(spell, monster, match[victim], True)

                    await self.construct_embeds_with_message(message, monster, turn, match, text)

                    if match[victim]['ability'] is not None:
                        if match[victim]["ability"] == "Glass Armor":
                            ability = Utils.get_ability(match[victim]['account']['slots'][4])
                            match[victim]["ability"] = "Glass Armor Done"
                            match[victim]['account']['stats']['defense'] -= ability['effect']
                            match, monster = Battle_Utils.match_check(match, monster)

                turn = self.change_turn(turn, len(match), monster)

                if len(match_cache) == 1:
                    if match_cache[0]["account"]["battles"]["bosses"] < 3:
                        await asyncio.sleep(5)
                    else:
                        await asyncio.sleep(3)
                else:
                    await asyncio.sleep(3)

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
                    turn = self.change_turn(turn, len(match_cache), monster)
                    continue

                reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '🔆': 4}
                def check(payload):
                    if payload.user_id == match[turn]['user'].id and payload.message_id == message.id:
                        if str(payload.emoji) in reaction_dict.keys():
                            return match[turn]['account']['slots'][reaction_dict[str(payload.emoji)]] is not None
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
                    turn = self.change_turn(turn, len(match), monster)
                    continue
                elif str(reaction) == "🏳️":
                    match[turn]['health'] = 0
                    match[turn]['mana'] = 0
                    turn = self.change_turn(turn, len(match), monster)
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue
                elif str(reaction) == "🔆" and match[turn]["ability"] is not None:
                    a_turn = True
                elif str(reaction) == "🔆" and match[turn]["ability"] is None:
                    ability = Utils.get_ability(match[turn]['account']['slots'][4])

                    match, text, monster = Battle_Utils.ability_effect(ability, match, turn, monster)

                    await self.construct_embeds_with_message(message, monster, turn, match, text)

                    # Only change turn if it's supposed to
                    if ability["name"] not in ["Amplify"]:
                        turn = self.change_turn(turn, len(match), monster)

                    if len(match_cache) == 1:
                        if match_cache[0]["account"]["battles"]["bosses"] < 3:
                            await asyncio.sleep(5)
                        else:
                            await asyncio.sleep(3)
                    else:
                        await asyncio.sleep(3)
                    continue

                elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                    spell = Utils.get_spell(match[turn]['account']['class'], match[turn]['account']['slots'][reaction_dict[str(reaction)]])

                    match[turn], monster, text = Battle_Utils.spell_effect(spell, match[turn], monster, True)

                    await self.construct_embeds_with_message(message, monster, turn, match, text)

                    # Remove amplify effect
                    if match[turn]["ability"] == "Amplify":
                        ability = Utils.get_ability(match[turn]['account']['slots'][4])
                        match[turn]["ability"] = "Amplify Done"
                        match[turn]['account']['stats']['strength'] -= ability['effect']
                        match = Battle_Utils.match_check(match)

                    turn = self.change_turn(turn, len(match), monster)
                    
                    if len(match_cache) == 1:
                        if match_cache[0]["account"]["battles"]["bosses"] < 3:
                            await asyncio.sleep(5)
                        else:
                            await asyncio.sleep(3)
                    else:
                        await asyncio.sleep(3)

                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue

            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and turn != len(match):
                    embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                          description="Your boss fight is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + message.jump_url + ")")
                    timeout_msg = await message.channel.send(match[turn]['user'].mention, embed=embed)
                    await timeout_msg.delete(delay=20)
                    match[turn]['afk'] += 1
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    turn = self.change_turn(turn, len(match), monster)
                    continue
                elif isinstance(e, discord.errors.NotFound):
                    return
                else:
                    match[turn]['mana'] -= 3
        try:
            await message.clear_reactions()
        except:
            await Config.LOGGING.error("Cannot remove emoji (not big deal)")

        for player in match_cache:
            broken_items = Utils.decrease_durability(player['account']['user_id'])
            if len(broken_items) > 0:
                embed = discord.Embed(title="Broken Tools", description=player['user'].mention + "! Your " + " and ".join([x['name'] for x in broken_items]) + " broke!", color=Config.MAINCOLOR)
                await message.channel.send(content=player['user'].mention, embed=embed)


        if monster['health'] > 0 and monster['mana'] > 0:
            embed = discord.Embed(color = Config.MAINCOLOR, description="**"+monster['name']+" Has bested the group...**")
            await message.edit(embed=embed)
        else:
            if len(match_cache) == 1:
                if match_cache[0]["account"]["battles"]["bosses"] < 3:
                    if match_cache[0]["account"]["battles"]["bosses"] == 0:
                        desc = "<:1_:786197490860818432><:0_:786197490466160641><:0_:786197490466160641>\nNext boss is going to be even stronger, but you'll get more rewards!"
                        amount = 10
                        coins_amount = 20
                    elif match_cache[0]["account"]["battles"]["bosses"] == 1:
                        desc = "<:1_:786197490860818432><:1_:786197490860818432><:0_:786197490466160641>\nNext boss is going to be even stronger, but you'll get more rewards!"
                        amount = 20
                        coins_amount = 40
                    else:
                        desc = "<:1_:786197490860818432><:1_:786197490860818432><:1_:786197490860818432>\nGood job, now it's time for the big boi leagues. From now on you can summon bosses where others can join as well. This is the end of the dummy bosses but you can always get more info on the wiki, tutorial or help command. Or join our Discord server for more guidance! **Good luck out there champion!**\n\n"
                        amount = 50
                        coins_amount = 50

                    embed = discord.Embed(
                        title="Dummy bot defeat!",
                        description="**GOOD JOB!** "
                        + "You did it, you beat one of your first bosses! "
                        + "<:E:730362458547421256> Now it's time to get your loot, you got:\n"
                        + "+" + str(amount) + " "+ Config.EMOJI['key'] + "\n+" + str(coins_amount) + " " + Config.EMOJI['coin'] + "\n\n"
                        + "You're getting the hang of it <:L:730356470905831434>\n"
                        + "__Training bosses:__ " + desc 
                        + "<:E:730362457541050478><:E:730362455716397127> If you want to continue, you can summon another boss or if you want more info you can check the wiki command!",
                        color = Config.OK
                    )
                    embed.set_thumbnail(url="https://media.discordapp.net/attachments/736320244649295894/786213274386694194/SPELL_Damage.png?width=450&height=430")
                    await message.edit(embed=embed)
                    
                    for user in match_cache:
                        user['account'] = Utils.get_account(user['user'].id)
                        user['account']['keys'] += amount
                        while user['account']['keys'] > 9:
                            user['account']['keys'] -= 10
                            user['account']['chests'] += 1
                        Config.USERS.update_one({'user_id': user['user'].id}, {'$set': {'chests': user['account']['chests'], 'keys': user['account']['keys']}, '$inc': {'coins': coins_amount, "battles.bosses": 1}})
                        
                        users = []
                        for user in match_cache:
                            users.append(user["user"].id)
                        i = 0
                        while i != len(self.battling_users):
                            if self.battling_users[i]["id"] in users:
                                self.battling_users.pop(i)
                            else:
                                i += 1
                        if message.channel.id in self.active_channels:
                            self.active_channels.remove(message.channel.id)
                        self.bosses -= 1
                        return                    
            if not monster['titan']:
                amount = random.randint(math.floor(0.3 * len(match_cache)) * 2 + 3, math.floor(0.3 * len(match_cache)) * 2 + 6)
                coins_amount = random.randint(len(match_cache) * 3, (len(match_cache) * 4) + 1)
            else:
                amount = random.randint(math.floor(0.5 * len(match_cache)) * 2 + 5, math.floor(0.5 * len(match_cache)) * 2 + 9)
                coins_amount = random.randint(len(match_cache) * 4, (len(match_cache) * 5) + 1)
            mystring = str(amount) + " "+ Config.EMOJI['key'] + "\n+" + str(coins_amount) + " " + Config.EMOJI['coin']
            for user in match_cache:
                user['account'] = Utils.get_account(user['user'].id)
                user['account']['keys'] += amount
                while user['account']['keys'] > 9:
                    user['account']['keys'] -= 10
                    user['account']['chests'] += 1
                Config.USERS.update_one({'user_id': user['user'].id}, {'$set': {'chests': user['account']['chests'], 'keys': user['account']['keys']}, '$inc': {'coins': coins_amount}})
            if monster['health'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has been killed!**\n\nEveryone gets:\n\n+" + mystring)
            elif monster['mana'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+monster['name']+" has fainted!**\n\nEveryone gets:\n\n+" + mystring)
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + monster['name'] + " has been destroyed completely!**\n\nEveryone gets:\n\n+ " + mystring)
            await message.edit(embed=embed)
        users = []
        for user in match_cache:
            users.append(user["user"].id)
        i = 0
        while i != len(self.battling_users):
            if self.battling_users[i]["id"] in users:
                self.battling_users.pop(i)
            else:
                i += 1
        if message.channel.id in self.active_channels:
            self.active_channels.remove(message.channel.id)
        self.bosses -= 1

    @commands.command()
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def boss(self, ctx):
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

        if ctx.author.id in self.waiting_users:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Finding Boss", description="You are already searching for a boss. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.channel.id in self.active_channels:
            embed=discord.Embed(color=Config.MAINCOLOR, title="Error Finding Boss", description="You are already battling a boss in this channel. Please finish that battle first.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        i = 0
        while i != len(self.battling_users):
            if self.battling_users[i]["id"] == ctx.author.id:
                if (self.battling_users[i]["time"]+600) > time.time():
                    embed=discord.Embed(color=Config.MAINCOLOR, title="Error entering Queue", description="You are already battling a boss. Please finish that battle first.")
                    if msg is None:
                        msg = await ctx.send(embed=embed)
                    else:
                        await msg.edit(embed=embed)
                    return
                else:
                    self.battling_users.pop(i)
                    continue
            else:
                i += 1

        if account["battles"]["bosses"] > 2:
            user_names = []
            user_ids = []
            quote = "*\""+Battle_Utils.quotes()+"\"*"
            self.waiting_users.append(ctx.author.id)
            self.active_channels.append(ctx.channel.id)

            user_ids.append(ctx.author.id)
            user_names.append(ctx.author.name)
            users_names = ""
            for user_n in user_names:
                users_names += user_n+"\n"
            embed=discord.Embed(color=Config.MAINCOLOR, title=ctx.author.name + " Is searching for a boss<a:dots:715134569355018284>", description=f"The battle will begin in 1 minute. React to join.\n⚔️ **Players ({str(len(user_ids))}/10):**\n{users_names}\n{quote}", timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
            embed.set_footer(text='React with the ✔️ to join | starting at ')
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320366116470815/779302235427438602/fire_1f525.png")
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
                        await msg.edit(embed=discord.Embed(title="Boss Search canceled", color = Config.MAINCOLOR, description=ctx.author.name + " has disbanded the search..."))
                        if ctx.channel.id in self.active_channels:
                            self.active_channels.remove(ctx.channel.id)
                        for u in user_ids:
                            if u in self.waiting_users:
                                self.waiting_users.remove(u)
                        return
                    elif Utils.get_account(user.id) is None:
                        await reaction.remove(user)
                        error_msg = await ctx.send(embed=discord.Embed(title="You don't have an account", color = Config.MAINCOLOR, description="Type `]profile` to choose a class and react again to join the battle!"))
                        await error_msg.delete(delay=20)
                        continue
                    elif user.id in self.waiting_users and user.id != ctx.author.id:
                        if user.id not in user_ids:
                            error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already searching", color = Config.MAINCOLOR, description="You are already searching for a boss"))
                            await error_msg.delete(delay=20)
                            await reaction.remove(user)
                            continue
                    elif user.id in self.battling_users and user.id != ctx.author.id:
                        error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already battling", color = Config.MAINCOLOR, description="You are already battling a boss"))
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
                            error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already full", color = Config.MAINCOLOR, description="The party is full. Only 10 people can fight a single boss."))
                            continue
                        user_ids.append(user.id)
                        user_names.append(user.name)
                        self.waiting_users.append(user.id)
                    users_names = ""
                    for user in user_names:
                        users_names += user+"\n"
                    embed=discord.Embed(color=Config.MAINCOLOR, title=ctx.author.name + " Is searching for a boss<a:dots:715134569355018284>", description=f"The battle will begin in 1 minute. React to join.\n⚔️ **Players ({str(len(user_ids))}/10):**\n{users_names}\n{quote}", timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
                    embed.set_footer(text='React with the ✔️ to join | starting at ')
                    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320366116470815/779302235427438602/fire_1f525.png")
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
                await msg.edit(embed=discord.Embed(title="Boss Search canceled", color=Config.MAINCOLOR, description="No one was brave enough to challenge a boss..."))
                if ctx.channel.id in self.active_channels:
                    self.active_channels.remove(ctx.channel.id)
                for u in user_ids:
                    if u in self.waiting_users:
                        self.waiting_users.remove(u)
                return
            match = []
            for user in user_ids:
                user = await self.bot.fetch_user(user)
                if user.id != self.bot.user.id:
                    account = Utils.get_account(user.id)
                    armor = None
                    weapon = None
                    if account["weapon"] is not None:
                        weapon = Utils.get_item(account['weapon']["name"])
                    if account["armor"] is not None:
                        armor = Utils.get_item(account['armor']["name"])
                    match.append({'ability': None, 'weapon': weapon, 'armor': armor, 'user': user, 'stunned': False,
                                  'account': account})
            monster_class = random.choice(list(Config.CLASSES.find({})))
            spells = list(Config.SPELLS.find({'class': monster_class['name'], 'type': {'$nin': ['STUN']}}).limit(6))

            for i in range(len(match)):
                if match[i]['account']['armor'] is not None:
                    match[i]['account']['stats']['defense'] += Utils.calc_item_effect(match[i]["account"]["armor"], match[i]['armor'])
                if match[i]['account']['weapon'] is not None:
                    match[i]['account']['stats']['strength'] += Utils.calc_item_effect(match[i]["account"]["weapon"], match[i]['weapon'])

            if random.randint(0, 7) == 0:
                strength = round(3 + (statistics.mean(x['account']['stats']['defense'] for x in match)
                                      * round(random.uniform(1.1, 1.4), 2)))
                defense = round(2 * (statistics.mean(x['account']['stats']['strength'] for x in match)
                                     * round(random.uniform(0.6, 0.7), 2)))
                monster = {'name': Battle_Utils.make_monster_name(True),
                           'titan': True, 'spells': spells,
                           'armor': {'name': "Titan's Breastplate", 'effect': random.randint(3, 9),
                                     'emoji': "<:helmet:675820506284556306>"},
                           'weapon': {'name': "Aged Sword", 'effect': random.randint(3, 9),
                                      'emoji': "<:battle:670882198450339855>"},
                           'stats': {'health': round(80 + (math.sqrt(len(match)) * 15)), 'strength': strength,
                                     'defense': defense, 'endurance': random.randint(140, 170) + len(match) * 12},
                           'stunned': False}
            else:
                strength = round(3 + (statistics.mean(x['account']['stats']['defense'] for x in match)
                                      * round(random.uniform(1, 1.2), 2)))
                defense = round(2 * (statistics.mean(x['account']['stats']['strength'] for x in match)
                                     * round(random.uniform(0.5, 0.65), 2)))
                monster = {'name': Battle_Utils.make_monster_name(),
                           'titan': False, 'spells': spells,
                           'stats': {'health': round(60 + (math.sqrt(len(match)) * 10)), 'strength': strength,
                                     'defense': defense, 'endurance': random.randint(90, 140) + len(match) * 10},
                           'stunned': False}
            for user in match:
                if user["account"]["user_id"] in self.waiting_users:
                    self.waiting_users.remove(user["account"]["user_id"])
                    Config.USERS.update_one({'user_id': user["account"]["user_id"]}, {'$inc': {'battles.bosses': 1}})
        else:
            if account["battles"]["bosses"] == 0:
                desc = "<:0_:786197490466160641><:0_:786197490466160641><:0_:786197490466160641>"
                spells = [{'name': 'Witchers Wind', 'class': 'Paladin', 'id': 0, 'damage': 10, 'scaling': 1.4, 'emoji': '<:D:761582483434242118>', 'cost': 20, 'type': 'DAMAGE'}, {'name': 'Ceremony of Absorption', 'class': 'Paladin', 'id': 1, 'damage': 5, 'scaling': 1.0, 'emoji': '<:H:761582482809159693>', 'cost': 15, 'type': 'HEAL'}]
                monster = {'name': Battle_Utils.make_monster_name(), 'titan': False, 'spells': spells, 'stats': {'health': 40, 'strength': 1, 'defense': 1, 'endurance': 60}, 'stunned': False}
            if account["battles"]["bosses"] == 1:
                desc = "<:1_:786197490860818432><:0_:786197490466160641><:0_:786197490466160641>\nWATCH OUT FOR MANA, you can die if it goes below 0"
                spells = [{'name': 'Hymn of Rage', 'class': 'Druid', 'id': 0, 'damage': 6, 'scaling': 1.3, 'emoji': '<:D:761582483434242118>', 'cost': 12, 'type': 'DAMAGE'}, {'name': 'Silence', 'class': 'Druid', 'id': 1, 'damage': 3, 'scaling': 1, 'emoji': '<:P:761582482708889631>', 'cost': 10, 'type': 'PEN'}, {'name': 'Flood', 'class': 'Druid', 'id': 4, 'damage': 10, 'scaling': 1, 'emoji': '<:H:761582482809159693>', 'cost': 40, 'type': 'HEAL'}, {'name': 'Mystic Burn', 'class': 'Druid', 'id': 6, 'damage': 10, 'scaling': 1.3, 'emoji': '<:D:761582483434242118>', 'cost': 23, 'type': 'DAMAGE'}]
                monster = {'name': Battle_Utils.make_monster_name(), 'titan': False, 'spells': spells, 'stats': {'health': 50, 'strength': 2, 'defense': 2, 'endurance': 80}, 'stunned': False}
            if account["battles"]["bosses"] == 2:
                desc = "<:1_:786197490860818432><:1_:786197490860818432><:0_:786197490466160641>\nWATCH OUT FOR MANA, you can die if it goes below 0"
                spells = [{'name': 'Revitalize', 'class': 'Arcane', 'id': 7, 'damage': 4, 'scaling': 1, 'emoji': '<:D:761582483237371914>', 'cost': 0, 'type': 'DRAIN'}, {'name': 'Seism', 'class': 'Arcane', 'id': 1, 'damage': 15, 'scaling': 1, 'emoji': '<:D:761582483237371914>', 'cost': 10, 'type': 'DRAIN'}, {'name': 'Upbringing', 'class': 'Arcane', 'id': 3, 'damage': 3, 'scaling': 1, 'emoji': '<:P:761582482708889631>', 'cost': 20, 'type': 'PEN'}, {'name': 'Void', 'class': 'Arcane', 'id': 5, 'damage': 6, 'scaling': 1.6, 'emoji': '<:D:761582483434242118>', 'cost': 30, 'type': 'DAMAGE'}, {'name': 'Depths', 'class': 'Arcane', 'id': 0, 'damage': 4, 'scaling': 1.5, 'emoji': '<:D:761582483434242118>', 'cost': 16, 'type': 'DAMAGE'}, {'name': 'Mirage', 'class': 'Arcane', 'id': 4, 'damage': 1, 'scaling': 1, 'emoji': '<:A:761582483153354752>', 'cost': 30, 'type': 'ARMOR'}]
                monster = {'name': Battle_Utils.make_monster_name(), 'titan': True, 'spells': spells, 'stats': {'health': 70, 'strength': 3, 'defense': 1, 'endurance': 80}, 'stunned': False}

            embed = discord.Embed(
                title="Time to show you the ropes!",
                description="**You're about to start one of your first bosses!** "
                + "How exciting! <:E:730362458547421256> The first three solo bosses you do are againt our training dummies, "
                + "designed to show you how to beat the bigger monsters \:)\n\n"
                + "__Training bosses:__ " + desc + "\n"
                + "If you're not sure how certain things work yet, don't worry. You'll figure it out! <:L:730356470905831434>\n"
                + "<:E:730362457541050478><:E:730362455716397127> If you're ready to rumble, click on the checkmark ✔",
                color = 0xffcd00
            )
            embed.set_thumbnail(url="https://media.discordapp.net/attachments/736320244649295894/786213274386694194/SPELL_Damage.png?width=450&height=430")

            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            await msg.add_reaction("✔️")
            await msg.add_reaction("❌")

            countdown = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
            def check(reaction, user):
                return user.id != self.bot.user.id and reaction.message.id == msg.id
            
            while datetime.datetime.utcnow() < countdown:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)
                    if str(reaction) == "❌" and user.id == ctx.author.id:
                        await msg.clear_reactions()
                        await msg.edit(embed=discord.Embed(title="Boss Search canceled", color = Config.MAINCOLOR, description=ctx.author.name + " has disbanded the search..."))
                        # if ctx.channel.id in self.active_channels:
                        #     self.active_channels.remove(ctx.channel.id)
                        # for u in user_ids:
                        #     if u in self.waiting_users:
                        #         self.waiting_users.remove(u)
                        return
                    elif user.id in self.waiting_users and user.id != ctx.author.id:
                        if user.id not in self.battling_users:
                            error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already searching", color = Config.MAINCOLOR, description="You are already searching for a boss"))
                            await error_msg.delete(delay=20)
                            await reaction.remove(user)
                            continue
                    elif user.id in self.battling_users and user.id != ctx.author.id:
                        error_msg = await ctx.send(content=user.mention, embed=discord.Embed(title="Already battling", color = Config.MAINCOLOR, description="You are already battling a boss"))
                        await error_msg.delete(delay=20)
                        await reaction.remove(user)
                        continue
                    elif reaction.message.id != msg.id or not reaction.me:
                        continue
                    elif str(reaction) == "✔️" and user.id == ctx.author.id:
                        await msg.clear_reactions()
                        break
                except asyncio.TimeoutError:
                    continue
            
            match = []
            if ctx.author.id != self.bot.user.id:
                account = Utils.get_account(ctx.author.id)
                armor = None
                weapon = None
                if account["weapon"] is not None:
                    weapon = Utils.get_item(account['weapon']["name"])
                if account["armor"] is not None:
                    armor = Utils.get_item(account['armor']["name"])
                match.append({'ability': None, 'weapon': weapon, 'armor': armor, 'user': user, 'account': account,
                              'stunned': False})
        if 'weapon' in monster.keys():
            monster['stats']['strength'] += monster['weapon']['effect']
        if 'armor' in monster.keys():
            monster['stats']['defense'] += monster['armor']['effect']

        monster['stats']['strength'] = round(monster['stats']['strength'])
        monster['stats']['defense'] = round(monster['stats']['defense'])
        monster['stats']['health'] = round(monster['stats']['health'])
        self.bosses += 1
        match_copy = match.copy()
        try:
            await self.boss_thread(match, msg, monster)
        except Exception as e:
            users = []
            for user in match_copy:
                users.append(user["user"].id)
            i = 0
            while i != len(self.battling_users):
                if self.battling_users[i]["id"] in users:
                    self.battling_users.pop(i)
                else:
                    i += 1
            if ctx.channel.id in self.active_channels:
                self.active_channels.remove(ctx.channel.id)
            self.bosses -= 1
            raise e

    @boss.error
    async def boss_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..", description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"), color = Config.ERRORCOLOR)

def setup(bot):
    bot.add_cog(Bosses(bot))
