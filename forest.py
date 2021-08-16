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
from bs4 import BeautifulSoup
import urllib.request

# db connection
from pymongo import MongoClient
import pymongo

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

connection = MongoClient()
db = connection['forest-db']

google_scholar_url = "https://scholar.google.fr/scholar?hl=fr&as_sdt=0,5&scisbd=2&q="

newsletter_collection = db['forest-newsletter']

embed_color = 0x339966
n_keywords = 10


@client.event
async def on_message(message):

    # avoid message from
    if message.author == client.user:
        return

    if message.content == '--forest-search':
        
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
            # get current keywords from channel
            current_keywords = channel_newsletter['keywords']
            query = '+'.join(current_keywords).replace(' ', '+')

            headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36", 'referer':'https://www.google.com/'}
            req = urllib.request.Request(url=google_scholar_url + query, headers=headers)
            read_content = urllib.request.urlopen(req).read()

            soup = BeautifulSoup(read_content,'html.parser')

            gs_results = soup.find_all('div', class_='gs_ri')

            # TODO: check if article is present or not and display it consequently
            for res in gs_results:
                article_data = {}

                link = res.find('h3').find('a')
                article_data['id'] = link['id']
                article_data['href'] = link['href']
                article_data['title'] = link.get_text()

                article_data['authors'] = res.find('div', class_='gs_a').get_text()
                ndays_text = res.find('span', class_='gs_age').get_text()
                ndays = [int(i) for i in ndays_text.split() if i.isdigit() ][0]
                print(article_data)

                # TODO: compute publication date
                print(ndays)
                


    if message.content.startswith('--forest-list'):

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

            # get current keywords from channel
            current_keywords = channel_newsletter['keywords']

            message_data = ''

            for k in current_keywords:
                message_data += f'- {k}\n'

            embed = discord.Embed(
                title=':scroll: Keywords list :scroll:', 
                description=message_data, 
                color=embed_color)

            embed.set_footer(text=f"Your newsletter is composed of {len(current_keywords)} keywords")

            await message.channel.send(embed=embed)

    if message.content.startswith('--forest-add'):
        
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

            # get current keywords from channel
            current_keywords = channel_newsletter['keywords']

            # get new expected keywords
            new_keywords = [ k.strip() for k in message.content.replace('--forest-add', '').replace('"', '').split(';') ]

            # merged keywords
            merged_keywords = list(set(current_keywords + new_keywords))
            restricted_list = merged_keywords[:10]
            
            newsletter_collection.update_one(
                { '_id': channel_newsletter['_id'] }, 
                { 
                    '$set': { 'keywords': restricted_list } 
                },
                upsert=False
            )

            message_data = ''

            for k in restricted_list:
                message_data += f'- {k}\n'

            if len(merged_keywords) > 10:

                embed = discord.Embed(
                title=':abacus: Keywords has been added but also truncated :abacus:', 
                description=f'Number of keywords is limited to 10, some were not taken into consideration:\n{message_data}', 
                color=embed_color)
            else:
                embed = discord.Embed(
                title=':white_check_mark: Keywords has been added :white_check_mark:', 
                description=message_data, 
                color=embed_color)

                embed.set_footer(text=f"Your newsletter is now composed of {len(restricted_list)} keywords")

            await message.channel.send(embed=embed)

    if message.content.startswith('--forest-remove'):
        
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
            # get current keywords from channel
            current_keywords = channel_newsletter['keywords']

            # get expected keywords to remove
            remove_keywords = [ k.strip() for k in message.content.replace('--forest-remove', '').replace('"', '').split(';') ]

            filtered_keywords = list(filter(lambda i: i not in remove_keywords, current_keywords))

            newsletter_collection.update_one(
                { '_id': channel_newsletter['_id'] }, 
                { 
                    '$set': { 'keywords': filtered_keywords } 
                },
                upsert=False
            )

            message_data = ''

            for k in filtered_keywords:
                message_data += f'- {k}\n'

            embed = discord.Embed(
                title=':white_check_mark: Keywords has been updated :white_check_mark:', 
                description=message_data, 
                color=embed_color)

            embed.set_footer(text=f"Your newsletter is now composed of {len(filtered_keywords)} keywords")
                
            await message.channel.send(embed=embed)

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
            newsletter_collection.update_one(
                { '_id': channel_newsletter['_id'] }, 
                { 
                    '$set': { 'activated': False } 
                },
                upsert=False
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
                    'articles': [],
                    'activated': True
                })

            embed = discord.Embed(
                title=':incoming_envelope: This channel has now a newsletter :incoming_envelope:', 
                description='You can now add your keywords using `--forest-add`', 
                color=embed_color)
        else:

            newsletter_collection.update_one(
                { '_id': channel_newsletter['_id'] }, 
                { 
                    '$set': { 'activated': True } 
                },
                upsert=False
            )

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

        embed.add_field(
            name="`--forest-add`",
            value=":white_small_square: Add if not exists specific keywords for current newsletter",
            inline=False)

        embed.add_field(
            name="\t__Example:__", 
            value="\t`--forest-add \"computer graphics;machine learning;perception\"`",
            inline=False)

        embed.add_field(
            name="`--forest-remove`",
            value=":white_small_square: Removes specific keyword for current newsletter",
            inline=False)

        embed.add_field(
            name="\t__Example:__", 
            value="\t`--forest-remove \"computer graphics;machine learning;perception\"`",
            inline=False)

        embed.add_field(
            name="`--forest-list`",
            value=":white_small_square: Display list of keywords of current newsletter (maximum number of keywords is set to 10)",
            inline=False)

        embed.add_field(
            name="`--forest-help`",
            value=":white_small_square: Gives information about all commands", 
            inline=False)
            
        embed.set_footer(text="Hope it helped!") #if you like to

        await message.channel.send(embed=embed)


@client.event
async def on_ready():
    
    print(
        f'{client.user} is connected\n'
    )
        
client.run(TOKEN)