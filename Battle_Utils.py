import datetime
import math
import random
from typing import Optional

import discord

import Config

# Setup matchmaking queue if it doesn't already exist
import Utils

if not ('matchmaking' in locals()):
    matchmaking = []


#############
# PVP Stuff #
#############


def get_season_timer():
    """
    Get's the current season timer

    Returns
    -------
    int
        The `time.time` of the next season reset
    """

    result = Config.MAIN.find_one({'name': "Season Reset"})
    return result["timer"]


def send_ticket(ticket):
    """
    Adds a ticket to matchmaking if it isn't already added

    Parameters
    ----------
    ticket
        Ticket to add to matchmaking

    Returns
    -------
    bool
        `False` if the ticket is already in matchmaking
    """

    if ticket in matchmaking:
        return False

    matchmaking.append(ticket)
    return True


def match_tickets():
    """
    Matches players together who are in matchmaking

    Returns
    -------
    Any
        The matched tickets
    """

    matched = []
    cancelled = []
    # Goes through all the players in matchmaking
    for ticket in matchmaking:
        # As long as the ticket hasn't been cancelled
        if ticket not in cancelled:
            # Check the ticket hasn't expired
            if ticket['expire'] < datetime.datetime.utcnow():
                cancelled.append(ticket)
                continue

            # Loop through all the tickets again
            for secondary_ticket in matchmaking:
                # As long as the ticket isn't the original and hasn't expired
                if secondary_ticket not in cancelled and ticket != secondary_ticket:
                    # If the two players are within 40 power of each other
                    if abs(abs(ticket['power']) - abs(secondary_ticket['power'])) <= 40:
                        # Match the tickets
                        matched.append([ticket, secondary_ticket])
                        cancelled.append(ticket)
                        cancelled.append(secondary_ticket)
                        # Both tickets have a match, no need to continue searching on this one
                        break

    # Remove all cancelled tickets if they're still in matchmaking
    for ticket in cancelled:
        if ticket in matchmaking:
            matchmaking.remove(ticket)

    # Return the made matches
    return matched


#################
# BOSS Creation #
#################


def make_monster_name(is_titan: Optional[bool] = False) -> str:
    """
    Generate a normal boss's name

    Parameters
    ----------
    is_titan : bool
        If the boss is a titan

    Returns
    -------
    str
        The name of the boss
    """

    # Boss is a titan
    if is_titan:
        first = ['Rel', 'Raid', 'Ur', 'Pal', 'Su']
        second = ['per', 'foul', 'es', 'idin', 'ipidimus']
        return random.choice(first) + random.choice(second) + " The TITAN"

    # Boss isn't a titan
    first = ['Gar', 'Hel', 'Bar', 'Or', 'Fre', 'Cra', 'Ju', 'Pre', 'Lue', 'Meu', 'Ve', 'Ki', 'Fr', 'Xse', "Har", 'Fai',
             'Ig', 'Tel', 'Ral', 'Gr', 'H']
    second = ['mold', 'gamlo', 'crem', 'ulk', 'opref', 'hold', 'joint', 'opold', 'ulf', 'rep', 'teft', 'dolt', 'fop',
              '', '', ',', ' Ulk', 'O', 'S']
    last = [' The Second', ' II', ' The Powerful', ' The Almighty', ' The Fourth', ' I', ' The Arrogant', ' The Troll',
            ' The Warrior', ' The Guard', ' Underwhelm', ' The Sorcerer', ' The King', ' The Queen', ' The Bard',
            ' The Traveler', ' The Scarred', ' The Lost Man', ' The Lonely', ' The Spider', ' The Giant Spider',
            ' The Elf', ' The Magician', ' The Trickster']
    # Halloween endings
    # last = [" The Ghost", " The Werewolf", " The Grim Reaper", " The Witch", " The Undead", " The Undead",
    # " The Spider", " The Troll", " The Maniac"]
    return random.choice(first) + random.choice(second) + random.choice(last)


#############
# BATTLE UI #
#############


def create_bar(bar_type, current, stat_max, min_emojis, max_emoji_value):
    """
    Creates a health or mana bar.
    A step is each part in an emoji

    Parameters
    ----------
    bar_type : str
        The type of bar to create, either "health" or "mana".
    current : float
        The current value of the hp/mana
    stat_max : int
        The maximum value to the hp/mana
    min_emojis : int
        The minimum amount of emojis the bar has
    max_emoji_value : int
        The maximum value each step has

    Returns
    -------
    str
        Bar icon and bar emojis in a string
    """

    emoji_count = math.ceil(stat_max / max_emoji_value)
    emoji_count = emoji_count if emoji_count > min_emojis else min_emojis
    bar = Config.BARS[bar_type]["icon"]

    # If we've hit bottom, we're empty
    if current <= 0:
        bar += Config.BARS[bar_type]["connector"][0] \
               + Config.BARS[bar_type]["middle"][0] * (emoji_count - 2) \
               + Config.BARS[bar_type]["end"][0]
        return bar

    # A step is a part of an emoji
    step_value = stat_max / (emoji_count * 5 - 1)
    numerator = current / step_value

    # As the end emoji has fewer steps, we're going to double the value at the first step.
    # This will make it seem like a close call is closer than it is
    if numerator > 1:
        filled_bars, partial_level = divmod(numerator, 5)
    else:
        filled_bars = 0
        partial_level = 1

    filled_bars = int(filled_bars)
    # Round to an int, and as it's an index, minus 1
    partial_level = math.ceil(partial_level)
    middle_emoji_count = emoji_count - 2

    # Add the connector bar emoji
    if filled_bars > 0:
        filled_bars -= 1
        bar += Config.BARS[bar_type]["connector"][6]
    else:
        # If the first emote is partially filled, we can easily add the rest
        bar += Config.BARS[bar_type]["connector"][partial_level] \
               + Config.BARS[bar_type]["middle"][0] * middle_emoji_count \
               + Config.BARS[bar_type]["end"][0]
        return bar

    # Add the full middle bars
    bar += Config.BARS[bar_type]["middle"][6] * filled_bars

    # Some of the middle bars are partially filled/empty
    if filled_bars != middle_emoji_count:
        bar += Config.BARS[bar_type]["middle"][partial_level] \
               + Config.BARS[bar_type]["middle"][0] * (middle_emoji_count - filled_bars - 1) \
               + Config.BARS[bar_type]["end"][0]
    else:
        partial_level = 5 if current == stat_max else partial_level
        bar += Config.BARS[bar_type]["end"][partial_level]

    return bar


def quotes():
    """
    Get a random quote to use on the searching embed

    Returns
    -------
    str
        The selected quote
    """

    battle_quotes = ["Nobody can hurt me without my permission.",
                     "If you can't go back to your mother's womb, you'd better learn to be a good fighter.",
                     "It's easier to fight for one's principles than to live up to them",
                     "War means fighting, and fighting means killing.",
                     "You'll never be entirely comfortable. This is the truth behind the champion - "
                     "he is always fighting something. To do otherwise is to settle.",
                     "There is no such thing as a fair fight. All vulnerabilities must be exploited.",
                     "Whenever we want to combat our enemies, first and foremost we must start by understanding them "
                     "rather than exaggerating their motives.",
                     "Where there is only a choice between cowardice and violence, I would advise violence.",
                     "It’s not whether you get knocked down, it’s whether you get up.",
                     "Some Warriors look fierce, but are mild. Some seem timid, but are vicious. "
                     "Look beyond appearances; position yourself for the advantage.",
                     "Strategy without tactics is the slowest route to victory. Tactics without strategy is the noise "
                     "before defeat.",
                     "You must not fight too often with one enemy, or you will teach him all your art of war.",
                     "You may have to fight a battle more than once to win it.",
                     "There are no pleasures in a fight but some of my fights have been a pleasure to win.",
                     "Supreme excellence consists in breaking the enemy’s resistance without fighting",
                     "Victory is always possible for the person who refuses to stop fighting.",
                     "We shall heal our wounds, collect our dead and continue fighting.",
                     "Don't fight a battle if you don't gain anything by winning.",
                     "He will win who knows when to fight and when not to fight.",
                     "You have to fight to reach your dream. You have to sacrifice and work hard for it.",
                     "If you hurt me, I wouldn't cry. I would hurt you back.", "Don't. Lose.", "FIGHT! Or go home.",
                     "Life is about how much you can take and keep fighting, how much you can suffer and keep moving "
                     "forward.",
                     "Victory is always possible for the person who refuses to stop fighting.",
                     "People who fight fire with fire usually end up with ashes.",
                     "You’ve got to keep your head up, keep fighting, and do the best you can.",
                     "Every spell is a journey.",
                     "Magic is an art; using reality and the world as its canvas.",
                     "You are the most powerful tool in your life. Use your energy, your thoughts and your magic "
                     "wisely!",
                     "We don’t grow when things are easy; we grow when we face challenges.",
                     "Don’t limit your challenges. Challenge your limits.",
                     "When life gets harder, challenge yourself to be stronger.",
                     "When you face difficult times, know that challenges are not sent to destroy you. They’re sent to "
                     "promote, increase and strengthen you.",
                     "The bigger the challenge, the bigger the opportunity for growth.",
                     "A challenge only becomes an obstacle when you bow to it.",
                     "Don’t run away from a challenge. Instead, run toward it, the only way to escape fear is to "
                     "trample it beneath your feet and the more difficult the victory; the greater the happiness "
                     "in winning.",
                     "The most challenging times bring us the most empowering lessons."]
    return random.choice(battle_quotes)


def generate_battle_stats(hp, max_hp, mana, max_mana, strength, weapon, defence, armor, effects):
    """
    Generate the UI for a player/boss in a battle.

    Parameters
    ----------
    hp : float
        The current hp of the user.
    max_hp : int
        The max health of the user.
    mana : float
        The current mana count of the user.
    max_mana : int
        The max mana of the user.
    strength : float
        The total strength of the user.
    weapon : str
        The emoji of the weapon.
    defence : float
        The total defence of the user.
    armor : str
        The emoji of the armor.
    effects : dict
        Emojis of any effects the user is under.

    Returns
    -------
    str
        A string of the user's stats formatted for embed display.
    """
    extra = ""
    # Loop through and add in the player's effect
    if len(effects) != 0:
        extra = "**|** "
        for effect in effects:
            if effect["name"] == "Poison":
                extra += "<:po:785900842037411840>"
            if effect["name"] == "Blinding":
                extra += "<:bl:785905140477329480>"
    # Add strength, weapon, defence, armor, effects, hp bar then mana bar
    return (str(float(strength)) + weapon + str(float(defence)) + armor + extra + "\n"
            + create_bar("health", hp, max_hp, 4, 30) + " " + str(hp) + "\n"
            + create_bar("mana", mana, max_mana, 4, 30) + " " + str(mana))

###########
# Boss AI #
###########


def pick_spell(monster):
    """
    Picks a spell with some AI.

    Parameters
    ----------
    monster
        The monster that's picking the spell.

    Returns
    -------
    Any
        dict - The spell the monster picked.
    """

    # Requires [:] as otherwise it edits the boss' spells
    # This is because otherwise both variables would reference the same values in memory
    # Look at mutability for more info
    # https://stackoverflow.com/questions/13538266/python-copy-of-a-variable
    spells = monster['spells'][:]
    max_hp = monster['stats']['health']
    cur_hp = monster['health']
    max_mana = monster['stats']['endurance']
    cur_mana = monster['mana']

    # Classify our spells
    heals = []
    recovery = []
    preps = []
    other = []
    for spell in spells:
        # Heal Spells
        if spell['type'] in ['HEAL', 'STEAL']:
            if cur_mana > spell['cost'] + 7:
                heals.append(spell)

                # If it's still an attack spell, we don't need to recover
                if spell['type'] in ['STEAL']:
                    other.append(spell)

        # Mana recovery spells
        elif spell['type'] in ['MANA', 'DRAIN']:
            if cur_hp > spell['cost'] + 20:
                recovery.append(spell)

                # If it's still an attack spell, we don't need to recover
                if spell['type'] in ['DRAIN']:
                    other.append(spell)

        # Preparation spells
        elif spell['type'] in ['PEN', 'ARMOR', 'IMPAIR', 'WEAKEN']:
            if cur_mana > spell['cost'] + 13:
                preps.append(spell)

        # Other spells must be damaging types
        # TODO - Choose correct damage spell?
        else:
            if cur_mana > spell['cost'] + 7:
                other.append(spell)

    # Heal if below 40% health
    if (cur_hp / max_hp) < 0.4:
        # Pick which heal
        if len(heals) > 0:
            return random.choice(heals)

    # Recover mana if below 30%
    if (cur_mana / max_mana) < 0.3:
        # Pick which mana recovery
        if len(recovery) > 0:
            return random.choice(recovery)

    # If we've got > 60% health and > 60% mana, we'll try prepping for damage
    if (cur_hp / max_hp) > 0.6 and (cur_mana / max_mana) > 0.6:
        # 40% chance of doing a damaging spell, to avoid player sleeping and us stacking too much
        if random.randint(1, 100) > 60:
            # Pick which preparation spell
            if len(preps) > 0:
                return random.choice(preps)

    # Otherwise, choose a damaging spell
    if len(other) > 0:
        chosen_spell = random.choice(other)
        return chosen_spell

    # Pass turn
    return None


########
# TURN #
########


def ability_effect(ability, match, turn, monster: Optional[dict] = None):
    """
    Performs the selected ability.

    Parameters
    ----------
    ability
        The ability used.
    match
        The current match data.
    turn
        The current turn number.
    monster
        The monster to target.

        This is optional.

    Returns
    -------
    Any
        list - The match data.
        str - The message to use when constructing the embeds.
        Optional[dict] - The monster if the user is against one.
    """

    match[turn]['ability'] = ability["name"]
    message = ""

    # If we haven't got a monster, must be pvp
    if monster is None:
        is_pve = False
        monster = match[int(not bool(turn))]
    else:
        is_pve = True

    if ability['name'] == "Switch":
        health = match[turn]['health']
        match[turn]['health'] = round(match[turn]['mana'] * ability["effect"])
        match[turn]['mana'] = round(health * ability["effect"])
        match = match_check(match, monster if is_pve else None)
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Their health and mana have been switched"

    elif ability['name'] == "Wish":
        if random.randint(1, 5) == 1:
            match[turn]['health'] -= ability["effect"]
            message = match[turn]['user'].name + " casts **" + ability['name'] \
                + "**. Oh no, bad luck. You take `" + str(ability['effect']) + "` damage"
        else:
            monster['health'] -= ability["effect"]
            message = match[turn]['user'].name + " casts **" + ability['name'] \
                + "**. The odds are in their favor. Their opponent takes `" + str(ability['effect']) + "` damage"
        match = match_check(match, monster if is_pve else None)

    elif ability['name'] == "Crushing Blow":
        for user in match:
            user['account']['stats']['defense'] = ability["effect"]
        if is_pve:
            monster['stats']['defense'] = ability["effect"]
            match, monster = match_check(match, monster)
        else:
            match = match_check(match)
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Everyone armor has been changed to `" + str(ability['effect']) + "`"

    elif ability['name'] == "Healing Blood":
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Switched mana regeneration to " + str(ability['effect']) + " health per turn"

    elif ability['name'] == "Stagnation":
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Halves their opponent's regeneration"

    elif ability['name'] == "Inner Light":
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Changed mana regeneration to " + str(ability['effect']) + " mana per turn"

    elif ability['name'] == "Cleanse":
        match[turn]['effects'] = []
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. All the effects you had have been removed"

    elif ability['name'] == "Alleviate":
        match[turn]['health'] += ability["effect"]
        match = match_check(match)
        message = match[turn]['user'].name + " casts **" + ability['name'] + \
            "**. You get `" + str(ability['effect']) + "` health"

    elif ability['name'] == "Blast":
        match[turn]['health'] -= ability["effect"]
        monster['health'] -= ability["effect"]
        match = match_check(match, monster if is_pve else None)
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. You and your opponent take `" + str(ability['effect']) + "` damage"

    elif ability['name'] == "Time Loop":
        for user in match:
            user['health'] += ability["effect"]
            user['mana'] += ability["effect"]
        match = match_check(match)
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. All players gets `" + str(ability['effect']) + "` health and mana"

    elif ability['name'] == "Amplify":
        match[turn]['account']['stats']['strength'] += ability['effect']
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Added `" + str(ability['effect']) + "` strength to boost their next spell"

    elif ability['name'] == "Glass Armor":
        match[turn]['account']['stats']['defense'] += ability['effect']
        message = match[turn]['user'].name + " casts **" + ability['name'] \
            + "**. Added `" + str(ability['effect']) + "` defense to protect them from their enemies next spell"

    if is_pve:
        return match, message, monster
    else:
        return match, message


def spell_stats(user):
    """
    Get's the player/boss' def, name and str.

    Useful as it's stored differently between bosses and players in a battle

    Returns
    -------
    Any
        float - The defence of the user.
        str - The name of the account.
        float - The defence of the account
    """
    # Get user stats for player/boss (as the data is stored differently)
    try:
        # Player
        u_def = user['account']['stats']['defense']
        u_name = user['user'].name
        u_str = user['account']['stats']['strength']
    except KeyError:
        # Boss
        u_def = user['stats']['defense']
        u_name = user['name']
        u_str = user['stats']['strength']

    return u_def, u_name, u_str


def spell_effect(spell, attacker, defender, can_stun: Optional[bool] = False):
    """
    Performs the spell used by the attacker on the defender.

    Parameters
    ----------
    spell
        The spell to perform
    attacker
        The player/boss that used the attack
    defender
        The player/boss that receives the attack
    can_stun
        Boolean if the target can be stunned

        This is optional. Defaults to `False`

    Returns
    -------
    Any
        dict - The attacker post spell
        dict - The defender post spell
        str - The message to display on embeds
    """

    if spell['type'] in ["MANA", "DRAIN"]:
        attacker['health'] -= spell['cost']
    else:
        attacker['mana'] -= spell['cost']

    atk_def, atk_name, atk_str = spell_stats(attacker)
    def_def, def_name, def_str = spell_stats(defender)
    message = ""

    # Damaging spells
    if spell['type'] == "DAMAGE":
        calculated_damage = round(((spell['damage'] + atk_str) * spell['scaling']) - def_def, 1)
        if calculated_damage < 0:
            calculated_damage = 0

        defender['health'] -= calculated_damage
        defender['health'] = round(defender['health'], 1)

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " takes `" \
            + str(calculated_damage) + "` damage total (`" + str(def_def) + "` blocked)"

    elif spell['type'] == "STUN":
        calculated_damage = round(((spell['damage'] + atk_str) * spell['scaling']) - def_def, 1)
        if calculated_damage < 0:
            calculated_damage = 0

        defender['health'] -= calculated_damage
        defender['health'] = round(defender['health'], 1)

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        chance = random.randint(0, 2)
        if chance == 0 and can_stun:
            message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " takes `" + str(calculated_damage) \
                      + "` damage total (`" + str(def_def) + "` blocked) and is stunned. (loses next turn)"
            defender['stunned'] = True
        elif not can_stun:
            message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " takes `" + str(calculated_damage) \
                      + "` damage total (`" + str(def_def) + "` blocked). This enemy can't be stunned..."
        else:
            message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " takes `" + str(calculated_damage) \
                      + "` damage total (`" + str(def_def) + "` blocked) and the stun failed..."

    elif spell['type'] == "TRUE":
        calculated_damage = round((spell['damage'] + atk_str) * spell['scaling'], 1)
        if calculated_damage < 0:
            calculated_damage = 0

        defender['health'] -= calculated_damage
        defender['health'] = round(defender['health'], 1)

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)
        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " takes `" \
            + str(calculated_damage) + "` true damage."

    # stat_regen_types spells
    elif spell['type'] == "HEAL":
        attacker['health'] += spell['damage']

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " gains `" \
            + str(spell['damage']) + "` health."

    elif spell['type'] == "MANA":
        attacker['mana'] += spell['damage']

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " transforms `" \
            + str(spell['cost']) + "` health into `" + str(spell['damage']) + "` mana."

    elif spell['type'] == "DRAIN":
        attacker['mana'] += spell['damage']
        defender['mana'] -= spell['damage']

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)
        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " stole `" + str(spell['damage']) \
            + "` mana from " + def_name + " using `" + str(spell['cost']) + "` health."

    elif spell['type'] == 'STEAL':
        calculated_damage = round(((spell['damage'] + atk_str) * spell['scaling']) - def_def, 1)
        if calculated_damage < 0:
            calculated_damage = 0

        defender['health'] -= calculated_damage
        attacker['health'] += round(0.7 * calculated_damage)

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)
        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name \
            + " dealt `" + str(calculated_damage) + "` damage and stole `" + str(round(0.7 * calculated_damage)) \
            + "` health from " + def_name

    # stat_affect_types spells
    elif spell['type'] == "PEN":
        atk_str += spell['damage']

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " boosted their Strength from `" \
            + str(round(atk_str - spell['damage'], 1)) + "` to `" + str(atk_str) + "`"

    elif spell['type'] == "ARMOR":
        atk_def += spell['damage']

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " boosted their Defense from `" \
            + str(round(atk_def - spell['damage'], 1)) + "` to `" + str(atk_def) + "`"

    elif spell['type'] == "IMPAIR":
        before_stat = def_def
        def_def -= spell['damage']

        try:
            # Player
            defender['account']['stats']['defense'] = def_def
        except KeyError:
            # Boss
            defender['stats']['defense'] = def_def

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name + "'s defense falls from `" \
            + str(before_stat) + "` to `" + str(def_def) + "`."

    elif spell['type'] == "WEAKEN":
        before_stat = def_str
        def_str -= spell['damage']

        try:
            # Player
            defender['account']['stats']['strength'] = def_str
        except KeyError:
            # Boss
            defender['stats']['strength'] = def_str

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name \
            + "'s strength falls from `" + str(before_stat) + "` to `" + str(def_str) + "`."

    # def_effect_types spells
    elif spell['type'] == "POISON":
        amount = round(spell['damage'], 1)

        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
        defender['effects'].append(effect)

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " gets effect `" + str(effect['name']) \
            + "` of `" + str(effect['amount']) + "` magnitude for `" + str(effect['turns']) + "` turns."

    elif spell['type'] == "BLIND":
        amount = round(spell['damage'], 1)

        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
        defender['effects'].append(effect)

        defender = user_match_check(defender)
        def_def, def_name, def_str = spell_stats(defender)

        message = atk_name + " casts **" + spell['name'] + "**. " + def_name + " gets effect `" + str(effect['name']) \
            + "` of `" + str(effect['amount']) + "` magnitude for `" + str(effect['turns']) + "` turns."

    # atk_effect_types spells
    elif spell['type'] == "REGEN":
        amount = round((spell['damage'] + atk_str) * spell['scaling'], 1)
        effect = {'name': "Regenerating", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
        attacker['effects'].append(effect)

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " gets effect `" + str(effect['name']) \
            + "` of `" + str(effect['amount']) + "` magnitude for `" + str(effect['turns']) + "` turns."

    elif spell['type'] == "RESTORE":
        amount = round((spell['damage'] + attacker['account']['stats']['strength']) * spell['scaling'], 1)
        effect = {'name': "Restoring", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
        attacker['effects'].append(effect)

        attacker = user_match_check(attacker)
        atk_def, atk_name, atk_str = spell_stats(attacker)

        message = atk_name + " casts **" + spell['name'] + "**. " + atk_name + " gets effect `" + str(effect['name']) \
            + "` of `" + str(effect['amount']) + "` magnitude for `" + str(effect['turns']) + "` turns."

    # Set user state for attacker
    try:
        # Player
        attacker['account']['stats']['defense'] = atk_def
        attacker['account']['stats']['strength'] = atk_str
    except KeyError:
        # Boss
        attacker['stats']['defense'] = atk_def
        attacker['stats']['strength'] = atk_str

    # Get user stats for defender
    try:
        # Player
        defender['account']['stats']['defense'] = def_def
        defender['account']['stats']['strength'] = def_str
    except KeyError:
        # Boss
        defender['stats']['defense'] = def_def
        defender['stats']['strength'] = def_str

    return attacker, defender, message


def user_match_check(user):
    """
    Makes sure the user's hp and mana aren't above max.
    Makes sure the user's str and def aren't below 1.

    Parameters
    ----------
    user
        The player/monster to check for

    Returns
    -------
    Any
        user - The player/monster post check
    """
    # They're a player
    try:
        # Make sure health and mana are not above max value, and round to make pretty
        if user['health'] > user['account']['stats']['health']:
            user['health'] = user['account']['stats']['health']
        else:
            user['health'] = round(user['health'], 1)
        if user['mana'] > user['account']['stats']['endurance']:
            user['mana'] = user['account']['stats']['endurance']
        else:
            user['mana'] = round(user['mana'], 1)

        # Round strength and make sure it's not less than the minimum
        strength_min = 1
        if user['account']['stats']['strength'] < strength_min:
            user['account']['stats']['strength'] = strength_min
        else:
            user['account']['stats']['strength'] = round(user['account']['stats']['strength'], 1)

        # Round armor and make sure it's not less than the minimum
        armor_min = 1
        if user['account']['stats']['defense'] < armor_min:
            user['account']['stats']['defense'] = armor_min
        else:
            user['account']['stats']['defense'] = round(user['account']['stats']['defense'], 1)

    # Are they actually a monster?
    except KeyError:
        # Make sure monster values are in check as well
        if user['health'] > user['stats']['health']:
            user['health'] = user['stats']['health']
        else:
            user['health'] = round(user['health'], 1)
        if user['mana'] > user['stats']['endurance']:
            user['mana'] = user['stats']['endurance']
        else:
            user['mana'] = round(user['mana'], 1)

        # Make sure strength stats are where they should be FOR MONSTER
        strength_min = 1
        if user['stats']['strength'] < strength_min:
            user['stats']['strength'] = strength_min
        else:
            user['stats']['strength'] = round(user['stats']['strength'], 1)

        # Make sure armor stats are where they should be FOR MONSTER
        armor_min = 1
        if user['stats']['defense'] < armor_min:
            user['stats']['defense'] = armor_min
        else:
            user['stats']['strength'] = round(user['stats']['strength'], 1)

    return user


def match_check(match, monster: Optional[dict] = None):
    """
    Loops through all the players in the match plus the monster and checks them.

    Parameters
    ----------
    match
        The match to check
    monster
        The monster to check (if any).

        This is optional
    Returns
    -------
    Any
        list - The checked match
        dict - The checked monster (if any)
    """

    # Loop through all players
    for i in range(len(match)):
        match[i] = user_match_check(match[i])

    # Do we have a monster
    if monster is not None:
        monster = user_match_check(monster)
        return match, monster

    return match


######################
# Embed Construction #
######################


def construct_boss_embed(match, turn, monster, title):
    """
    Creates an embed for a boss fight

    Parameters
    ----------
    match
        The match data for the fight
    turn
        The current turn number
    monster
        The current monster the players are fighting against
    title
        The title of the embed

    Returns
    -------
    embed
        A discord embed, processed to display the information
    """

    user_turn = True
    if 'turn' in monster.keys():
        if monster['turn']:
            user_turn = False
    elif turn == len(match):
        user_turn = False

    # User's turn
    if user_turn:
        if match[turn]['stunned']:
            embed = discord.Embed(color=int(match[turn]['account']['selected_embed_color']['value'], 16),
                                  description="It is " + match[turn]['user'].name + "'s turn " +
                                              "but they're stunned so can't do anything!")
        else:
            embed = discord.Embed(color=int(match[turn]['account']['selected_embed_color']['value'], 16),
                                  description="It is " + match[turn]['user'].name + "'s turn.")

        # Add Spells
        embed.description += "\n\n**" + match[turn]['user'].name + "'s Spellbook**:" + construct_spell_book(match[turn])

        # Check for resource abilities
        if match[turn]['ability'] == "Healing Blood":
            footer_text = match[turn]['user'].name + " gains 5 health at the beginning of their turn."
        elif match[turn]['ability'] == "Inner Light":
            footer_text = match[turn]['user'].name + " gains 6 mana at the beginning of their turn."
        # No ability, so base 3 mana
        else:
            footer_text = match[turn]['user'].name + " gains 3 mana at the beginning of their turn."

        for effect in match[turn]['effects']:
            footer_text += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " \
                           + str(effect['turns']) + " turns."

        embed.set_footer(text=footer_text)

    # Bosses turn
    else:
        if monster['stunned']:
            embed = discord.Embed(color=Config.NOTTURN, description="It is " + monster['name'] + "'s turn " +
                                                                    "but they're stunned so can't do anything!")
        else:
            embed = discord.Embed(color=Config.NOTTURN, description="It is " + monster['name'] + "'s turn.")

        # Spells display
        embed.description += "\n\n**" + monster['name'] + "'s Spellbook**:" + construct_spell_book(monster)

        # Resource generation
        abilities = []
        for user in match:
            abilities.append(user["ability"])
        if "Stagnation" in abilities:
            footer_text = monster['name'] + " gains 4 mana at the beginning of their turn," \
                                            " an enemy used Stagnation on them."
        else:
            footer_text = monster['name'] + " gains 8 mana at the beginning of their turn."

        for effect in monster['effects']:
            footer_text += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " \
                           + str(effect['turns']) + " turns."

        embed.set_footer(text=footer_text)

    # Stuff in both boss and player turns
    embed = add_monster_to_embed(monster, embed)

    # Add user display
    embed = add_users_to_embed(match, embed)

    # Embed title
    embed.title = title

    return embed


def construct_boss_embed_with_message(match, turn, monster, title, text):
    user_turn = True
    if 'turn' in monster.keys():
        if monster['turn']:
            user_turn = False
    elif turn == len(match):
        user_turn = False

    if user_turn:
        embed = discord.Embed(title=title, color=Config.OK, description=text)

        embed.set_footer(text=match[turn]['user'].name + " is planning their next move.")

    else:
        embed = discord.Embed(title=title, color=Config.DAMAGE, description=text)

        embed.set_footer(text=monster['name'] + " is planning their next move.")

    embed = add_users_to_embed(match, embed)

    embed = add_monster_to_embed(monster, embed)

    return embed


def construct_pvp_embed(match, turn, user_number, chat_log):
    # Create embed
    if turn == user_number:
        if match[turn]['stunned']:
            embed = discord.Embed(color=int(match[turn]['account']['selected_embed_color']['value'], 16),
                                  description="It's your turn, but you're stunned! You can't do anything!")
        else:
            embed = discord.Embed(color=int(match[turn]['account']['selected_embed_color']['value'], 16),
                                  description="It's your turn. React with a number to use a spell. Or react with "
                                  "💤 to pass")
    else:
        if match[turn]['stunned']:
            embed = discord.Embed(color=Config.NOTTURN,
                                  description="It is " + match[int(not bool(user_number))]['ctx'].author.name
                                              + "'s turn, but they're stunned and can't do anything!")
        else:
            embed = discord.Embed(color=Config.NOTTURN,
                                  description="It is " + match[int(not bool(user_number))]['ctx'].author.name
                                              + "'s turn. Please wait for them to cast a spell.")

    # Spell book
    equipped_string = construct_spell_book(match[user_number])
    embed.description += "\n\n**Spellbook**:" + equipped_string

    # Add users to embed
    embed = add_users_to_embed(match, embed)

    # Title
    embed.title = "Battle against " + match[int(not bool(user_number))]['ctx'].author.name \
                  + match[int(not bool(user_number))]['account']['selected_title']

    # Effects
    footer_string = ""
    for effect in match[turn]['effects']:
        footer_string += " | " + str(effect['amount']) + "x " + effect['name'] \
                         + " effect for " + str(effect['turns']) + " turns."

    # Mana Generation
    # Stagnation
    if match[int(not bool(user_number))]["ability"] == "Stagnation":
        if match[user_number]['ability'] == "Healing Blood":
            embed.set_footer(text="You gain 2.5 health at the beginning of your turn, "
                                  "your enemy used Stagnation on you." + footer_string)
        elif match[user_number]['ability'] == "Inner Light":
            embed.set_footer(text="You gain 3 mana at the beginning of your turn, "
                                  "your enemy used Stagnation on you" + footer_string)
        else:
            embed.set_footer(text="You gain 1.5 mana at the beginning of your turn, "
                                  "your enemy used Stagnation on you." + footer_string)
    # No Stagnation
    else:
        if match[user_number]['ability'] == "Healing Blood":
            embed.set_footer(text="You gain 5 health at the beginning of your turn." + footer_string)
        elif match[user_number]['ability'] == "Inner Light":
            embed.set_footer(text="You gain 6 mana at the beginning of your turn." + footer_string)
        else:
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)

    embed.add_field(name="💬 **Chat**", value=chat_log, inline=False)

    return embed


def construct_pvp_embed_with_message(match, turn, user_number, chat_log, message):

    if turn == user_number:
        embed = discord.Embed(color=Config.OK, description=message)
    else:
        embed = discord.Embed(color=Config.DAMAGE, description=message)

    # Spell book
    equipped_string = construct_spell_book(match[user_number])
    embed.description += "\n\n**Spellbook**:" + equipped_string

    # Add users to embed
    embed = add_users_to_embed(match, embed)

    # Title
    embed.title = "Battle against " + match[int(not bool(user_number))]['ctx'].author.name \
                  + match[int(not bool(user_number))]['account']['selected_title']

    # Effects
    footer_string = ""
    for effect in match[turn]['effects']:
        footer_string += " | " + str(effect['amount']) + "x " + effect['name'] \
                         + " effect for " + str(effect['turns']) + " turns."

    # Mana Generation
    # Stagnation
    if match[int(not bool(user_number))]["ability"] == "Stagnation":
        if match[user_number]['ability'] == "Healing Blood":
            embed.set_footer(text="You gain 2.5 health at the beginning of your turn, "
                                  "your enemy used Stagnation on you." + footer_string)
        elif match[user_number]['ability'] == "Inner Light":
            embed.set_footer(text="You gain 3 mana at the beginning of your turn, "
                                  "your enemy used Stagnation on you" + footer_string)
        else:
            embed.set_footer(text="You gain 1.5 mana at the beginning of your turn, "
                                  "your enemy used Stagnation on you." + footer_string)
    # No Stagnation
    else:
        if match[user_number]['ability'] == "Healing Blood":
            embed.set_footer(text="You gain 5 health at the beginning of your turn." + footer_string)
        elif match[user_number]['ability'] == "Inner Light":
            embed.set_footer(text="You gain 6 mana at the beginning of your turn." + footer_string)
        else:
            embed.set_footer(text="You gain 3 mana at the beginning of your turn." + footer_string)

    embed.add_field(name="💬 **Chat**", value=chat_log, inline=False)
    return embed


def construct_spell_book(user):
    """
    Generates a spell book for a player/monster

    Parameters
    ----------
    user
        A player/monster to generate the spell book for.

    Returns
    -------
    str
        The player/monster's spell book.
    """

    equipped_string = ""

    # Try get a user's spells first
    try:
        # Spells
        for spell in user['account']['slots'][:4]:
            if spell is None:
                equipped_string += "\n> " + Config.EMOJI["spell"] + " *Nothing is written on this page...*"
                continue
            spell = Utils.get_spell(user['account']['class'], spell)
            if spell is not None:
                equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + spell['name'] + \
                                   "** - [ " + str(spell['damage']) + " effect] [ " + \
                                   str(spell['cost']) + " cost] [ " + str(spell['scaling']) + " scaling]"
        # Display Ability
        if len(user['account']['slots']) >= 5:
            if user['account']['slots'][4] is not None:
                ability = Utils.get_ability(user['account']["slots"][4])
                if user['ability'] is not None:
                    equipped_string += "\n> " + Config.EMOJI['broken'] + " **" + ability["name"] + "** " + \
                                       ability['desc']
                else:
                    equipped_string += "\n> " + ability['emoji'] + " **" + ability["name"] + "** " + ability['desc']

    except KeyError:
        # Loop through and display all the bosses spells
        for spell in user['spells']:
            equipped_string += "\n> " + spell['emoji'] + " **" + " [" + spell['type'] + "] " + spell['name'] + \
                               "** - [ " + str(spell['damage']) + " effect] [ " + str(spell['cost']) + " cost] [ " + \
                               str(spell['scaling']) + " scaling]"

    return equipped_string


def add_users_to_embed(match, embed):
    """
    Adds users to a battle embed

    Parameters
    ----------
    match
        The current match data for the fight
    embed
        The embed the fight is using

    Returns
    -------
    embed
        The embed with the users added
    """

    for user in match:
        # User equipment
        weapon_additive_string = " " + Config.EMOJI["sword"] + " "
        if user['weapon'] is not None:
            weapon_additive_string = " " + user['weapon']['emoji'] + " "

        armor_additive_string = " " + Config.EMOJI["shield"] + " "
        if user['armor'] is not None:
            armor_additive_string = " " + user['armor']['emoji'] + " "

        # Add the user as a field
        embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + " " + user['user'].name +
                        user['account']['selected_title'],
                        value=generate_battle_stats(round(user["health"], 1), user['account']['stats']['health'],
                                                    round(user["mana"], 1), user['account']['stats']['endurance'],
                                                    user['account']['stats']['strength'],
                                                    weapon_additive_string,
                                                    user['account']['stats']['defense'], armor_additive_string,
                                                    user["effects"]))

    return embed


def add_monster_to_embed(monster, embed):
    """
    Adds a monster to a battle embed

    Parameters
    ----------
    monster
        The monster the player's are fighting
    embed
        The embed the fight is using

    Returns
    -------
    embed
        The embed with the monster added
    """

    # Strength of boss
    weapon_additive_string = " " + Config.EMOJI["sword"] + " "
    if 'weapon' in monster.keys():
        weapon_additive_string = " " + monster['weapon']['emoji'] + " "

    # Defence of boss
    armor_additive_string = " " + Config.EMOJI["shield"] + " "
    if 'armor' in monster.keys():
        armor_additive_string = " " + monster['armor']['emoji'] + " "

    # Add to embed
    boss_class = Utils.get_class(monster['spells'][0]["class"])
    if 'turn' in monster.keys():
        embed.description += "\n\n**" + boss_class['emote'] + " " + monster['name'] + "**\n" + \
                             generate_battle_stats(round(monster["health"], 1), monster['stats']['health'],
                                                   round(monster["mana"], 1), monster['stats']['endurance'],
                                                   monster['stats']['strength'], weapon_additive_string,
                                                   monster['stats']['defense'], armor_additive_string,
                                                   monster["effects"]) + "\n‎‎‏‏‎ ‎"
    else:
        embed.description += "\n\n**" + monster['name'] + "**\n" + \
                             generate_battle_stats(monster["health"], monster['stats']['health'],
                                                   monster["mana"], monster['stats']['endurance'],
                                                   monster['stats']['strength'], weapon_additive_string,
                                                   monster['stats']['defense'], armor_additive_string,
                                                   monster["effects"]) + "\n‎‎‏‏‎ ‎"

    return embed


#######
# EOF #
#######

print("Battle Utilities loaded")
