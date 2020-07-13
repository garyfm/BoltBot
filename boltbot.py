#!/bin/python3
import os.path
import json
import argparse as arg
import requests as req
import difflib
from io import BytesIO
from PIL import Image
import discord
from discord.ext import commands

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'

#CONSTS
CARDS_FILE = 'all_cards.json'
TOKEN_FILE = 'token.json'
MTG_API_URL = "https://api.magicthegathering.io/v1/cards"
NUM_OF_MATCHES = 5
MATCH_CUTOFF = 0.2

def get_all_cards():
    query_rsp = req.get(MTG_API_URL)
    if query_rsp.status_code != 200:
        print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
        os.remove(CARDS_FILE)
        return query_rsp.status_code
    page_count = 1

    with open(CARDS_FILE, 'w') as f:
        cards = json.loads(query_rsp.text)
        cards = cards['cards']

        while 'next' in query_rsp.links:
            query_rsp = req.get(query_rsp.links['next']['url'])
            if query_rsp.status_code != 200:
                # TODO If fails delete the file
                print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
                os.remove(CARDS_FILE)
                return query_rsp.status_code
            
            page = json.loads(query_rsp.text)
            page = page['cards']
            cards.extend(page)
            page_count  += 1 
            print(GREEN + "Got Page: " + str(page_count) + ENDC)

        json.dump(cards, f, ensure_ascii = False, indent = 4) 
        
def get_card(query):
    matches = list()
    unique_matches = list() 
    card_names = list() 
    matched_card = None

    with open(CARDS_FILE, 'r') as f:
        raw_cards = f.read()
        cards = json.loads(raw_cards)
    
    for card in cards:
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
        best_matches = difflib.get_close_matches(query.lower(), card_names, NUM_OF_MATCHES, MATCH_CUTOFF) # TODO Use this for getting inital matches ??
        if len(best_matches) == 0:
            print(RED + "Failed to get closed match" + ENDC)
            return
        
        matched_card = [card for card in unique_matches if card['name'] == best_matches[0]][0]
        if matched_card == None:
            print(RED + "Failed to get match in list of best matches" + ENDC)
            return

    return matched_card


def display_card_text(card):
    print(GREEN + "Card Found: " + str(card['name']) + ENDC)
    print(GREEN + "Mana Cost: " + str(card['manaCost']) + ENDC)
    print(GREEN + "Type:  " + str(card['type']) + ENDC)
    print(GREEN + "Text:  " + str(card['text']) + ENDC)
    print(GREEN + "Card URL: " + str(card['imageUrl']) + ENDC + "\r\n")
    return

def display_card_image(card):
    get_image = req.get(card['imageUrl'])
    card_image = Image.open(BytesIO(get_image.content))
    card_image.show()
    return

def main():
    token = None

    print(GREEN + "BoltBot" + ENDC)

    if not os.path.exists(CARDS_FILE):
        # TODO Check if empty
        get_all_cards() 

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

        await ctx.send(response)

    with open(TOKEN_FILE, 'r') as f:
        raw_token = f.read()
        token = json.loads(raw_token)

    bot.run(token['DISCORD_TOKEN'])

if __name__ == "__main__":
    main()