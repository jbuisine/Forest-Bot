# bot.py
import os
import datetime
import random
import requests

import pymongo
import discord
import asyncio
import time
from dotenv import load_dotenv


# db connection
from pymongo import MongoClient
import pymongo

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

connection = MongoClient()
db = connection['forest-db']

google_scholar_url = "https://scholar.google.fr/scholar?hl=fr&as_sdt=0,5&scisbd=1&q=perception+in+computer+graphics"
newsletter_collection = db['forest-newsletter']
articles_collection = db['forest-articles']

embed_color = 0x339966
n_keywords = 10


@client.event
async def on_message(message):

    # avoid message from
    if message.author == client.user:
        return

#     sentences_list = newsletter_collection.find()
#     n_sentences = sentences_list.count()

#     user_creator = discord.utils.find(lambda m: m.id == int(CREATOR_ID), client.users)

#     # send messaged if mentionned or with probability
#     if discord.utils.find(lambda m: m.id == int(client.user.id), message.mentions) or random.uniform(0, 1) < 0.02:

#         if n_sentences == 0:
#             embed = discord.Embed(
#                 title=':warning: No sentences added :warning:', 
#                 description='It seems I have no knowledge!', 
#                 color=embed_color)
#             embed.add_field(
#                 name=":white_small_square: If you want to add me knowledge (please not stupid thing), please use", 
#                 value="`--waiter-add {{your-sentence}}`", 
#                 inline=False)
#             embed.add_field(
#                 name="\t__Example:__", 
#                 value="\t`--waiter-add The sky is blue!`",
#                 inline=False)
#             embed.set_footer(text="Do not hesitate to contact {0} for further information".format(str(user_creator))) 

#             await message.channel.send(embed=embed)

#         else:
#             n_rand = random.randrange(n_sentences)

#             print('Waiter says', sentences_list[n_rand]['sentence'])

#             embed = discord.Embed(
#                 description="<@{0}>, {1}".format(message.author.id, sentences_list[n_rand]['sentence']), 
#                 color=embed_color)

#             await message.channel.send(embed=embed)

#     # add new sentence for the bot
#     if message.content.startswith('--waiter-add'):

#         sentence = message.content.replace('--waiter-add', '').strip()

#         print(sentence)

#         # check if sentence is correct
#         if len(sentence) > 0:
            
#             print('here')
#             last_sentence = sentences_collection.find_one(
#                     #{'doc_id': doc_id},
#                     sort=[( '_id', pymongo.DESCENDING )]
#                 )

#             if last_sentence:
#                 new_sentence_id = int(last_sentence['sentence_id']) + 1
#             else:
#                 new_sentence_id = 0

#             print(new_sentence_id)

#             sentences_collection.insert_one({
#                 'sentence_id': new_sentence_id, 
#                 'sentence': str(sentence), 
#                 'added_by': message.author.id,
#                 'added_by_username': str(message.author)})

#             embed = discord.Embed(
#                 title=':ballot_box_with_check: Sentence has been added :ballot_box_with_check:', 
#                 description='I now have more knowledge thanks to {0}'.format(str(message.author)), 
#                 color=embed_color)
#             embed.add_field(
#                 name="Sentence added:", 
#                 value=sentence, 
#                 inline=False)
#             embed.set_footer(text="Thanks a lot for your contributions!") 
        
#         else:

#             embed = discord.Embed(
#                 title=':warning: Unvalid use of command :warning:', 
#                 description='It seems your sentence is not valid', 
#                 color=embed_color)
#             embed.add_field(
#                 name=":white_small_square: If you want to add me knowledge (please not stupid thing), please use", 
#                 value="`--waiter-add {{your-sentence}}`", 
#                 inline=False)
#             embed.add_field(
#                 name="\t__Example:__", 
#                 value="\t`--waiter-add The sky is blue!`",
#                 inline=False)
#             embed.set_footer(text="Do not hesitate to contact {0} for further information".format(str(user_creator))) 

#         await message.channel.send(embed=embed)


#     # print all available sentence of the bot
#     if message.content.startswith('--waiter-list'):

#         if message.author.id == int(CREATOR_ID):

#             embed = discord.Embed(
#                 title=':ledger: Waiter-bot dataset :ledger:', 
#                 description='All available sentence',
#                 color=embed_color)

#             sentences = sentences_list

#             if n_sentences > n_display_sentences:
#                 sentences = sentences.sort('_id', -1).limit(n_display_sentences)
            
#             for sentence in sentences:
#                 embed.add_field(
#                     name="`{0}`, sentence added by {1}".format(sentence['sentence_id'], sentence['added_by_username']), 
#                     value="{0}".format(sentence['sentence']),
#                     inline=False)

#             await message.channel.send(embed=embed)
    
#     if message.content.startswith('--forest-show'):

#         response = requests.get(google_scholar_url).json()

#         embed = discord.Embed(
#             title='Why Chuck Norris is the best ?', 
#             description=response['value'], 
#             color=embed_color)
#         embed.set_thumbnail(url=response['icon_url'])

#         await message.channel.send(embed=embed)
        
#      # print all available sentence of the bot
#     if message.content.startswith('--waiter-delete'):

#             sentence_elements = message.content.lower().split(' ')

#             if len(sentence_elements) > 1 and len(sentence_elements) <= 2:
                
#                 sentence_id = sentence_elements[1]
#                 sentence_obj= sentences_collection.find_one({'sentence_id': int(sentence_id)})

#                 # if object exists we can remove it
#                 if sentence_obj:
                    
#                     sentences_collection.delete_one({'sentence_id': int(sentence_id)})

#                     embed = discord.Embed(
#                         title=':ballot_box_with_check: Sentence has been deleted :ballot_box_with_check:', 
#                         description='Sentence with :id: {0} removed from my knowledge'.format(str(sentence_id)), 
#                         color=embed_color)

#                 else:
#                     embed = discord.Embed(
#                         title=':warning: Sentence not found :warning:', 
#                         description='It seems sentence with :id: {0} does not exist'.format(str(sentence_id)), 
#                         color=embed_color)

#             else:

#                 # sentence id not correct
#                 embed = discord.Embed(
#                     title=':warning: Unvalid use of command :warning:', 
#                     description='It seems your sentence :id: is not valid', 
#                     color=embed_color)
#                 embed.add_field(
#                     name=":white_small_square: If you want to delete a sentence, please use correctly:", 
#                     value="`--waiter-delete {{sentence-id}}`", 
#                     inline=False)
#                 embed.add_field(
#                     name="\t__Example:__", 
#                     value="\t`--waiter-delete 42`",
#                     inline=False)

#             await message.channel.send(embed=embed)

    print(f'{message.content} from {message.author.name}')

    if message.content.startswith('--forest-add'):
        pass


    if message.content == '--forest-disable':
        
        channel_newsletter = newsletter_collection.find_one(
            {'channel_id': message.channel.id},
            sort=[( '_id', pymongo.DESCENDING )]
        )

        if channel_newsletter is None:

            embed = discord.Embed(
                title=':no_entry: There is no newsletter for this channel :no_entry:', 
                description='You can add newsletter whenever you want using `--forest-enable`', 
                color=embed_color)

        else:
            # Using update_one() method for single 
            newsletter_collection.update_one(
                { 'channel_id': 'message.channel.id' }, 
                { "$set": { 'activated': False } }
            )

            embed = discord.Embed(
                title=':lock: Newsletter has been deactivated for this channel :lock:', 
                description='You can reactivate it whenever you want using `--forest-enable`', 
                color=embed_color)

        await message.channel.send(embed=embed)

    if message.content == '--forest-enable':
        
        channel_newsletter = newsletter_collection.find_one(
                    {'channel_id': message.channel.id},
                    sort=[( '_id', pymongo.DESCENDING )]
                )

        if channel_newsletter is None:
            
            newsletter_collection.insert_one({
                'channel_id': message.channel.id,
                'keywords': [],
                'activated': True
                })

            embed = discord.Embed(
                title=':incoming_envelope: This channel has now a newsletter :incoming_envelope:', 
                description='You can now add your keywords using `--forest-add`', 
                color=embed_color)
        else:
            embed = discord.Embed(
                title=':incoming_envelope: Newsletter has been reactivated for this channel :incoming_envelope:', 
                description='You can now update your keywords using `--forest-add` or `--forest-remove`', 
                color=embed_color)

        await message.channel.send(embed=embed)

     # send all available commands of forest bot
    if message.content == '--forest-help':

        embed = discord.Embed(
            title=':ledger: Forest-bot documentation :ledger:', 
            description=':computer: All available commands :computer:',
            color=embed_color)

        embed.add_field(
            name="`--forest-enable`",
            value=":white_small_square: Allows the bot to provide a newsletter to the current channel",
            inline=False)

        embed.add_field(
            name="`--forest-disable`",
            value=":white_small_square: Disables newsletter of the current channel if exists",
            inline=False)

        # embed.add_field(
        #     name="\t__Example:__", 
        #     value="\t`--waiter-add Something not stupid please!`",
        #     inline=False)
        # embed.add_field(
        #     value="`--waiter-chuck-fact`",
        #     name=":white_small_square: True fact of Chuck Norris displayed!",
        #     inline=False)

        embed.add_field(
            name="`--forest-help`",
            value=":white_small_square: Gives information about all commands", 
            inline=False)
            
        embed.set_footer(text="That was a pleasure!") #if you like to

        await message.channel.send(embed=embed)


@client.event
async def on_ready():
    
    print(
        f'{client.user} is connected\n'
    )
        
client.run(TOKEN)