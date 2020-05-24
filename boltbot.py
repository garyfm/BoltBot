#!/usr/bin/python3
import os.path
import json
import requests as req
from io import BytesIO
from PIL import Image

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'
#CONSTS
TEST_CARD = "Lightning"
#TEST_CARD = "Ponder"
#TEST_CARD = "lightning"
TEST_SET = "IKO"
CARDS_FILE = 'all_cards.json'
MTG_API_URL = "https://api.magicthegathering.io/v1/cards"

# TODO Pass in seach queires as an optional arg
def get_card(query):

    if os.path.exists(CARDS_FILE):
        with open(CARDS_FILE, 'r') as f:
            cards = json.load(f)
    else: 
    # TODO: Define updated function based on local sets vs queired sets
        query_rsp = req.get(MTG_API_URL, params={'name': TEST_CARD})
        # TODO Catch Failure
        with open(CARDS_FILE, 'w') as f:
            cards = json.loads(query_rsp.text)
            json.dump(cards, f, ensure_ascii = False, indent = 4) 

    for i, card in enumerate(cards['cards']):

        # TODO Filter out Dups in json 
        # Keep card instance with has a multiverid 
        if card['name'] == cards['cards'][i - 1]['name']:
              continue;
        
        print(GREEN + "Card Found: " + str(card['name']) + ENDC)
        print(GREEN + "Mana Cost: " + str(card['manaCost']) + ENDC)
        print(GREEN + "Type:  " + str(card['type']) + ENDC)
        print(GREEN + "Text:  " + str(card['text']) + ENDC + "\r\n")
        #print(GREEN + "Card URL: " + str(card['imageUrl']) + ENDC + "\r\n")
        
        

    #get_image = req.get(card.image_url)
    #card_image = Image.open(BytesIO(get_image.content))
    #card_image.show()

def main():
    print(GREEN + "BoltBot" + ENDC)
    #all_cards = Card.all()

    get_card(TEST_CARD)
    
if __name__ == "__main__":
    main()