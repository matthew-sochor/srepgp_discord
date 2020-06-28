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


def get_prio() -> Dict:
    with open(f"prio.yaml", "r") as fp:
        prio = yaml.load(fp, Loader=yaml.FullLoader)
    return prio


def get_whisper(state: Dict) -> str:
    return f'!srepgp:{state["name"]}:{state["class"]}:{state["MS"]}:{state["first_reserve"]}:{state["second_reserve"]}'


def get_player_prio_list(message: discord.message.Message) -> Tuple[list, str]:
    if Path(f"{message.author}_state.yaml").is_file():
        with open(f"{message.author}_state.yaml", "r") as fp:
            state = yaml.load(fp, Loader=yaml.FullLoader)
    else:
        return (
            [],
            "You need to first provide a class and main spec to see your prio list",
        )

    if state["class"] is None:
        return [], "You need to first provide your class to see your prio list"
    elif state["MS"] is None:
        return [], "You need to first provide your main spec to see your prio list"

    prio = get_prio()
    player_prio_list = []
    reply_list = []
    player = f'{state["MS"]}_{state["class"]}'
    for item in prio.keys():
        if "a" in prio[item].keys():
            if player in prio[item]["a"]:
                player_prio_list.append(item)
                reply_list.append(f"(A) {item} - {prio[item]['link']}\n")
        elif "b" in prio[item].keys():
            if player in prio[item]["b"]:
                player_prio_list.append(item)
                reply_list.append(f"(B) {item} - {prio[item]['link']}\n")
        elif "c" in prio[item].keys():
            if player in prio[item]["c"]:
                player_prio_list.append(item)
                reply_list.append(f"(C) {item} - {prio[item]['link']}\n")
    prefix = "Here are the items you can soft reserve.\nNote, even though an item is in this list, you may still not have prio over another class/spec combination in the raid.\nPrio A > B > C\n\n"
    reply = f'{prefix}{"".join(reply_list)}'
    return player_prio_list, reply


def get_first_reserve(
    message: discord.message.Message, state: Dict
) -> Tuple[str, Dict]:
    player_prio_list, _ = get_player_prio_list(message)
    for item in player_prio_list:
        if item.startswith(message.content.lower()):
            state["conversation_state"] = "get_second_reserve"
            state["first_reserve"] = item
            reply = f"I have assigned your first reserve as: {item}\nWhat would you like for your second reserve? You can double reserve if you like"
            return reply, state
    reply = f'I did not find anything that matches and is available for a {state["MS"]} {state["class"]}\nTo see your prio list, type: !prio\nTo chance your character and class/spec, type: !respec'
    return reply, state


def get_second_reserve(
    message: discord.message.Message, state: Dict
) -> Tuple[str, Dict]:
    player_prio_list, _ = get_player_prio_list(message)
    for item in player_prio_list:
        if item.startswith(message.content.lower()):
            state["conversation_state"] = "complete"
            state["second_reserve"] = item
            whisper = get_whisper(state)
            reply = f"I have assigned your second reserve as: {item}\nTo complete your SREPGP configuration, send the following whisper to your raid loot leader in classic WoW:\n\n{whisper}\n\nYou can change your reserve by typing: !softres\nYou can change your character and class/spec by typing: !respec\nYou can always get your whisper string again by typing: !whisper"
            return reply, state
    reply = f'That item is not available for a {state["MS"]} {state["class"]}\nTo see your prio list, type: !prio\nTo chance your character and class/spec, type: !respec'
    return reply, state


def get_complete_message(
    message: discord.message.Message, state: Dict
) -> Tuple[str, Dict]:
    whisper = get_whisper(state)
    reply = f'Hi, you have the following setup:\nCharacter name: {state["name"]}\nClass: {state["class"]}\nMain spec: {state["MS"]}\nOff spec: {state["OS"]}\nFirst reserve: {state["first_reserve"]}\nSecond reserve: {state["second_reserve"]}\n\nYou can change your reserve by typing: !softres\nYou can change your class/spec by typing: !respec\nTo complete your SREPGP configuration, send the following whisper to your raid loot leader in classic WoW:\n\n{whisper}\n\nIf you just want to know what you set up, I can explain more details on SREPGP, just type: !explain'
    return reply, state


def get_name(message: discord.message.Message, state: Dict) -> Tuple[str, Dict]:
    state["conversation_state"] = "get_class"
    state["name"] = message.content
    reply = f'Hi, {state["name"]}.  What is your class?'
    return reply, state


def get_class(message: discord.message.Message, state: Dict) -> Tuple[str, Dict]:
    classes_and_specs = get_classes_and_specs()
    if message.content.lower() in classes_and_specs.keys():
        state["class"] = message.content.lower()
        if len(classes_and_specs[state["class"]]) == 1:
            state["conversation_state"] = "get_first_reserve"
            state["MS"] = classes_and_specs[state["class"]][0]
            state["OS"] = "pvp"
            suffix = f'I have selected your main spec to be {state["MS"]} and your off spec to be {state["OS"]}\nYou can change your character and class/spec by typing: !respec\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing !prio.\nAlso, order matters!  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\n What is your first reserve?'
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
            reply = f'Your main spec is set to {state["MS"]} and I have selected your off spec to be {state["OS"]}\nYou can change your character and class/spec by typing: !respec\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing: !prio.\nAlso, soft reserve order matters.  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\nWhat is your first reserve?'
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
        reply = f'Your off spec is set to {state["OS"]}\nYou can change your character and class/spec by typing: !respec\nTime to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing !prio.\nAlso, order matters!  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\n What is your first reserve?'
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

    if message.content == "!respec":
        state = {
            "conversation_state": "hello",
            "class": None,
            "MS": None,
            "OS": None,
            "first_reserve": None,
            "second_reserve": None,
        }
    elif message.content == "!prio":
        _, reply = get_player_prio_list(message)
        return reply

    elif message.content == "!whisper":
        whisper = get_whisper(state)
        reply = f"To complete your SREPGP configuration, send the following whisper to your raid loot leader in classic WoW:\n\n{whisper}\n\nYou can change your reserve by typing: !softres\nYou can change your character and class/spec by typing: !respec\nYou can always get your whisper string again by typing: !whisper"
        return reply
    elif message.content == "!softres":
        if state["OS"] is None:
            reply = "You first need to have name, class, mainspec and offspec selected.  You can restart this process by typing: !respec"
            return reply
        else:
            state["first_reserve"] = None
            state["second_reserve"] = None
            state["conversation_state"] = "get_first_reserve"
            reply = "Time to select loot to reserve, you can only reserve items you have MS prio for.  You can see your available items by typing !prio.\nAlso, order matters!  So pick your most wanted item as your first reserve.  You can double down and it will increase the chance of you getting the item.\n What is your first reserve?"
            return reply
    elif message.content == "!explain":
        reply = [
            "SREPGP combines the best parts of soft reserve and EP/GP",
            "Players will earn EP and spend GP for items they recieve in a raid",
            "All items cost the same GP whether they are awarded as main spec or off spec",
            "What?  Why you say?  Its to prevent people from 'banking' EP/GP.  You got the item, it costs what it costs.  You can always pass, its up to you!",
            "So whats the soft reserve part?",
            "Great question, well in my experience EP/GP works great for most stuff, but as you get down to needing 1 or 2 competetive items, it starts to suck.  In that case soft reserve just works better.",
            "Soft reserve forces the player to explicitly say their #1 and #2 priorities.  Or they can double down on a single item.",
            "So if you are new to a raid and need lots of items, you will primarily grab things outside of your soft res list and get tons of gear based on your EP/GP ratio.  Yay!",
            "If you have a few items left, soft reserve what you want.  If it drops, the following decision tree will be followed:",
            "",
            "1. Look for players who soft reserved the item, go to step 5",
            "2. Filter them down based on raid loot priority.  Group A has prio over B over C.",
            "3. For everyone left, weight EP/GP ratio by soft reserve.  Double res has a 1.3 multiplier.  First res is a 1.0 multiplier.  Second res is a 0.7 multiplier.",
            "4. Highest EP/GP * soft_res_multiplier wins.  They pay GP and get the item",
            "5. No one has soft reserve, filter raid players down based on Main Spec raid loot priority.  Group A has prio over B over C.",
            "6. Ask people to WANT or PASS an item.  Do EP/GP for everyone that wants",
            "7. If everyone Main spec passes in Group A, go back to step 6 for group B, then group C",
            "8. If all main spec groups pass, go back to step 5 but for offspec",
            "9. If everyone off spec passes.  Open full raid to ROLEPLAY/COSPLAY or PASS.  This is FREE!!!!  Doesn't cost GP",
            "10. If everyone passes just DE the fucking thing." "",
            "Send complaints to chuntttttt#5554",
            "Send compliments to your mom",
        ]
        return "\n".join(reply)

    if state["conversation_state"] == "hello":
        state["conversation_state"] = "get_name"
        reply = "Let's set up your soft reserves.\nWhat is your character's name?"
    elif state["conversation_state"] == "get_name":
        reply, state = get_name(message, state)
    elif state["conversation_state"] == "get_class":
        reply, state = get_class(message, state)
    elif state["conversation_state"] == "get_main_spec":
        reply, state = get_main_spec(message, state)
    elif state["conversation_state"] == "get_off_spec":
        reply, state = get_off_spec(message, state)
    elif state["conversation_state"] == "get_first_reserve":
        reply, state = get_first_reserve(message, state)
    elif state["conversation_state"] == "get_second_reserve":
        reply, state = get_second_reserve(message, state)
    elif state["conversation_state"] == "complete":
        reply, state = get_complete_message(message, state)

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
