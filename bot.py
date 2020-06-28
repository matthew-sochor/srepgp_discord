# bot.py
import os
from pathlib import Path
import discord
import yaml
from typing import Dict, Tuple

with open(".secrets.yaml", "r") as fp:
    env = yaml.load(fp, Loader=yaml.FullLoader)

TOKEN = env["discord_token"]

client = discord.Client()


def get_classes_and_specs() -> Dict:
    return {
        "druid": ["resto", "bear", "kitten", "boomie"],
        "warrior": ["tank", "dps"],
        "priest": ["heals", "shadow"],
        "hunter": ["dps"],
        "shaman": ["resto", "pewpew"],
        "paladin": ["heals", "tank", "dps"],
        "rogue": ["dps"],
        "warlock": ["dps"],
        "mage": ["dps"],
    }


def get_class(message: discord.message.Message, state: Dict) -> Tuple[str, Dict]:
    classes_and_specs = get_classes_and_specs()
    if message.content.lower() in classes_and_specs.keys():
        state["class"] = message.content.lower()
        state["conversation_state"] = "get_main_spec"
        reply = (
            f"Welcome {message.content.lower().capitalize()}\nWhat is your main spec?"
        )
        return reply, state
    else:
        reply = f"Dear sir or madam, that is not a class in classic wow. Its one of:\n\n {list(classes_and_specs.keys())}.\n\nWhat is your class?"
        return reply, state


def get_

def get_reply(message: discord.message.Message) -> str:

    if Path(f"{message.author}_state.yaml").is_file():
        with open(f"{message.author}_state.yaml", "r") as fp:
            state = yaml.load(fp, Loader=yaml.FullLoader)
    else:
        state = {
            "conversation_state": "hello",
            "class": None,
            "MS": None,
            "OS": None,
            "first_reserve": None,
            "second_reserve": None,
        }

    if state["conversation_state"] == "hello":
        state["conversation_state"] = "get_class"
        reply = "Let's set up your soft reserves.\nWhat is your class?"
    elif state["conversation_state"] == "get_class":
        reply, state = get_class(message, state)
    else:
        reply = "tbd"

    with open(f"{message.author}_state.yaml", "w") as fp:
        yaml.dump(state, fp)
    return reply


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.message.Message) -> None:

    if message.author == client.user:
        return

    if message.content.lower().startswith("!srepgp") or isinstance(
        message.channel, discord.channel.DMChannel
    ):
        dm = get_reply(message)
        await message.author.send(dm)


client.run(TOKEN)
