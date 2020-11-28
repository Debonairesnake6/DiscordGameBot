"""
The main brains of the game. This handles all of the interactions with discord.
"""

import os
import urllib
import time
import sys
import csv
import database_handler
import main_game_window
import inventory_window

from discord import ActivityType, Activity
from discord.ext import commands
from dotenv import load_dotenv


class DiscordBot:
    """
    Discord Game Bot
    """

    def __init__(self):
        # Bot variables
        self.channel = None
        self.user_name = None
        self.user_id = None
        self.display_name = None
        self.message = None
        self.reaction_payload = None
        self.message_type = None
        self.bot_ids = [731973634519728168, 731973183275532419]  # First one is Ryan's, second is Sebastian's.

        # Game variables
        self.all_user_info = {}
        self.image_url = 'https://discordgamebotimages.s3.us-east-2.amazonaws.com/'
        self.location_description = None
        self.encounter_occurred = False
        self.direction = None

        # Embeds
        self.main_embed = None
        self.inventory_embed = None

        # Load world map into array from CSV
        with open("../extra_files/WorldMap.csv") as csv_to_map:
            reader = csv.reader(csv_to_map, delimiter=',')
            self.world_map = list(reader)

        # New variables after refactor
        self.bot = commands.Bot(command_prefix='!')
        self.user_object = None

        # Start listening to chat
        self.start_bot()

    async def load_game(self, send_messages: bool = True):
        """
        Load the player's information from the database if it is not already loaded. If the user does not exist, create them.

        :param send_messages: If the messages should be sent or not. They do not need to be resent if using a reaction,
         as the image will reload instead.
        """
        self.all_user_info, database_messages = await database_handler.DatabaseHandler().load_player_info(self.all_user_info, self.user_object, self.bot)
        self.main_embed = main_game_window.MainGameWindow(self.all_user_info[self.user_name], self.user_name, self.direction).play_game()
        self.inventory_embed = inventory_window.InventoryWindow(self.all_user_info[self.user_name], self.user_name, self.direction).display_inventory()

        # # Send info and error message
        # for message, message_type in [[message, message_type]
        #                               for file_type in [self.inventory_embed['messages'],
        #                                                 self.main_embed['messages'],
        #                                                 database_messages]
        #                               for message_type in file_type
        #                               for message in file_type[message_type]]:
        #     # Coming from a reaction
        #     if not send_messages:
        #         channel = await self.bot.fetch_channel(self.reaction_payload.channel_id)
        #         await channel.send(f'{message_type.upper()}: {message}')
        #
        #     # Coming from a regular message
        #     else:
        #         await self.message.channel.send(f'{message_type.upper()}: {message}')

        # Send embeds for the game windows
        if send_messages:
            for embed, embed_type, reactions, _ in [self.inventory_embed.values(), self.main_embed.values()]:
                message_sent = await self.channel.send('', embed=embed)
                self.all_user_info[self.user_name]['PreviousMessages'][embed_type] = message_sent
                await self.add_reactions(message_sent, reactions)

        # Save the user dictionary to the database
        database_handler.DatabaseHandler().save_user_info_to_table(self.all_user_info, self.user_name, self.user_id)

        # Reset variables
        self.direction = None

    async def handle_reaction_result(self):
        """
        Handle what clicking the reaction actual does in the game
        """
        directions = {
            '⬆️': 'north',
            '⬇️': 'south',
            '⬅️': 'west',
            '➡️': 'east'
        }
        options = {
            '♻️': 'reset'
        }

        # Load the current user's information
        self.all_user_info, _ = await database_handler.DatabaseHandler().load_player_info(self.all_user_info, self.user_object, self.bot)

        # Determine the type of message reacted to
        for message_type in self.all_user_info[self.user_name]['PreviousMessages']:
            if self.all_user_info[self.user_name]['PreviousMessages'][message_type].id == self.reaction_payload.message_id:
                self.message_type = message_type

        reaction = self.reaction_payload.emoji.name
        if reaction in options:
            if options[reaction] == 'reset':
                await self.load_game()

        elif reaction in directions:
            if self.message_type in ['Main', 'Inventory']:
                self.direction = directions[self.reaction_payload.emoji.name], self.message_type
                await self.load_game(send_messages=False)
                embeds = {
                    'Main': self.main_embed,
                    'Inventory': self.inventory_embed
                }
                await self.all_user_info[self.user_name]['PreviousMessages'][self.message_type].edit(embed=embeds[self.message_type]['embed'])

    @staticmethod
    async def add_reactions(message: object, reactions: list):
        """
        Add reactions to the given message

        :param message: Message to add the reactions to
        :param reactions: List of reactions to add
        """
        reactions_dict = {
            1: '1️⃣',
            2: '2️⃣',
            3: '3️⃣',
            4: '4️⃣',
            5: '5️⃣',
            6: '6️⃣',
            7: '7️⃣',
            8: '8️⃣',
            9: '9️⃣',
            'north': '⬆️',
            'south': '⬇️',
            'east': '⬅️',
            'west': '➡️',
            'reset': '♻️'
        }
        for reaction in reactions:
            await message.add_reaction(reactions_dict[reaction])

    async def help_message(self):
        """
        Display the help message for the bot
        """
        await self.message.channel.send('`Use !game to start using the game`')

    async def unknown_command(self):
        """
        Tell the user the given command is unknown
        """
        await self.message.channel.send(f'Unknown command')

    def start_bot(self):
        """
        Start the bot
        """
        valid_commands = {
            'game': self.load_game,
            'help': self.help_message
        }

        @self.bot.event
        async def on_message(message: object):
            """
            Receive any message

            :param message: Context of the message
            """
            if message.content != '' \
                    and message.content.split()[0][1:] in valid_commands \
                    and message.content[0] == '!'\
                    and message.author.id not in self.bot_ids:
                self.user_name = message.author.name
                self.user_object = message.author
                self.display_name = message.author.display_name
                self.user_id = message.author.id
                self.message = message
                self.channel = message.channel
                await valid_commands[message.content.split()[0][1:]]()

        @self.bot.event
        async def on_raw_reaction_add(reaction_payload: object):
            """
            Checks if a reaction is added to the message

            :param reaction_payload: Payload information about the reaction
            """
            if reaction_payload.user_id not in self.bot_ids:
                self.reaction_payload = reaction_payload
                if reaction_payload.member is not None:
                    self.user_object = reaction_payload.member
                    self.user_name = reaction_payload.member.name
                    self.display_name = reaction_payload.member.display_name
                    self.user_id = reaction_payload.member.id
                else:
                    self.user_object = await self.bot.fetch_user(reaction_payload.user_id)
                    self.user_name = self.user_object.name
                    self.display_name = self.user_object.display_name
                    self.user_id = self.user_object.id
                self.channel = await self.bot.fetch_channel(self.reaction_payload.channel_id)
                await self.handle_reaction_result()

        @self.bot.event
        async def on_raw_reaction_remove(reaction_payload: object):
            """
            Checks if a reaction is removed from the message

            :param reaction_payload: Payload information about the reaction
            """
            if reaction_payload.user_id not in self.bot_ids:
                self.reaction_payload = reaction_payload
                self.user_object = await self.bot.fetch_user(reaction_payload.user_id)
                self.user_name = self.user_object.name
                self.display_name = self.user_object.display_name
                self.user_id = self.user_object.id
                self.channel = await self.bot.fetch_channel(self.reaction_payload.channel_id)
                await self.handle_reaction_result()

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')

            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='!game'))

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':

    # Load environment variables
    load_dotenv()

    while True:

        # Wait until retrying if the service is down
        try:
            DiscordBot()
            break

        # Catch if service is down
        except urllib.error.HTTPError as e:
            error_msg = "Service Temporarily Down"
            print(error_msg)
            print(e)
            # post_message(error_msg)
            time.sleep(60)

        # Catch random OS error
        except OSError as e:
            print(e, file=sys.stderr)
            time.sleep(60)
