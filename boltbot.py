#!/bin/python3
import os.path
import json
import argparse as arg
import requests as req
from io import BytesIO
from PIL import Image

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'
#CONSTS
CARDS_FILE = 'all_cards.json'
MTG_API_URL = "https://api.magicthegathering.io/v1/cards"

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
    exact_match = None

    with open(CARDS_FILE, 'r') as f:
        raw_cards = f.read()
        cards = json.loads(raw_cards)
    
    
    for card in cards:
        if query.lower() == card['name'].lower():
            exact_match = card
            break
        elif query.lower() in card['name'].lower(): 
            matches.append(card)
            
    # Filter out Dups in json 
    # Keep card instance with has a multiverid 
    if exact_match == None:
        unique_matches = {each['name'] : each for each in matches if "multiverseid" in each}.values()
        print(GREEN + "Found " + str(len(unique_matches)) + " unique matches" + ENDC)
    else:
        unique_matches.append(exact_match)

    for card in unique_matches:
        if args.text:
            display_card_text(card)
        if args.image:
            display_card_image(card)

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