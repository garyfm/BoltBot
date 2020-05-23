#!/usr/bin/python3
import os.path
import requests as req
import json
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
    card = Card.where(set='m11').where(name=TEST_CARD).all()
    print(GREEN + "Card Found: " + str(card[0].name))
    print(GREEN + "Mana Cost: " + str(card[0].mana_cost))
    print(GREEN + "Type:  " + str(card[0].type))
    print(GREEN + "Text:  " + str(card[0].text))

if __name__ == "__main__":
    main()