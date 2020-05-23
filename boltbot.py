#!/usr/bin/python3
import os.path
import requests as req
import json
from io import BytesIO
from PIL import Image

from mtgsdk import Card
from mtgsdk import Set

# Colors
RED = '\033[91m'
GREEN = '\033[92m'
ENDC = '\033[0m'
#CONSTS
TEST_CARD = "Lightning Bolt"
TEST_SET = "IKO"

def main():
    print(GREEN + "BoltBot" + ENDC)
    #all_cards = Card.all()

    card = Card.where(name=TEST_CARD).all()

    print(GREEN + "Card Found: " + str(card[0].name))
    print(GREEN + "Mana Cost: " + str(card[0].mana_cost))
    print(GREEN + "Type:  " + str(card[0].type))
    print(GREEN + "Text:  " + str(card[0].text))
    print(GREEN + "Card URL: " + str(card[0].image_url))
    
    get_image = req.get(card[0].image_url)
    card_image = Image.open(BytesIO(get_image.content))
    card_image.show()

if __name__ == "__main__":
    main()