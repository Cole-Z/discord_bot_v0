import os
import openai
import tiktoken
import discord
from discord.ext import commands

TOKEN = "your bot token"

openai.api_key = 'your api key'

keywords = {
    "warzone": "You are a Z League support rep, we have Warzone 1, but Warzone 2 will be on Z League soon!",
    "verify": "You are an AI assistant specialized in customer support for Z League. Players will need to verify "
              "their ID through persona our third party partner. If they need further assistance, please have the "
              "reach out to us at contact@zleague.gg",
    "banned": "You are a Z League support rep, if a player is banned, please ensure they have filled out the ban "
              "appeal form",
    "delete": "If a user wants to delete their Z League account, advise them to contact the support team to action "
              "this at contact@zleague.gg "
    # Add more keywords and corresponding system messages here
}

max_response_tokens = 250
token_limit = 4096
max_conversation_length = 5
conversation = [{"role": "system", "content": "You are a helpful customer service rep for Z League, an online "
                                              "tournament platform for e-sports and popular video games."}]

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += -1
    num_tokens += 2
    return num_tokens


async def process_message(user_input):
    lower_user_input = user_input.lower()
    matched_keyword = False
    instruction = ""

    for keyword, message in keywords.items():
        if keyword in lower_user_input:
            instruction = message
            matched_keyword = True
            break

    if not matched_keyword:
        instruction = (
            "You are customer support AI for Z League. Answer questions related to Z League and gaming only"
            "If you cannot find the answer, please ask the user to contact us at contact@zleague.gg"
        )

    user_input_with_instruction = f"{instruction} {user_input}"
    conversation.append({"role": "user", "content": user_input_with_instruction})

    if len(conversation) > max_conversation_length:
        conversation.pop(0)

    conv_history_tokens = num_tokens_from_messages(conversation)

    while conv_history_tokens + max_response_tokens >= token_limit:
        del conversation[0]
        conv_history_tokens = num_tokens_from_messages(conversation)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        temperature=0.7,
        max_tokens=max_response_tokens,
    )

    conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
    return response['choices'][0]['message']['content']


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.command()
async def chat(ctx, *, user_input):
    response = await process_message(user_input)
    await ctx.send(response)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.guild is None:
        response = await process_message(message.content)
        await message.channel.send(response)
    else:
        await bot.process_commands(message)


bot.run(TOKEN)
