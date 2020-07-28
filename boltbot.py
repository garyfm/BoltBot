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
CARDS_FILE = 'atomic_cards.json'
TOKEN_FILE = 'token.json'
SET_LIST_FILE = 'set_list.json'
MTG_BASE_API = "https://mtgjson.com/api/v5/" 
ALL_CARD_ENDPOINT = "AllPrintings.sqlite.zip"
ALL_CARD_SQL = "AllPrintings.sqlite"

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

    # Get all cards to search
    query = "SELECT DISTINCT name FROM cards WHERE multiverseid"
    all_cards = query_mtg_db(query)
    if all_cards == False:
        print(RED + "ERROR: Failed to get cards from DB" + ENDC)
        return

    # Fuzzy Search
    match = process.extract(card_name, all_cards, scorer=fuzz.token_sort_ratio)
    # Construct Image url using the cards multiverse ID
    query = "SELECT multiverseid FROM cards WHERE name=\"" + str(match[0][0]) + "\"AND multiverseid"
    multiverse_id = query_mtg_db(query)
    if multiverse_id == False:
        print(RED + "ERROR: Failed to get multiverse id for matched card" + ENDC)
        return
    image_url = "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=" + str(multiverse_id[0]) + "&type=card"
    
    return image_url

def get_sets_list():
    query_rsp = req.get(MTG_SET_API)
    if query_rsp.status_code != 200:
        print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
        return False

    set_list = json.loads(query_rsp.text)
    # Extract set codes
    set_codes = [mtg_set['code'] for mtg_set in set_list['sets']]
    return set_codes

def update_cards():
    new_sets_list = get_sets_list()

    with open(SET_LIST_FILE, 'r') as f:
        current_sets_list_raw = f.read()
        current_set_list = json.loads(current_sets_list_raw)

    # Check for new sets
    if len(new_sets_list) == len(current_set_list):
        print(GREEN + "No new sets")
        return

    set_difference = list(set(new_sets_list) - set(current_set_list))
    
    # Save new sets to file
    with open(CARDS_FILE, 'r+') as f:
        raw_cards = f.read()
        # TODO: Loading all MTG cards ever 
        # into ram in json is not a good idea!!!!
        cards = json.loads(raw_cards)

    # Get new sets
    for mtg_set in set_difference:
        print(GREEN + "Getting New Set: " + mtg_set + ENDC)
        query_resp = query_cards_api(MTG_BASE_API + "cards?set=" + mtg_set.lower()) 
        if query_resp == False:
            print(RED + "Failed to get cards from " + mtg_set + ENDC)
            return 
        cards.extend(query_resp)
        
    with open(CARDS_FILE, 'w+') as f:
        json.dump(cards, f, ensure_ascii = False, indent = 4) 

    print(GREEN + "Update Cards Complete" + ENDC)
    # Update set list
    with open(SET_LIST_FILE, 'w') as f:
        json.dump(new_sets_list, f, ensure_ascii = False, indent = 4) 

    return

def main():
    token = None
    set_list = None 
    print(GREEN + "BoltBot" + ENDC)

    # Initilise Card Database
    if not os.path.exists(ALL_CARD_SQL) or os.stat(ALL_CARD_SQL).st_size == 0:
        # Get all Cards
        status = get_card_database(ALL_CARD_ENDPOINT) 
        if status != True:
            print(RED + "ERROR: Failed to initilise card database" + ENDC)
            return 

    #if not os.path.exists(SET_LIST_FILE) or os.stat(SET_LIST_FILE).st_size == 0:
    #    # Get list of Sets
    #    set_list = get_sets_list()
    #    if query_resp == False:
    #        print(RED + "Failed to initilise set data" + ENDC)
    #        return 
    #    with open(SET_LIST_FILE, 'w') as f:
    #        json.dump(set_list, f, ensure_ascii = False, indent = 4) 

    ## Check for updates
    #if set_list == None:
    #   update_cards()

    ## Setup Discord Bot
    bot = commands.Bot(command_prefix = '!')

    @bot.event
    async def on_ready():
        print('We have logged in as {0.user}'.format(bot))
        print('Bolt the Bird!'.format(bot))

    @bot.command()
    async def test(ctx, arg):
        await ctx.send(arg) 

    @bot.command()
    async def card(ctx, name):
        image_url = None
        image_url = get_card_url(name)
        if image_url != None:
            response = image_url 
        else:
            response = "Countered! Failed to find card"

        await ctx.send(ctx.message.author.mention +  "\r\n" + response)

    with open(TOKEN_FILE, 'r') as f:
        raw_token = f.read()
        token = json.loads(raw_token)

    bot.run(token['DISCORD_TOKEN'])

if __name__ == "__main__":
    main()