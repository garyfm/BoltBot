#!/bin/python3
import os.path
import json
import argparse as arg
import requests as req
import difflib
from io import BytesIO
from PIL import Image

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'
#CONSTS
CARDS_FILE = 'all_cards.json'
MTG_API_URL = "https://api.magicthegathering.io/v1/cards"
NUM_OF_MATCHES = 5
MATCH_CUTOFF = 0.2

# TODO: Define updated function based on local sets vs queired sets

def get_all_cards():
    #query_rsp = req.get(MTG_API_URL, params={'name':"Lightning"})
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
        
def get_card(query, args):
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
        best_matches = difflib.get_close_matches(query.lower(), card_names, NUM_OF_MATCHES, MATCH_CUTOFF)
        if len(best_matches) == 0:
            print(RED + "Failed to get closed match" + ENDC)
            return
        
        matched_card =  [card for card in unique_matches if card['name'] == best_matches[0]][0]
        if matched_card == None:
            print(RED + "Failed to get match in list of best matches" + ENDC)
            return

        if len(best_matches) > 1:
            print("Best 5 matches: ")
            for name in best_matches:
                print(name)

    # Display matched card 
    if args.text:
        display_card_text(matched_card)
    if args.image:
        display_card_image(matched_card)

    return

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
    print(GREEN + "BoltBot" + ENDC)

    parser = arg.ArgumentParser(description='BoltBot: MTG Card Search Bot')
    parser.add_argument('query',help='a query of card names')
    parser.add_argument('-t', '--text', help='Displays card text', action="store_true")
    parser.add_argument('-i', '--image', help='Displays card image', action="store_true")
    parser.add_argument('-e', '--exact', help='Exact match for card name', action="store_true")

    args = parser.parse_args()

    if not os.path.exists(CARDS_FILE):
        # TODO Check if empty
        get_all_cards() 

    get_card(args.query, args)
    


if __name__ == "__main__":
    main()