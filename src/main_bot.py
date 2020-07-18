import os
import urllib
import time
import sys
import sqlite3
import csv
import random
import boto3
import datetime

from discord import File
from discord import Activity
from discord import ActivityType
from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from src import text_to_image
from threading import Lock
from PIL import Image
from botocore.exceptions import NoCredentialsError

# Load environment variables
load_dotenv()


class DiscordBot:
    """
    Discord Game Bot
    """

    def __init__(self):
        # Bot variables
        self.user = None
        self.display_name = None
        self.message = None
        self.file_lock = Lock()
        self.arguments = None
        self.reaction_payload = None

        # Game variables
        self.user_info = {}
        self.previous_messages = {}
        self.image_url = 'https://discordgamebotimages.s3.us-east-2.amazonaws.com/'

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

        self.cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={self.message.author.id}  ;""")

        if self.cursor.fetchone() is not None:
            await self.message.channel.send('You\'re already registered.')
            return
        else:
            self.cursor.execute(
                f"""INSERT INTO UserInfo (UID, Name, isBusy, Money, LVL, EXP, HP, STAM, ATK, DEF, SPD, EqpdItem, Location)
                                   VALUES ('{self.message.author.id}', '{self.message.author.name}', 0, 0, 1, 0, 100, 10, 10, 10, 10, 'None', 'Home');""")
            self.connection.commit()
            await self.message.channel.send(f'You\'ve been registered with name: {self.message.author.name} ')

        return

    async def start_encounter(self):
        """
        Start a random encounter
        """
        await self.message.channel.send(f'An encounter has started!')
        self.get_user_info()
        with self.file_lock:
            self.create_user_info_table()
            my_embed = Embed()
            my_embed.set_image(url=f'{self.image_url}{self.user}_user_info.jpg')
            self.previous_messages[self.user] = await self.message.channel.send(embed=my_embed)
            await self.add_reactions(self.previous_messages[self.user],
                                     ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'])

    # Travel Function to allow map traversal.
    async def travel(self):

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
        self.cursor.execute(f"""SELECT Location FROM UserInfo WHERE UID={self.message.author.id}""")
        unformatted_location = self.cursor.fetchone()
        self.currentLocation = ''.join(unformatted_location).split("-")
        for i in range(0, len(self.currentLocation)): self.currentLocation[i] = int(self.currentLocation[i])

        # Adjust location by command.
        if self.arguments[0] == 'north':
            self.newLocation = [(self.currentLocation[0] - 1), self.currentLocation[1]]
        elif self.arguments[0] == 'south':
            self.newLocation = [(self.currentLocation[0] + 1), self.currentLocation[1]]
        elif self.arguments[0] == 'east':
            self.newLocation = [self.currentLocation[0], (self.currentLocation[1] + 1)]
        elif self.arguments[0] == 'west':
            self.newLocation = [self.currentLocation[0], (self.currentLocation[1] - 1)]

        # Verify that the movement is within the bounds of the map, and not into a body of water.
        if self.newLocation[0] not in range(0,len(self.world_map)) or self.newLocation[1] not in range(0,len(self.world_map[0])):
            await self.message.channel.send('Invalid movement!')
            return
        elif self.world_map[self.newLocation[0]][self.newLocation[1]] == 'W':
            await self.message.channel.send('Cannot travel into water!')
            return

        # Format new location info to publish to SQL database.
        toPublish = str(self.newLocation[0]) + "-" + str(self.newLocation[1])

        # Commit new location to database.
        self.cursor.execute(f"""UPDATE UserInfo SET Location = '{toPublish}' WHERE UID = {self.message.author.id}""")
        self.connection.commit()

        overview = ''

        # Create overview map.

        map_image = Image.new('RGBA', (150, 150))

        for x in range(-1,2):
            for y in range(-1,2):

                xOffset = 50 + (y*50)
                yOffset = 50 + (x*50)

                if (self.newLocation[0] + x) in range(0,len(self.world_map[0])) and (self.newLocation[1] + y) in range(0,len(self.world_map[0])):
                    # Paste tile player is on.
                    to_paste = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[self.newLocation[0] + x][self.newLocation[1] + y]]}.png')
                    map_image.paste(to_paste,(xOffset,yOffset))

                    if x == 0 and y == 0:
                        # Paste player sprite.
                        map_sprite = to_paste = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[self.newLocation[0] + x][self.newLocation[1] + y]]}.png').convert("RGBA")
                        player_sprite = Image.open('../extra_files/tileImages/player.png').convert("RGBA")

                        player_on_tile = Image.alpha_composite(map_sprite,player_sprite)

                        map_image.paste(player_on_tile, (xOffset, yOffset))
                else:
                    to_paste = Image.open('../extra_files/tileImages/border.png')
                    map_image.paste(to_paste, (xOffset, yOffset))

        map_image.save('overview_map.png')

        await self.message.channel.send('', file=File('overview_map.png', filename='overview_map.png'))
        await self.message.channel.send(f'{location_legend[str(self.world_map[self.newLocation[0]][self.newLocation[1]])]}')

        await self.check_for_encounter()

        return

    async def add_reactions(self, message: object, reactions: list):
        """
        Add reactions to the given message

        :param message: Message to add the reactions to
        :param reactions: List of reactions to add
        """
        for reaction in reactions:
            await message.add_reaction(reaction)

    async def check_for_encounter(self):

        # Lists the likelihoods of a random encounter happening on that tile.
        encounter_likelihood = {
            '0': 50,
            'H': 0,
            'W': 0
        }

        encounter_chance = random.randint(0,100)

        if encounter_chance <= encounter_likelihood[str(self.world_map[self.newLocation[0]][self.newLocation[1]])]:
            await self.message.channel.send('Encounter occurred!')

        return

    def create_user_info_table(self, width: int = False):
        """
        Create the pretty table version of the user's info

        :param width: The size of the column width if specified
        """
        if not width:
            width = 3
        ignored_columns = ['UID', 'Name', 'isBusy']
        text_to_image.CreateImage(titles=[title for title in self.user_info.keys() if title not in ignored_columns],
                                  rows=[[str(value) for title, value in self.user_info.items() if title not in ignored_columns]],
                                  file_name=f'../extra_files/{self.user}_user_info.jpg',
                                  column_width=width)
        self.upload_to_aws()

    def upload_to_aws(self):
        """
        Upload the current game image to AWS
        """
        auth = boto3.client('s3', aws_access_key_id=os.environ['AWSAccessKeyId'],
                            aws_secret_access_key=os.environ['AWSSecretKey'])
        try:
            auth.upload_file(f'../extra_files/{self.user}_user_info.jpg',
                             'discordgamebotimages',
                             f'{self.user}_user_info.jpg',
                             ExtraArgs={'GrantRead': 'uri=http://acs.amazonaws.com/groups/global/AllUsers'})
            return True
        except FileNotFoundError:
            return False
        except NoCredentialsError:
            return False

    def get_user_info(self):
        """
        Query the user info from the database
        """
        self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.message.author.id}')
        values = self.cursor.fetchone()
        results = [[stat[0], values[cnt]] for cnt, stat in enumerate(self.cursor.description)]
        for stat in results:
            self.user_info[stat[0]] = stat[1]

    async def process_reaction_event(self):
        """
        Do something based on the reaction a player used
        """
        my_bot_id = 731973634519728168
        if self.reaction_payload.user_id != my_bot_id:
            await self.change_image(self.reaction_payload.emoji.name)
            self.previous_messages[self.user] = await self.message.channel.fetch_message(self.previous_messages[self.user].id)
            await self.previous_messages[self.user].remove_reaction(self.reaction_payload.emoji.name,
                                                                    self.reaction_payload.member)

    async def change_image(self, value: str):
        """
        Change the image from the previous message based on the reaction used

        :param value: Reaction used
        """
        columns = {
            '1️⃣': 1,
            '2️⃣': 2,
            '3️⃣': 3,
            '4️⃣': 4,
            '5️⃣': 5,
            '6️⃣': 6,
            '7️⃣': 7,
            '8️⃣': 8,
            '9️⃣': 9
        }
        self.create_user_info_table(columns[value])
        my_embed = Embed()
        timestamp = int(datetime.datetime.now().timestamp())
        my_embed.set_image(url=f'{self.image_url}{self.user}_user_info.jpg?{timestamp}')
        await self.previous_messages[self.user].edit(embed=my_embed)

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
            'test': self.start_encounter,
            'travel': self.travel
        }

        @self.bot.event
        async def on_message(message: object):
            """
            Receive any message

            :param message: Context of the message
            """
            if message.content != '' \
                    and message.content.split()[0][1:] in valid_commands \
                    and message.content[0] == '!':
                self.user = message.author.name
                self.display_name = message.author.display_name
                self.message = message
                self.arguments = message.content.split()[1:]
                await valid_commands[message.content.split()[0][1:]]()

        @self.bot.event
        async def on_raw_reaction_add(reaction_payload: object):
            """
            Checks if a reaction is added to the message

            :param reaction_payload: Payload information about the reaction
            """
            self.reaction_payload = reaction_payload
            await self.process_reaction_event()

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
