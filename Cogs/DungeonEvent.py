import asyncio
import datetime
import math
import random

import discord
import pymongo
from discord.ext import commands

import Config
import Utils


async def get_monster_name(floor):
    names = ["Bubbles", "Pinkie", "Hoppity", "Eggy", "Sparkle", "Dizzy", "Pop", "Hop", "Nibbles", "Sprinkles", "Fluff",
             "Rainbow", "Carrot", "Candy", "Lily", "Smartie"]
    jobs_cluck = [" the Nest Maker", ", Maid of Cluck", ", Chef of Cluck", ", Son of Cluck", ", Daughter of Cluck"]
    jobs_other = [" the Egg Painter", " the Egg Hider", " the Chocolate Taster", " the Chocolate Mixer",
                  " the Egg Transporter", " of Egg Quality Assurance", " the Nest Maker"]
    if floor == 5:
        return "Cluck, layer of 🥚"
    if floor == 10:
        return "Easter Bunny"
    if floor == 15:
        return "Killer Bunny"
    if floor < 5:
        return random.choice(names) + random.choice(jobs_cluck)
    else:
        return random.choice(names) + random.choice(jobs_other)


def skip_limit(page_size, page_num):
    """returns a set of documents belonging to page number `page_num`
    where size of each page is `page_size`.
    """
    # Calculate number of documents to skip
    skips = page_size * (page_num - 1)

    # Skip and limit
    cursor = Config.USERS.aggregate([{"$sort": {'event.tower.high': pymongo.DESCENDING, "user_id": pymongo.DESCENDING}},
                                     {"$match": {"event.tower.high": {"$gt": 0}}}, {"$skip": skips}, {"$limit": 10}])
    # Return documents
    return [x for x in cursor]


async def generate_rewards(account):
    options = {'1': None, '2': None, '3': None}
    for key in options.keys():
        choices = ['spell', 'item-mat', 'item-level', 'ability']
        chances = (30, 10, 35, 20)
        choice = random.choices(choices, chances)
        item_type = None

        # Stops duplicate rewards
        while True:
            if choice == ['spell']:
                spells = []
                for spell in Config.SPELLS.find({}):
                    if spell['class'] == account['class'] and spell['id'] not in account['slots'][:4]:
                        spells.append(spell['id'])

                spell = random.choice(spells)
                if {'type': 'spell', 'id': spell} not in options.values():
                    options[key] = {'type': 'spell', 'id': spell}
                    break

            elif choice == ['ability']:
                abilities = list(Config.ABILITIES.find({'id': {'$nin': [6, 7, 8, 11, account['slots'][4]]}}))
                ability = random.choice(abilities)

                if {'type': 'ability', 'id': ability['id']} not in options.values():
                    options[key] = {'type': 'ability', 'id': ability['id']}
                    break

            elif choice == ['item-level']:
                item_type = random.choice(['weapon', 'armor'])
                # If the user doesn't have an item, we have nothing to add level to
                # So we'll give them an item!
                if account[item_type] is None:
                    choice = ['item-mat']
                    continue

                # Select level up amount
                levels = [2, 3, 4, 5, 6, 7]
                level_chances = [20, 20, 30, 20, 20, 10]
                up_level = random.choices(levels, level_chances)[0]

                # If the item exceeds the maximum, we'll upgrade the item!
                if account[item_type]['level'] + up_level > Utils.get_item(account[item_type]['name'])['max']:
                    choice = ['item-mat']
                    continue
                else:
                    is_in = False
                    for level in levels:
                        if {'type': f'{item_type}-level', 'amount': level} in options.values():
                            is_in = True

                # We're already upgrading this item, choose another reward
                if is_in:
                    choice = random.choices(choices, chances)
                else:
                    options[key] = {'type': f'{item_type}-level', 'amount': up_level}
                    break

            if choice == ['item-mat']:
                if item_type is None:
                    item_type = random.choice(['weapon', 'armor'])
                materials = ['wood', 'bronze', 'iron', 'emerald', 'enchanted', 'phantom']
                material = None

                # Get tier
                if account[item_type] is not None:
                    # Get current material
                    for item in materials:
                        if account[item_type]['name'].lower().startswith(item):
                            material = item

                    # If possible, set next material, otherwise re-choose reward
                    if material != 'phantom':
                        material = materials[materials.index(material) + 1]
                    else:
                        choice = random.choices(choices, chances)
                        continue
                else:
                    material = 'wood'

                # Get all items at new tier and type
                items = []
                for item in Utils.get_all_weapons():
                    if item['type'] == item_type and item['tier'] == material:
                        items.append(item)

                # Choose and select the next item
                item = random.choice(items)
                if {'type': f'{item_type}-mat', 'name': item['name']} not in options.values():
                    options[key] = {'type': f'{item_type}-mat', 'name': item['name']}
                    break

    return options


async def display_reward(reward, account):
    if reward['type'] == 'spell':
        spell = Utils.get_spell(account['class'], reward['id'])
        return "New Spell: " + spell['emoji'] + " **" + " " + spell['name'] + "** - [ " + \
               str(spell['damage']) + " effect] [ " + str(spell['cost']) + " cost] [ " + str(spell['scaling']) + \
               " scaling]"

    elif reward['type'] == 'ability':
        ability = Utils.get_ability(reward['id'])
        return "New Ability: " + ability['emoji'] + " **" + ability['name'] + "** - " + \
               ability['desc']

    else:
        # Setup weapon data
        if reward['type'].startswith('weapon'):
            try:
                item = Utils.get_item(reward['name'])
            except KeyError:
                item = Utils.get_item(account['weapon']['name'])
            try:
                item_level = account['weapon']['level']
            except TypeError:
                item_level = 1
        # Setup armor data
        elif reward['type'].startswith('armor'):
            try:
                item = Utils.get_item(reward['name'])
            except KeyError:
                item = Utils.get_item(account['armor']['name'])
            try:
                item_level = account['armor']['level']
            except TypeError:
                item_level = 1

        # Display the data
        if reward['type'] == 'weapon-mat':
            return "New Weapon: " + str(item['emoji']) + " **" + str(item['name']) + "** - `" + \
                   str(Utils.calc_item_effect({'level': item_level}, item)) + "`"

        elif reward['type'] == 'armor-mat':
            return "New Armor: " + str(item['emoji']) + " **" + str(item['name']) + "** - `" + \
                   str(Utils.calc_item_effect({'level': item_level}, item)) + "`"

        elif reward['type'] == 'weapon-level':
            return f"Upgrade Weapon x{reward['amount']}: " + str(item['emoji']) + " **" + item['name'] + "** - `" + \
                   str(Utils.calc_item_effect({'level': item_level}, item)) + "` -> `" + \
                   str(Utils.calc_item_effect({'level': item_level + reward['amount']}, item)) + "`"

        elif reward['type'] == 'armor-level':
            return f"Upgrade Armor x{reward['amount']}: " + str(item['emoji']) + " **" + item['name'] + "** - `" + \
                   str(Utils.calc_item_effect({'level': item_level}, item)) + "` -> `" + \
                   str(Utils.calc_item_effect({'level': item_level + reward['amount']}, item)) + '`'

        else:
            await Config.LOGGING.error("Somehow generated invalid tower floor reward")
            return


async def construct_embeds(match, turn, floor, message, monster):
    # SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    # User's turn
    if not monster['turn']:
        if match[turn]['stunned']:
            embed = discord.Embed(color=Config.EVENTCOLOR,
                                  description="It is " + match[turn]['user'].name + "'s turn " +
                                              "but they're stunned so can't do anything!")
        else:
            embed = discord.Embed(color=Config.EVENTCOLOR, description="It is " + match[turn]['user'].name + "'s turn.")
        equipped_string = ""

        # Get Spells
        for spell in match[turn]['account']['slots'][:4]:
            if spell is None:
                equipped_string += "\n> " + Config.EMOJI["spell"] + " *Nothing is written on this page...*"
                continue
            spell = Utils.get_spell(match[turn]['account']['class'], spell)
            if spell is not None:
                equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + spell['name'] + \
                                   "** - [ " + str(spell['damage']) + " effect] [ " + \
                                   str(spell['cost']) + " cost] [ " + str(spell['scaling']) + " scaling]"
        # Display Ability
        if len(match[turn]['account']['slots']) >= 5:
            if match[turn]['account']['slots'][4] is not None:
                ability = Utils.get_ability(match[turn]['account']["slots"][4])
                if match[turn]['ability'] is not None:
                    equipped_string += "\n> " + Config.EMOJI['broken'] + " **" + ability["name"] + "** " + \
                                       ability['desc']
                else:
                    equipped_string += "\n> " + ability['emoji'] + " **" + ability["name"] + "** " + ability['desc']
        embed.description += "\n\n**" + match[turn]['user'].name + "'s Spellbook**:" + equipped_string

        # Strength of boss
        weapon_additive_string = " " + Config.EMOJI["sword"] + " "
        if 'weapon' in monster.keys():
            # weapon_additive_string = " [+" + str(monster['weapon']['effect']) + monster['weapon']['emoji'] + "]"
            weapon_additive_string = " " + monster['weapon']['emoji'] + " "
        # Defence of boss
        armor_additive_string = " " + Config.EMOJI["shield"] + " "
        if 'armor' in monster.keys():
            # armor_additive_string = " [+" + str(monster['armor']['effect']) + monster['armor']['emoji'] + "]"
            armor_additive_string = " " + monster['armor']['emoji'] + " "
        # Add to embed
        embed.description += "\n\n**" + monster['name'] + "**\n" + \
                             Utils.generate_battlestats(monster["health"], monster['stats']['health'],
                                                        monster["mana"], monster['stats']['endurance'],
                                                        monster['stats']['strength'], weapon_additive_string,
                                                        monster['stats']['defense'], armor_additive_string,
                                                        monster["effects"]) + "\n‎‎‏‏‎ ‎"

        # User stats
        for user in match:
            # User strength
            weapon_additive_string = " " + Config.EMOJI["sword"] + " "
            if user['account']['weapon'] is not None:
                # weapon_additive_string = " [+" + str(Utils.calc_item_effect(user["account"]["weapon"],
                # user['weapon'])) + user['weapon']['emoji'] + "]"
                weapon_additive_string = " " + user['weapon']['emoji'] + " "

            # User defence
            armor_additive_string = " " + Config.EMOJI["shield"] + " "
            if user['account']['armor'] is not None:
                # armor_additive_string = " [+" + str(Utils.calc_item_effect(user["account"]["armor"],
                # user['armor'])) + user['armor']['emoji'] + "]"
                armor_additive_string = " " + user['armor']['emoji'] + " "

            # Add to embed
            embed.add_field(name=Utils.get_class(user['account']['class'])['emote'] + " " + user['user'].name +
                                 user['selected_title'],
                            value=Utils.generate_battlestats(user["health"], user['account']['stats']['health'],
                                                             user["mana"], user['account']['stats']['endurance'],
                                                             user['account']['stats']['strength'],
                                                             weapon_additive_string,
                                                             user['account']['stats']['defense'], armor_additive_string,
                                                             user["effects"]))

        # Embed title
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        embed.title = boss_class["emote"] + " | Tower fight against " + monster['name'] + " | Floor " + str(floor)

        # Embed Footer
        footer_string = ""
        for effect in match[turn]['effects']:
            footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(
                effect['turns']) + " turns."

        # Check for resource abilities
        if match[turn]['ability'] == "Healing Blood":
            embed.set_footer(text=match[turn]['user'].name + " gains 5 health at the beginning of their turn." +
                                  footer_string)
        elif match[turn]['ability'] == "Inner Light":
            embed.set_footer(text=match[turn]['user'].name + " gains 6 mana at the beginning of their turn." +
                                  footer_string)
        # No ability, so base 3 mana
        else:
            embed.set_footer(text=match[turn]['user'].name + " gains 3 mana at the beginning of their turn." +
                                  footer_string)

        await message.edit(embed=embed)

    # Bosses turn
    else:
        if monster['stunned']:
            embed = discord.Embed(color=Config.EVENTCOLOR, description="It is " + monster['name'] + "'s turn " +
                                                                       "but they're stunned so can't do anything!")
        else:
            embed = discord.Embed(color=Config.NOTTURN, description="It is " + monster['name'] + "'s turn.")
        # Spells display
        equipped_string = ""
        for spell in monster['spells']:
            equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + spell['name'] + \
                               "** - [ " + str(spell['damage']) + " effect] [ " + str(spell['cost']) + " cost] [ " + \
                               str(spell['scaling']) + " scaling]"
        embed.description += "\n\n**" + monster['name'] + "'s Spellbook**:" + equipped_string

        # Equipment and stats
        weapon_additive_string = " " + Config.EMOJI["sword"] + " "
        if 'weapon' in monster.keys():
            weapon_additive_string = " " + monster['weapon']['emoji'] + " "
        armor_additive_string = " " + Config.EMOJI["shield"] + " "
        if 'armor' in monster.keys():
            armor_additive_string = " " + monster['armor']['emoji'] + " "

        # Add stats to display
        embed.description += "\n\n**" + monster['name'] + "**\n" + \
                             Utils.generate_battlestats(monster["health"], monster['stats']['health'],
                                                        monster["mana"], monster['stats']['endurance'],
                                                        monster['stats']['strength'], weapon_additive_string,
                                                        monster['stats']['defense'], armor_additive_string,
                                                        monster["effects"]) + "\n‎‎‏‏‎ ‎"

        # Add user display
        for user in match:
            # User equipment
            weapon_additive_string = " " + Config.EMOJI["sword"] + " "
            if user['account']['weapon'] is not None:
                # weapon_additive_string = " [+" + str(Utils.calc_item_effect(user["account"]["weapon"],
                # user['weapon'])) + user['weapon']['emoji'] + "]"
                weapon_additive_string = " " + user['weapon']['emoji'] + " "
            armor_additive_string = " " + Config.EMOJI["shield"] + " "
            if user['account']['armor'] is not None:
                # armor_additive_string = " [+" + str(Utils.calc_item_effect(user["account"]["armor"],
                # user['armor'])) + user['armor']['emoji'] + "]"
                armor_additive_string = " " + user['armor']['emoji'] + " "

            embed.add_field(name=Utils.get_class(user['account']['class'])['emote'] + " " + user['user'].name +
                                 user['selected_title'],
                            value=Utils.generate_battlestats(user["health"], user['account']['stats']['health'],
                                                             user["mana"], user['account']['stats']['endurance'],
                                                             user['account']['stats']['strength'],
                                                             weapon_additive_string,
                                                             user['account']['stats']['defense'], armor_additive_string,
                                                             user["effects"]))

        # Embed title
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        embed.title = boss_class["emote"] + " | Tower fight against " + monster['name'] + " | Floor " + str(floor)

        # Embed footer
        footer_string = ""
        for effect in monster['effects']:
            footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + \
                             str(effect['turns']) + " turns."
        # Resource generation
        abilities = []
        for user in match:
            abilities.append(user["ability"])
        if "Stagnation" in abilities:
            embed.set_footer(text=monster['name'] + " doesn't regenerate anything, an enemy used Stagnation on them."
                                  + footer_string)
        else:
            embed.set_footer(text=monster['name'] + " gains 4 mana at the beginning of their turn." + footer_string)
        await message.edit(embed=embed)


async def construct_embeds_with_message(message, monster, turn, floor, match, text):
    # SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

    # User turn
    if not monster['turn']:
        embed = discord.Embed(color=Config.OK, description=text)
        for user in match:
            # User equipment
            weapon_additive_string = " " + Config.EMOJI["sword"] + " "
            if user['account']['weapon'] is not None:
                weapon_additive_string = " " + user['weapon']['emoji'] + " "
            armor_additive_string = " " + Config.EMOJI["shield"] + " "
            if user['account']['armor'] is not None:
                armor_additive_string = " " + user['armor']['emoji'] + " "
            # Add user stats display
            embed.add_field(name=Utils.get_class(user['account']['class'])['emote'] + " " + user['user'].name +
                                 user['selected_title'],
                            value=Utils.generate_battlestats(user["health"], user['account']['stats']['health'],
                                                             user["mana"], user['account']['stats']['endurance'],
                                                             user['account']['stats']['strength'],
                                                             weapon_additive_string,
                                                             user['account']['stats']['defense'], armor_additive_string,
                                                             user["effects"]))

        # Embed title
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        embed.title = boss_class["emote"] + " | Tower fight against " + monster['name'] + " | Floor " + str(
            floor)
        # Boss equipment
        weapon_additive_string = " " + Config.EMOJI["sword"] + " "
        if 'weapon' in monster.keys():
            weapon_additive_string = " " + monster['weapon']['emoji'] + " "
        armor_additive_string = " " + Config.EMOJI["shield"] + " "
        if 'armor' in monster.keys():
            armor_additive_string = " " + monster['armor']['emoji'] + " "
        # Add boss stats to display
        embed.description += "\n\n**" + monster['name'] + "**\n" + \
                             Utils.generate_battlestats(monster["health"], monster['stats']['health'],
                                                        monster["mana"], monster['stats']['endurance'],
                                                        monster['stats']['strength'], weapon_additive_string,
                                                        monster['stats']['defense'], armor_additive_string,
                                                        monster["effects"]) + "\n‎‎‏‏‎ ‎"

        # Set footer
        embed.set_footer(text=match[turn]['user'].name + " is planning their next move.")
        await message.edit(embed=embed)

    # Boss move
    else:
        embed = discord.Embed(color=Config.DAMAGE, description=text)
        for user in match:
            # User equipment
            weapon_additive_string = " " + Config.EMOJI["sword"] + " "
            if user['account']['weapon'] is not None:
                weapon_additive_string = " " + user['weapon']['emoji'] + " "
            armor_additive_string = " " + Config.EMOJI["shield"] + " "
            if user['account']['armor'] is not None:
                armor_additive_string = " " + user['armor']['emoji'] + " "
            # Add user stats to display
            embed.add_field(name=Utils.get_class(user['account']['class'])['emote'] + " " + user['user'].name +
                                 user['selected_title'],
                            value=Utils.generate_battlestats(user["health"], user['account']['stats']['health'],
                                                             user["mana"], user['account']['stats']['endurance'],
                                                             user['account']['stats']['strength'],
                                                             weapon_additive_string,
                                                             user['account']['stats']['defense'], armor_additive_string,
                                                             user["effects"]))

        # Embed title
        boss_class = Utils.get_class(monster['spells'][0]["class"])
        embed.title = boss_class["emote"] + " | Tower fight against " + monster['name'] + " | Floor " + str(floor)

        # Boss equipment
        weapon_additive_string = " " + Config.EMOJI["sword"] + " "
        if 'weapon' in monster.keys():
            weapon_additive_string = " " + monster['weapon']['emoji'] + " "
        armor_additive_string = " " + Config.EMOJI["shield"] + " "
        if 'armor' in monster.keys():
            armor_additive_string = " " + monster['armor']['emoji'] + " "
        # Add boss stats to display
        embed.description += "\n\n**" + monster['name'] + "**\n" + \
                             Utils.generate_battlestats(monster["health"], monster['stats']['health'],
                                                        monster["mana"], monster['stats']['endurance'],
                                                        monster['stats']['strength'], weapon_additive_string,
                                                        monster['stats']['defense'], armor_additive_string,
                                                        monster["effects"]) + "\n‎‎‏‏‎ ‎"

        # Set footer
        embed.set_footer(text=monster['name'] + " is planning their next move.")
        await message.edit(embed=embed)


def change_turn(turn, max_turn, monster):
    if monster["turn"]:
        turn += 1
        if turn >= max_turn:
            turn = 0
        monster["turn"] = False
    else:
        monster["turn"] = True
    return turn


def clean_up_match(turn, match, monster):
    # Make sure health and mana are not above max value
    for _ in match:
        if _['health'] > _['account']['stats']['health']:
            _['health'] = _['account']['stats']['health']
        if _['mana'] > _['account']['stats']['endurance']:
            _['mana'] = _['account']['stats']['endurance']

        # Make sure strength stats are where they should be
        strength_min = 1
        # if _['account']['weapon'] is not None:
        #     strength_min = Utils.calc_item_effect(_['account']['weapon'], _['weapon'])
        if _['account']['stats']['strength'] < strength_min:
            _['account']['stats']['strength'] = strength_min
        else:
            _['account']['stats']['strength'] = round(_['account']['stats']['strength'], 1)

        # make sure armor stats are where they should be
        armor_min = 1
        # if _['account']['armor'] is not None:
        #     armor_min = Utils.calc_item_effect(_['account']['armor'], _['armor'])
        if _['account']['stats']['defense'] < armor_min:
            _['account']['stats']['defense'] = armor_min
        else:
            _['account']['stats']['defense'] = round(_['account']['stats']['defense'], 1)

    # make sure monster values are in check as well
    if monster['health'] > monster['stats']['health']:
        monster['health'] = monster['stats']['health']
    if monster['mana'] > monster['stats']['endurance']:
        monster['mana'] = monster['stats']['endurance']

    # make sure strength stats are where they should be FOR MONSTER
    strength_min = 1
    if 'weapon' in monster.keys():
        strength_min = monster['weapon']['effect']
    if monster['stats']['strength'] < strength_min:
        monster['stats']['strength'] = strength_min
    else:
        monster['stats']['strength'] = round(monster['stats']['strength'], 1)

    # make sure armor stats are where they should be FOR MONSTER
    armor_min = 1
    if 'armor' in monster.keys():
        armor_min = monster['armor']['effect']
    if monster['stats']['defense'] < armor_min:
        monster['stats']['defense'] = armor_min
    else:
        monster['stats']['strength'] = round(monster['stats']['strength'], 1)

    return turn, match, monster


class DungeonEvent(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.waiting_users = []
        self.towers = 0
        self.active_channels = []
        self.battling_users = []

    async def generate_search_description(self, user_classes, quote):
        classes_text = ""
        player_count = 0
        # Loop through classes to add to embed
        for user_class in user_classes.keys():
            if user_classes[user_class] is None:
                classes_text += Utils.get_class(user_class)['emote'] + " `None`" + "\n"
            else:
                user = await self.bot.fetch_user(user_classes[user_class])
                player_count += 1
                classes_text += Utils.get_class(user_class)['emote'] + " " + user.name + "\n"

        # Generate embed to display
        return f"The quest will begin in 1 minute. React to join.\n⚔️ **Players ({str(player_count)}/3):**" \
               f"\n{classes_text}\n{quote}"

    async def reward_selection(self, ctx, account, user):
        numbers = ["1️⃣", "2️⃣", "3️⃣"]
        full_rewards = ""
        rewards = await generate_rewards(account)

        i = 0
        for reward in rewards.values():
            string_addition = numbers[i] + " " + await display_reward(reward, account) + "\n"
            full_rewards += string_addition
            i += 1

        embed = discord.Embed(title="Please Select a Reward", color=Config.EVENTCOLOR,
                              description=full_rewards)
        embed.set_footer(text='React to select a reward or wait 30s to cancel ')
        embed.set_author(name=user.name, icon_url=user.avatar_url)

        message = await ctx.send(content=user.mention, embed=embed, delete_after=90)

        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")

        def check(check_reaction, check_user):
            return check_user.id == user.id and check_reaction.message.id == message.id and \
                   str(check_reaction) in numbers

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            await ctx.send(user.mention + " no reward selected in time", delete_after=20)
            return None

        try:
            await message.clear_reactions()
        except discord.Forbidden:
            pass

        if str(reaction) == "1️⃣":
            embed = discord.Embed(title="Reward Selected", color=Config.EVENTCOLOR,
                                  description=await display_reward(rewards['1'], account))
            embed.set_author(name=user.name, icon_url=user.avatar_url)

            await message.edit(embed=embed, delete_after=30)
            return rewards['1']

        elif str(reaction) == "2️⃣":
            embed = discord.Embed(title="Reward Selected", color=Config.EVENTCOLOR,
                                  description=await display_reward(rewards['2'], account))
            embed.set_author(name=user.name, icon_url=user.avatar_url)

            await message.edit(embed=embed, delete_after=30)
            return rewards['2']

        elif str(reaction) == "3️⃣":
            embed = discord.Embed(title="Reward Selected", color=Config.EVENTCOLOR,
                                  description=await display_reward(rewards['3'], account))
            embed.set_author(name=user.name, icon_url=user.avatar_url)

            await message.edit(embed=embed, delete_after=30)
            return rewards['3']

        await ctx.send(user.mention + " no reward selected in time")
        return {'type': None}

    @commands.group(aliases=['ev'])
    @commands.bot_has_permissions(send_messages=True, external_emojis=True)
    async def event(self, ctx):
        # Check the event is active
        if not Config.EVENT_ACTIVE and str(ctx.invoked_subcommand) != "event stats":
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Events",
                                  description=f"Current Event: `None`")
            await ctx.send(embed=embed)
            return

        if ctx.invoked_subcommand is None:
            nothing, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
            if account is None:
                return

            try:
                high_floor = account['event']['tower']['high']
                attempts = str(account['event']['tower']['attempts'])
                tickets = str(account['event']['tower']['tickets'])
            except KeyError:
                high_floor = '`None`'
                attempts = "0"
                tickets = "3"

            embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Events",
                                  description=f"Current Event: **Tower of Beginnings**\nHighest Floor: {high_floor}\n"
                                              f"Attempts: {attempts}\nTickets remaining: {tickets} :ticket:")
            embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/3sZN5xE-M3sA0KzszBbqnVCqKgr56sn4Lcy-m"
                                    "Chm6Wg/https/cdn.discordapp.com/emojis/758745644893732914.png")

            embed.add_field(name="Commands", inline=False,
                            value="`start` - Begins party searching for a Tower Quest"
                                  "\n`top` - Displays the top 10 players with the highest floor count"
                                  "\n`stats <mention>` - Checks the event stats for a user")
            embed.add_field(name="How it works", inline=False,
                            value="When searching, you must be one of the three starter classes: "
                                  "\n:open_hands: `Arcane`\n:shamrock: `Druid`\n:cherry_blossom: `Warden`"
                                  "\nOnly one of each type is allowed per quest."
                                  "\nYou begin with just the starter spells and wooden items, no abilities."
                                  "\nEach time you clear a floor, you can pick one of three rewards. "
                                  "Either an item level/material upgrade, new spell or ability."
                                  "\nRemember, you can only carry up to 4 spells, so if you overwrite one, it's gone. "
                                  "Abilities last for one floor, but you can still gain and use them after use. "
                                  "Item upgrades persist, even if the material changes."
                                  "\nAs a fun bonus, stuns work on bosses, and can be used on you too!")
            embed.add_field(name="Event Rewards", inline=False,
                            value="Floor - Reward\n"
                                  f"1 - 350 {Config.EMOJI['coin']}, 30 {Config.EMOJI['key']},"
                                  f" 300 {Config.EMOJI['ruby']}\n"
                                  f"2 - 2 {Config.EMOJI['crown']}\n"
                                  "3 - '🥚' title\n"
                                  f"4 - 4 {Config.EMOJI['crown']}\n"
                                  "5 - Egg Profile Icon\n"
                                  f"6 - 6 {Config.EMOJI['crown']}\n"
                                  "7 - Spring Green Embed Color (0x00ff7f)\n"
                                  f"8 - 8 {Config.EMOJI['crown']}\n"
                                  "10 - 'the Golden Egg' title")

            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    @event.command(aliases=['start', 'begin', 'join'])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def tower(self, ctx):
        # Check the event is active
        if not Config.EVENT_ACTIVE:
            return

        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        # Bot in maintenance.
        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.ERRORCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under Maintenance.")

            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        # Error when starting search
        if ctx.author.id in self.battling_users or ctx.author.id in self.waiting_users or \
                ctx.channel.id in self.active_channels:

            # Already battling
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Error Entering The Tower",
                                  description="You are already in The Tower. Please finish that quest first.")

            # Already searching
            if ctx.author.id in self.waiting_users:
                embed.description = "You are already entering The Tower. Please finish that battle first."

            # Channel already doing dungeon
            if ctx.channel.id in self.active_channels:
                embed.description = "This channel is already exploring The Tower. " \
                                    "Please finish that quest first."

            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        # Get tickets left
        try:
            tickets = account['event']['tower']['tickets']
        except KeyError:
            tickets = 3
        # Check user has enough to enter
        if tickets <= 0:
            embed = discord.Embed(color=Config.EVENTCOLOR, title="No Tickets left",
                                  description="You don't have any tickets left to enter the tower. You can gain more "
                                              "by voting for the bot or the Enchanted server with `]vote`.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        # Check user is in the three starter classes
        user_classes = {'Arcane': None,
                        'Druid': None,
                        'Warden': None}
        # User isn't a valid class
        if account['class'] not in user_classes.keys():
            embed = discord.Embed(color=Config.EVENTCOLOR, title="Invalid Class",
                                  description="You aren't using one of the three starter classes! "
                                              "Please select one first. Valid classes:"
                                              "\n:open_hands: `Arcane`"
                                              "\n:shamrock: `Druid`"
                                              "\n:cherry_blossom: `Warden`")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        user_names = []
        user_ids = []

        # Open UI for getting other party members
        user_classes[account['class']] = ctx.author.id
        user_names.append(ctx.author.name)
        user_ids.append(ctx.author.id)
        quote = "*\"" + Utils.quotes() + "\"*"
        self.waiting_users.append(ctx.author.id)
        self.active_channels.append(ctx.channel.id)

        # Generate embed to display
        embed = discord.Embed(color=Config.EVENTCOLOR,
                              title=ctx.author.name + " is starting The Tower!",
                              description=await self.generate_search_description(user_classes, quote),
                              timestamp=datetime.datetime.utcnow() + datetime.timedelta(minutes=1))
        embed.set_footer(text='React with the ✔️ to join | starting at ')
        embed.set_thumbnail(
            url="https://images-ext-1.discordapp.net/external/3sZN5xE-M3sA0KzszBbqnVCqKgr56sn4Lcy-m"
                "Chm6Wg/https/cdn.discordapp.com/emojis/758745644893732914.png")
        # Send embed
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)

        await msg.add_reaction("✔️")
        await msg.add_reaction("❌")
        await msg.add_reaction("⏩")
        countdown = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)

        def check(check_reaction, check_user):
            return check_user.id != self.bot.user.id and check_reaction.message.id == msg.id

        # While still searching for party members
        while datetime.datetime.utcnow() < countdown:
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=10, check=check)

                # User skips wait
                if str(reaction) == "⏩" and user.id == ctx.author.id:
                    break

                # User stops searching
                elif str(reaction) == "❌" and user.id == ctx.author.id:
                    await msg.clear_reactions()
                    await msg.edit(embed=discord.Embed(title="The Tower Quest canceled", color=Config.EVENTCOLOR,
                                                       description=ctx.author.name + " has disbanded the quest..."))

                    # Clean up self.check_lists
                    if ctx.channel.id in self.active_channels:
                        self.active_channels.remove(ctx.channel.id)
                    for u in user_ids:
                        if u in self.waiting_users:
                            self.waiting_users.remove(u)
                    return

                # Check added user is new
                elif Utils.get_account(user.id) is None:
                    await reaction.remove(user)
                    error_msg = await ctx.send(
                        embed=discord.Embed(title="You don't have an account", color=Config.EVENTCOLOR,
                                            description="Type `]profile` to choose a class and react again to join "
                                                        "the party!"))
                    await error_msg.delete(delay=20)
                    continue

                # Check the new user isn't in a different event dungeon
                elif user.id in self.waiting_users and user.id != ctx.author.id:
                    if user.id not in user_ids:
                        error_msg = await ctx.send(content=user.mention,
                                                   embed=discord.Embed(title="Already entering",
                                                                       color=Config.EVENTCOLOR,
                                                                       description="You are already entering an "
                                                                                   "The Tower!"))
                        await error_msg.delete(delay=20)
                        await reaction.remove(user)
                        continue

                # Check the user isn't already battling an event dungeon
                elif user.id in self.battling_users and user.id != ctx.author.id:
                    error_msg = await ctx.send(content=user.mention,
                                               embed=discord.Embed(title="Already exploring", color=Config.EVENTCOLOR,
                                                                   description="You are already exploring an "
                                                                               "The Tower!"))
                    await error_msg.delete(delay=20)
                    await reaction.remove(user)
                    continue

                # Check it's a valid reaction
                elif reaction.message.id != msg.id or not reaction.me:
                    continue

                await reaction.remove(user)
                # Ignore if the non-author does anything other than use the check
                if str(reaction) != "✔️":
                    continue

                # If the user is in the party, remove them
                if user.id in user_ids:
                    user_ids.remove(user.id)
                    user_names.remove(user.name)
                    self.waiting_users.remove(user.id)
                    # Remove them from the class
                    for user_class in user_classes.keys():
                        if user_classes[user_class] == user.id:
                            user_classes[user_class] = None

                else:
                    # Check we haven't hit the player cap
                    if len(user_ids) > 3:
                        await ctx.send(content=user.mention,
                                       embed=discord.Embed(title="Already full", color=Config.EVENTCOLOR,
                                                           description="The party is full. Up to 3 people "
                                                                       "per quest for this event."))
                        continue

                    # Get tickets left
                    user_account = Utils.get_account(user.id)
                    try:
                        tickets = user_account['event']['tower']['tickets']
                    except KeyError:
                        tickets = 3
                    # Check user has enough to enter
                    if tickets <= 0:
                        await ctx.send(content=user.mention,
                                       embed=discord.Embed(color=Config.EVENTCOLOR, title="No Tickets left",
                                                           description="You don't have any tickets left to enter the "
                                                                       "tower. You can gain more by voting for the bot "
                                                                       "or the Enchanted server with `]vote`."))
                        continue

                    # Check user has a valid class
                    user_class = user_account['class']
                    if user_class not in user_classes.keys():
                        await ctx.send(content=user.mention,
                                       embed=discord.Embed(color=Config.EVENTCOLOR, title="Invalid Class",
                                                           description="You aren't using one of the three starter "
                                                                       "classes! Please select one first. Valid "
                                                                       "classes: "
                                                                       "\n:open_hands: `Arcane`"
                                                                       "\n:shamrock: `Druid`"
                                                                       "\n:cherry_blossom: `Warden`"))
                        continue
                    # Don't overwrite existing player
                    if user_classes[user_class] is not None:
                        await ctx.send(content=user.mention,
                                       embed=discord.Embed(color=Config.EVENTCOLOR, title="Invalid Class",
                                                           description=f"{user_class} has already been added! "
                                                                       "Choose another class."))
                        continue

                    # Add the user to the stats
                    user_ids.append(user.id)
                    user_names.append(user.name)
                    self.waiting_users.append(user.id)
                    user_classes[user_class] = user.id

                embed.description = await self.generate_search_description(user_classes, quote)

                if msg is None:
                    msg = await ctx.send(embed=embed)
                else:
                    await msg.edit(embed=embed)

            # Joining time has ended
            except asyncio.TimeoutError:
                continue

        # Check we don't have 0 players
        if len(user_ids) == 0:
            await msg.clear_reactions()
            await msg.edit(embed=discord.Embed(title="The Tower quest cancelled", color=Config.EVENTCOLOR,
                                               description="No one was brave enough to join"))
            # Remove active channel
            if ctx.channel.id in self.active_channels:
                self.active_channels.remove(ctx.channel.id)
            # If there's anybody left, remove them
            for u in user_ids:
                if u in self.waiting_users:
                    self.waiting_users.remove(u)
            return

        # Start creating the match
        match = []
        # Add user info to match
        for user in user_ids:
            user = await self.bot.fetch_user(user)
            if user.id != self.bot.user.id:
                account = Utils.get_account(user.id)

                # Gets the class the user signed up with
                for ev_class in user_classes.keys():
                    if user_classes[ev_class] == user.id:
                        user_class = ev_class

                # Event data
                event_data = {'weapon': None, 'armor': None, 'slots': [0, 1, None, None, None],
                              'stats': Utils.get_class(user_class)['stats'], 'class': user_class}

                # Equip wooden weapon
                item = Utils.get_item(random.choice(['Wooden Sword', 'Wooden Scythe', 'Wooden Axe']))
                event_data['weapon'] = {'name': item['name'], 'level': 1, 'emoji': item['emoji']}
                weapon = item
                # Equip wooden armor
                item = Utils.get_item(random.choice(['Wooden Tunic', 'Wooden Helmet', 'Wooden Shield']))
                event_data['armor'] = {'name': item['name'], 'level': 1, 'emoji': item['emoji']}
                armor = item

                # Add user data to match
                match.append({'ability': None, 'weapon': weapon, 'armor': armor, 'user': user, 'stunned': False,
                              'account': event_data, 'selected_title': account['selected_title']})

                # Increments their timer count
                user_account = Utils.get_account(user.id)
                try:
                    event_data = user_account['event']
                    event_data['tower']['attempts'] += 1
                    event_data['tower']['tickets'] -= 1
                except KeyError:
                    event_data = {'tower': {'attempts': 1, 'high': 0, 'tickets': 2}}
                Config.USERS.update_one({'user_id': user.id}, {'$set': {'event': event_data}})

        # Setup base
        self.towers += 1
        floors = 1
        match_copy = match.copy()

        # Transfer users to battling from waiting lists
        for i in range(len(match)):
            self.battling_users.append(match[i]['user'].id)
            self.waiting_users.remove(match[i]['user'].id)

        # Main Tower loop
        do_continue = True
        while do_continue:
            monster_class = random.choice(list(Config.CLASSES.find({})))
            # Randomly selects 6 spells
            spells = list(Config.SPELLS.find({'class': monster_class['name']}))
            random.shuffle(spells)
            spells = spells[:6]

            # Base Monster Stats
            strength = 2 + round((len(match_copy) * 0.5 + 1) * floors, 1)
            defense = 1 + round((len(match_copy) * 0.5 + 0.5) * floors, 1)

            # REAL
            monster = {'name': await
            get_monster_name(floors), 'titan': False, 'spells': spells, 'turn': False,
                       'stats': {'health': 40 + round(math.sqrt(len(match_copy)) * 10, 1) + floors * 5,
                                 'strength': strength, 'defense': defense,
                                 'endurance': random.randint(90, 120) + len(match_copy) * 10 + floors * 5},
                       'stunned': False}

            # CHEAT
            # monster = {'name': Utils.make_monster_name(), 'titan': False, 'spells': spells, 'turn': False,
            #            'stats': {'health': 1 + math.sqrt(len(match_copy)) * 10, 'strength': strength,
            #                      'defense': defense, 'endurance': random.randint(90, 150) + len(match_copy) * 10},
            #            'stunned': False}

            # Calculate bonus user stats based on items
            for i in range(len(match)):
                if match[i]['armor'] is not None:
                    if match[i]["account"]["armor"] is not None:
                        match[i]['account']['stats']['defense'] += Utils.calc_item_effect(match[i]["account"]["armor"],
                                                                                          match[i]['armor'])
                if match[i]['weapon'] is not None:
                    if match[i]["account"]["weapon"] is not None:
                        match[i]['account']['stats']['strength'] += Utils.calc_item_effect(
                            match[i]["account"]["weapon"], match[i]['weapon'])

            # Attempt to begin the floor
            try:
                match, floors, do_continue, msg = await self.event_thread(match, msg, monster, floors)
            except Exception as e:
                for user in match_copy:
                    if user['user'].id in self.battling_users:
                        self.battling_users.remove(user['user'].id)
                if msg.channel.id in self.active_channels:
                    self.active_channels.remove(msg.channel.id)
                self.towers -= 1
                raise e

            # Grant Floor Rewards
            for user in match:
                reward = await self.reward_selection(ctx, user['account'], user['user'])

                if reward is not None:
                    if reward['type'] == "ability":
                        user['account']['slots'][4] = reward['id']

                    elif reward['type'] == "spell":
                        # Get the user to pick the slot to place the spell
                        # Generate embed
                        embed = discord.Embed(title="Please Pick a Spell to Replace", color=Config.EVENTCOLOR,
                                              description="")
                        embed.set_footer(text='React to select a slot, or wait 40s to cancel.')
                        embed.set_author(name=user['user'].name, icon_url=user['user'].avatar_url)

                        # Generate spellbook
                        equipped_string = ""
                        for spell in user['account']['slots'][:4]:
                            if spell is None:
                                equipped_string += "\n> " + Config.EMOJI["spell"] + \
                                                   " *Nothing is written on this page...*"
                                continue
                            spell = Utils.get_spell(user['account']['class'], spell)
                            if spell is not None:
                                equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + \
                                                   spell['name'] + "** - [ " + str(spell['damage']) + " effect] [ " + \
                                                   str(spell['cost']) + " cost] [ " + str(spell['scaling']) + \
                                                   " scaling]"
                        embed.description = "\n\n**" + user['user'].name + "'s Spellbook**:" + equipped_string

                        message = await ctx.send(content=user['user'].mention, embed=embed)

                        # Get result
                        await message.add_reaction("1️⃣")
                        await message.add_reaction("2️⃣")
                        await message.add_reaction("3️⃣")
                        await message.add_reaction("4️⃣")

                        numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

                        def check(check_reaction, check_user):
                            return check_user.id == user['user'].id and check_reaction.message.id == message.id and \
                                   str(check_reaction) in numbers

                        try:
                            reaction, reactor = await self.bot.wait_for('reaction_add', timeout=40, check=check)
                        except asyncio.TimeoutError:
                            await ctx.send(user['user'].mention + " no slot selected in time")
                            return None

                        try:
                            await message.clear_reactions()
                        except discord.Forbidden:
                            pass

                        if str(reaction) == "1️⃣":
                            # Equip Spell
                            user['account']['slots'][0] = reward['id']

                            # Set embed title
                            embed.title = "Spell placed in slot 1"

                        elif str(reaction) == "2️⃣":
                            # Equip Spell
                            user['account']['slots'][1] = reward['id']

                            # Set embed title
                            embed.title = "Spell placed in slot 2"

                        elif str(reaction) == "3️⃣":
                            # Equip Spell
                            user['account']['slots'][2] = reward['id']

                            # Set embed title
                            embed.title = "Spell placed in slot 3"

                        elif str(reaction) == "4️⃣":
                            # Equip Spell
                            user['account']['slots'][3] = reward['id']

                            # Set Embed title
                            embed.title = "Spell placed in slot 4"

                        else:
                            # Set embed title
                            embed.title = "Spell not equipped"

                        # Get spellbook
                        equipped_string = ""
                        for spell in user['account']['slots'][:4]:
                            if spell is None:
                                equipped_string += "\n> " + Config.EMOJI["spell"] + \
                                                   " *Nothing is written on this page...*"
                                continue
                            spell = Utils.get_spell(user['account']['class'], spell)
                            if spell is not None:
                                equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + \
                                                   spell['name'] + "** - [ " + str(spell['damage']) + " effect] [ " + \
                                                   str(spell['cost']) + " cost] [ " + str(spell['scaling']) + \
                                                   " scaling]"
                        embed.description = "\n\n**" + user['user'].name + "'s Spellbook**:" + equipped_string

                        # Edit embed
                        await message.edit(embed=embed, delete_after=15)

                    # Items Reward
                    else:
                        # Weapon Reward
                        if reward['type'].startswith("weapon"):
                            try:
                                item_level = user['account']['weapon']['level']
                            except TypeError:
                                item_level = 1

                            if reward['type'] == "weapon-mat":
                                item = Utils.get_item(reward['name'])
                                user['account']['weapon'] = {'name': reward['name'], 'level': item_level,
                                                             'emoji': item['emoji']}
                                user['weapon'] = item
                            elif reward['type'] == "weapon-level":
                                user['account']['weapon']['level'] += reward['amount']

                        # Armor Reward
                        elif reward['type'].startswith("armor"):
                            try:
                                item_level = user['account']['armor']['level']
                            except TypeError:
                                item_level = 1

                            if reward['type'] == "armor-mat":
                                item = Utils.get_item(reward['name'])
                                user['account']['armor'] = {'name': reward['name'], 'level': item_level,
                                                            'emoji': item['emoji']}
                                user['armor'] = item
                            elif reward['type'] == "armor-level":
                                user['account']['armor']['level'] += reward['amount']

        for user in match_copy:
            if user['user'].id in self.battling_users:
                self.battling_users.remove(user['user'].id)
        if msg.channel.id in self.active_channels:
            self.active_channels.remove(msg.channel.id)
        self.towers -= 1

    async def event_thread(self, match, message, monster, floor):
        match_cache = match.copy()

        # Everyone has died
        if len(match) < 1:
            emoji = Utils.get_class(monster['spells'][0]["class"])["emote"]
            embed = discord.Embed(color=Config.EVENTCOLOR,
                                  description=emoji + " | **" + monster['name'] + " Has bested the group...**\n\n" +
                                              "You made it past " + str(floor - 1) +
                                              " floors! This has been recorded in "
                                              "your account")

            await message.edit(embed=embed)
            # Clean up lists and exit
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)
            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.towers -= 1

            return match, floor - 1, False, message

        # Clean up waiting and prepare for floor
        Config.LOGGING.info("Tower thread started: Current threads: " + str(self.towers))
        await message.clear_reactions()
        monster['health'] = monster['stats']['health']
        monster['mana'] = monster['stats']['endurance']
        await message.delete()

        # Start next floor
        embed = discord.Embed(title="You enter floor " + str(floor) + "...", color=Config.EVENTCOLOR,
                              description="[jump](" + message.jump_url + ")")
        message = await message.channel.send(", ".join(x['user'].mention for x in match), embed=embed)

        monster['effects'] = []
        # Setup users
        for user in match:
            user['health'] = user['account']['stats']['health']
            user['mana'] = user['account']['stats']['endurance']
            user['effects'] = []
            user['afk'] = 0

        # Add reactions and begin turn
        turn = random.randint(0, len(match) - 1)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("🔆")
        await message.add_reaction("💤")
        await message.add_reaction("🏳️")

        # Amplify bonus turn
        a_turn = False

        while len(match) > 0 and monster['health'] > 0 and monster['mana'] > 0:
            restart = False
            # Remove any users that have died or gone afk
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                    match.remove(user)
                    turn -= 1
                    restart = True
            if turn < 0:
                turn = 0
            # Restart the loop
            if restart:
                continue

            # Calculate effects for beginning of round
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

            # Restart if needed after effects applied
            for user in match:
                if user['health'] <= 0 or user['mana'] <= 0:
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

            # Player's turn
            # So add resources
            if not monster['turn']:
                # Base Regen
                resource = 'mana'
                resource_number = 3

                try:
                    # Ability Regen
                    if match[turn]['ability'] is not None:
                        if match[turn]['ability'] == "Healing Blood":
                            resource = 'health'
                            resource_number = 5
                        elif match[turn]['ability'] == "Inner Light":
                            resource_number = 6
                except IndexError:
                    pass

                # If it's amplify bonus turn
                if a_turn is True:
                    resource_number = 0
                    a_turn = False
                # Check if the user is stunned
                elif match[turn]['stunned']:
                    resource_number = 0

                match[turn][resource] += resource_number
            # Monster turn
            # Add 4 mana if stagnation hasn't been used
            else:
                abilities = []
                for user in match:
                    abilities.append(user["ability"])
                if "Stagnation" not in abilities and not monster['stunned']:
                    monster['mana'] += 4

            # make sure health and mana are not above max value
            for _ in match:
                if _['health'] > _['account']['stats']['health']:
                    _['health'] = _['account']['stats']['health']
                if _['mana'] > _['account']['stats']['endurance']:
                    _['mana'] = _['account']['stats']['endurance']

            # make sure monster values are in check as well
            if monster['health'] > monster['stats']['health']:
                monster['health'] = monster['stats']['health']
            if monster['mana'] > monster['stats']['endurance']:
                monster['mana'] = monster['stats']['endurance']

            # If the monster has died
            if monster['health'] <= 0 or monster['mana'] <= 0:
                break

            await construct_embeds(match, turn, floor, message, monster)

            if monster['stunned']:
                monster['stunned'] = False
                await asyncio.sleep(3)
                turn = change_turn(turn, len(match_cache), monster)
                continue

            # Check if monster's turn
            if monster['turn']:

                # Simulate monster thinking lol
                await asyncio.sleep(3)

                # Check we have enough mana
                if monster['mana'] < 25:
                    turn = change_turn(turn, len(match), monster)
                    continue
                # We're gonna use a spell
                else:
                    spell = random.choice(monster['spells'])
                    victim = random.randint(0, len(match) - 1)

                    # Remove cost
                    if spell['type'] not in ["MANA", "DRAIN"]:
                        monster['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        monster['health'] -= spell['cost']

                    # Spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round((spell['damage'] + monster['stats']['strength']) * spell['scaling'] -
                                                  match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            match[victim]['health'] -= calculated_damage
                            match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]['user'].name + " takes `" +
                                                            str(calculated_damage) + "` damage total (`" +
                                                            str(match[victim]['account']['stats']['defense']) +
                                                            "` blocked)")

                    elif spell['type'] == "HEAL":
                        monster['health'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] + " gains `" +
                                                            str(spell['damage']) + "` health.")

                    elif spell['type'] == "STUN":
                        calculated_damage = round((spell['damage'] + monster['stats']['strength']) * spell['scaling']
                                                  - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            match[victim]['health'] -= calculated_damage
                            match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        chance = random.choices(["stun", "no stun"], (33, 66))

                        if chance == ["stun"]:
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                monster['name'] + " casts **" + spell['name'] +
                                                                "**. " + match[victim]["user"].name + " takes `" +
                                                                str(calculated_damage) + "` damage total (`" +
                                                                str(monster['stats']['defense']) +
                                                                "` blocked) and is stunned.")
                            match[victim]['stunned'] = True

                        elif chance == ["no stun"]:
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                monster['name'] + " casts **" + spell['name'] +
                                                                "**. " + match[victim]["user"].name + " takes `" +
                                                                str(calculated_damage) + "` damage total (`" +
                                                                str(monster['stats']['defense']) +
                                                                "` blocked) the stun failed...")

                    elif spell['type'] == "MANA":
                        monster['mana'] += spell['damage']
                        monster['health'] -= spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] + " transforms `" +
                                                            str(spell['damage']) + "` health into mana.")

                    elif spell['type'] == "DRAIN":
                        monster['mana'] += spell['damage']
                        match[victim]['mana'] -= spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] + " stole `" +
                                                            str(spell['damage']) + "` mana from " +
                                                            match[victim]['user'].name + " using `" +
                                                            str(spell['cost']) + "` health.")

                    elif spell['type'] == "PEN":
                        monster['stats']['strength'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] +
                                                            " boosted their Strength from `" +
                                                            str(monster['stats']['strength'] - spell['damage']) +
                                                            "` to `" + str(monster['stats']['strength']) + "`")

                    elif spell['type'] == "ARMOR":
                        monster['stats']['defense'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] +
                                                            " boosted their Defense from `" +
                                                            str(monster['stats']['defense'] - spell['damage']) +
                                                            "` to `" + str(monster['stats']['defense']) + "`")

                    elif spell['type'] == "POISON":
                        amount = round((spell['damage'] + monster['stats']['strength']) * spell['scaling'] /
                                       match[victim]['account']['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]['user'].name +
                                                            " gets effect `" + str(effect['name']) + "` of `" +
                                                            str(effect['amount']) + "` magnitude for `" +
                                                            str(effect['turns']) + "` turns.")

                    elif spell['type'] == "BLIND":
                        amount = round((spell['damage'] + monster['stats']['strength']) * spell['scaling'] /
                                       match[victim]['account']['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
                        match[victim]['effects'].append(effect)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]['user'].name +
                                                            " gets effect `" + str(effect['name']) +
                                                            "` of `" + str(effect['amount']) +
                                                            "` magnitude for `" + str(effect['turns']) +
                                                            "` turns.")

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round((spell['damage'] + monster['stats']['strength']) * spell['scaling'] -
                                                  match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            match[victim]['health'] -= calculated_damage
                            monster['health'] += round(0.7 * calculated_damage, 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + monster['name'] + " stole `" +
                                                            str(calculated_damage) + "` health from " +
                                                            match[victim]['user'].name)

                    elif spell['type'] == "IMPAIR":
                        before_stat = match[victim]['account']['stats']['defense']
                        match[victim]['account']['stats']['defense'] -= spell['damage']
                        if match[victim]['account']['stats']['defense'] < 1:
                            match[victim]['account']['stats']['defense'] = 1
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]['user'].name +
                                                            "'s defense falls from `" + str(before_stat) +
                                                            "` to `" +
                                                            str(match[victim]['account']['stats']['defense']) +
                                                            "`.")

                    elif spell['type'] == "WEAKEN":
                        before_stat = match[victim]['account']['stats']['strength']
                        match[victim]['account']['stats']['strength'] -= spell['damage']
                        if match[victim]['account']['stats']['strength'] < 1:
                            match[victim]['account']['stats']['strength'] = 1
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster['name'] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]['user'].name +
                                                            "'s strength falls from `" + str(before_stat) +
                                                            "` to `" +
                                                            str(match[victim]['account']['stats']['strength']) +
                                                            "`.")

                    elif spell['type'] == "TRUE":
                        calculated_damage = round((spell['damage'] + monster['stats']['strength']) * spell['scaling'],
                                                  1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            match[victim]['health'] -= calculated_damage
                            match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            monster["name"] + " casts **" + spell['name'] +
                                                            "**. " + match[victim]["user"].name +
                                                            " takes `" + str(calculated_damage) +
                                                            "` true damage.")

                    if match[victim]['ability'] is not None:
                        if match[victim]["ability"] == "Glass Armor":
                            ability = Utils.get_ability(match[victim]['account']['slots'][4])
                            match[victim]["ability"] = "Glass Armor Done"
                            match[victim]['account']['stats']['defense'] -= ability['effect']
                            turn, match, monster = clean_up_match(turn, match, monster)
                    await asyncio.sleep(3)

                    turn = change_turn(turn, len(match), monster)
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue

            # User's turn
            try:
                # Check if the user is stunned
                if match[turn]['stunned']:
                    match[turn]['stunned'] = False
                    await asyncio.sleep(3)
                    turn = change_turn(turn, len(match_cache), monster)
                    continue

                reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '🔆': 4}

                # Check it was user's turn, and they reacted to the correct message with a valid reaction
                def check(check_payload):
                    if check_payload.user_id == match[turn]['user'].id and check_payload.message_id == message.id:
                        if str(check_payload.emoji) in reaction_dict.keys():
                            return match[turn]['account']['slots'][reaction_dict[str(check_payload.emoji)]] is not None
                        else:
                            return True
                    else:
                        return False

                # Remove user's reaction
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

                # No reaction
                if reaction is None:
                    payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                    reaction = payload.emoji

                    try:
                        await message.remove_reaction(payload.emoji, match[turn]['user'])
                    except:
                        await Config.LOGGING.error("Cannot remove emoji (not big deal)")

                # User skips turn
                if str(reaction) == "💤":
                    turn = change_turn(turn, len(match), monster)
                    continue

                # User ends Tower attempt
                elif str(reaction) == "🏳️":
                    match[turn]['health'] = 0
                    match[turn]['mena'] = 0
                    turn = change_turn(turn, len(match), monster)
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue

                # Abilities
                elif str(reaction) == "🔆" and match[turn]["ability"] is not None:
                    a_turn = True
                # User hasn't use ability yet
                elif str(reaction) == "🔆" and match[turn]["ability"] is None:
                    ability = Utils.get_ability(match[turn]['account']['slots'][4])
                    match[turn]['ability'] = ability["name"]

                    # Ability options
                    if ability['name'] == "Switch":
                        health = match[turn]['health']
                        match[turn]['health'] = round(match[turn]['mana'] * ability["effect"], 1)
                        match[turn]['mana'] = round(health * ability["effect"], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. Their health and mana have been switched")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Wish":
                        if random.randint(1, 5) == 1:
                            match[turn]['health'] -= ability["effect"]
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                match[turn]['user'].name + " casts **" +
                                                                ability['name'] +
                                                                "**. Owhh no, bad luck. They take `" +
                                                                str(ability['effect']) + "` damage")
                        else:
                            monster['health'] -= ability["effect"]
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                match[turn]['user'].name + " casts **" +
                                                                str(ability['name']) +
                                                                "**. The odds are in their favor." +
                                                                "Their opponent takes `" +
                                                                str(ability['effect']) + "` damage")

                        turn, match, monster = clean_up_match(turn, match, monster)
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Crushing Blow":
                        for user in match:
                            user['account']['stats']['defense'] = ability["effect"]
                        monster['stats']['defense'] = ability["effect"]
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. Everyone armor has been changed to `" +
                                                            str(ability['effect']) + "`")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Healing Blood":
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. Switched mana regeneration to " +
                                                            str(ability['effect']) + " health per turn")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Stagnation":
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. Removes their opponent's regeneration")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Inner Light":
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. Changed mana regeneration to " +
                                                            str(ability['effect']) + " mana per turn")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Cleanse":
                        match[turn]['effects'] = []
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. All the effects you had have been removed")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Alleviate":
                        for user in match:
                            user['health'] += ability["effect"]
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] + "**. Your allies get `" +
                                                            str(ability['effect']) + "` health")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Blast":
                        match[turn]['health'] -= ability["effect"]
                        monster['health'] -= ability["effect"]
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] +
                                                            "**. You and your opponent take `" +
                                                            str(ability['effect']) + "` damage")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Time Loop":
                        for user in match:
                            user['health'] += ability["effect"]
                            user['mana'] += ability["effect"]
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] + "**. Everyone gets `" +
                                                            str(ability['effect']) + "` health and mana")
                        turn = change_turn(turn, len(match), monster)

                    elif ability['name'] == "Amplify":
                        match[turn]['account']['stats']['strength'] += ability['effect']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] + "**. Added `" +
                                                            str(ability['effect']) +
                                                            "` strength to boost their next spell")

                    elif ability['name'] == "Glass Armor":
                        match[turn]['account']['stats']['defense'] += ability['effect']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            ability['name'] + "**. Added `" +
                                                            str(ability['effect']) +
                                                            "` defense to protect them from their enemies next "
                                                            "spell")
                        turn = change_turn(turn, len(match), monster)

                    await asyncio.sleep(3)
                    continue

                # The user cast a spell
                elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                    spell = Utils.get_spell(match[turn]['account']['class'],
                                            match[turn]['account']['slots'][reaction_dict[str(reaction)]])

                    # Remove cost
                    if spell['type'] not in ["MANA", "DRAIN"]:
                        match[turn]['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        match[turn]['health'] -= spell['cost']

                    # Spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                                  spell['scaling'] - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            monster['health'] -= calculated_damage
                            monster['health'] = round(monster['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] + " takes `" +
                                                            str(calculated_damage) + "` damage total (`" +
                                                            str(monster['stats']['defense']) + "` blocked)")

                    elif spell['type'] == "HEAL":
                        match[turn]['health'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " gains `" + str(spell['damage']) + "` health.")

                    elif spell['type'] == "STUN":
                        calculated_damage = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                                  spell['scaling'] - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            monster['health'] -= calculated_damage
                            monster['health'] = round(monster['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        chance = random.choices(["stun", "no"], (33, 66))

                        if chance == ["stun"]:
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                match[turn]['user'].name + " casts **" +
                                                                spell['name'] + "**. " + monster['name'] + " takes `" +
                                                                str(calculated_damage) + "` damage total (`" +
                                                                str(monster['stats']['defense']) +
                                                                "` blocked) and is stunned.")
                            monster['stunned'] = True

                        elif chance == ["no"]:
                            await construct_embeds_with_message(message, monster, turn, floor, match,
                                                                match[turn]['user'].name + " casts **" +
                                                                spell['name'] + "**. " + monster['name'] + " takes `" +
                                                                str(calculated_damage) + "` damage total (`" +
                                                                str(monster['stats']['defense']) +
                                                                "` blocked) the stun failed...")

                    elif spell['type'] == "MANA":
                        match[turn]['mana'] += spell['damage']
                        match[turn]['health'] -= spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " transforms `" + str(spell['damage']) +
                                                            "` health into mana.")

                    elif spell['type'] == "DRAIN":
                        match[turn]['mana'] += spell['damage']
                        monster['mana'] -= spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " stole `" + str(spell['damage']) + "` mana from " +
                                                            monster['name'] + " using `" + str(spell['cost']) +
                                                            "` health.")

                    elif spell['type'] == "PEN":
                        match[turn]['account']['stats']['strength'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " boosted their Strength from `" +
                                                            str(match[turn]['account']['stats']['strength'] -
                                                                spell['damage']) + "` to `" +
                                                            str(match[turn]['account']['stats']['strength']) + "`")

                    elif spell['type'] == "ARMOR":
                        match[turn]['account']['stats']['defense'] += spell['damage']
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " boosted their Defense from `" +
                                                            str(match[turn]['account']['stats']['defense'] -
                                                                spell['damage']) + "` to `" +
                                                            str(match[turn]['account']['stats']['defense']) + "`")

                    elif spell['type'] == "POISON":
                        amount = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                       spell['scaling'] / monster['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
                        monster['effects'].append(effect)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] +
                                                            " gets effect `" + str(effect['name']) + "` of `" +
                                                            str(effect['amount']) + "` magnitude for `" +
                                                            str(effect['turns']) + "` turns.")

                    elif spell['type'] == "BLIND":
                        amount = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                       spell['scaling'] / monster['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
                        monster['effects'].append(effect)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] +
                                                            " gets effect `" + str(effect['name']) + "` of `" +
                                                            str(effect['amount']) + "` magnitude for `" +
                                                            str(effect['turns']) + "` turns.")

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                                  spell['scaling'] - monster['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            match[turn]['health'] += round(0.7 * calculated_damage, 1)
                            monster['health'] -= calculated_damage
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + match[turn]['user'].name +
                                                            " stole `" + str(calculated_damage) +
                                                            "` health from " + monster['name'])

                    elif spell['type'] == "IMPAIR":
                        before_stat = monster['stats']['defense']
                        monster['stats']['defense'] -= spell['damage']
                        if monster['stats']['defense'] < 1:
                            monster['stats']['defense'] = 1
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] +
                                                            "'s defense falls from `" + str(before_stat) +
                                                            "` to `" + str(monster['stats']['defense']) + "`.")

                    elif spell['type'] == "WEAKEN":
                        before_stat = monster['stats']['strength']
                        monster['stats']['strength'] -= spell['damage']
                        if monster['stats']['strength'] < 1:
                            monster['stats']['strength'] = 1
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] +
                                                            "'s strength falls from `" + str(before_stat) +
                                                            "` to `" + str(monster['stats']['strength']) + "`.")

                    elif spell['type'] == "TRUE":
                        calculated_damage = round((spell['damage'] + match[turn]['account']['stats']['strength']) *
                                                  spell['scaling'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        else:
                            monster['health'] -= calculated_damage
                            monster['health'] = round(monster['health'], 1)
                        turn, match, monster = clean_up_match(turn, match, monster)
                        await construct_embeds_with_message(message, monster, turn, floor, match,
                                                            match[turn]['user'].name + " casts **" +
                                                            spell['name'] + "**. " + monster['name'] +
                                                            " takes `" + str(calculated_damage) + "` true damage")

                    # If we've got an ability active
                    if match[turn]['ability'] is not None:
                        # We've taken the amplify bonus turn
                        if match[turn]["ability"] == "Amplify":
                            ability = Utils.get_ability(match[turn]['account']['slots'][4])
                            match[turn]["ability"] = "Amplify Done"
                            match[turn]['account']['stats']['strength'] -= ability['effect']
                            turn, match, monster = clean_up_match(turn, match, monster)

                    turn = change_turn(turn, len(match), monster)

                    await asyncio.sleep(3)
                    # Remove dead users
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    continue

            except Exception as e:
                # If the user didn't react on time
                if isinstance(e, asyncio.TimeoutError) and not monster['turn']:
                    embed = discord.Embed(title="AFK WARNING", color=Config.EVENTCOLOR,
                                          description="Your quest is still going! You lost this turn because you took "
                                                      "over 30 seconds to choose a spell.\n\n[Click to go to fight](" +
                                                      message.jump_url + ")")
                    timeout_msg = await message.channel.send(match[turn]['user'].mention, embed=embed)
                    await timeout_msg.delete(delay=20)
                    # Increase user's afk count
                    match[turn]['afk'] += 1
                    for user in match:
                        if user['health'] <= 0 or user['mana'] <= 0 or user['afk'] > 2:
                            match.remove(user)
                            turn -= 1
                    turn = change_turn(turn, len(match), monster)
                    continue

                elif isinstance(e, discord.errors.NotFound):
                    return

                else:
                    match[turn]['mana'] -= 3
                    await message.channel.send(
                        embed=discord.Embed(title="Uh oh..",
                                            description="Something went wrong\n```\n" + str(e) + "```",
                                            color=Config.ERRORCOLOR))
        # Battle is over, clean up the embed
        try:
            await message.clear_reactions()
        except:
            await Config.LOGGING.error("Cannot remove emoji (not big deal)")

        # If the users all died
        if monster['health'] > 0 and monster['mana'] > 0:

            embed = discord.Embed(color=Config.EVENTCOLOR, description="**" + monster['name'] +
                                                                       " Has bested the group...**\n\n"
                                                                       "You made it past " + str(
                floor - 1) + " floors!")
            await message.edit(embed=embed)
            # Remove users and channel from lists
            for user in match_cache:
                if user['user'].id in self.battling_users:
                    self.battling_users.remove(user['user'].id)

                # Add score to event data
                user_account = Utils.get_account(user['user'].id)
                try:
                    event_data = user_account['event']
                    if event_data['tower']['high'] < floor - 1:
                        event_data['tower']['high'] = floor - 1
                except KeyError:
                    event_data = {'tower': {'high': floor - 1, 'tickets': 2, 'attempts': 1}}
                Config.USERS.update_one({'user_id': user['user'].id}, {'$set': {'event': event_data}})

            if message.channel.id in self.active_channels:
                self.active_channels.remove(message.channel.id)
            self.towers -= 1
            return match, floor - 1, False, message

        # The users beat the boss
        else:
            # Grant some coins
            coins_amount = random.randint(5, (len(match_cache) * 2) + 5) * 2

            mystring = "+`" + str(coins_amount) + "` " + Config.EMOJI['coin']
            # Reset stats and add counts
            for user in match_cache:
                user['account']['stats'] = Utils.get_account(user['user'].id)['stats']
                if user['account']["weapon"] is not None:
                    user['weapon'] = Utils.get_item(user['account']['weapon']["name"])
                if user['account']["armor"] is not None:
                    user['armor'] = Utils.get_item(user['account']['armor']["name"])
                Config.USERS.update_one({'user_id': user['user'].id}, {'$inc': {'coins': coins_amount}})

                user['stunned'] = False

            if monster['health'] <= 0:
                embed = discord.Embed(color=Config.EVENTCOLOR, description="**Congratulations! " + monster['name'] +
                                                                           " has been killed!**\n\nEveryone gets:\n\n" +
                                                                           mystring + "\nNext Floor: " +
                                                                           str(floor + 1) + "\n\n*Rewards in 10s*")
            elif monster['mana'] <= 0:
                embed = discord.Embed(color=Config.EVENTCOLOR, description="**Congratulations! " + monster['name'] +
                                                                           " has fainted!**\n\nEveryone gets:\n\n" +
                                                                           mystring + "\nNext Floor: " +
                                                                           str(floor + 1) + "\n\n*Rewards in 10s*")
            # Neither mana or health is 0?
            else:
                embed = discord.Embed(color=Config.EVENTCOLOR, description="**Congratulations! " + monster['name'] +
                                                                           " has been destroyed completely!"
                                                                           "**\n\nEveryone gets:\n\n" + mystring +
                                                                           "\nNext Floor: " + str(floor + 1) +
                                                                           "\n\n*Rewards in 10s*")

            # Remove any abilities that the users may have used
            for user in match:
                if user['ability'] is not None:
                    user['ability'] = None
                    user['account']['slots'][4] = None

            # Updates floor score
            for user in match_cache:
                user_account = Utils.get_account(user['user'].id)
                try:
                    event_data = user_account['event']
                    if event_data['tower']['high'] < floor - 1:
                        event_data['tower']['high'] = floor - 1
                except KeyError:
                    event_data = {'tower': {'high': floor - 1}}
                Config.USERS.update_one({'user_id': user['user'].id}, {'$set': {'event': event_data}})

            await message.edit(embed=embed)
            await asyncio.sleep(10)
            return match, floor + 1, True, message

    async def generate_lb_embed(self, page, total):
        """
        Generate the leaderboard embed to display
        """
        if total < page:
            page = total
        docs = skip_limit(10, page)
        embed = discord.Embed(title="**Tower of Beginnings** Leaderboard", description="", color=Config.EVENTCOLOR)
        embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/3sZN5xE-M3sA0KzszBbqnVCqKgr56sn4Lcy-m"
                                "Chm6Wg/https/cdn.discordapp.com/emojis/758745644893732914.png")
        index = (page - 1) * 10
        # Loop through the users and add them
        for doc in docs:
            index += 1
            # try:
            user = await self.bot.fetch_user(doc['user_id'])
            try:
                embed.description += str(index) + " | " + str(doc['event']['tower']['high']) + " floors **" + \
                                     user.name + "** \n"
            except KeyError:
                continue

        return embed, page

    @event.command(aliases=['top', 'lb'])
    async def leaderboard(self, ctx, page: int = 1):
        # Check the event is active
        if not Config.EVENT_ACTIVE:
            return
        """
        Command to show the top players in power with reactions to choose other stat type leaderboards
        """
        total = math.ceil(Config.USERS.count_documents({}) / 10)

        embed, page = await self.generate_lb_embed(page, total)
        msg = await ctx.send(embed=embed)

    @event.command(aliases=['toggle'])
    async def toggle_event(self, ctx):
        if ctx.author.id in Config.OWNERIDS:
            if Config.EVENT_ACTIVE != "tower":
                Config.EVENT_ACTIVE = "tower"
            else:
                Config.EVENT_ACTIVE = None

    @event.command()
    async def stats(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        msg, account = await Utils.get_account_lazy(self.bot, ctx, member.id)
        if account is None:
            await ctx.send(
                embed=discord.Embed(title="User has no profile", description=member.name + " does not have a profile.",
                                    color=Config.MAINCOLOR))
            return

        try:
            event_data = account['event']
        except KeyError:
            event_data = None

        embed = discord.Embed(color=Config.EVENTCOLOR, title="Enchanted Event Stats",
                              description=f"Stats for " + member.name + "#" + member.discriminator)
        embed.set_author(name=member.name, icon_url=member.avatar_url)

        if event_data is None:
            embed.description = member.name + " hasn't participated in any events yet."

        try:
            embed.add_field(name="🥚 Tower of Beginnings - Easter 2021",
                            value="Highest Floor: " + str(event_data['tower']['high']) +
                                  "\nAttempts: " + str(event_data['tower']['attempts']))
        except KeyError:
            pass
        except TypeError:
            pass
        try:
            embed.add_field(name="🥚 Tower of Beginnings - Easter 2021",
                            value="Highest Floor: " + str(event_data['easter2021']['high']) +
                                  "\nAttempts: " + str(event_data['easter2021']['attempts']))
        except KeyError:
            pass
        except TypeError:
            pass

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DungeonEvent(bot))
