import os
import json
import urllib
import time
import sys
import sqlite3

from discord import File
from discord import Activity
from discord import ActivityType
from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv
from src import text_to_image
from threading import Lock

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

        # Game variables
        self.user_info = {}

        # SQL variables
        self.connection = sqlite3.connect("../extra_files/serverDatabase.db")
        self.cursor = self.connection.cursor()

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

        self.cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={self.message.author.id}  ;""")

        if self.cursor.fetchone() is not None:
            await self.message.channel.send('You\'re already registered.')
            return
        else:
            self.cursor.execute(
                f"""INSERT INTO UserInfo (UID, Name, isBusy, Money, LVL, EXP, HP, STAM, ATK, DEF, SPD, EqpdItem, Location)
                                   VALUES ('{self.message.author.id}', '{self.message.author.name}', 0, 0, 1, 0, 100, 10, 10, 10, 10, 10, 'None', 'Home');""")
            self.connection.commit()
            await self.message.channel.send(f'You\'ve been registered with name: {self.message.author.name} ')

        return

    async def start_encounter(self):
        """
        Start an random encounter
        """
        await self.message.channel.send(f'An encounter has started!')
        self.get_user_info()
        with self.file_lock:
            self.create_user_info_table()
            await self.message.channel.send('', file=File('../extra_files/user_info.jpg', filename='user_info.jpg'))

    def create_user_info_table(self):
        """
        Create the pretty table version of the user's info
        """
        ignored_columns = ['UID', 'Name', 'isBusy']
        text_to_image.CreateImage(titles=[title for title in self.user_info.keys() if title not in ignored_columns],
                                  rows=[[str(value) for title, value in self.user_info.items() if title not in ignored_columns]],
                                  file_name='../extra_files/user_info.jpg',
                                  column_width=4)

    def get_user_info(self):
        """
        Query the user info from the database
        """
        self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.message.author.id}')
        values = self.cursor.fetchone()
        results = [[stat[0], values[cnt]] for cnt, stat in enumerate(self.cursor.description)]
        for stat in results:
            self.user_info[stat[0]] = stat[1]

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
            'start_encounter': self.start_encounter
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
                await valid_commands[message.content.split()[0][1:]]()

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
            #  -
            #  -
            #  -
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
