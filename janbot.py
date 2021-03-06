# bot.py
import ast
import glob
#import praw
import itertools
import operator
import os
import random
import re
import sys

import discord

from discord.ext import tasks
import robin_stocks
import requests
import robin_stocks
from discord.ext import commands
from dotenv import load_dotenv
#import praw
import itertools
import glob
import sys
import pymongo
import operator
import ast
import re
import random
import time
from embed import create_embed
from price_check import price_check

load_dotenv()


# setting up discord api info
token = os.getenv('DISCORD_TOKEN')


# setting up robinhood api info
login = robin_stocks.login(os.getenv('ROBINHOOD_LOGIN'), os.getenv('ROBINHOOD_PW'))


# setting up richard image paths
richardPicDir = glob.glob('richardpics/*')
richardPics = []
for path in richardPicDir:
    richardPics.append(path.replace('\\', '/'))


# setting up interview questions
with open('text_file_resources/interviewquestions.txt') as f:
    interviewQuestions = [question for question in f]


# setting up poe ninja routes and league info
current_league = 'Ritual'
item_type_routes = [
    'UniqueWeapon',
    'DivinationCard',
    'UniqueArmour',
    'UniqueAccessory',
    'UniqueJewel',
    'UniqueFlask',
    'UniqueMap',
    'Oil',
    'Incubator',
    'Scarab',
    'SkillGem',
    'Fossil',
    'Resonator',
    'Prophecy',
    'Beast',
    'Essence',
]


currency_type_routes = ['Currency', 'Fragment']

"""
# setting up a read-only reddit instance
reddit = praw.Reddit(
     client_id= os.getenv('REDDIT_CLIENT_ID'),
     client_secret= os.getenv('REDDIT_CLIENT_SECRET'),
     user_agent="my user agent"
)
"""
# connect to db

try:
    client = pymongo.MongoClient('mongodb+srv://kevin:{env}@cluster0.8xh0x.mongodb.net/poe.users?retryWrites=true&w=majority'.format(env=os.getenv('MONGO_PW')))
    poe_client = client.poe
    poe_users = poe_client.users
    print('Successful connection')
except:
    print('no connection')


bot = commands.Bot(command_prefix='', help_command=None)

# todo: auto update current_league, update and move to different modules?



def strip(input_string):
    return input_string.lower().replace("'", "")


@bot.command(name="help")

async def help(ctx):
    """
    Displays a discord embed object with a list of commands
    :param ctx:
    :return: Prints an embed object
    """
    embedVar = discord.Embed(title='Janbot Commands', description='look at that boy go', color=0xff0000)
    embedVar.add_field(name="c 'currency'", value='Returns the chaos orb equivalent of currency', inline=False)
    embedVar.add_field(name="e 'currency'", value='Returns the exalted orb equivalent of currency', inline=False)
    embedVar.add_field(name="ce 'currency'", value='Returns the total exalted and chaos orb equivalent of currency', inline=False)
    embedVar.add_field(name="ci 'item' 'optional: 0l,5l,6l'", value='Returns the chaos orb equivalent of item', inline=False)
    embedVar.add_field(name="ei 'item'", value='Returns the exalted orb equivalent of item', inline=False)
    embedVar.add_field(name="id 'item", value='Info about item (supports uniques, divination cards, and prophecies)', inline=False)
    embedVar.add_field(name='!stonks', value='Displays portfolio value', inline=False)
    embedVar.add_field(name='!positions', value='Displays account positions', inline=False)
    embedVar.add_field(name='!richard', value='Random richard picture', inline=False)
    await ctx.send(embed=embedVar)


@bot.command(name='ci')
async def item_chaos_price(ctx, *args):
    """
    Given any item, displays the chaos value of object
    :param ctx:
    :param args: first argument is the name of the item, second optional argument is number of links if possible
    :return: Returns string with chaos value
    """
    requested_item = ' '.join(args)



    await ctx.send(price_check(requested_item))

    return_statement = 'Cannot find: {item}. \nPlease make sure that you are typing the full name of the item.'.format(item=requested_item)
    await ctx.send(return_statement)


@bot.command(name='ei')
async def item_exalt_price(ctx, *args):
    """
    Given any item, displays the exalt value of object
    :param ctx:
    :param args: first argument is the name of the item, second optional argument is number of links if possible
    :return: Returns string with exalt value
    """
    requested_item = ' '.join(args)
    for item_type in item_type_routes:
        request_string = 'https://poe.ninja/api/data/itemoverview?league={league}&type={type}'.format(league=current_league, type=item_type)
        r = requests.get(request_string)
        if item_type in ['UniqueWeapon', 'UniqueArmour']:  # items that have different price per links
            if requested_item[-2:] in ['0L', '0l', '5L', '5l', '6l', '6L']:  # checking for specific linkage (0,5,6)
                links = requested_item[-2:]  # last two chars are the num links
                requested_item_name = requested_item[:-3]  # strip the num links and whitespace
                for item in r.json()['lines']:
                    if (item['name'].replace("'", '').lower() in [requested_item_name, requested_item_name.replace("'", '').lower()]) and str(item['links']) == str(requested_item[-2]):
                        return_statement = 'A {arg1} linked {arg2} is currently worth {arg3} exalted orbs.'.format(arg1=str(item['links']), arg2=item['name'], arg3=str(item['exaltedValue']))
                        await ctx.send(return_statement)
                        return
            else:  # if no listed links, assume 0 links
                for item in r.json()['lines']:
                    if (item['name'].replace("'", '').lower() in [requested_item, requested_item.replace("'", '').lower()]) and str(item['links']) == str(0):
                        return_statement = 'A {arg1} linked {arg2} is currently worth {arg3} exalted orbs.'.format(arg1=str(item['links']), arg2=item['name'], arg3=str(item['exaltedValue']))
                        await ctx.send(return_statement)
                        return
        else:  # otherwise, links don't matter
            for item in r.json()['lines']:
                if item['name'].replace("'", '').lower() in [requested_item, requested_item.replace("'", '').lower()]:
                    return_statement = '{item} is currently worth {price} exalted orbs.'.format(item=item['name'], price=str(item['exaltedValue']))
                    await ctx.send(return_statement)
                    return

    return_statement = 'Cannot find: {item}. \nPlease make sure that you are typing the full name of the item.'.format(item=requested_item)
    await ctx.send(return_statement)


@bot.command(name='exalt')
async def exalt(ctx):
    """
    Displays the current chaos value for a single exalt
    :param ctx:
    :return: Returns string with chaos value of single exalt
    """
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={league}&type=Currency&language=en'.format(league=current_league)
    r = requests.get(request_string)
    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == 'Exalted Orb':
            returnStatement = '{curr}s are currently worth {chaos} chaos orbs.'.format(curr=currency['currencyTypeName'], chaos=str(currency['chaosEquivalent']))
    await ctx.send(returnStatement)


@bot.command(name='c', aliases=['chaos'])
async def chaosEquivalent(ctx, *args):
    """
    Displays the chaos equivalent of any items with "currency" tag
    :param ctx:
    :param args: item with "currency" tag (e.g. Orb of Transmutation)
    :return: Returns string with chaos value of requested currency
    """
    requested_currency = ' '.join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={league}&type=Currency&language=en'.format(league=current_league)
    r = requests.get(request_string)
    currency_dict = {}  # dict format -- name: [correct name: chaos equivalent]
    simplified_user_request = requested_currency.replace("'", '').lower()

    for currency in r.json()['lines']:
        simplified_name = currency['currencyTypeName'].replace("'", '').lower()  # remove apostrophe and lowercase
        price = [currency['currencyTypeName'], str(currency['chaosEquivalent'])]
        currency_dict[simplified_name] = price
    try:
        return_statement = "{arg1}\'s are worth **{arg2}** chaos orbs.".format(arg1=currency_dict[simplified_user_request][0], arg2=currency_dict[simplified_user_request][1])
        await ctx.send(return_statement)
    except:
        return_statement = 'Cannot find: {curr}. \nPlease make sure that you are typing the full name of the currency.'.format(curr=requested_currency)
        await ctx.send(return_statement)


@bot.command(name='e', aliases=['ex'])
async def exaltEquivalent(ctx, *args):
    """
    Displays the exalt equivalent of any items with "currency" tag
    :param ctx:
    :param args: item with "currency" tag (e.g. Orb of Transmutation)
    :return: Return string with exalt value of requested currency
    """
    requested_currency = ' '.join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={league}&type=Currency&language=en'.format(league=current_league)
    r = requests.get(request_string)
    simplified_user_request = requested_currency.replace("'", '').lower()
    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == 'Exalted Orb':
            exalt_value = currency['chaosEquivalent']
            break

    currency_dict = {}  # dict format -- {simplified name: [correct name: exalt equivalent]}
    for currency in r.json()['lines']:
        simplified_currency = currency['currencyTypeName'].replace("'", '').lower()  # remove apostrophe and lowercase
        currency_dict[simplified_currency] = [currency['currencyTypeName'], str(round(currency['chaosEquivalent'] / exalt_value, 2))]
    try:
        return_statement = "{arg1}\'s are worth **{arg2}** exalted orbs.".format(arg1=currency_dict[simplified_user_request][0], arg2=currency_dict[simplified_user_request][1])
        await ctx.send(return_statement)
    except:  # make less broad
        return_statement = 'Cannot find: {curr}. \nPlease make sure that you are typing the full name of the currency.'.format(curr=requested_currency)
        await ctx.send(return_statement)


@bot.command(name='ec', aliases=['ce'])
async def exaltChaosEquivalent(ctx, *args):
    """
    Displays the exalt and chaos remainder equivalent of any items with "currency" tag
    :param ctx:
    :param args: item with "currency" tag (e.g. Mirror Shard)
    :return: Return string with exalt and chaos value of requested currency
    """
    requested_currency = ' '.join(args)
    request_string = 'https://poe.ninja/api/data/CurrencyOverview?league={league}&type=Currency&language=en'.format(league=current_league)
    r = requests.get(request_string)

    for currency in r.json()['lines']:
        if currency['currencyTypeName'] == 'Exalted Orb':
            exalt_value = currency['chaosEquivalent']
            break

    currency_dict = {}  # dict format -- {name: [correct name, exalt quotient, chaos remainder]}
    for currency in r.json()['lines']:
        simplified_name = currency['currencyTypeName'].replace("'", '').lower()  # remove apostrophe and lowercase
        currency_dict[simplified_name] = [currency['currencyTypeName'], str(currency['chaosEquivalent'] // exalt_value), str(round(currency['chaosEquivalent'] % exalt_value))]
        currency_dict[currency['currencyTypeName']] = [currency['currencyTypeName'], str(currency['chaosEquivalent'] // exalt_value), str(round(currency['chaosEquivalent'] % exalt_value))]
    try:
        return_statement = "{arg1}\'s are worth a total of **{arg2}** exalted orbs and {arg3} chaos orbs.".format(arg1=currency_dict[requested_currency][0], arg2=currency_dict[requested_currency][1], arg3=currency_dict[requested_currency][2])
        await ctx.send(return_statement)
    except:  # make less broad
        return_statement = 'Cannot find: {curr}. \nPlease make sure that you are typing the full name of the currency'.format(curr=requested_currency)
        await ctx.send(return_statement)


@bot.command(name='!positions')
async def positions(ctx):  # portfolio
    """
    Displays a table of current stock holdings
    :param ctx:
    :return: Return string with multiple lines of stocks
    """
    my_stocks = robin_stocks.build_holdings()
    positions = ''
    for key, value in my_stocks.items():
        positions += ''.join(('{key}, Price: {price}, Quantity: {quantity}\n'.format(key=key, price=str(round(float(value['price']), 2)), quantity=str(round(float(value['quantity']))))))
    await ctx.send(positions)

'''
@bot.command(name="!stonks")
async def stonks(ctx):
    """
    Displays current account portfolio
    :param ctx:
    :return: Return string with amount in robinhood account
    """
    await ctx.send(robin_stocks.profiles.load_portfolio_profile(info="equity"))
'''


@bot.command(name='random')
async def positions(ctx, *args):
    if len(args) != 2:
        await ctx.send('must be two numbers dummy')
    else:
        random_num = random.randrange(int(args[0]), int(args[1]))
        await ctx.send(random_num)


@bot.command(name='hello', aliases=['Hello', 'Hi', 'hi'])
async def hello(ctx):
    return_string = 'Hello, {name}'.format(name=ctx.message.author.name)
    await ctx.send(return_string)


@bot.command(name='choke')
async def choke(ctx):
    await ctx.send(file=discord.File('richardpics/richardchoke.jpg'))


@bot.command(name='whoisright')
async def whoisright(ctx):
    await ctx.send(file=discord.File('richardpics/fiddle.jpg'))


@bot.command(name='richardree')
async def richardree(ctx):
    await ctx.send(file=discord.File('richardpics/richardgasm.jpg'))


@bot.command(name='swagswagbitch')
async def richardree(ctx):
    await ctx.send(file=discord.File('richardpics/richard9.jpg'))


@bot.command(name='gunmo')
async def gunmo(ctx):
    response = ('<@{num}>\n'.format(num=str(121871886673117184)))
    await ctx.send(response)


@bot.command(name='!richard')
async def randomRichard(ctx):
    await ctx.send(file=discord.File(random.choice(richardPics)))


@bot.command(name='poggers')
async def ryanO(ctx):
    await ctx.send(file=discord.File('images/ryanO.png'))


@bot.command(name='jimothy')
async def jimothy(ctx):
    await ctx.send(file=discord.File('images/jimothy.png'))


@bot.command(name='burger')
async def burger(ctx):
    await ctx.send(file=discord.File('images/burger.jpg'))


@bot.command(name='sike')
async def sike(ctx):
    await ctx.send(file=discord.File('images/sike.png'))


@bot.command(name='!question')
async def interviewquestion(ctx):
    await ctx.send(random.choice(interviewQuestions))


"""
@bot.command(name="wsb")
# apparently this already exists
async def positions(ctx):
    post_number = 1
    limit = 20
    await ctx.send("Here are the top {} hot posts on wsb:".format(limit))
    for submission in reddit.subreddit("wallstreetbets").hot(limit=limit):
        post_number_return_string = "The current post number: " + str(post_number_return_string)
        await ctx.send()
        for top_level_comment in submission.comments:
            try:
                return_statement = top_level_comment.body + str(top_level_comment.score)
                await ctx.send(return_statement)
            except discord.errors.HTTPException:  # body length too long
                await ctx.send("2000 length")
"""


@bot.command(name='commit')
async def death(ctx, arg):
    """
    Ends program if user is authorized
    :param ctx:
    :param arg: must equal "death"
    :return: n/a
    """
    authorized = [142739501557481472]
    if arg == 'die' and ctx.message.author.id in authorized:
        await ctx.send('u have killed me')
        sys.exit(0)
    else:
        await ctx.send('woosh u missed')


@bot.command(name='!register')  # todo: add user custom item array, add/remove
async def register(ctx):
    requester_id = ctx.message.author.id
    if poe_users.find_one({'id': requester_id}):
        registered_string = '{name} is already registered'.format(name=ctx.message.author.name)
        await ctx.send(registered_string)
    else:
        user_to_register = {'id': requester_id, 'items': []}
        poe_users.insert_one(user_to_register)
        register_string = '{name} is now registered'.format(name=ctx.message.author.name)
        await ctx.send(register_string)

def find(requested_item) -> bool:
    item_collections = poe_client.list_collection_names()
    item_collections.remove('currencies')
    item_collections.remove('users')
    exact_requested_item = '^{item}$'.format(item=requested_item)  # regex for exact match
    stripped_requested_item = requested_item.lower().replace("'", '')  # punctuation removed and lowercase

    for collection_name in item_collections:
        specific_type_collection = poe_client.get_collection(collection_name)

        name_item_search = specific_type_collection.find_one({'name': {'$regex': exact_requested_item, '$options': 'i'}})  # search only by name
        stripped_search = specific_type_collection.find_one({'aliases': stripped_requested_item})

        if name_item_search or stripped_search:  # search by name, case insensitive
            found_item = dict(name_item_search or stripped_search)  # todo: figure out how to not search twice
            return found_item

    return None



@bot.command(name='id')
async def identify(ctx, *args):
    requested_item = ' '.join(arg.capitalize() for arg in args)
    found_item = find(requested_item)
    if found_item:  # todo: create embed class/ embed function depending on item type
        e = create_embed(found_item)
        await ctx.send(embed=e)
    else:
        not_found_response = '{item} was not found. Please @ADKarry if you think this is an error.'.format(item=requested_item)
        await ctx.send(not_found_response)

# todo: move to separate module
_OP_MAP = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Invert: operator.neg,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
}


class Calc(ast.NodeVisitor):

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return _OP_MAP[type(node.op)](left, right)

    def visit_Num(self, node):
        return node.n

    def visit_Expr(self, node):
        return self.visit(node.value)

    @classmethod
    def evaluate(cls, expression):
        tree = ast.parse(expression)
        calc = cls()
        return calc.visit(tree.body[0])


@bot.command(name='calc')
async def calc(ctx, arg):
    try:
        await ctx.send(Calc.evaluate(arg))
    except Exception as err:
        await ctx.send(err)


# WIP ---

@bot.command(name="!add")
async def add(ctx, *args):  # check registered, check item exists, check user has item already
    requester_id = ctx.message.author.id  # discord id
    requester = poe_users.find_one({"id": requester_id})  # single requester document
    requested_item = " ".join(args)
    item_to_find = find(requested_item.capitalize())  # check item does exist and return item object
    # todo: fix this cursed code block
    # check if item already exists in user list
    if not requester:
        await ctx.send("You are not currently registered. You can register using **!register**.")
    elif not item_to_find:
        await ctx.send("Item does not exist.")
    elif poe_users.find_one({"id": requester_id, "items": {"$in": [item_to_find["name"]]}}):
        await ctx.send("This item is already on your list.")
    else:
        poe_users.find_one_and_update(
            {"id": requester_id},
            {"$push": {"items": item_to_find["name"]},
             })
        return_string = item_to_find["name"] + " has now been added to your list."
        await ctx.send(return_string)



@bot.command(name="!pricecheck") # todo: break price check code to separate function and call here
async def pricecheck(ctx):
    requester_id = ctx.message.author.id  # discord id
    requester = poe_users.find_one({"id": requester_id})  # single requester document
    requester_items = requester['items']
    for item in requester_items:
        await ctx.send(price_check(item))

@bot.command(name="!remove")
async def remove(ctx, *args):
    pass

global resting
resting = True
@bot.command(name="z")
async def countdown(ctx):
    resting = True
    i = 90
    while resting and i > 0:
        if i >= 15: # and i % 15 == 0:
            await ctx.send(i)
        elif i < 15:
            await ctx.send(i)
        i -= 1
        time.sleep(1)
        print(resting)
    await ctx.send("sadge")
    resting = False

@bot.command(name="cancel")
async def cancel_resting(ctx):
    resting = False
    await ctx.send("cancled resting")
    print(resting)
bot.run(token)
