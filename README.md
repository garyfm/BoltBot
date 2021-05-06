# BoltBot 
A simple discord bot for requesting Magic the Gathering cards in chat.
Uses the https://mtgjson.com/ database and API.

## Dependencies
* python3
* discord py
```
python3 -m pip install -U discord.py
```
* fuzzywuzzy
```
pip3 install fuzzywuzzy
```

## Setup
Create a discord bot account for the bot to use:
https://discordpy.readthedocs.io/en/stable/discord.html

Create a file called token.json. This will be used to store the bots auth token.
```
{
    "DISCORD_TOKEN": "6qrZcUqja7812RVdnEKjpzOL4CvHBFG.12RVdn.15773059ghq9183habn"
}
```
The token can be found on the Discord Developer portal once you create the bot:

![alt text](https://github.com/garyfm/BoltBot/pic/discord_token.png)

## Usage
To get a request a card in chat simple use the `!card` command:
```
!card <card_name>
```
Examples:
```
!card opt
```
![alt text](https://github.com/garyfm/BoltBot/pic/example_opt.png)

```
!card "Lightning Bolt"
```
![alt text](https://github.com/garyfm/BoltBot/pic/example_lightning_bolt.png)

