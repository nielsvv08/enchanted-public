import asyncio
import statistics

import Config
import math
import discord
import datetime
from discord.ext import commands
import Utils
import random
import time


class Raids(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.battling_users = []
        self.waiting_users = []
        self.active_channels = []
        self.bosses = 0

    def get_numbers(self, number_string):
        final_string = ""
        for character in number_string:
            try:
                int(character)
                final_string += character
            except:
                continue
        return int(final_string)

    def change_turn(self, turn, max):
        turn += 1
        if turn > max:
            turn = 0
        return turn

    def clean_up_match(self, turn, match, raid_boss):
        # make sure health and mana are not above max value
        if match['health'] > match['account']['stats']['health']:
            match['health'] = match['account']['stats']['health']
        if match['mana'] > match['account']['stats']['endurance']:
            match['mana'] = match['account']['stats']['endurance']
        # make sure strength stats are where they should be
        strength_min  = 1
        # if _['account']['weapon'] is not None:
        #     strength_min = Utils.calc_item_effect(_['account']['weapon'], _['weapon'])
        if match['account']['stats']['strength'] < strength_min:
            match['account']['stats']['strength'] = strength_min
        else:
            match['account']['stats']['strength'] = round(match['account']['stats']['strength'], 1)
        # make sure armor stats are where they should be
        armor_min = 1
        # if _['account']['armor'] is not None:
        #     armor_min = Utils.calc_item_effect(_['account']['armor'], _['armor'])
        if match['account']['stats']['defense'] < armor_min:
            match['account']['stats']['defense'] = armor_min
        else:
            match['account']['stats']['defense'] = round(match['account']['stats']['defense'], 1)

        # make sure monster values are in check as well
        raid_boss = Utils.RAIDS.find_one({"name": raid_boss["name"]})
        if raid_boss['health'] > raid_boss['stats']['health']:
            raid_boss['health'] = raid_boss['stats']['health']
        if raid_boss['mana'] > raid_boss['stats']['endurance']:
            raid_boss['mana'] = raid_boss['stats']['endurance']

        # make sure strength stats are where they should be FOR MONSTER
        strength_min = 1
        if raid_boss['stats']['strength'] < strength_min:
            raid_boss['stats']['strength'] = strength_min
        else:
            raid_boss['stats']['strength'] = round(raid_boss['stats']['strength'], 1)

        # make sure armor stats are where they should be FOR MONSTER
        armor_min = 1
    
        if raid_boss['stats']['defense'] < armor_min:
            raid_boss['stats']['defense'] = armor_min
        else:
            raid_boss['stats']['strength'] = round(raid_boss['stats']['strength'], 1)

        return turn, match, raid_boss


    async def construct_embeds(self, match, turn, message, raid_boss):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        raid_boss = Config.RAIDS.find_one({"name": raid_boss["name"]})
        if turn != len(match):
            embed = discord.Embed(color = Config.MAINCOLOR, description="it is " + match['user'].name + "'s turn.")
            equipped_string = ""
            for spell in match['account']['slots'][:4]:
                if spell is None:
                    equipped_string += "\n> "+Config.EMOJI["spell"]+" *Nothing is written on this page...*"
                    continue
                for x in Utils.get_users_spells(match['account']):
                    if spell == x['id']:
                        spell = x
                if spell is not None:
                    equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
            if len(match['account']['slots']) >= 5:
                if match['account']['slots'][4] is not None:
                    ability = Utils.get_ability(match['account']["slots"][4])
                    if match['ability'] is not None:
                        equipped_string += "\n> "+Config.EMOJI['broken']+" **" + ability["name"] + "** " + ability['desc']
                    else:
                        equipped_string += "\n> "+ability['emoji']+" **" + ability["name"] + "** " + ability['desc']
            embed.description += "\n\n**"+match['user'].name+"'s Spellbook**:" + equipped_string
            weapon_additive_string = ""
            if 'weapon' in raid_boss.keys():
                weapon_additive_string = " [+" + str(raid_boss['weapon']['effect']) + raid_boss['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in raid_boss.keys():
                armor_additive_string = " [+" + str(raid_boss['armor']['effect']) + raid_boss['armor']['emoji'] + "]"
            embed.description += "\n\n**" + raid_boss['name'] + "**\nHealth: " + str(raid_boss['health']) + "/" + str(raid_boss['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(raid_boss['mana']) + "/" + str(raid_boss['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(raid_boss['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(raid_boss['stats']['defense']) + armor_additive_string
            weapon_additive_string = ""
            if match['account']['weapon'] is not None:
                weapon_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["weapon"], match['weapon'])) + match['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if match['account']['armor'] is not None:
                armor_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["armor"], match['armor'])) + match['armor']['emoji'] + "]"
            embed.add_field(name=Utils.get_rank_emoji(match['account']['power']) + match['user'].name + match['account']['selected_title'], value="Health: " + str(match['health']) + "/" + str(match['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match['mana']) + "/" + str(match['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match['account']['stats']['strength'])+ weapon_additive_string + "\nDefense: " + str(match['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Raid Boss fight against " + raid_boss['name']
            footer_string = ""
            for effect in match['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            embed.set_footer(text=match['user'].name + " gains 3 mana at the beginning of their turn." + footer_string)
            if match['ability'] is not None:
                if match['ability'] == "Healing Blood":
                    embed.set_footer(text=match['user'].name + " gains 5 health at the beginning of their turn." + footer_string)
                elif match['ability'] == "Inner Light":
                    embed.set_footer(text=match['user'].name + " gains 6 mana at the beginning of their turn." + footer_string)
            await message.edit(embed=embed)
        else:
            embed = discord.Embed(color = Config.NOTTURN, description="it is " + raid_boss['name'] + "'s turn.")
            equipped_string = ""
            for spell in raid_boss['spells']:
                equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
            embed.description += "\n\n**"+raid_boss['name']+"'s Spellbook**:" + equipped_string
            weapon_additive_string = ""
            if 'weapon' in raid_boss.keys():
                weapon_additive_string = " [+" + str(raid_boss['weapon']['effect']) + raid_boss['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in raid_boss.keys():
                armor_additive_string = " [+" + str(raid_boss['armor']['effect']) + raid_boss['armor']['emoji'] + "]"
            embed.description += "\n\n**" + raid_boss['name'] + "**\nHealth: " + str(raid_boss['health']) + "/" + str(raid_boss['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(raid_boss['mana']) + "/" + str(raid_boss['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(raid_boss['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(raid_boss['stats']['defense']) + armor_additive_string
            weapon_additive_string = ""
            if match['account']['weapon'] is not None:
                weapon_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["weapon"], match["weapon"])) + user["weapon"]['emoji'] + "]"
            armor_additive_string = ""
            if match['account']['armor'] is not None:
                armor_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["armor"], match["armor"])) + user["armor"]['emoji'] + "]"
            embed.add_field(name=Utils.get_rank_emoji(match['account']['power']) + match['user'].name + match['account']['selected_title'], value="Health: " + str(match['health']) + "/" + str(match['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match['mana']) + "/" + str(match['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(match['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Raid Boss fight against " + raid_boss['name']
            footer_string = ""
            for effect in raid_boss['effects']:
                footer_string += " | " + str(effect['amount']) + "x " + effect['name'] + " effect for " + str(effect['turns']) + " turns."
            abilities = []
            abilities.append(match["ability"])
            if "Stagnation" in abilities:
                embed.set_footer(text=raid_boss['name'] + " doesn't regenerate anything, an enemy used Stagnation on them." + footer_string)
            else:
                embed.set_footer(text=raid_boss['name'] + " gains 8 mana at the beginning of their turn." + footer_string)
            await message.edit(embed=embed)

    async def construct_embeds_with_message(self, message, raid_boss, turn, match, text):
        SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        if turn != len(match):
            embed = discord.Embed(color = Config.OK, description=text)
            weapon_additive_string = ""
            if match['account']['weapon'] is not None:
                weapon_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["weapon"], match["weapon"])) + match["weapon"]['emoji'] + "]"
            armor_additive_string = ""
            if match['account']['armor'] is not None:
                armor_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["armor"], match["armor"])) + match["armor"]['emoji'] + "]"
            embed.add_field(name=Utils.get_rank_emoji(match['account']['power']) + match['user'].name + match['account']['selected_title'], value="Health: " + str(match['health']) + "/" + str(match['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match['mana']) + "/" + str(match['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(match['account']['stats']['defense']) + armor_additive_string)
            # embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value=Utils.create_hp_bar(user['health'], user['account']['stats']['health']) + " " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI["hp"] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength'])+ weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Raid Boss fight against " + raid_boss['name']
            weapon_additive_string = ""
            if 'weapon' in raid_boss.keys():
                weapon_additive_string = " [+" + str(raid_boss['weapon']['effect']) + raid_boss['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in raid_boss.keys():
                armor_additive_string = " [+" + str(raid_boss['armor']['effect']) + raid_boss['armor']['emoji'] + "]"
            embed.description += "\n\n**" + raid_boss['name'] + "**\nHealth: " + str(raid_boss['health']) + "/" + str(raid_boss['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(raid_boss['mana']) + "/" + str(raid_boss['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(raid_boss['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(raid_boss['stats']['defense']) + armor_additive_string
            embed.set_footer(text=match['user'].name + " is casting a spell.")
            await message.edit(embed=embed)
        else:
            embed = discord.Embed(color = Config.DAMAGE, description=text)
            weapon_additive_string = ""
            if match['account']['weapon'] is not None:
                weapon_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["weapon"], match["weapon"])) + match["weapon"]['emoji'] + "]"
            armor_additive_string = ""
            if match['account']['armor'] is not None:
                armor_additive_string = " [+" + str(Utils.calc_item_effect(match["account"]["armor"], match["armor"])) + match["armor"]['emoji'] + "]"
            embed.add_field(name=Utils.get_rank_emoji(match['account']['power']) + match['user'].name + match['account']['selected_title'], value="Health: " + str(match['health']) + "/" + str(match['account']['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(match['mana']) + "/" + str(match['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(match['account']['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(match['account']['stats']['defense']) + armor_additive_string)
            # embed.add_field(name=Utils.get_rank_emoji(user['account']['power']) + user['user'].name + user['account']['selected_title'], value=Utils.create_hp_bar(user['health'], user['account']['stats']['health']) + " " + str(user['health']) + "/" + str(user['account']['stats']['health']).translate(SUB) + Config.EMOJI["hp"] + "\nMana: " + str(user['mana']) + "/" + str(user['account']['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(user['account']['stats']['strength'])+ weapon_additive_string + "\nDefense: " + str(user['account']['stats']['defense']) + armor_additive_string)
            embed.title = "Raid Boss fight against " + raid_boss['name']
            weapon_additive_string = ""
            if 'weapon' in raid_boss.keys():
                weapon_additive_string = " [+" + str(raid_boss['weapon']['effect']) + raid_boss['weapon']['emoji'] + "]"
            armor_additive_string = ""
            if 'armor' in raid_boss.keys():
                armor_additive_string = " [+" + str(raid_boss['armor']['effect']) + raid_boss['armor']['emoji'] + "]"
            embed.description += "\n\n**" + raid_boss['name'] + "**\nHealth: " + str(raid_boss['health']) + "/" + str(raid_boss['stats']['health']).translate(SUB) + Config.EMOJI['hp'] + "\nMana: " + str(raid_boss['mana']) + "/" + str(raid_boss['stats']['endurance']).translate(SUB) + Config.EMOJI['flame'] + "\nStrength: " + str(raid_boss['stats']['strength']) + weapon_additive_string + "\nDefense: " + str(raid_boss['stats']['defense']) + armor_additive_string
            embed.set_footer(text=raid_boss['name'] + " is casting a spell.")
            await message.edit(embed=embed)

    async def raid_thread(self, match, message, raid_boss):
        match_cache = match.copy()
        await message.clear_reactions()
        raid_boss['health'] = raid_boss['stats']['health']
        raid_boss['mana'] = raid_boss['stats']['endurance']
        embed = discord.Embed(title="Raid Boss fight started!", color=Config.MAINCOLOR,
                              description="[jump](" + message.jump_url + ")")
        one_message = await message.channel.send(match['user'].mention, embed=embed)
        await one_message.delete(delay=10)
        match['health'] = match['account']['stats']['health']
        match['mana'] = match['account']['stats']['endurance']
        match['effects'] = []
        match['afk'] = 0
        turn = random.randint(0, len(match) - 1)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("🔆")
        await message.add_reaction("💤")
        await message.add_reaction("🏳️")
        a_turn = False
        while len(match) > 0 and raid_boss['health'] > 0 and raid_boss['mana'] > 0:
            restart = False
            if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                match = []
                turn -= 1
                restart = True
            if turn < 0:
                turn = 0
            if restart:
                continue


            # calculate effects for beginning of round
            effects_remove = []
            for effect in match['effects']:
                match[effect['type']] -= effect['amount']
                match[effect['type']] = round(match[effect['type']], 1)
                effect['turns'] -= 1
                if effect['turns'] < 1:
                    effects_remove.append(effect)
            for effect in effects_remove:
                match['effects'].remove(effect)

            # restart if needed after effects applied
            restart = False
            if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                # if turn >= match.index(match):
                #     turn -= 1
                match = []
                restart = True
            if restart:
                continue

            # effects for monster
            effects_remove = []
            for effect in raid_boss['effects']:
                raid_boss[effect['type']] -= effect['amount']
                raid_boss[effect['type']] = round(raid_boss[effect['type']], 1)
                effect['turns'] -= 1
                if effect['turns'] < 1:
                    effects_remove.append(effect)
            for effect in effects_remove:
                raid_boss['effects'].remove(effect)

            if turn != len(match):
                resource = 'mana'
                resource_number = 3
                if match['ability'] is not None:
                    if match['ability'] == "Healing Blood":
                        resource = 'health'
                        resource_number = 5
                    elif match['ability'] == "Inner Light":
                        resource_number = 6 
                
                if a_turn is True:
                    resource_number = 0
                a_turn = False

                match[resource] += resource_number
            else:
                abilities = []
                abilities.append(match["ability"])
                if "Stagnation" not in abilities:
                    raid_boss['mana'] += 8

            # make sure health and mana are not above max value
            if match['health'] > match['account']['stats']['health']:
                match['health'] = match['account']['stats']['health']
            if match['mana'] > match['account']['stats']['endurance']:
                match['mana'] = match['account']['stats']['endurance']

            # make sure monster values are in check as well
            if raid_boss['health'] > raid_boss['stats']['health']:
                raid_boss['health'] = raid_boss['stats']['health']
            if raid_boss['mana'] > raid_boss['stats']['endurance']:
                raid_boss['mana'] = raid_boss['stats']['endurance']

            if raid_boss['health'] <= 0 or raid_boss['mana'] <= 0:
                break

            await self.construct_embeds(match, turn, message, raid_boss)

            # check if monster's turn
            if turn == len(match):

                # simulate monster thinking lol
                await asyncio.sleep(3)


                if raid_boss['mana'] < 25:
                    turn = self.change_turn(turn, len(match))
                    continue
                else:
                    spell = random.choice(raid_boss['spells'])
                    victim = random.randint(0, len(match) - 1)

                    if spell['type'] not in ["MANA", "DRAIN"]:
                        raid_boss['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        raid_boss['health'] -= spell['cost']

                    # spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round(((spell['damage'] + raid_boss['stats']['strength']) * spell['scaling']) - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+match[victim]['user'].name+" takes `" + str(calculated_damage) + "` damage total (`" + str(match[victim]['account']['stats']['defense']) + "` blocked)")

                    elif spell['type'] == "HEAL":
                        raid_boss['health'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" gains `" + str(spell['damage']) + "` health.")

                    elif spell['type'] == "MANA":
                        raid_boss['mana'] += spell['damage']
                        raid_boss['health'] -= spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" transforms `" + str(spell['damage']) + "` health into mana.")

                    elif spell['type'] == "DRAIN":
                        raid_boss['mana'] += spell['damage']
                        match[victim]['mana'] -= spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" stole `" + str(spell['damage']) + "` mana from "+match[victim]['user'].name+" using `" + str(spell['cost']) + "` health.")

                    elif spell['type'] == "PEN":
                        raid_boss['stats']['strength'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" boosted their Strength from `" + str(raid_boss['stats']['strength'] - spell['damage']) + "` to `"+str(raid_boss['stats']['strength'])+"`")

                    elif spell['type'] == "ARMOR":
                        raid_boss['stats']['defense'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" boosted their Defense from `" + str(raid_boss['stats']['defense'] - spell['damage']) + "` to `"+str(raid_boss['stats']['defense'])+"`")

                    elif spell['type'] == "POISON":
                        amount = round(((spell['damage'] + raid_boss['stats']['strength']) * spell['scaling']) / match[victim]['account']['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
                        match[victim]['effects'].append(effect)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == "BLIND":
                        amount = round((spell['damage'] + raid_boss['stats']['strength']) * spell['scaling'] / match[victim]['account']['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
                        match[victim]['effects'].append(effect)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+match[victim]['user'].name+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + raid_boss['stats']['strength']) * spell['scaling']) - match[victim]['account']['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        raid_boss['health'] += round(0.7 * calculated_damage, 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. "+raid_boss['name']+" stole `" + str(calculated_damage) + "` health from "+match[victim]['user'].name)

                    elif spell['type'] == "IMPAIR":
                        before_stat = match[victim]['account']['stats']['defense']
                        match[victim]['account']['stats']['defense'] -= spell['damage']
                        if match[victim]['account']['stats']['defense'] < 1:
                            match[victim]['account']['stats']['defense'] = 1
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. " + match[victim]['user'].name + "'s defense falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['defense']) + "`.")

                    elif spell['type'] == "WEAKEN":
                        before_stat = match[victim]['account']['stats']['strength']
                        match[victim]['account']['stats']['strength'] -= spell['damage']
                        if match[victim]['account']['stats']['strength'] < 1:
                            match[victim]['account']['stats']['strength'] = 1
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss['name'] + " casts **" + spell['name'] + "**. " + match[victim]['user'].name + "'s strength falls from `" + str(before_stat) + "` to `" + str(match[victim]['account']['stats']['strength']) + "`.")

                    elif spell['type'] == "TRUE":
                        calculated_damage = round((spell['damage'] + raid_boss['stats']['strength']) * spell['scaling'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match[victim]['health'] -= calculated_damage
                        match[victim]['health'] = round(match[victim]['health'], 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, raid_boss["name"] + " casts **" + spell['name'] + "**. "+match[victim]["user"].name+" takes `" + str(calculated_damage) + "` true damage.")

                    if match[victim]['ability'] is not None:
                        if match[victim]["ability"] == "Glass Armor":
                            ability = Utils.get_ability(match[victim]['account']['slots'][4])
                            match[victim]["ability"] = "Glass Armor Done"
                            match[victim]['account']['stats']['defense'] -= ability['effect']
                            turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                    await asyncio.sleep(5)

                    turn = self.change_turn(turn, len(match))
                    if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                        match = []
                        turn -= 1
                    continue

            try:
                reaction_dict = {'1️⃣': 0, '2️⃣': 1, '3️⃣': 2, '4️⃣': 3, '🔆': 4}
                def check(payload):
                    if payload.user_id == match['user'].id and payload.message_id == message.id:
                        if str(payload.emoji) in reaction_dict.keys():
                            return match['account']['slots'][reaction_dict[str(payload.emoji)]] is not None
                        else:
                            return True
                    else:
                        return False

                temp_msg = await message.channel.fetch_message(message.id)
                reaction = None
                for temp_reaction in temp_msg.reactions:
                    users = await temp_reaction.users().flatten()
                    if match['user'].id in [x.id for x in users] and temp_reaction.me:
                        reaction = temp_reaction
                        try:
                            await temp_reaction.remove(match['user'])
                        except:
                            await Config.LOGGING.error("Cannot remove emoji (not big deal)")
                if reaction is None:
                    payload = await self.bot.wait_for('raw_reaction_add', timeout=30.0, check=check)
                    reaction = payload.emoji

                    try:
                        await message.remove_reaction(payload.emoji, match['user'])
                    except:
                        await Config.LOGGING.error("Cannot remove emoji (not big deal)")

                if str(reaction) == "💤":
                    turn = self.change_turn(turn, len(match))
                    continue
                elif str(reaction) == "🏳️":
                    match['health'] = 0
                    match['mena'] = 0
                    turn = self.change_turn(turn, len(match))
                    if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                        match = []
                        turn -= 1
                    continue
                elif str(reaction) == "🔆" and match["ability"] is not None:
                    a_turn = True
                elif str(reaction) == "🔆" and match["ability"] is None:
                    ability = Utils.get_ability(match['account']['slots'][4])
                    match['ability'] = ability["name"]
                    if ability['name'] == "Switch":
                        health = match['health']
                        match['health'] = round(match['mana'] * ability["effect"])
                        match['mana'] = round(health * ability["effect"])
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Their health and mana have been switched")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Wish":
                        if random.randint(1, 5) == 1:
                            match['health'] -= ability["effect"]
                            await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Owhh no, bad luck. You take `"+str(ability['effect'])+"` damage")
                        else:
                            raid_boss['health'] -= ability["effect"]                                
                            await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. The odds are in your favor, your opponent takes `"+str(ability['effect'])+"` damage")
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        turn = self.change_turn(turn, len(match))
                        
                    elif ability['name'] == "Crushing Blow":
                        match['account']['stats']['defense'] = ability["effect"]
                        raid_boss['stats']['defense'] = ability["effect"]
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Everyone armor has been changed to `" +str(ability['effect'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Healing Blood":
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Switched mana regeneration to "+str(ability['effect'])+" health per turn")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Stagnation":
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Remove your enemies regeneration")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Inner Light":
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Changed mana regeneration to "+str(ability['effect'])+" mana per turn")
                        turn = self.change_turn(turn, len(match))
                        
                    elif ability['name'] == "Cleanse":
                        match['effects'] = []
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. All the effects you had have been removed")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Alleviate":
                        match['health'] += ability["effect"]
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Your allies get `"+str(ability['effect'])+"` health")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Blast":
                        match['health'] -= ability["effect"]
                        raid_boss['health'] -= ability["effect"]
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. You and your opponent take `"+str(ability['effect'])+"` damage")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Time Loop":
                        match['health'] += ability["effect"]
                        match['mana'] += ability["effect"]
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Everyone gets `"+str(ability['effect'])+"` health and mana")
                        turn = self.change_turn(turn, len(match))

                    elif ability['name'] == "Amplify":
                        match['account']['stats']['strength'] += ability['effect']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Added `"+str(ability['effect'])+"` strength to boost your next spell")

                    elif ability['name'] == "Glass Armor":
                        match['account']['stats']['defense'] += ability['effect']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + ability['name'] + "**. Added `"+str(ability['effect'])+"` defense to protect you from your enemies next spell")
                        turn = self.change_turn(turn, len(match))

                    await asyncio.sleep(5)
                    continue
                elif str(reaction) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
                    spell = Utils.get_spell(match['account']['class'], match['account']['slots'][reaction_dict[str(reaction)]])
                    if spell['type'] not in ["MANA", "DRAIN"]:
                        match['mana'] -= spell['cost']
                    elif spell['type'] == "DRAIN":
                        match['health'] -= spell['cost']

                    # spell types
                    if spell['type'] == "DAMAGE":
                        calculated_damage = round(((spell['damage'] + match['account']['stats']['strength']) * spell['scaling']) - raid_boss['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        raid_boss['health'] -= calculated_damage
                        raid_boss['health'] = round(raid_boss['health'], 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+raid_boss['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(raid_boss['stats']['defense']) + "` blocked)")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "HEAL":
                        match['health'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" gains `" + str(spell['damage']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "STUN":
                        calculated_damage = round(((spell['damage'] + match['account']['stats']['strength']) * spell['scaling']) - raid_boss['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        Config.RAIDS.find_one_and_update({"name": raid_boss["name"]}, {"$inc": {"health": -calculated_damage}})
                        raid_boss['health'] = round(raid_boss['health'], 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+raid_boss['name']+" takes `" + str(calculated_damage) + "` damage total (`" + str(raid_boss['stats']['defense']) + "` blocked) the stun failed...")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "MANA":
                        match['mana'] += spell['damage']
                        match['health'] -= spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" transforms `" + str(spell['damage']) + "` health into mana.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "DRAIN":
                        match['mana'] += spell['damage']
                        Config.RAIDS.find_one_and_update({"name": raid_boss["name"]}, {"$inc": {"mana": -spell["damage"]}})
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" stole `" + str(spell['damage']) + "` mana from "+raid_boss['name']+" using `" + str(spell['cost']) + "` health.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "PEN":
                        match['account']['stats']['strength'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" boosted their Strength from `" + str(match['account']['stats']['strength'] - spell['damage']) + "` to `"+str(match['account']['stats']['strength'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "ARMOR":
                        match['account']['stats']['defense'] += spell['damage']
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" boosted their Defense from `" + str(match['account']['stats']['defense'] - spell['damage']) + "` to `"+str(match['account']['stats']['defense'])+"`")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "POISON":
                        amount = round((spell['damage'] + match['account']['stats']['strength']) * spell['scaling'] / raid_boss['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Poison", 'turns': random.randint(2, 8), 'type': 'health', 'amount': amount}
                        raid_boss['effects'].append(effect)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+raid_boss['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "BLIND":
                        amount = round((spell['damage'] + match['account']['stats']['strength']) * spell['scaling'] / raid_boss['stats']['defense'], 1)
                        if amount < 3:
                            amount = 3
                        effect = {'name': "Blinding", 'turns': random.randint(2, 8), 'type': 'mana', 'amount': amount}
                        raid_boss['effects'].append(effect)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+raid_boss['name']+" gets effect `" + effect['name'] + "` of `"+str(effect['amount'])+"` magnitude for `"+str(effect['turns'])+"` turns.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == 'STEAL':
                        calculated_damage = round(((spell['damage'] + match['account']['stats']['strength']) * spell['scaling']) - raid_boss['stats']['defense'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        match['health'] += round(0.7 * calculated_damage)
                        raid_boss['health'] -= calculated_damage
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+match['user'].name+" stole `" + str(calculated_damage) + "` health from "+raid_boss['name'])
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "IMPAIR":
                        before_stat = raid_boss['stats']['defense']
                        raid_boss['stats']['defense'] -= spell['damage']
                        if raid_boss['stats']['defense'] < 1:
                            raid_boss['stats']['defense'] = 1
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. " + raid_boss['name'] + "'s defense falls from `" + str(before_stat) + "` to `" + str(raid_boss['stats']['defense']) + "`.")
                        turn = self.change_turn(turn, len(match))

                    elif spell['type'] == "WEAKEN":
                        before_stat = raid_boss['stats']['strength']
                        raid_boss['stats']['strength'] -= spell['damage']
                        if raid_boss['stats']['strength'] < 1:
                            raid_boss['stats']['strength'] = 1
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. " + raid_boss['name'] + "'s strength falls from `" + str(before_stat) + "` to `" + str(raid_boss['stats']['strength']) + "`.")
                        turn = self.change_turn(turn, len(match))
                    
                    elif spell['type'] == "TRUE":
                        calculated_damage = round((spell['damage'] + match['account']['stats']['strength']) * spell['scaling'], 1)
                        if calculated_damage < 0:
                            calculated_damage = 0
                        raid_boss['health'] -= calculated_damage
                        raid_boss['health'] = round(raid_boss['health'], 1)
                        turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                        await self.construct_embeds_with_message(message, raid_boss, turn, match, match['user'].name + " casts **" + spell['name'] + "**. "+raid_boss['name']+" takes `" + str(calculated_damage) + "` true damage")
                        turn = self.change_turn(turn, len(match))

                    if match[int(not bool(turn))]['ability'] is not None:
                        if match[int(not bool(turn))]["ability"] == "Amplify":
                            ability = Utils.get_ability(match[int(not bool(turn))]['account']['slots'][4])
                            match[int(not bool(turn))]["ability"] = "Amplify Done"
                            match[int(not bool(turn))]['account']['stats']['strength'] -= ability['effect']
                            turn, match, raid_boss = self.clean_up_match(turn, match, raid_boss)
                    
                    await asyncio.sleep(5)
                    if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                        match = []
                        turn -= 1
                    continue
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and turn != len(match):
                    embed = discord.Embed(title="AFK WARNING", color=Config.MAINCOLOR,
                                          description="Your battle is still going! You lost this turn because you took over 30 seconds to choose a spell.\n\n[Click to go to fight](" + message.jump_url + ")")
                    timeout_msg = await message.channel.send(match['user'].mention, embed=embed)
                    await timeout_msg.delete(delay=20)
                    match['afk'] += 1
                    if match['health'] <= 0 or match['mana'] <= 0 or match['afk'] > 2:
                        match = []
                        turn -= 1
                    turn = self.change_turn(turn, len(match))
                    continue
                elif isinstance(e, discord.errors.NotFound):
                    return
                else:
                    match['mana'] -= 3
        try:
            await message.clear_reactions()
        except:
            await Config.LOGGING.error("Cannot remove emoji (not big deal)")

        broken_items = Utils.decrease_durability(match_cache['account']['user_id'])
        if len(broken_items) > 0:
            embed = discord.Embed(title="Broken Tools", description=match_cache['user'].mention + "! Your " + " and ".join([x['name'] for x in broken_items]) + " broke!", color=Config.MAINCOLOR)
            await message.channel.send(content=match_cache['user'].mention, embed=embed)


        if raid_boss['health'] > 0 and raid_boss['mana'] > 0:
            embed = discord.Embed(color = Config.MAINCOLOR, description="**"+raid_boss['name']+" Has bested the group...**")
            await message.edit(embed=embed)
        else:
            if not raid_boss['titan']:
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
            if raid_boss['health'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+raid_boss['name']+" has been killed!**\n\nEveryone gets:\n\n+" + mystring)
            elif raid_boss['mana'] <= 0:
                embed = discord.Embed(color = Config.MAINCOLOR, description="**Congratulations! "+raid_boss['name']+" has fainted!**\n\nEveryone gets:\n\n+" + mystring)
            else:
                embed = discord.Embed(color=Config.MAINCOLOR, description="**Congratulations! " + raid_boss['name'] + " has been destroyed completely!**\n\nEveryone gets:\n\n+ " + mystring)
            await message.edit(embed=embed)
            users = []
            for user in match_cache:
                users += user["user"].id
            x = 0
            for b_user in self.battling_users:
                if b_user["id"] in users:
                    self.battling_users.remove(battling_user[x])
                x += 1
        if message.channel.id in self.active_channels:
            self.active_channels.remove(message.channel.id)
        self.bosses -= 1

    @commands.command(aliases=["raids", "giant", "r"])
    @commands.bot_has_permissions(add_reactions=True, manage_messages=True, send_messages=True, external_emojis=True)
    async def raid(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        raid_boss = Config.RAIDS.find_one({"active": True})
        if raid_boss is False:
            embed = discord.Embed(color=Config.MAINCOLOR, title="It's awefully quiet in here",
                                  description="There is no raid boss to be found.. at the moment. Always prepare for the worst.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if not Config.OPEN_QUEUES:
            embed = discord.Embed(color=Config.ERRORCOLOR, title="Enchanted Maintenance",
                                  description="Queuing is disabled at the moment. Enchanted is under Maintenance.")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return

        if ctx.author.id in raid_boss["users"]:
            embed=discord.Embed(color=Config.MAINCOLOR, title="You did your part", description="You already fought the raid boss. Let's hope other people finish the monster.")
            if msg is None:
                await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)
            return


        user_names = []
        user_ids = []
        quote = "*\""+Utils.quotes()+"\"*"
        self.waiting_users.append(ctx.author.id)
        self.active_channels.append(ctx.channel.id)

        user_ids.append(ctx.author.id)
        user_names.append(ctx.author.name)
        users_names = ""
        for user_n in user_names:
            users_names += user_n+"\n"
        embed=discord.Embed(color=Config.MAINCOLOR, title=ctx.author.name + " are you sure?", description=f"You can only fight "+raid_boss["name"]+" once. React to start the battle.", timestamp=datetime.datetime.utcnow())
        embed.set_footer(text='React with the ✔️ to start')
        embed.set_thumbnail(url=raid_boss["image"])
        if msg is None:
            msg = await ctx.send(embed=embed)
        else:
            await msg.edit(embed=embed)
        await msg.add_reaction("✔️")

        countdown = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
        def check(reaction, user):
            return user.id != self.bot.user.id and reaction.message.id == msg.id and user.id == ctx.author.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
            if str(reaction) != "✔️":
                await reaction.message.clear_reactions()
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
                embed.set_footer(text='Time-out, run the command again to continue')
                await msg.edit(embed=embed)
            except:
                Config.LOGGING.info("Error deleting message of user. Don't have the permission or message does not exist.")
        # temp_msg = await ctx.channel.fetch_message(msg.id)
        # users = []
        # for temp_reaction in temp_msg.reactions:
        #     if str(temp_reaction) == "✔️":
        #         users = await temp_reaction.users().flatten()
        # if ctx.author.id not in [x.id for x in users]:
        #     users.append(ctx.author)

        account = Utils.get_account(user.id)
        armor = None
        weapon = None
        if account["weapon"] is not None:
            weapon = Utils.get_item(account['weapon']["name"])
        if account["armor"] is not None:
            armor = Utils.get_item(account['armor']["name"])
        match = {'ability': None, 'weapon': weapon, 'armor': armor, 'user': user, 'account': account}

        if match['account']['armor'] is not None:
            match['account']['stats']['defense'] += Utils.calc_item_effect(match["account"]["armor"], match['armor'])
        if match['account']['weapon'] is not None:
            match['account']['stats']['strength'] += Utils.calc_item_effect(match["account"]["weapon"], match['weapon'])


        raid_boss['stats']['strength'] = round(raid_boss['stats']['strength'])
        raid_boss['stats']['defense'] = round(raid_boss['stats']['defense'])
        raid_boss['stats']['health'] = round(raid_boss['stats']['health'])
        
        await self.raid_thread(match, msg, raid_boss)

    @raid.error
    async def raid_error(self, error, ctx):
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=discord.Embed(title="Uh oh..", description="I'm missing some permissions, please make sure i have the following:\n\nadd_reactions, manage_messages, send_messages, external_emojis"), color = Config.ERRORCOLOR)

def setup(bot):
    bot.add_cog(Raids(bot))
