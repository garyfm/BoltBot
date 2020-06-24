# BoltBot - WIP
A discord bot for getting MTG Cards in chat

## Usage:
positional arguments:  
query        a query of card names  

optional arguments:  
  -h, --help   show this help message and exit  
  -t, --text   Displays card text  
  -i, --image  Displays card image  
  -e, --exact  Exact match for card name  
  
## WIP Notes

API Used: https://docs.magicthegathering.io/
SDK: Didnt allow for querying local copy of cards

### Completed:
* Gets a list of unquie cards that match the query - DOne
* Can display cards using Pillow  - Done
* Get all cards - Done
* Search local cards - Done

### TODO:
* Imporve searching
* Store unique cards
* Exact matching vs Best fit vs List all match
* Store list of sets
* Check for new cards (Set update)