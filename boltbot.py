#!/usr/bin/python3
import os.path
import json
import zipfile
import requests as req
import difflib
import discord
from discord.ext import commands
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sqlite3

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'

#CONSTS 
MATCH_CUT_OFF = 80
TOKEN_FILE = 'token.json'
MTG_BASE_API = "https://mtgjson.com/api/v5/" 
ALL_CARD_ENDPOINT = "AllPrintings.sqlite.zip"
ALL_CARD_SQL = "AllPrintings.sqlite"
SET_LIST_ENDPOINT = "SetList.json"

def get_card_database(endpoint): 
    print(GREEN + "Get: " + endpoint + ENDC)
    
    rsp = req.get(MTG_BASE_API + endpoint, stream=True)
    if rsp.status_code != 200:
        print(RED + "ERROR: GET Failed [HTTP Status Code: " + rsp.status_code + "]"+ ENDC)
        return False
    # Download DB in chunks
    with open(endpoint, 'wb') as f:
        for chunk in rsp.iter_content(chunk_size=8192):
            if rsp.status_code != 200:
                print(RED + "ERROR: GET Chunk Failed [HTTP Status Code: " + rsp.status_code + "]" + ENDC)
                os.remove(endpoint)
                return False
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

    with zipfile.ZipFile(endpoint) as zf:
        zf.extractall("./")

    print(GREEN + "Card DB download Complete" + ENDC)
    return True

def query_mtg_db(query):
    try:
        connection = sqlite3.connect(ALL_CARD_SQL)
        # Return results as list
        connection.row_factory = lambda cursor, row: row[0] 
        cursor = connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as error:
        print(RED + "ERROR: Query Failed [" + str(error) + "]" + ENDC)
        return False

def get_card_url(card_name):

    print(GREEN + "Get: " + card_name + ENDC)
    # Get all cards to search
    query = "SELECT DISTINCT name FROM cards WHERE multiverseid"
    all_cards = query_mtg_db(query)
    if all_cards == False:
        print(RED + "ERROR: Failed to get cards from DB" + ENDC)
        return

    # Fuzzy Search
    match = process.extract(card_name, all_cards, scorer=fuzz.token_sort_ratio)
    if match[0][1] < MATCH_CUT_OFF:
       return False 
    # Construct Image url using the cards multiverse ID
    query = "SELECT multiverseid FROM cards WHERE name=\"" + str(match[0][0]) + "\"AND multiverseid"
    multiverse_id = query_mtg_db(query)
    if multiverse_id == False:
        print(RED + "ERROR: Failed to get multiverse id for matched card" + ENDC)
        return
    image_url = "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=" + str(multiverse_id[0]) + "&type=card"
    
    return image_url

def get_sets_list():
    print(GREEN + "Get: " + SET_LIST_ENDPOINT + ENDC)

    rsp = req.get(MTG_BASE_API + SET_LIST_ENDPOINT)
    if rsp.status_code != 200:
        print(RED + "ERROR: Query Failed [HTTP Status Code: " + rsp.status_code + "]" +ENDC)
        return False

    set_list = json.loads(rsp.text)
    # Extract set codes
    set_codes = [set_code['code'] for set_code in set_list['data']]
    return set_codes

def update_cards():
    new_sets_list = get_sets_list()

    with open(SET_LIST_ENDPOINT, 'r') as f:
        current_sets_list_raw = f.read()
        current_set_list = json.loads(current_sets_list_raw)

    # Check for new sets
    if len(new_sets_list) == len(current_set_list):
        print(GREEN + "No new sets" + ENDC)
        return False

    set_difference = list(set(new_sets_list) - set(current_set_list))
    
    # Get new sets
    print(GREEN + "New Sets found: " + str(set_difference) + ENDC)
    status = get_card_database(ALL_CARD_ENDPOINT) 
    if status != True:
        print(RED + "ERROR: Failed to initilise card database" + ENDC)
        return False
            
    # Update set list
    with open(SET_LIST_ENDPOINT, 'w') as f:
        json.dump(new_sets_list, f, ensure_ascii = False, indent = 4) 

    print(GREEN + "Update Cards Complete" + ENDC)
    return set_difference

def main():
    token = None
    set_list = None 
    status = None
    print(GREEN + "BoltBot" + ENDC)

    # Initilise Card Database
    if not os.path.exists(ALL_CARD_SQL) or os.stat(ALL_CARD_SQL).st_size == 0:
        status = get_card_database(ALL_CARD_ENDPOINT) 
        if status != True:
            print(RED + "ERROR: Failed to initilise card database" + ENDC)
            return 

    # Initilise Set List
    if not os.path.exists(SET_LIST_ENDPOINT) or os.stat(SET_LIST_ENDPOINT).st_size == 0:
        set_list = get_sets_list()
        if set_list == False:
            print(RED + "ERROR: Failed to initilise set data" + ENDC)
            return 
        with open(SET_LIST_ENDPOINT, 'w') as f:
            json.dump(set_list, f, ensure_ascii = False, indent = 4) 

    # Check for updates
    if set_list == None:
       update_cards()

    # Setup Discord Bot
    bot = commands.Bot(command_prefix = '!')

    @bot.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(bot))
        print('Bolt the Bird!'.format(bot))

    @bot.command()
    async def cardtest(ctx, arg):
        await ctx.send(arg) 

    @bot.command()
    async def card(ctx, name):
        image_url = get_card_url(name)
        if image_url == False :
            response = "Countered! Failed to find card"
        else:
            response = image_url 

        await ctx.send(ctx.message.author.mention +  "\r\n" + response)

    @bot.command()
    async def cardupdate(ctx):
        print("Updating Card Database")
        new_sets = update_cards()
        if new_sets:
            await ctx.send(ctx.message.author.mention + " new sets found:\r\n" + str(new_sets)); 
        else:
            await ctx.send(ctx.message.author.mention + " no new sets found")


    with open(TOKEN_FILE, 'r') as f:
        raw_token = f.read()
        token = json.loads(raw_token)

    bot.run(token['DISCORD_TOKEN'])

if __name__ == "__main__":
    main()
