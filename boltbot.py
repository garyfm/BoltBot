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

def get_all_cards():
    # TODO: Define updated function based on local sets vs queired sets
    # Get all cards
    query_rsp = req.get(MTG_API_URL, params={'name':"Lightning"})
    if query_rsp.status_code != 200:
        print(RED + "ERROR: Query Failed HTTP Status Code: " + query_rsp.status_code + ENDC)
        return query_rsp.status_code

    # Save Cards 
    with open(CARDS_FILE, 'w') as f:
        cards = json.loads(query_rsp.text)
        json.dump(cards, f, ensure_ascii = False, indent = 4) 

def get_card(query, args):
    with open(CARDS_FILE, 'r') as f:
        raw_cards = f.read()
        cards = json.loads(raw_cards)
    
    matches = list()
    for card in cards['cards']:
        if query in card['name']: 
            matches.append(card)

    # Filter out Dups in json 
    # Keep card instance with has a multiverid 
    unique_cards = {each['name'] : each for each in matches if "multiverseid" in each}.values()
    print(GREEN + "Found " + str(len(unique_cards)) + " unique matches" + ENDC)
    for i, card in enumerate(unique_cards):
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
        get_all_cards() 

    get_card(args.query, args)
    


if __name__ == "__main__":
    main()