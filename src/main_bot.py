import os
import urllib
import time
import sys
import sqlite3
import csv
import random
import datetime
from src import enemies
from src import AWS
import numpy as np
import json

from discord import Activity
from discord import ActivityType
from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from src import text_to_image
from src import inventory_manager
from src import item_manager
from threading import Lock
from PIL import Image, ImageDraw

# Load environment variables
load_dotenv()


class DiscordBot:
    """
    Discord Game Bot
    """

    def __init__(self):
        # Bot variables
        self.user = None
        self.user_id = None
        self.display_name = None
        self.message = None
        self.file_lock = Lock()
        self.arguments = None
        self.reaction_payload = None
        self.message_type = None
        self.embed = Embed()
        self.bot_ids = [731973634519728168, 731973183275532419]  # First one is Ryan's, second is Sebastian's.

        # Initializers
        self.AWS = AWS.AWSHandler() # Create an AWS handler object.

        # Game variables
        self.user_info = {}
        self.image_url = 'https://discordgamebotimages.s3.us-east-2.amazonaws.com/'
        self.location_description = None
        self.encounter_occurred = False
        self.direction = None

        # SQL variables
        self.connection = sqlite3.connect("../extra_files/serverDatabase.db")
        self.cursor = self.connection.cursor()

        # Load world map into array from CSV
        with open("../extra_files/WorldMap.csv") as csv_to_map:
            reader = csv.reader(csv_to_map, delimiter=',')
            self.world_map = list(reader)

        # Start listening to chat
        self.bot = commands.Bot(command_prefix='!')
        self.start_bot()

    async def help_message(self):
        """
        Display the help message for the bot
        """
        await self.message.channel.send('``')

    async def unknown_command(self):
        """
        Tell the user the given command is unknown
        """
        await self.message.channel.send(f'Unknown command')

    async def register_me(self):
        """
        Register a new user in the database
        """

        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS UserInfo('
                            f'UID INTEGER PRIMARY KEY,'
                            f'Name TEXT,'
                            f'isBusy INTEGER,'
                            f'Money,'
                            f'LVL INTEGER,'
                            f'EXP INTEGER,'
                            f'HP INTEGER,'
                            f'STAM INTEGER,'
                            f'ATK INTEGER,'
                            f'DEF INTEGER,'
                            f'SPD INTEGER,'
                            f'Location TEXT,'
                            f'Inventory Text,'
                            f'PreviousMessages Text)')
        self.cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={self.message.author.id}  ;""")

        if self.cursor.fetchone() is not None:
            await self.message.channel.send('You\'re already registered.')
            return
        else:
            self.cursor.execute(
                f"""INSERT INTO UserInfo (UID, Name, isBusy, Money, LVL, EXP, HP, STAM, ATK, DEF, SPD, Location, Inventory, PreviousMessages)
                                   VALUES ('{self.message.author.id}', '{self.message.author.name}', 0, 0, 1, 0, 100, 10, 10, 10, 10, 'Home', {dict()}, {None});""")
            self.connection.commit()
            await self.message.channel.send(f'You\'ve been registered with name: {self.message.author.name} ')

    async def start_encounter(self):
        """
        Start a random encounter
        """
        await self.message.channel.send(f'An encounter has started!')
        with self.file_lock:
            self.create_user_info_table()
            my_embed = Embed()
            my_embed.set_image(url=f'{self.image_url}{self.user}_user_info.jpg')
            self.user_info[self.user]['PreviousMessages']['Encounter'] = await self.message.channel.send(embed=my_embed)
            await self.add_reactions(self.user_info[self.user]['PreviousMessages']['Encounter'],
                                     [1, 2, 3, 4, 5, 6, 7, 8, 9])

    # Travel Function to allow map traversal.
    async def travel(self):
        new_location = False

        # Compendium for what messages to display depending on where you are on the map.
        location_legend = {
            '0': 'You find yourself on clear land.',
            'H': 'You find yourself home! Home sweet home!',
            'W': 'WATER'
        }

        tile_image_legend = {
            '0': 'clearLand',
            'H': 'home',
            'W': 'water'
        }

        # Gather the location info and format it into local variables.
        self.currentLocation = ''.join(self.user_info[self.user]['Location']).split("-")
        for i in range(0, len(self.currentLocation)): self.currentLocation[i] = int(self.currentLocation[i])

        # Adjust location by command.
        if self.direction is not None:
            if self.direction == 'north':
                self.newLocation = [(self.currentLocation[0] - 1), self.currentLocation[1]]
            elif self.direction == 'south':
                self.newLocation = [(self.currentLocation[0] + 1), self.currentLocation[1]]
            elif self.direction == 'east':
                self.newLocation = [self.currentLocation[0], (self.currentLocation[1] + 1)]
            elif self.direction == 'west':
                self.newLocation = [self.currentLocation[0], (self.currentLocation[1] - 1)]

            # Verify that the movement is within the bounds of the map, and not into a body of water.
            if self.newLocation[1] not in range(0, len(self.world_map)) or self.newLocation[0] not in range(0, len(self.world_map[0])):

                await self.user_info[self.user]['PreviousMessages']['Travel'].channel.send('Invalid movement!')
                return

            elif self.world_map[self.newLocation[0]][self.newLocation[1]] == 'W':
                await self.user_info[self.user]['PreviousMessages']['Travel'].channel.send('Cannot travel into water!')
                return

            self.user_info[self.user]['Location'] = str(self.newLocation[0]) + "-" + str(self.newLocation[1])
            new_location = True

        if not new_location:
            self.newLocation = self.currentLocation

        # Create overview map.

        map_image = Image.new('RGBA', (150, 160))

        # Draw skybox
        time_from_morning = random.randint(0, 100)

        for x in range(-1, 2):
            xOffset = 50 + (50 * x)
            img1 = ImageDraw.Draw(map_image)

            img1.rectangle([(xOffset, 0), (xOffset + 50, 40)], fill=(170-time_from_morning, 190-time_from_morning, 235-time_from_morning))

        # Draw rest of map overview
        for y in range(-1, 2):
            yOffset = ((y+1)*40)
            tile_y = self.newLocation[0] + y

            for x in range(-1, 2):
                xOffset = 50 + (x * 50)
                tile_x = self.newLocation[1] + x

                if tile_x in range(0, len(self.world_map[1])) and tile_y in range(0, len(self.world_map[0])):

                    to_paste = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[tile_y][tile_x]]}.png')
                    background = map_image.crop([xOffset, yOffset, xOffset+50, yOffset+80])
                    final_paste = Image.alpha_composite(background, to_paste)
                    map_image.paste(final_paste, ([xOffset, yOffset, xOffset+50, yOffset+80]))

                    # If on player space.
                    if x == 0 and y == 0:
                        # Paste player sprite.
                        map_sprite = to_paste = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[tile_y][tile_x]]}.png').convert( "RGBA")
                        player_sprite = Image.open('../extra_files/tileImages/player.png').convert("RGBA")

                        background = map_image.crop([50, 40, 100, 120])

                        map_sprite = Image.alpha_composite(background, map_sprite)

                        player_on_tile = Image.alpha_composite(map_sprite, player_sprite)

                        map_image.paste(player_on_tile, (xOffset, yOffset))
                else:
                    to_paste = Image.open('../extra_files/tileImages/border.png')
                    background = map_image.crop([xOffset, yOffset, xOffset + 50, yOffset + 80])
                    final_paste = Image.alpha_composite(background, to_paste)
                    map_image.paste(final_paste, (xOffset, yOffset))


        map_image.save(f'../extra_files/{self.user}_overview_map.png')

        self.location_description = location_legend[str(self.world_map[self.newLocation[0]][self.newLocation[1]])]
        self.check_for_encounter()

        self.AWS.upload_image(self.user, 'overview_map.png')

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

    def check_for_encounter(self):

        # Lists the likelihoods of a random encounter happening on that tile.
        encounter_likelihood = {
            '0': 50,
            'H': 0,
            'W': 0
        }

        encounter_chance = random.randint(0, 100)

        if encounter_chance <= encounter_likelihood[str(self.world_map[self.newLocation[1]][self.newLocation[0]])]:
            self.encounter_occurred = True

    def create_user_info_table(self, width: int = False):
        """
        Create the pretty table version of the user's info

        :param width: The size of the column width if specified
        """
        if not width:
            width = 3
        ignored_columns = ['UID', 'Name', 'isBusy']
        text_to_image.CreateImage(titles=[title for title in self.user_info[self.user].keys() if title not in ignored_columns],
                                  rows=[[str(value) for title, value in self.user_info[self.user].items() if
                                         title not in ignored_columns]],
                                  file_name=f'../extra_files/{self.user}_user_info.jpg',
                                  column_width=width)
        self.AWS.upload_image(self.user, 'user_info.jpg')

    async def get_and_remove_reaction(self):
        """
        Get the reaction and remove it
        """
        # todo determine what type of message was reacted on and act accordingly
        if self.reaction_payload.user_id:
            await self.handle_reaction_result()
            await self.user_info[self.user]['PreviousMessages'][self.message_type].remove_reaction(self.reaction_payload.emoji.name,
                                                                                                   self.reaction_payload.member)

    async def change_image(self, file_name: str, fields: dict = False):
        """
        Change the image from the previous message based on the reaction used

        :param file_name: Name of the image without the username. e.g. _user_info.jpg
        :param fields: Fields to add to the message. e.g. {'field1': 'name1', 'field2': 'name2'}
        """
        timestamp = int(datetime.datetime.now().timestamp())
        self.embed.clear_fields()
        self.embed.set_image(url=f'{self.image_url}{self.user}_{file_name}?{timestamp}')
        if fields:
            for field_name, field_value in fields.items():
                self.embed.add_field(name=field_name, value=field_value)
        await self.user_info[self.user]['PreviousMessages'][self.message_type].edit(embed=self.embed)

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

        # Determine the type of message reacted to
        if self.reaction_payload.message_id == self.user_info[self.user]['PreviousMessages']['Inventory'].id:
            self.message_type = 'Inventory'
        elif self.reaction_payload.message_id == self.user_info[self.user]['PreviousMessages']['Travel'].id:
            self.message_type = 'Travel'

        reaction = self.reaction_payload.emoji.name
        timestamp = int(datetime.datetime.now().timestamp())
        if reaction in options:  # todo fix this with the new previous messages
            if options[reaction] == 'reset':
                self.embed.set_image(url=f'{self.image_url}{self.user}_overview_map.png?{timestamp}')
                self.user_info[self.user]['PreviousMessages'][self.message_type] = \
                    await self.user_info[self.user]['PreviousMessages'][self.message_type].channel.send('', embed=self.embed)
                await self.add_reactions(self.user_info[self.user]['PreviousMessages'][self.message_type],
                                         ['east', 'north', 'south', 'west', 'reset'])
        elif reaction in directions:
            if self.message_type == 'Travel':
                self.direction = directions[self.reaction_payload.emoji.name]
                await self.travel()
                fields = {'Info': self.location_description}
                if self.encounter_occurred:
                    fields['Bring out the lube'] = 'An encounter has occurred!'
                await self.change_image('overview_map.png', fields)
            elif self.message_type == 'Inventory':
                self.move_inventory_cursor(directions[reaction])
                self.create_inventory_embed()
                await self.user_info[self.user]['PreviousMessages']['Inventory'].edit(embed=self.embed)

    async def first_travel(self):
        """
        First load the travel before you can click on the reactions
        """
        await self.travel()
        timestamp = int(datetime.datetime.now().timestamp())
        self.embed.set_image(url=f'{self.image_url}{self.user}_overview_map.png?{timestamp}')
        print(f'Image path: {self.image_url}{self.user}_overview_map.png')
        self.embed.add_field(name='Info', value=self.location_description)
        if self.encounter_occurred:
            self.embed.add_field(name='Bring out the lube', value='An encounter has occurred!')
        message_sent = await self.message.channel.send('', embed=self.embed)
        self.user_info[self.user]['PreviousMessages']['Travel'] = message_sent
        await self.add_reactions(message_sent, ['east', 'north', 'south', 'west', 'reset'])

    async def sayHi(self):
        self.enemy = enemies.Enemies()

        await self.enemy.printMe(self)

    async def display_inventory(self):
        """
        Display the player's current inventory is discord
        """
        self.create_inventory_embed()
        self.user_info[self.user]['PreviousMessages']['Inventory'] = await self.message.channel.send(embed=self.embed)
        await self.add_reactions(self.user_info[self.user]['PreviousMessages']['Inventory'], ['east', 'north', 'south', 'west'])

    def create_inventory_embed(self):
        """
        Create an embed for the current user's inventory
        """
        timestamp = int(datetime.datetime.now().timestamp())
        self.create_inventory_image()
        self.embed.clear_fields()
        self.embed.set_image(url=f'{self.image_url}{self.user}_inventory.png?{timestamp}')

        highlight = self.user_info[self.user]['Inventory']['highlight']
        if highlight in self.user_info[self.user]['Inventory']:
            self.embed.add_field(name='Name', value=self.user_info[self.user]['Inventory'][highlight].display_name)
            self.embed.add_field(name='Stats', value='\n'.join([f'{stat.replace("_", " ").capitalize()}: {value}'
                                                                for stat, value in self.user_info[self.user]['Inventory'][highlight].stats.items()
                                                                if value != 0]))

    def create_inventory_image(self):
        """
        Create the image to display the user's inventory
        """
        # todo these values need to be dynamically grabbed and saved per player
        if self.user_info[self.user]['Inventory'] == {}:
            self.user_info[self.user]['Inventory'] = {
                0: item_manager.BaseItem('bow', 'Awesome Bow of Shooting', {'attack': 1}),
                3: item_manager.BaseItem('sword', 'Pointy Stick', {'attack': 2}),
                9: item_manager.BaseItem('sword', 'Big Knife', {'friends': -2}),
                7: item_manager.BaseItem('bow', 'Twig and String', {'attack_range': -5}),
                14: item_manager.BaseItem('bow', 'Deluxe Master 3001', {'attack_speed': 6}),
                'highlight': 10,
                'columns': 4,
                'rows': 4
            }
        # Just used to shorten calls
        inventory = self.user_info[self.user]['Inventory']
        inventory_manager.CreateInventoryImage(f'{self.user}_inventory.png',
                                               columns=inventory['columns'],
                                               rows=inventory['rows'],
                                               highlight=inventory['highlight'],
                                               items=self.user_info[self.user]['Inventory'])
        self.AWS.upload_image(self.user, 'inventory.png')

    def move_inventory_cursor(self, direction: str):
        """
        Move the cursor on the inventory screen based on the reaction given
        """
        inventory = self.user_info[self.user]['Inventory']
        if direction == 'north':
            inventory['highlight'] = (inventory['highlight'] - inventory['rows']) % (inventory['rows'] * inventory['columns'])
        elif direction == 'south':
            inventory['highlight'] = (inventory['highlight'] + inventory['rows']) % (inventory['rows'] * inventory['columns'])
        elif direction == 'west':
            if (inventory['highlight'] - 1) % inventory['columns'] == inventory['columns'] - 1:
                inventory['highlight'] += inventory['columns'] - 1
            else:
                inventory['highlight'] -= 1
        elif direction == 'east':
            if (inventory['highlight'] + 1) % inventory['columns'] == 0:
                inventory['highlight'] -= inventory['columns'] - 1
            else:
                inventory['highlight'] += 1

    async def load_player_info(self):
        """
        Load the player's information from the database if not in memory
        """
        if self.user not in self.user_info and self.user_id not in self.bot_ids:
            self.user_info[self.user] = {}
            self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.user_id}')
            values = self.cursor.fetchone()

            # Only for one time use to fix old table todo remove once run
            if 'Inventory' not in [column_name[0] for column_name in self.cursor.description]:
                self.update_user_info_table()
                self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.user_id}')
                values = self.cursor.fetchone()

            results = [[stat[0], values[cnt]] for cnt, stat in enumerate(self.cursor.description)]
            for stat in results:
                if stat[0] == 'Inventory':
                    self.user_info[self.user]['Inventory'] = {}
                    for key, value in json.loads(stat[1]).items():
                        if key.isdecimal():
                            value = json.loads(value)
                            self.user_info[self.user]['Inventory'][int(key)] = item_manager.BaseItem(value['real_name'], value['display_name'], value['modifiers'])
                        else:
                            self.user_info[self.user]['Inventory'][key] = value
                elif stat[0] == 'PreviousMessages':
                    self.user_info[self.user]['PreviousMessages'] = {}
                    for key, value in json.loads(stat[1]).items():
                        channel = self.bot.get_channel(value['channel_id'])
                        self.user_info[self.user]['PreviousMessages'][key] = await channel.fetch_message(value['message_id'])
                else:
                    self.user_info[self.user][stat[0]] = stat[1]

    def update_user_info_table(self):
        """
        Update the user info table to get rid or old and include new columns
        """
        self.cursor.execute('ALTER TABLE UserInfo ADD COLUMN Inventory JSON')
        self.cursor.execute('ALTER TABLE UserInfo ADD COLUMN PreviousMessages JSON')
        self.cursor.execute(f'UPDATE UserInfo SET Inventory = ?, PreviousMessages = ? WHERE UID = {self.user_id}',
                            [json.dumps({}), json.dumps({})])
        self.connection.commit()

    def save_user_info_to_table(self):
        """
        Save the current user information to the database. This is automatically called at the end of execution
        """
        dictionaries = ['Inventory', 'PreviousMessages']
        modified_dictionaries = [{}, {}]

        # Convert the inventory to serializable objects
        for item in self.user_info[self.user]['Inventory']:
            if type(item) == int:
                modified_dictionaries[0][item] = self.user_info[self.user]['Inventory'][item].json_object
            else:
                modified_dictionaries[0][item] = self.user_info[self.user]['Inventory'][item]

        # Change the previous messages to their id's
        for message in self.user_info[self.user]['PreviousMessages']:
            modified_dictionaries[1][message] = {'channel_id': self.user_info[self.user]['PreviousMessages'][message].channel.id,
                                                 'message_id': self.user_info[self.user]['PreviousMessages'][message].id}

        self.cursor.execute(f'UPDATE UserInfo SET {" = ?, ".join([column for column in self.user_info[self.user]])} = ? WHERE UID = {self.user_id}',
                            [self.user_info[self.user][column] for column in self.user_info[self.user] if column not in dictionaries] +
                            [json.dumps(column) for column in modified_dictionaries])
        self.connection.commit()

    @staticmethod
    async def message_user(user: object, message: str):
        """
        Send a private message to the user. For the message variable you can use message.author.send()

        :param user: User to send the message to
        :param message: Message contents to send to the user
        """
        await user.send(message)

    def start_bot(self):
        """
        Start the bot
        """
        valid_commands = {
            'registerMe': self.register_me,
            'start_encounter': self.start_encounter,
            'travel': self.first_travel,
            'sayHi': self.sayHi,
            'test': self.display_inventory
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
                self.user = message.author.name
                self.display_name = message.author.display_name
                self.user_id = message.author.id
                self.message = message
                self.arguments = message.content.split()[1:]
                await self.load_player_info()
                await valid_commands[message.content.split()[0][1:]]()
                self.save_user_info_to_table()

        @self.bot.event
        async def on_raw_reaction_add(reaction_payload: object):
            """
            Checks if a reaction is added to the message

            :param reaction_payload: Payload information about the reaction
            """
            if reaction_payload.member.id not in self.bot_ids:
                self.reaction_payload = reaction_payload
                self.user = reaction_payload.member.name
                self.display_name = reaction_payload.member.display_name
                self.user_id = reaction_payload.member.id
                await self.load_player_info()
                await self.get_and_remove_reaction()
                self.save_user_info_to_table()

        @self.bot.event
        async def on_ready():
            """
            Set the bot status on discord
            """
            if os.name == 'nt':
                print('Ready')

            await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name='WIP'))

        # Run the bot
        self.bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':

    while True:

        # Wait until retrying if the service is down
        try:

            # ToDo list:
            #  -    Create inventory system
            #  -    Single game window
            #  -
            #  -
            #  -
            #  -
            #  -
            #  -
            #  -
            #  -
            #  -

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
