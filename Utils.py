import math
from bisect import bisect, bisect_left

import Battle_Utils
import Config
import datetime
import random
import discord
import asyncio
import re


def get_class(name):
    return Config.CLASSES.find_one({'name': name})


def get_code(_id):
    return Config.CODES.find_one({'id': _id})


def get_code_by_name(name):
    return Config.CODES.find_one({'name': name})


def fetch_prefix(guild):
    return Config.SERVERS.find_one({'guild_id': guild})


def fetch_prefix(ctx):
    server = Config.SERVERS.find_one({'guild_id': ctx.guild.id})
    if server is not None:
        return server['prefix']
    else:
        return "]"


def insert_guild(ctx):
    Config.SERVERS.insert_one({'guild_id': ctx.guild.id, 'prefix': "]", 'channel_blacklist': [], "code": None})


def get_all_classes():
    return list(Config.CLASSES.find({}))


def get_new_classes():
    return list(Config.CLASSES.find({'name': {'$in': ["Arcane", "Druid", "Warden"]}}))


async def get_account_lazy(bot, ctx, id):
    account = Config.USERS.find_one({'user_id': id})
    if account is None:
        return await tutorial(bot, ctx, id, True)
    else:
        return None, account


async def tutorial(bot, ctx, id, new):
    if new:
        embed = discord.Embed(title="Please select your class to start your journey!",
                              description="Use the emojis to choose", color=Config.MAINCOLOR)
        embed.set_footer(text="Message will be deleted in 30 seconds")
        for _class in get_new_classes():
            embed.add_field(name=_class['name'] + " " + _class['emote'], value=_class['desc'])
        msg = await ctx.send(embed=embed)
        for _class in get_new_classes():
            await msg.add_reaction(_class['emote'])

        def check(check_reaction, check_user):
            return check_user.id == ctx.author.id and check_reaction.message.channel.id == ctx.channel.id and \
                   check_reaction.message.id == msg.id and check_reaction.me and check_reaction.emoji \
                   in [x['emote'] for x in get_new_classes()]

        try:
            reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30.0)
            for _class in get_new_classes():
                if _class['emote'] == str(reaction):
                    print(_class["name"])
                    account = create_account(ctx.author.id, _class['name'])
                    await msg.clear_reactions()
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await msg.delete()
            if new:
                return None, None
        title = "Your journey begins!"
        _class = get_class(account["class"])
        desc = "You selected **" + _class['name'] + "** " + _class["emote"] + "\n"
    else:
        account = Config.USERS.find_one({'user_id': id})
        title = "Knowledge is power!"
        _class = get_class(account["class"])
        desc = "You're currently a **" + _class['name'] + "** " + _class["emote"] + "\n"

    embed = discord.Embed(title=title,
                          description=desc + "__Your starting stats are:__\n" +
                                             "> Health: " + str(account['stats']['health']) +
                                             "\n> Strength: " + str(account['stats']['strength']) +
                                             "\n> Defense: " + str(account['stats']['defense']) +
                                             "\n> Endurance: " + str(account['stats']['endurance']) + "\n\n" +
                                             "**Health**, if you fall below 0 health in battle you lose.\n" +
                                             "**Strength**, will boost your spells.\n" +
                                             "**Defense**, protects you from incoming damage.\n" +
                                             "**Endurance/Mana**, the resources used in battle to cast your spells. "
                                             "If it falls below 0 you lose.\n",
                          color=Config.MAINCOLOR)
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments/736320244649295894/736899297848852530/en_shield.png")
    embed.set_footer(text='Click ✔ to continue')
    if new:
        await msg.edit(embed=embed)
    else:
        msg = await ctx.send(embed=embed)
    await asyncio.sleep(2)
    await msg.add_reaction("✅")

    def check(check_reaction, check_user):
        return check_reaction.message.id == msg.id and check_user.id == ctx.author.id

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30.0)
        if str(reaction) == "✅":
            await msg.clear_reactions()
    except asyncio.TimeoutError:
        print("Continue")
    prefix = fetch_prefix(ctx)
    user_spells = get_users_spells_class(account, _class["name"])
    spell_string = ""
    for spell in user_spells[:2]:
        spell_string += "\n" + spell['emoji'] + " **" + " [" + spell['type'] + "] " + spell['name'] + "** - [ " +\
                        str(spell['damage']) + " effect] [ " + str(spell['cost']) + " cost] [ " +\
                        str(spell['scaling']) + " scaling]"
        if spell["type"] == "DAMAGE":
            spell_string += "\nDeals damage to your opponent. Costs: (cost) mana"
        elif spell["type"] == "DRAIN":
            spell_string += "\nWill steal mana of your opponent and add it to yours. Costs: (cost) health"
        elif spell["type"] == "STUN":
            spell_string += "\nWill deal damage to your opponent, and has a 33% chance of stunning your opponent. " \
                            "Costs: (cost) mana"
        elif spell["type"] == "PEN":
            spell_string += "\nWill give you strength. Costs: (cost) mana"
    embed = discord.Embed(
        title=title,
        description=desc
                    + "Your starting spells are:\n"
                    + spell_string + "\n\n"
                    + f"__Check all your spells with the `{prefix}spells` command. "
                      "You can unlock more spells from chests!__",
        color=Config.MAINCOLOR
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320244649295894/736899292626944050/damage.png")
    embed.set_footer(text='Click ✔ to continue')
    await msg.edit(embed=embed)
    await asyncio.sleep(2)
    await msg.add_reaction("✅")

    def check(check_reaction, user):
        return check_reaction.message.id == msg.id and user.id == ctx.author.id

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30.0)
        if str(reaction) == "✅":
            await msg.clear_reactions()
    except asyncio.TimeoutError:
        print("Continue")

    embed = discord.Embed(
        title=title,
        description=desc
                    + f"For more info check the `{prefix}wiki` and `{prefix}help` command or join our [**Discord**]"
                      f"(https://discord.com/) server.\n\n"
                    + f"Try doing a `{prefix}boss` to get familiar with the controls :smile:\n\n"
                    + f"**Good luck on your journey, champion!**\n\"*{Battle_Utils.quotes()}\"*",
        color=Config.MAINCOLOR)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/736320244649295894/736899344636051456/crown.png")
    embed.set_footer(text='Click ✔ to start your journey!')
    await msg.edit(embed=embed)
    await asyncio.sleep(2)
    await msg.add_reaction("✅")

    def check(check_reaction, check_user):
        return check_reaction.message.id == msg.id and check_user.id == ctx.author.id

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=30.0)
        if str(reaction) == "✅":
            await msg.clear_reactions()
            if new:
                return msg, account
            else:
                embed.set_footer()
                await msg.edit(embed=embed)
    except asyncio.TimeoutError:
        if new:
            return msg, account


def get_account(id):
    return Config.USERS.find_one({'user_id': id})


def create_account(user, _class):
    account = get_account(user)
    class_obj = get_class(_class)
    if account is None:
        account = {'user_id': user, 'rubies': 0, 'crowns': 0, 'claimed_contract': {}, 'coins': 0, 'xp': 0,
                   'inventory': [], 'weapon': None, 'armor': None, 'class': _class,
                   'cosmetics': [{'type': 'color', 'name': 'Basic color', 'value': "0xdb58dd"},
                                 {'type': 'title', 'value': " the " + _class}, {'type': 'emote', 'value': "Wow!"},
                                 {'type': 'emote', 'value': "Good Game!"},
                                 {'type': 'emote', 'value': '<:S:730356471178461184>'}],
                   'selected_title': " The " + _class,
                   'selected_embed_color': {'name': "Basic color", 'value': "0xdb58dd"}, 'selected_embed_image': None,
                   'keys': 0, 'grown': [],
                   'crops': [{'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0},
                             {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}, {'type': 0, 'growth': 0}],
                   'stats': class_obj['stats'], 'seeds': [{'id': 0, 'amount': 1}],
                   'battles': {"pvp": 0, "bosses": 0, "dungeons": 0}, 'power': 2, 'chests': 0,
                   'spells': [{'class': _class, 'spells': [0, 1]}], 'abilities': [], 'slots': [0, 1, None, None, None],
                   'code': None, 'registered': datetime.datetime.utcnow()}
        Config.USERS.insert_one(account)
        return account
    else:
        return account


def get_rank_name(power):
    return get_rank_object(power)['name']


def get_rank_emoji(power):
    return get_rank_object(power)['emoji'] + " "


def get_rank_object(power):
    if power < 0:
        return Config.RANK_LINKS[-1]

    power_levels = list(Config.RANK_LINKS.keys())
    bisection = bisect(power_levels, power)
    return Config.RANK_LINKS[power_levels[bisection - 1]]


def get_reset_power(power):
    if power < 0:
        return power
    elif power < 10:
        return 1

    power_levels = list(Config.RANK_LINKS.keys())
    bisection = bisect(power_levels, power)
    return power_levels[bisection - 2]


def decrease_durability(userid):
    account = get_account(userid)
    broken_items = []
    if account['armor'] is not None:
        for item in account['inventory']:
            if item['name'] == account['armor']['name']:
                the_item = get_item(item["name"])
                if 'current_durability' not in item.keys():
                    if 'durability' in item.keys():
                        item['current_durability'] = the_item['durability']
                    else:
                        dura = 25
                        if the_item['tier'] == "bronze":
                            dura = 100
                        elif the_item['tier'] == "iron":
                            dura = 500
                        elif the_item['tier'] == "emerald":
                            dura = 1000
                        elif the_item['tier'] in ["enchanted", "phantom"]:
                            dura = 5000
                        item['current_durability'] = dura
                item['current_durability'] -= 1
                try:
                    account['armor']['current_durability'] -= 1
                except:
                    print("ignore this")
                if item['current_durability'] < 1:
                    account['armor'] = None
                    broken_items.append(item)
                break
    if account['weapon'] is not None:
        for item in account['inventory']:
            if item['name'] == account['weapon']['name']:
                the_item = get_item(item["name"])
                if 'current_durability' not in item.keys():
                    if 'durability' in item.keys():
                        item['current_durability'] = the_item['durability']
                    else:
                        dura = 25
                        if the_item['tier'] == "bronze":
                            dura = 100
                        elif the_item['tier'] == "iron":
                            dura = 500
                        elif the_item['tier'] == "emerald":
                            dura = 1000
                        elif the_item['tier'] in ["enchanted", "phantom"]:
                            dura = 5000
                        item['current_durability'] = dura
                item['current_durability'] -= 1
                try:
                    account['weapon']['current_durability'] -= 1
                except:
                    print("ignore this")
                if item['current_durability'] < 1:
                    account['weapon'] = None
                    broken_items.append(item)
                break
    Config.USERS.update_one({'user_id': userid}, {'$set': {'inventory': account['inventory']}})
    if len(broken_items) > 0:
        Config.USERS.update_one({'user_id': userid}, {'$pull': {'inventory': {'$in': broken_items}},
                                                      '$set': {'armor': account['armor'], 'weapon': account['weapon']}})
    return broken_items


def get_contract_tier(xp):
    tier = Config.CONTRACTS[Config.ACTIVE_CONTRACT][str(len(Config.CONTRACTS[Config.ACTIVE_CONTRACT]))]
    final_key = str(len(Config.CONTRACTS[Config.ACTIVE_CONTRACT]))
    for key, value in Config.CONTRACTS[Config.ACTIVE_CONTRACT].items():
        try:
            if xp < value['xp']:
                tier = value
                final_key = key
                break
            else:
                continue
        except:
            break
    return tier, final_key


def get_plant(id):
    return Config.PLANTS.find_one({'id': id})


## UPGRADE FORMULAS
def calc_strength_upgrade_cost(strength):
    return math.floor(40 * 1.15 ** math.floor(strength))


def calc_defense_upgrade_cost(defense):
    return math.floor(40 * 1.15 ** math.floor(defense))


def calc_health_upgrade_cost(health):
    return math.floor(20 * 1.1 ** (health / 10))


def calc_item_upgrade_cost(effect, scale=1.1):
    return math.floor(15 * 1.25 ** effect)


def calc_item_effect(account, weapon):
    return round(weapon["upgrade_amount"] * (account["level"] - 1) + weapon["effect"], 1)


def calc_clan_upgrade_cost(amount):
    return math.floor(10 * 1.05 ** amount)


def calc_endurance_upgrade_cost(endurance):
    return math.floor(1.03 ** math.floor(endurance))


def change_crate_amount(user, amount):
    Config.USERS.update_one({'user_id': user}, {'$inc': {'chests': amount}})


def change_money_amount(user, amount):
    Config.USERS.update_one({'user_id': user}, {'$inc': {'rubies': amount}})


def get_spell(_class, id):
    return Config.SPELLS.find_one({'class': _class, 'id': id})


def get_ability(id):
    return Config.ABILITIES.find_one({'id': id})


def get_spell_by_name(_class, name):
    return Config.SPELLS.find_one({'class': _class, 'name': re.compile('^' + re.escape(name) + '$', re.IGNORECASE)})


def get_ability_by_name(name):
    return Config.ABILITIES.find_one({'name': re.compile('^' + re.escape(name) + '$', re.IGNORECASE)})


def get_all_crops():
    crop_dict = {}
    for crop in Config.PLANTS.find({}):
        crop_dict[crop['id']] = crop
    return crop_dict


def get_plant_by_name(name):
    return Config.PLANTS.find_one({'name': re.compile('^' + re.escape(name) + '$', re.IGNORECASE)})


def get_users_spells_class(account, _class):
    loop = 0
    while loop < len(account["spells"]):
        if account["spells"][loop]["class"] == _class:
            return list(Config.SPELLS.find({'class': _class, 'id': {'$in': account['spells'][loop]["spells"]}}))
        loop += 1


def get_users_spells(account):
    loop = 0
    while loop < len(account["spells"]):
        if account["spells"][loop]["class"] == account["class"]:
            return list(
                Config.SPELLS.find({'class': account["class"], 'id': {'$in': account['spells'][loop]["spells"]}}))
        loop += 1


def get_users_abilities(account):
    return list(Config.ABILITIES.find({'id': {'$in': account['abilities']}}))


def check_user_has_spell(user, id):
    return id in get_account(user)['spells']


def equip_spell(user, id, slot):
    account = get_account(user)
    last_slot = account['slots'][slot]
    account['slots'][slot] = id
    Config.USERS.update_one({'user_id': user}, {'$set': account})
    return last_slot


def equip_ability(account, id):
    last_slot = account['slots'][4]
    account['slots'][4] = id
    Config.USERS.update_one({'user_id': account["user_id"]}, {'$set': account})
    return last_slot


def get_not_owned_spells(account):
    return Config.SPELLS.count_documents({'class': account['class'], 'id': {'$nin': account['spells']}})


def win_spell(account):
    number = random.randint(0, (len(account["spells"]) - 1))
    spells = list(Config.SPELLS.find(
        {'class': account["spells"][number]["class"], 'id': {'$nin': account['spells'][number]["spells"]}}))
    if len(spells) < 1:
        return None
    else:
        spell = random.choice(spells)
        return spell


def win_ability(account):
    if "abilities" in Config.DISABLED:
        return
    if account["power"] < 100:
        return None
    abilities = list(Config.ABILITIES.find({'id': {'$nin': (account['abilities'] + [7, 8, 11])}}))
    if len(abilities) < 1:
        return None
    else:
        return random.choice(abilities)


def win_class(account):
    classes = []
    loop = 0
    while loop < len(account["spells"]):
        classes.append(account["spells"][loop]["class"])
        loop += 1
    _class = list(Config.CLASSES.find({'name': {'$nin': classes}}))
    if len(_class) < 1:
        return None
    else:
        _class = random.choice(_class)
        return _class


def win_seed():
    seeds = get_all_crops()
    return random.choice(list(seeds.values()))


def get_user_clan(id):
    return Config.CLANS.find_one({'members': id})


def get_all_items():
    return list(Config.ITEMS.find({}))


def get_item(name):
    # if name == "Phantom Sword":
    #     name = "Enchanted Sword"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Sword"
    #     item["emoji"] = "<:P:730362458643890187>"
    #     return item
    # elif name == "Phantom Axe":
    #     name = "Enchanted Axe"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Axe"
    #     item["emoji"] = "<:P:730362459013251102>"
    #     return item
    # elif name == "Phantom Scythe":
    #     name = "Enchanted Scythe"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Scythe"
    #     item["emoji"] = "<:P:730362458765787157>"
    #     return item
    # elif name == "Phantom Shield":
    #     name = "Enchanted Shield"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Shield"
    #     item["emoji"] = "<:P:730362459134885918>"
    #     return item
    # elif name == "Phantom Tunic":
    #     name = "Enchanted Tunic"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Tunic"
    #     item["emoji"] = "<:P:730362459239743519>"
    #     return item
    # elif name == "Phantom Helmet":
    #     name = "Enchanted Helmet"
    #     item = Config.ITEMS.find_one({'name': name})
    #     item["name"] = "Phantom Helmet"
    #     item["emoji"] = "<:P:730362459071709195>"
    #     return item
    # else:
    return Config.ITEMS.find_one({'name': name})


def get_all_weapons():
    items = []
    for item in Config.ITEMS.find({}):
        if item["type"] in ["weapon", "armor"]:
            items.append(item)
    return items


def get_all_cosmetics():
    items = []
    for item in Config.ITEMS.find({}):
        if item["type"] in ["title", "emote", "color", "image"]:
            items.append(item)
    return items
