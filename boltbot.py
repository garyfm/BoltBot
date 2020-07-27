#!/usr/bin/python3
import os.path
import json
import requests as req
import difflib
import discord
from discord.ext import commands
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'

#CONSTS
CARDS_FILE = 'all_cards.json'
TOKEN_FILE = 'token.json'
SET_LIST_FILE = 'set_list.json'
MTG_BASE_API = "https://api.magicthegathering.io/v1/"
MTG_CARD_API = "https://api.magicthegathering.io/v1/cards"
MTG_SET_API = "https://api.magicthegathering.io/v1/sets"
NUM_OF_MATCHES = 5
MATCH_CUTOFF = 0.2

def query_cards_api(query):
    print(GREEN + "Query: " + query + ENDC)
    query_rsp = req.get(query)
    if query_rsp.status_code != 200:
        print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
        return False

    print(GREEN + "\tGot Page: 1"  + ENDC)
    page_count = 1

    cards = json.loads(query_rsp.text)
    cards = cards['cards']

    while 'next' in query_rsp.links:
        query_rsp = req.get(query_rsp.links['next']['url'])
        if query_rsp.status_code != 200:
            # TODO If fails delete the file
            print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
            return False
        
        page = json.loads(query_rsp.text)
        page = page['cards']
        cards.extend(page)
        page_count  += 1 
        print(GREEN + "\tGot Page: " + str(page_count) + ENDC)
    print(GREEN + "Query Complete" + ENDC)
    return cards
            
def get_card(query):
    matches = list()
    unique_matches = list() 
    card_names = list() 
    matched_card = None

    with open(CARDS_FILE, 'r') as f:
        raw_cards = f.read()
        # TODO: Loading all MTG cards ever 
        # into ram in json is not a good idea!!!!
        cards = json.loads(raw_cards)
    
    for card in cards:
        # TODO: Would it be quiker to get all matches then check for an exact match ?
        # It would half the checks
        if query.lower() == card['name'].lower():
            matched_card = card
            break
        elif query.lower() in card['name'].lower(): 
            matches.append(card)
            
    # No exact match found, Get closet match 
    if matched_card == None:
        # Filter out Dups in json 
        # Keep card instance with has a multiverid 
        unique_matches = {each['name'] : each for each in matches if "multiverseid" in each}.values() # TODO Filter Dups from card file ??
        print(GREEN + "Matches Found: " + str(len(unique_matches)) + ENDC)
        if len(unique_matches) == 0:
            print(RED + "Failed to get unique match" + ENDC)
            return

        card_names = [card['name'] for card in unique_matches]
        best_matches = process.extract(query.lower(), card_names) # TODO Use this for getting inital matches ??
        if len(best_matches) == 0:
            print(RED + "Failed to get closed match" + ENDC)
            return
            
        matched_card = [card for card in unique_matches if card['name'] == best_matches[0][0]][0]
        if matched_card == None:
            print(RED + "Failed to get match in list of best matches" + ENDC)
            return

    return matched_card

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

    # Setup Card Data
    if not os.path.exists(CARDS_FILE) or os.stat(CARDS_FILE).st_size == 0:
        # Get all Cards
        query_resp = query_cards_api(MTG_CARD_API) 
        if query_resp == False:
            print(RED + "Failed to initilise card data" + ENDC)
            return 
        with open(CARDS_FILE, 'w') as f:
            json.dump(query_resp, f, ensure_ascii = False, indent = 4) 

    if not os.path.exists(SET_LIST_FILE) or os.stat(SET_LIST_FILE).st_size == 0:
        # Get list of Sets
        set_list = get_sets_list()
        if query_resp == False:
            print(RED + "Failed to initilise set data" + ENDC)
            return 
        with open(SET_LIST_FILE, 'w') as f:
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
    async def test(ctx, arg):
        await ctx.send(arg) 

    @bot.command()
    async def card(ctx, query):
        card = get_card(query)
        if card != None:
            response = card['imageUrl']
        else:
            response = "Countered! Failed to find card"
        await ctx.send(ctx.message.author.mention +  "\r\n" + response)

    with open(TOKEN_FILE, 'r') as f:
        raw_token = f.read()
        token = json.loads(raw_token)

    bot.run(token['DISCORD_TOKEN'])

if __name__ == "__main__":
    main()