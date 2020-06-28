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
        if len(classes_and_specs[state["class"]]) == 1:
            state["conversation_state"] = "get_first_reserve"
            state["MS"] = classes_and_specs[state["class"]][0]
            state["OS"] = "pvp"
            suffix = f'I have selected your main spec to be {state["MS"]} and your off spec to be {state["OS"]}\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing !prio.\nAlso, order matters!  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\n What is your first reserve?'
        else:
            state["conversation_state"] = "get_main_spec"
            suffix = f"What is your main spec: {' or '.join(classes_and_specs[state['class']])}?"
        reply = f"Welcome {message.content.lower().capitalize()}\n{suffix}"
        return reply, state
    else:
        reply = f"Dear sir or madam, that is not a class in classic wow. Its one of:\n\n{list(classes_and_specs.keys())}.\n\nWhat is your class?"
        return reply, state


def get_main_spec(message: discord.message.Message, state: Dict) -> Tuple[str, Dict]:
    classes_and_specs = get_classes_and_specs()
    if message.content.lower() in classes_and_specs[state["class"]]:
        if len(classes_and_specs[state["class"]]) == 2:
            state["conversation_state"] = "get_first_reserve"
            state["MS"] = message.content.lower()
            state["OS"] = list(
                set(classes_and_specs[state["class"]]) - set([state["MS"]])
            )[0]
            reply = f'Your main spec is set to {state["MS"]} and I have selected your off spec to be {state["OS"]}\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing: !prio.\nAlso, soft reserve order matters.  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\nWhat is your first reserve?'
        else:
            state["conversation_state"] = "get_off_spec"
            state["MS"] = message.content.lower()
            reply = f'Your main spec is set to {state["MS"]}\n What is your off spec?'
    else:
        reply = f'That is not a valid spec for a {state["class"]}, please select one of:\n\n{list(classes_and_specs[state["class"]])}\n\nWhat is your main spec?'
    return reply, state


def get_off_spec(message: discord.message.Message, state: Dict) -> Tuple[str, Dict]:
    classes_and_specs = get_classes_and_specs()
    off_specs = list(set(classes_and_specs[state["class"]]) - set([state["MS"]]))
    if message.content.lower() in off_specs:
        state["conversation_state"] = "get_first_reserve"
        state["OS"] = message.content.lower()
        reply = f'Your off spec is set to {state["OS"]}\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing !prio.\nAlso, order matters!  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\n What is your first reserve?'
    else:
        reply = f'That is not a valid spec for a {state["class"]}, please select one of:\n\n{off_specs}\n\nWhat is your off spec?'
    return reply, state


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
    elif state["conversation_state"] == "get_main_spec":
        reply, state = get_main_spec(message, state)
    elif state["conversation_state"] == "get_off_spec":
        reply, state = get_off_spec(message, state)
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
