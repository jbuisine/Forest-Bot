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
from discord.ext import tasks, commands

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
n_articles_results = 5

# Task every minutes
@tasks.loop(seconds=60.0)
async def cron_event(client):

    # for each newsletter
    newsletters = newsletter_collection.find()

    # keep same date for each newsletter (avoid time issue)
    current_date = datetime.datetime.now()

    for channel_newsletter in newsletters:
        
        channel = client.get_channel(channel_newsletter['channel_id'])  

        # only use newsletter if activated
        if channel_newsletter['activated']:

            config_time = datetime.datetime.strptime(channel_newsletter['time'], "%H:%M")

            if current_date.hour == config_time.hour and current_date.minute == config_time.minute:
            
                # get current keywords from channel
                current_keywords = channel_newsletter['keywords']

                keyword_query = ''
                for k_id, keyword in enumerate(current_keywords):

                    if k_id != 0:
                        keyword_query += '+'

                    keyword_query += '"' + keyword.replace(' ', '+') + '"'
                    
                articles_list = get_gscholar_results(keyword_query)

                # check if article is already present in collections or not
                # depending of the number of wished articles
                reduced_articles = []
                for article in articles_list[:n_articles_results]:

                    machting_article = list(filter(lambda a: a['id'] == article['id'], channel_newsletter['articles']))

                    if len(machting_article) == 0:
                        reduced_articles.append(article)

                # add unknown articles into collection
                all_articles = list(channel_newsletter['articles'] + reduced_articles)

                newsletter_collection.update_one(
                    { '_id': channel_newsletter['_id'] }, 
                    { 
                        '$set': { 'articles': all_articles } 
                    },
                    upsert=False
                )

                message_data = ':evergreen_tree: :mailbox_with_mail: Newsletter search results :mailbox_with_mail: :evergreen_tree:\n\n'
                # display into message only new articles found
                for article in reduced_articles[:n_articles_results]:
                    message_data += f':newspaper: {article["title"]}\n'
                    message_data += f':link: <{article["href"]}>\n'
                    message_data += f':busts_in_silhouette: *{article["authors"]}*\n'

                    if article["date"] is not None:
                        message_data += f':calendar_spiral: {article["date"]}\n\n'

                # Remove this message
                # if len(articles_list) == 0:
                #     message_data += ':man_shrugging: There is no new articles, it seems your up to date! :man_shrugging:'

                print(f'{current_date} -- Forest send message to {channel.id}')
                print(f'\t\t -- Google Scholar search: {google_scholar_url + keyword_query}')

                # Send message only if new article has been found
                if len(reduced_articles) > 0:
                    await channel.send(message_data)
            
            else:
                print(f'{current_date} -- No message sent from Forest to {channel.id}')
        else:
            print(f'{current_date} -- No message sent from Forest to {channel.id} (newsletter is disabled)')

def get_gscholar_results(query):

    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36", 'referer':'https://www.google.com/'}
    req = urllib.request.Request(url=google_scholar_url + query, headers=headers)
    read_content = urllib.request.urlopen(req).read()

    soup = BeautifulSoup(read_content,'html.parser')

    gs_results = soup.find_all('div', class_='gs_ri')

    articles_list = []

    for res in gs_results:
        article_data = {}

        # get basic data
        link = res.find('h3').find('a')
        article_data['id'] = link['id']
        article_data['href'] = link['href']
        article_data['title'] = link.get_text()

        # get authors and journal data
        article_data['authors'] = res.find('div', class_='gs_a').get_text()

        ndays_element = res.find('span', class_='gs_age')

        # get publication date if exists
        if ndays_element:
            ndays_text = ndays_element.get_text()
            ndays = [int(i) for i in ndays_text.split() if i.isdigit() ][0]

            today = datetime.date.today()
            publication_date = today - datetime.timedelta(days = ndays)
            article_data['date'] = publication_date.strftime("%B %d, %Y")
        else:
            article_data['date'] = None

        articles_list.append(article_data)
    
    return articles_list

@client.event
async def on_message(message):

    # avoid message from
    if message.author == client.user:
        return

    if message.content.startswith('--forest-config'):

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
            try:

                if len(message.content.split(' ')) <= 1:

                    embed = discord.Embed(
                    title=':interrobang: Configuration error :interrobang:', 
                    description=f'Please refer to this example: `--forest-config 10:30`\n:clock2: Current configuration is set to `{channel_newsletter["time"]}` :clock2:', 
                    color=embed_color)

                else:
                    time_set = message.content.split(' ')[1].strip()

                    # check format 
                    bool(datetime.datetime.strptime(time_set, "%H:%M"))

                    newsletter_collection.update_one(
                        { '_id': channel_newsletter['_id'] }, 
                        { 
                            '$set': { 'time': time_set } 
                        },
                        upsert=False
                    )

                    print('Configuration updated...')

                    embed = discord.Embed(
                        title=':clock1: Newsletter configuration updated :clock1: ', 
                        description=f'New configuration is set to `{time_set}`', 
                        color=embed_color)

            except ValueError:
                
                embed = discord.Embed(
                    title=':interrobang: Configuration error :interrobang:', 
                    description=f'Please refer to this example: `--forest-config 10:30`\n:clock2: Current configuration is set to `{channel_newsletter["time"]}`:clock2:', 
                    color=embed_color)

        await message.channel.send(embed=embed)

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
            
            await message.channel.send(embed=embed)
        else:
            # get current keywords from channel
            current_keywords = channel_newsletter['keywords']
            
            keyword_query = ''
            for k_id, keyword in enumerate(current_keywords):

                if k_id != 0:
                    keyword_query += '+'

                keyword_query += '"' + keyword.replace(' ', '+') + '"'
                
            articles_list = get_gscholar_results(keyword_query)
            print(f'{datetime.datetime.now()} -- {message.author.name} search {google_scholar_url + keyword_query}')

            message_data = ':evergreen_tree: :evergreen_tree: Quick search results :evergreen_tree: :evergreen_tree:\n\n'
            # display into message only new articles found
            for article in articles_list[:n_articles_results]:
                message_data += f':newspaper: {article["title"]}\n'
                message_data += f':link: <{article["href"]}>\n'
                message_data += f':busts_in_silhouette: *{article["authors"]}*\n'

                if article["date"] is not None:
                    message_data += f':calendar_spiral: {article["date"]}\n\n'

            await message.channel.send(message_data)

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
            restricted_list = merged_keywords[:n_keywords]
            
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

            if len(merged_keywords) > n_keywords:

                embed = discord.Embed(
                title=':abacus: Keywords has been added but also truncated :abacus:', 
                description=f'Number of keywords is limited to {n_keywords}, some were not taken into consideration:\n{message_data}', 
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
                    'activated': True,
                    'time': '10:30'
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
            name="`--forest-search`",
            value=f":white_small_square: Display quick search results of the {n_articles_results} latest articles",
            inline=False)

        embed.add_field(
            name="`--forest-config`",
            value=":white_small_square: Specific newsletter hour and minutes configuration",
            inline=False)

        embed.add_field(
            name="\t__Example:__", 
            value="\t`--forest-config 10:30`",
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

    cron_event.start(client)
    print(f'Cron task launched...')

client.run(TOKEN)