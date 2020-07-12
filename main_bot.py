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

# Load environment variables
load_dotenv()

connection = sqlite3.connect("serverDatabase.db")
cursor = connection.cursor()

class DiscordBot:

    def __init__(self):
        self.user = None
        self.display_name = None
        self.message = None
        self.bot = commands.Bot(command_prefix='!')

        # Start listening to chat
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

        cursor.execute(f"""SELECT UID FROM UserInfo WHERE UID={self.message.author.id}  ;""")

        if (cursor.fetchone() != None):
            await self.message.channel.send('You\'re already registered.')
            return
        else:
            cursor.execute(
                f"""INSERT INTO UserInfo (UID, Name, isBusy, Money, LVL, EXP, HP, STAM, ATK, DEF, SPD, EqpdItem, Location)
                                   VALUES ('{self.message.author.id}', '{self.message.author.name}', 0, 0, 1, 0, 100, 10, 10, 10, 10, 'None', 'Home');""")
            connection.commit()
            await self.message.channel.send(f'You\'ve been registered with name: {self.message.author.name} ')

        return

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
            'registerMe': self.register_me
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