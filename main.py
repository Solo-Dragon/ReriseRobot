
import logging
from typing import Tuple, Optional

from telegram import Update, Chat, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
)

import os, logging, asyncio, io, sys, traceback
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from git import Repo
from os import environ, execle
import sys
from git.exc import GitCommandError, InvalidGitRepositoryError
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - [%(levelname)s] - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# --- STARTING BOT --- #
api_id = int(os.environ.get("APP_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("TOKEN")
auth_chts = set(int(x) for x in os.environ.get("AUTH_USERS", "").split())
banned_usrs = set(int(x) for x in os.environ.get("BANNED_USRS", "").split())
client = TelegramClient('client', api_id, api_hash).start(bot_token=bot_token)

# --- BAN --- #
@client.on(events.NewMessage(pattern="/ban"))
async def banE(event):
    k = await event.get_reply_message()
    banned_usrs.append(k.from_id.user_id)
# --- PINGING BOT --- #
@client.on(events.NewMessage(pattern="/ping"))
async def pingE(event):
    start = datetime.now()
    catevent = await event.respond("`!....`")
    await asyncio.sleep(0.3)
    await catevent.edit("`..!..`")
    await asyncio.sleep(0.3)
    await catevent.edit("`....!`")
    end = datetime.now()
    tms = (end - start).microseconds / 1000
    ms = round((tms - 0.6) / 3, 3)
    await catevent.edit(f"Pong!\n`{ms} ms`")
    LOGGER.info("Bot Pinging")

# --- UPDATE BOT --- #
@client.on(events.NewMessage(pattern="/update"))
async def updateE(event):
    if not event.sender_id in auth_chts:
        return
    try:
     repo = Repo()
    except InvalidGitRepositoryError:
     repo = Repo.init()
     origin = repo.create_remote("upstream", "https://github.com/Solo-Dragon/ReriseRobot")
     origin.fetch()
     repo.create_head("master", origin.refs.master)
     repo.heads.master.set_tracking_branch(origin.refs.master)
     repo.heads.master.checkout(True)
    repo.create_remote("upstream", 'https://github.com/Solo-Dragon/ReriseRobot')
    ac_br = repo.active_branch.name
    ups_rem = repo.remote("upstream")
    ups_rem.fetch(ac_br)
    try:
            ups_rem.pull(ac_br)
    except GitCommandError:
            repo.git.reset("--hard", "FETCH_HEAD")
    args = [sys.executable, "main.py"]
    execle(sys.executable, *args, environ)


    
# --- RESTART BOT --- #
@client.on(events.NewMessage(pattern="/restart"))
async def restartE(event):
    if not event.sender_id in auth_chts:
        return
    await event.respond("Restarting")
    executable = sys.executable.replace(" ", "\\ ")
    args = [executable, "main.py"]
    os.execle(executable, *args, os.environ)
    sys.exit(0)
    LOGGER.info("Bot Restarting")

# --- EVAL DEF HERE --- #
async def aexec(code, smessatatus):
    message = event = smessatatus
    p = lambda _x: print(_format.yaml_format(_x))
    reply = await event.get_reply_message()
    exec(
        f"async def __aexec(message, event , reply, client, p, chat): "
        + "".join(f"\n {l}" for l in code.split("\n"))
    )
    return await locals()["__aexec"](
        message, event, reply, message.client, p, message.chat_id
    )
 
# --- EVAL EVENT HERE --- # 
@client.on(events.NewMessage(chats=auth_chts, pattern="/eval ?(.*)"))
async def evalE(event):
    if event.sender_id in banned_usrs:
        return await event.respond("You are Banned!")
    cmd = "".join(event.message.message.split(maxsplit=1)[1:])
    if not cmd:
        return
    cmd = (
        cmd.replace("send_message", "send_message")
        .replace("send_file", "send_file")
        .replace("edit_message", "edit_message")
    )
    catevent = await event.respond("`Running ...`")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    try:
        t = asyncio.create_task(aexec(cmd, event))
        await t
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    final_output = (
        f"**•  Eval : **\n```{cmd}``` \n\n**•  Result : **\n```{evaluation}``` \n"
    )
    try:
        await catevent.edit(final_output)
    except:
        with io.open("output.txt", "w", encoding="utf-8") as k:
            k.write(str(final_output).replace("`", "").replace("*", ""))
            k.close()
        await event.client.send_file(event.chat_id, "output.txt")
        os.remove('output.txt')
        await catevent.delete()
    LOGGER.info(f"Eval: {cmd}\nExcute by: {event.sender_id}")

# --- BASH DEF HERE --- #
async def bash(cmd):

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    err = stderr.decode().strip()
    out = stdout.decode().strip()
    return out, err

# bshhhhhhhhhh
@client.on(events.NewMessage(chats=auth_chts, pattern="/bash ?(.*)"))
async def bashE(event):
    if event.sender_id in banned_usrs:
        return await event.respond("You are Banned!")
    cmd = "".join(event.message.message.split(maxsplit=1)[1:])
    oldmsg = await event.respond("`Running...`")
    out, err = await bash(cmd)
    LOGGER.info(f"Bash: {cmd}\nExcute by: {event.sender_id}")
    if not out:
        out = None
    elif not err:
        err = None
    try:
        await oldmsg.edit(f'**CMD:** `{cmd}`\n**ERROR:**\n `{err}`\n**OUTPUT:**\n `{out}`')
    except:
        with io.open("AriseRobot.txt", "w", encoding="utf-8") as k:
            k.write(f'CMD: {cmd}\nERROR:\n {err}\nOUTPUT:\n {out}')
            k.close()
        await event.client.send_file(event.chat_id, "output.txt", reply_to=event)
        os.remove('AriseRobot.txt')
        await oldmsg.delete()

print('heyaaaaaaaaaaa')
os.system("python -V")
client.run_until_disconnected()


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )

    return was_member, is_member


def track_chats(update: Update, context: CallbackContext) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


def show_chats(update: Update, context: CallbackContext) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    update.effective_message.reply_text(text)


def greet_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        update.effective_chat.send_message(
            f"{member_name} was added by {cause_name}. Welcome!",
            parse_mode=ParseMode.HTML,
        )
    elif was_member and not is_member:
        update.effective_chat.send_message(
            f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("TOKEN")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Keep track of which chats the bot is in
    dispatcher.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))
    dispatcher.add_handler(CommandHandler("show_chats", show_chats))

    # Handle members joining/leaving chats.
    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Start the Bot
    # We pass 'allowed_updates' handle *all* updates including `chat_member` updates
    # To reset this, simply pass `allowed_updates=[]`
    updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if name == "main":
    main()
