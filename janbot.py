# bot.py
import os
import discord
import robin_stocks
import requests
import re
from discord.ext import commands
from dotenv import load_dotenv

import glob
import random

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

login = robin_stocks.login(os.getenv('ROBINHOOD_LOGIN'),os.getenv('ROBINHOOD_PW'))


bot = commands.Bot(command_prefix='', help_command=None)

richardPicDir = glob.glob("richardpics/*")
richardPics = []

with open("text_file_resources/interviewquestions.txt") as f:
    interviewQuestions = [question for question in f]

for path in richardPicDir:
    richardPics.append(path.replace("\\", "/"))


current_league = "Ritual"
item_type_routes = ["UniqueWeapon", "DivinationCard", "UniqueArmour", "UniqueAccessory", "UniqueJewel", "UniqueFlask", "UniqueMap",
                    "Oil", "Incubator", "Scarab", "SkillGem","Fossil", "Resonator", "Prophecy", "Beast", "Essence"]


#to do: add remaining item type routes [fragments, ..], figure out how to display linked items, auto update current_league, error messages

@bot.command(name="help")
async def help(ctx):
    embedVar = discord.Embed(title="Janbot Commands", description="look at that boy go", color=0xff0000)
    embedVar.add_field(name="c 'currency'", value="Returns the chaos orb equivalent of currency", inline=False)
    embedVar.add_field(name="e 'currency'", value="Returns the exalted orb equivalent of currency", inline=False)
    embedVar.add_field(name="ce 'currency'", value="Returns the total exalted and chaos orb equivalent of currency", inline=False)
    embedVar.add_field(name="ci 'item' 'optional: 0l,5l,6l'", value="Returns the chaos orb equivalent of item", inline=False)
    embedVar.add_field(name="ei 'item'", value="Returns the exalted orb equivalent of item", inline=False)
    embedVar.add_field(name="!stonks", value="Displays portfolio value", inline=False)
    embedVar.add_field(name="!positions", value="Displays account positions", inline=False)
    embedVar.add_field(name="!richard", value="Random richard picture", inline=False)
    await ctx.send(embed=embedVar)

@bot.command(name="ci")
async def item_chaos_price(ctx, *args):
    requested_item = " ".join(args)
    for type in item_type_routes:
        request_string = 'https://poe.ninja/api/data/itemoverview?league={}&type={}'.format(current_league, type)
        r = requests.get(request_string)
        if type in ["UniqueWeapon", "UniqueArmour"]:  # items that have different price per links
            if (requested_item[-2:] in ["0L", "0l", "5L", "5l", "6l", "6L"]):  # checking for specific linkage (0,5,6)
                links = requested_item[-2:]  # last two chars are the num links
                requested_item_name = requested_item[:-3]  # strip the num links and whitespace
                for item in r.json()['lines']:
                    if (item['name'].replace("'", "").lower() in [requested_item_name, requested_item_name.replace("'", "").lower()]) and str(item['links']) == str(requested_item[-2]):
                        return_statement = "A " + str(item['links']) + " linked " + item['name'] + ' is currently worth ' + str(item['chaosValue']) + " chaos orbs."
                        await ctx.send(return_statement)
                        return
            else:  # if no listed links, assume 0 links
                for item in r.json()['lines']:
                    if (item['name'].replace("'", "").lower() in [requested_item, requested_item.replace("'","").lower()]) and str(item['links']) == str(0):
                        return_statement = "A " + str(item['links']) + " linked " + item['name'] + ' is currently worth ' + str(item['chaosValue']) + " chaos orbs."
                        await ctx.send(return_statement)
                        return
        else:  # otherwise, links don't matter
            for item in r.json()['lines']:
                if item['name'].replace("'", "").lower() in [requested_item, requested_item.replace("'", "").lower()]:
                    return_statement = item['name'] + ' is currently worth ' + str(item['chaosValue']) + " chaos orbs."
                    await ctx.send(return_statement)
                    return


@bot.command(name="ei")
async def item_chaos_price(ctx, *args):
    requested_item = " ".join(args)
    for type in item_type_routes:
        request_string = 'https://poe.ninja/api/data/itemoverview?league={}&type={}'.format(current_league, type)
        r = requests.get(request_string)
        for item in r.json()['lines']:
            if item['name'].replace("'", "").lower() in [requested_item, requested_item.replace("'", "").lower()]:
                return_statement = item['name'] + ' is currently worth ' + str(item['exaltedValue']) + " exalted orbs."
                await ctx.send(return_statement)
                return


@bot.command(name="exalt")
async def exalt(ctx):
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={}&type=Currency&language=en'.format(current_league)
    r = requests.get(request_string)
    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == "Exalted Orb":
            returnStatement = currency['currencyTypeName'] +'s' + ' are currently worth ' + str(currency['chaosEquivalent']) + " chaos orbs."
    await ctx.send(returnStatement)


@bot.command(name="c", aliases=["chaos"])
async def chaosEquivalent(ctx, *args):
    requested_currency = " ".join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={}&type=Currency&language=en'.format(current_league)
    r = requests.get(request_string)
    currency_dict = {}  # dict format -- name: [correct name: chaos equivalent]
    for currency in r.json()['lines']:
        simplified_name = currency['currencyTypeName'].replace("'", "").lower()  # remove apostrophe and lowercase
        price = [currency['currencyTypeName'], str(currency['chaosEquivalent'])]
        currency_dict[simplified_name] = price
        currency_dict[currency['currencyTypeName']] = price
    try:
        return_statement = currency_dict[requested_currency][0] + '\'s' + " are worth " + "**" + currency_dict[requested_currency][1] + "**" + " chaos orbs."
        await ctx.send(return_statement)
    except:
        return_statement = "Cannot find: " + requested_currency + ". \n" + "Please make sure that you are typing the full name of the currency."
        await ctx.send(return_statement)


@bot.command(name="e")
async def exaltEquivalent(ctx, *args):
    requested_currency = " ".join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={}&type=Currency&language=en'.format(current_league)
    r = requests.get(request_string)

    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == "Exalted Orb":
            exalt_value = currency['chaosEquivalent']
            break

    currency_dict = {}  # dict format -- name: [correct name: exalt equivalent]
    for currency in r.json()['lines']:
        simplified_name = currency['currencyTypeName'].replace("'", "").lower()  # remove apostrophe and lowercase
        currency_dict[simplified_name] = [currency['currencyTypeName'], str(round(currency['chaosEquivalent'] / exalt_value, 2))]
        currency_dict[currency['currencyTypeName']] = [currency['currencyTypeName'], str(round(currency['chaosEquivalent'] / exalt_value, 2))]
    try:
        return_statement = currency_dict[requested_currency][0] + '\'s' + " are worth " + "**" + currency_dict[requested_currency][1] + "**" + " exalted orbs."
        await ctx.send(return_statement)
    except:  # make less broad
        return_statement = "Cannot find: " + requested_currency + ". \n" + "Please make sure that you are typing the full name of the currency."
        await ctx.send(return_statement)


@bot.command(name="ec", aliases=["ce"])
async def exaltChaosEquivalent(ctx, *args):
    requested_currency = " ".join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={}&type=Currency&language=en'.format(current_league)
    r = requests.get(request_string)

    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == "Exalted Orb":
            exalt_value = currency['chaosEquivalent']
            break

    currency_dict = {}  # dict format -- {name: [correct name, exalt quotient, chaos remainder]}
    for currency in r.json()['lines']:
        simplified_name = currency['currencyTypeName'].replace("'", "").lower()  # remove apostrophe and lowercase
        currency_dict[simplified_name] = [currency['currencyTypeName'], str(currency['chaosEquivalent'] // exalt_value), str(round(currency['chaosEquivalent'] % exalt_value))]
        currency_dict[currency['currencyTypeName']] = [currency['currencyTypeName'], str(currency['chaosEquivalent'] // exalt_value), str(round(currency['chaosEquivalent'] % exalt_value))]
    try:
        return_statement = currency_dict[requested_currency][0] + '\'s' + " are worth a total of " + \
                           "**" + currency_dict[requested_currency][1] + "**" + " exalted orbs and " + currency_dict[requested_currency][2] + " chaos orbs."
        await ctx.send(return_statement)
    except:  # make less broad
        return_statement = "Cannot find: " + requested_currency + ". \n" + "Please make sure that you are typing the full name of the currency."
        await ctx.send(return_statement)


@bot.command(name="hello")
async def hello(ctx):
    await ctx.send("im janbot")


@bot.command(name="choke")
async def choke(ctx):
    await ctx.send(file=discord.File('richardpics/richardchoke.jpg'))


@bot.command(name="whoisright")
async def whoisright(ctx):
    await ctx.send(file=discord.File('richardpics/fiddle.jpg'))


@bot.command(name="richardree")
async def richardree(ctx):
    await ctx.send(file=discord.File('richardpics/richardgasm.jpg'))


@bot.command(name="swagswagbitch")
async def richardree(ctx):
    await ctx.send(file=discord.File('richardpics/richard9.jpg'))


@bot.command(name='gunmo')
async def gunmo(ctx):

    response = ("<@" + str(121871886673117184) + ">" + "\n")

    await ctx.send(response)


@bot.command(name="!richard")
async def randomRichard(ctx):
    await ctx.send(file=discord.File(random.choice(richardPics)))


@bot.command(name="poggers")
async def ryanO(ctx):
    await ctx.send(file=discord.File('images/ryanO.png'))


@bot.command(name="!jimothy")
async def jimothy(ctx):
    await ctx.send(file=discord.File('images/jimothy.png'))


@bot.command(name="!burger")
async def burger(ctx):
    await ctx.send(file=discord.File('images/burger.jpg'))


@bot.command(name="sike")
async def sike(ctx):
    await ctx.send(file=discord.File('images/sike.png'))


@bot.command(name="!question")
async def interviewquestion(ctx):
    await ctx.send(random.choice(interviewQuestions))


@bot.command(name="!stonks")
async def stonks(ctx):  # portfolio
    await ctx.send(robin_stocks.profiles.load_portfolio_profile(info="equity"))


@bot.command(name="!positions")
async def positions(ctx):  # portfolio
    my_stocks = robin_stocks.build_holdings()
    positions = ""
    for key, value in my_stocks.items():
        positions += "".join((key + ", " + "Price: " + str(round(float(value["price"]), 2)) + "," + " Quantity: " + str(round(float(value["quantity"]))))) + "\n"
    await ctx.send(positions)

bot.run(token)
