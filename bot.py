#!/usr/bin/env python3
"Bot Handler"
import logging
import random
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, filters, \
        PicklePersistence
import config

from boards import BOARDS
from sal import Board, NotTurnError


def start(update, context):
    "/start"
    if update.effective_chat.id > 0:
        message = ("Single player is not supported at the moment. "
                   "Send /newgame in a group to start the game.")
    else:
        message = "Send /newgame to start the game."
    context.bot.send_message(update.effective_chat.id, message)


def newgame(update, context):
    "/newgame"
    if update.effective_chat.id > 0:
        context.bot.send_message(update.effective_chat.id, "Run in a group!")
        return

    if "game" in context.chat_data:
        context.bot.send_message(update.effective_chat.id, "Game in progress!")
        return

    if "new_turn_on_six" not in context.chat_data:
        context.chat_data["new_turn_on_six"] = False

    board = random.choice(BOARDS)
    game = context.chat_data["game"] = Board(
        board.data,
        board.image,
        new_turn_on_six=context.chat_data["new_turn_on_six"]
    )
    context.chat_data["admin"] = update.effective_user.id
    caption = (f"Starting new game with board {board.name}. Join via /join. "
               "Configure via /settings.")
    context.bot.send_photo(update.effective_chat.id, game.draw(),
                           caption=caption)


def join(update, context):
    "/join"
    if "game" not in context.chat_data:
        context.bot.send_message(update.effective_chat.id,
                                 "No game in progress.")
        return

    game = context.chat_data["game"]
    first_name = update.effective_user.first_name
    color = game.add_player(update.effective_user.id, first_name)
    message = f"{first_name} joined with {color}!"
    context.bot.send_message(update.effective_chat.id, message)


def begin(update, context):
    "/begin"
    if "game" not in context.chat_data:
        context.bot.send_message(update.effective_chat.id,
                                 "No game in progress.")
        return

    game = context.chat_data["game"]
    context.chat_data["begin"] = True
    player_name = game.turn["name"]
    message = f"Game has begun! Current turn: {player_name}"
    context.bot.send_message(update.effective_chat.id, message)


def status(update, context):
    "/status"
    if "game" not in context.chat_data:
        context.bot.send_message(update.effective_chat.id,
                                 "No game in progress.")
        return

    game = context.chat_data["game"]
    message = "List of players: \n\n"
    for player in game.players:
        if game.turn == player:
            message += "* "
        else:
            message += "   "
        message += (f"{player['position']}: {player['name']} "
                    f"({player['color'].name} {player['shape'].name})\n")
    context.bot.send_message(update.effective_chat.id, message)


def settings(update, context):
    "/settings"
    message = f"""
Another turn if the player rolls 6

Status: {"Enabled" if context.chat_data.get("new_turn_on_six", False) else "Disabled"}
Enable: /enable_6
Disable: /disable_6


Delete previous boards when new board is sent

Status: {"Enabled" if context.chat_data.get("delete_boards", True) else "Disabled"}
Enable: /enable_delete
Disable: /disable_delete
    """
    context.bot.send_message(update.effective_chat.id, message)


def update_setting(update, context, setting, state, attribute=None):
    """
    /enable_* and /disable_*
    Parameters:
        update: telegram.Update
        context: telegram.ext.CallbackContext
        setting: str, Key to be modified
        state: any, Value to be set
        attribute: None | str, attribute to be updated on Board class
    """
    if update.effective_user.id != context.chat_data.get("admin", 0):
        message = "Only the game creator can configure the settings."
    else:
        message = "Enabled!" if state else "Disabled!"
        context.chat_data[setting] = state
        if attribute is not None:
            if "game" in context.chat_data:
                game = context.chat_data["game"]
                setattr(game, attribute, state)
    context.bot.send_message(update.effective_chat.id, message)


def kill(update, context):
    "/kill"
    if "game" not in context.chat_data:
        context.bot.send_message(update.effective_chat.id,
                                 "No game in progress.")
        return
    if update.effective_user.id != context.chat_data["admin"]:
        context.bot.send_message(update.effective_chat.id,
                                 "Only game creator can kill the game.")
        return

    del context.chat_data["game"]
    del context.chat_data["admin"]
    context.chat_data["begin"] = False
    context.bot.send_message(update.effective_chat.id, "Killed!")


def dice(update, context):
    "Handles dice being thrown"
    if "game" not in context.chat_data:
        return

    if update.message.forward_date is not None:
        return

    if not context.chat_data.get("begin", False):
        context.bot.send_message(update.effective_chat.id,
                                 "Game has not started yet.")
        return

    game = context.chat_data["game"]
    pid = update.effective_user.id

    if pid != game.turn["pid"]:
        return

    steps = update.message.dice.value
    # Wait for dice to roll on client side
    time.sleep(3.9)
    try:
        player = game.turn
        final_position, direction = game.move(pid, steps, check_turn=True)
    except NotTurnError:
        return
    img = game.draw()
    if final_position == 100:
        message = f"{player['name']} ({player['color'].name}) won! Game ended."
        del context.chat_data["game"]
        context.chat_data["begin"] = False
        del context.chat_data["admin"]
    elif direction == 1:
        message = (f"{player['name']} grabbed a ladder and reached "
                   f"{final_position}.")
    elif direction == 0:
        message = f"{player['name']} reached {final_position}."
    elif direction == -1:
        message = (f"{player['name']} was dragged down by a snake and reached "
                   f"{final_position}.")

    if final_position != 100:
        next_player = game.turn
        message += f" Current turn: {next_player['name']}"
    upd = context.bot.send_photo(update.effective_chat.id, img, caption=message)
    if context.chat_data.get("delete_boards", True):
        if "last_message" in context.chat_data:
            context.bot.delete_message(update.effective_chat.id,
                                       context.chat_data["last_message"])
    context.chat_data["last_message"] = upd.message_id


def main():
    "Main function"
    logging.basicConfig(level=logging.INFO)
    if config.PERSIST:
        persist = PicklePersistence(config.PERSIST_FILENAME)
    else:
        persist = None
    updater = Updater(token=config.API_KEY, use_context=True, persistence=persist)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler("start", start)
    newgame_handler = CommandHandler("newgame", newgame)
    join_handler = CommandHandler("join", join)
    begin_handler = CommandHandler("begin", begin)
    status_handler = CommandHandler("status", status)
    settings_handler = CommandHandler("settings", settings)
    enable_6_handler = CommandHandler(
        "enable_6",
        lambda x, y: update_setting(x, y, "new_turn_on_six", True,
                                    "new_turn_on_six")
    )
    disable_6_handler = CommandHandler(
        "disable_6",
        lambda x, y: update_setting(x, y, "new_turn_on_six", False,
                                    "new_turn_on_six")
    )
    enable_delete_handler = CommandHandler(
        "enable_delete",
        lambda x, y: update_setting(x, y, "delete_boards", True)
    )
    disable_delete_handler = CommandHandler(
        "disable_delete",
        lambda x, y: update_setting(x, y, "delete_boards", False)
    )
    kill_handler = CommandHandler("kill", kill)
    dice_handler = MessageHandler(filters.Filters.dice, dice)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(newgame_handler)
    dispatcher.add_handler(join_handler)
    dispatcher.add_handler(begin_handler)
    dispatcher.add_handler(status_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(kill_handler)
    dispatcher.add_handler(dice_handler)
    dispatcher.add_handler(enable_6_handler)
    dispatcher.add_handler(disable_6_handler)
    dispatcher.add_handler(enable_delete_handler)
    dispatcher.add_handler(disable_delete_handler)
    updater.start_polling()

if __name__ == "__main__":
    main()
