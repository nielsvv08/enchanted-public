import Config
import discord
from discord.ext import commands
import Utils
from Paginator import EmbedPaginatorSession

class Spells(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def make_spell(self, ctx, class_name:str=None, effect:int=None, scaling:int=None, emoji:str=None, cost:int=None, type:str=None, *, name:str=None):
        if ctx.author.id not in Config.OWNERIDS:
            return
        prefix = Utils.fetch_prefix(ctx)
        if None in [class_name, scaling, emoji, cost, type, name] or type not in ['DAMAGE', 'STUN', 'MANA', 'STEAL', 'ARMOR', 'PEN', 'POISON', 'HEAL'] or class_name not in ['Paladin', 'Druid', 'Arcane']:
            await ctx.send(f"You need to use this command like this: `{prefix}make_spell <class> <effect> <scailing> <emoji> <cost> <type> <name>`. The ID will be generated automatically. Types are:\nDAMAGE, STUN, HEAL, MANA, PEN, ARMOR, POISON, STEAL\nClasses are: Paladin, Druid, Arcane")
        else:
            top_id = 0
            id = Config.SPELLS.count_documents({'class': class_name})
            spell = {'name': name, 'class': class_name, 'id': id, 'damage': effect, 'scaling': scaling, 'emoji': emoji, 'cost': cost, 'type': type}
            Config.SPELLS.insert_one(spell)
            await ctx.send(embed=discord.Embed(color = Config.MAINCOLOR, title="Spell created for class " + class_name + " ID: " + str(id), description = "> " + spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"))


    @commands.command(aliases=['enchants', 's', 'spell'])
    async def spells(self, ctx):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        loop = -1
        embeds = []
        while loop < (len(account["spells"]) - 1):
            desc = ""
            loop += 1
            spell_string = ""
            equipped_string = ""
            user_spells = Utils.get_users_spells_class(account, account["spells"][loop]["class"])
            if account["spells"][loop]["class"] == account["class"]:
                for spell in account['slots'][:4]:
                    if spell is None:
                        equipped_string += "\n> "+Config.EMOJI["spell"]+" *Nothing is written on this page...*"
                        continue
                    for _ in user_spells:
                        if spell == _['id']:
                            spell = _
                    if spell is not None and not isinstance(spell, int):
                        equipped_string += "\n> "+spell['emoji']+" **" +" ["+spell['type']+"] "+ spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
                ability = Utils.get_ability(account["slots"][4])
                if ability is not None:
                    equipped_string += "\n> "+ability['emoji']+" **" + ability["name"] + "** " + ability['desc']
                else:
                    equipped_string += "\n> "+Config.EMOJI["ability"]+" *No ability has been selected...*"
                total = 0
                amount_of_slots = 0
                for spell in user_spells:
                    if spell['id'] in account['slots'][:4]:
                        total += spell['cost']
                        amount_of_slots += 1
                if amount_of_slots == 0:
                    desc = "**Spellbook** (Average Spell Cost: "+ str(amount_of_slots) + ")\nThe spells you take with you on your travels."+equipped_string+"\n\n"
                else:
                    desc = "**Spellbook** (Average Spell Cost: "+ str(total / amount_of_slots) + ")\nThe spells you take with you on your travels."+equipped_string+"\n\n"
            for spell in user_spells:
                spell_string += "\n"+spell['emoji']+" **" + " ["+spell['type']+"] " + spell['name'] + "** - [ "+str(spell['damage'])+" effect] [ "+str(spell['cost'])+" cost] [ "+str(spell['scaling'])+" scaling]"
                #embed.add_field(name=spell['name'] + " " + spell['emoji'], value="**Cost:** " + str(spell['cost']) + "\n**Damage:** " + str(spell['damage']) + "\n**scaling:** " + str(spell['scaling']))
            prefix = Utils.fetch_prefix(ctx)
            embed=discord.Embed(color = Config.MAINCOLOR, title=f"Spells | {account['spells'][loop]['class']}", description=desc + "**Library**\nA list of all spells you have learned.\n" + spell_string)
            embed.set_footer(text=f"Use {prefix}equip <slot> <spell> to equip a spell.")
            if account["spells"][loop]["class"] == account["class"]:
                first = embed
            else:
                embeds.append(embed)
        
        paginator = EmbedPaginatorSession(ctx, first, *embeds)
        await paginator.run()

    @commands.command(aliases=['e'])
    async def equip(self, ctx, slot:int=1, *, name:str="none"):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return await ctx.send("Huts")

        # if name is None:
        #     prefix = Utils.fetch_prefix(ctx)
        #     embed=discord.Embed(color=Config.ERRORCOLOR, description=f"Please define the spell...\n`{prefix}equip <slot> <name>`")
        #     if msg is not None:
        #         await msg.edit(embed=embed)
        #     else:
        #         await ctx.send(embed=embed)
        #     return

        loop = -1
        while loop <= (len(account["spells"]) - 1):
            if account["spells"][loop]["class"] == account["class"]:
                spells = Utils.get_users_spells_class(account, account["spells"][loop]["class"])
                break
            loop += 1
        if slot > 4:
            embed=discord.Embed(color=Config.ERRORCOLOR, description="Spell slot must be between 1 and 4.")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        elif name.lower() not in [x['name'].lower() for x in spells] and name.lower() != "none":
            embed=discord.Embed(color=Config.ERRORCOLOR, description="You do not know that spell...")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            slot -= 1
            if name.lower() == 'none':
                spell = Utils.get_spell(account['class'], Utils.equip_spell(ctx.author.id, None, slot))
                if account['slots'][slot] is None:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="You wrote nothing on a blank page...")
                else:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(spell['name'])+"' has been erased from your spellbook")
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            spell = Utils.get_spell_by_name(account['class'], name)
            if spell['id'] in account['slots'][:4]:
                embed=discord.Embed(color=Config.ERRORCOLOR, description="This spell is already written in your spellbook on page " + str(account['slots'].index(spell['id']) + 1))
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            Utils.equip_spell(ctx.author.id, spell['id'], slot)
            if account['slots'][slot] is not None:
                embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(Utils.get_spell(account['class'], account['slots'][slot])['name'])+"' has been replaced with '"+str(spell['name'])+"' in your spellbook")
            else:
                embed=discord.Embed(color=Config.MAINCOLOR, description="The spell '"+str(spell['name'])+"' has been written on page "+str(slot + 1)+" of your spellbook")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)

    @commands.group(aliases=['ability', 'abiliti', 'ab'])
    async def abilities(self, ctx):
        if ctx.invoked_subcommand is not None:
            return
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return
        user_ab = Utils.get_users_abilities(account)

        if len(user_ab) < 1:
            embed=discord.Embed(color = Config.MAINCOLOR, title="Abilties", description="You have no abilites. If you're rank silver or higher you can unlock them from chests :)")
        else:
            ab_string = ""
            equipped_string = ""
            ab = account['slots'][4]
            if ab is None:
                equipped_string += "\n> "+Config.EMOJI["ability"]+" *No ability has been selected...*"
            else:
                for _ in user_ab:
                    if ab == _['id']:
                        ab = _
                if ab is not None:
                    equipped_string += "\n> "+ab['emoji']+" **"+ ab['name'] + "** - "+ab['desc']
            if len(user_ab) > 0:
                for ab in user_ab:
                    ab_string += "\n> "+ab['emoji']+" **"+ ab['name'] + "** - "+ab['desc']
            prefix = Utils.fetch_prefix(ctx)
            embed=discord.Embed(color = Config.MAINCOLOR, title="Abilities", description="**Selected ability**\nThe ability you take with you on your travels."+equipped_string+"\n\n**Library**\nA list of all abilities you have learned. Abilties can be obtianed from chests (silver or higher only)\n" + ab_string)
            embed.set_footer(text=f"Use {prefix}ability equip <ability name> to equip an ability.")
        if msg is not None:
            await msg.edit(embed=embed)
        else:
            await ctx.send(embed=embed)

    @abilities.command(aliases=['e', 'select', 'equip'])
    async def ability_equip(self, ctx,*, name:str="none"):
        msg, account = await Utils.get_account_lazy(self.bot, ctx, ctx.author.id)
        if account is None:
            return

        abilities = Utils.get_users_abilities(account)
        if name.lower() not in [x['name'].lower() for x in abilities] and name.lower() != "none":
            embed=discord.Embed(color=Config.ERRORCOLOR, description="You do not know that ability...")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            if name.lower() == 'none':
                ability = Utils.get_ability(Utils.equip_ability(account, None))
                if account['slots'][4] is None:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="You wrote nothing on a blank page...")
                else:
                    embed=discord.Embed(color=Config.MAINCOLOR, description="The ability '"+str(ability['name'])+"' has been erased from your spellbook")
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            ability = Utils.get_ability_by_name(name)
            if ability['id'] == account['slots'][4]:
                embed=discord.Embed(color=Config.ERRORCOLOR, description="This ability has been selected already")
                if msg is not None:
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            Utils.equip_ability(account, ability['id'])
            embed=discord.Embed(color=Config.MAINCOLOR, description="The ability '"+str(ability['name'])+"' has been written on your spellbook")
            if msg is not None:
                await msg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Spells(bot))
