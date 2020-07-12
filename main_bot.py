"""
This is the brain of the bot which parses input and manages the discord server
"""

import os
import json
import urllib
import time
import sys

from discord import File
from discord import Activity
from discord import ActivityType
from discord.errors import HTTPException
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DiscordBot:
    """
    Social Credit Discord bot
    """

    def __init__(self):
        """
        Social Credit Discord bot
        """
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
        await self.message.channel.send('Social Credit commands:```'
                                        'Whenever I have multiple commands like ussr/USSR that means any of the listed '
                                        'ones work. Anything in square brackets [] is optional, curly braces {} are '
                                        'required but have an obvious substitute for the word. All commands start '
                                        'with !'
                                        ''
                                        '\n\n!ussr/USSR'
                                        '\n\t-\tBasic commands to use the bot. This will display your current balance.'
                                        '\n\t-\tAll of the following commands work with all of these options, but I '
                                        'will just show using USSR as it is redundant to list all of them.'
                                        ''
                                        '\n\n!USSR add {amount} [@Citizen]'
                                        '\n\t-\tAdd social credits to your account. Replace {amount} with the value you'
                                        ' want to add.'
                                        '\n\t-\tIf you ping a user or group at the end of the message it will '
                                        'add credits to their account instead.'
                                        '\n\t-\te.g. !USSR add 12345'
                                        '\n\t-\te.g. !USSR add 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR add 123 @TheSquad'
                                        ''
                                        '\n\n!USSR remove {amount} [@Citizen]'
                                        '\n\t-\tRemove social credits from your account. Replace {amount} with the '
                                        'value you want to remove.'
                                        '\n\t-\tIf you ping a user or group at the end of the '
                                        'message it will remove credits from their account instead.'
                                        '\n\t-\te.g. !USSR remove 12345'
                                        '\n\t-\te.g. !USSR remove 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR remove 123 @TheSquad'
                                        ''
                                        '\n\n!USSR set {amount} [@Citizen]'
                                        '\n\t-\tSet the amount of social credits in your account. Replace {amount} '
                                        'with the value you want to set it to.'
                                        '\n\t-\tIf you ping a user or group at the end '
                                        'of the message it will set their credits to that amount instead.'
                                        '\n\t-\te.g. !USSR set 12345'
                                        '\n\t-\te.g. !USSR set 54321 @Debonairesnake6'
                                        '\n\t-\te.g. !USSR set 123 @TheSquad'
                                        ''
                                        '\n\n!USSR leaderboard'
                                        '\n\t-\tDisplay the leaderboard for each citizen\'s bank account.'
                                        '\n\t-\te.g. !USSR leaderboard'
                                        ''
                                        '\n\n!USSR help'
                                        '\n\t-\tShow this help message.```')

    async def unknown_command(self):
        """
        Tell the user the given command is unknown
        """
        await self.message.channel.send(f'Unknown command: {self.message.content.split()[1]}. Use the following command'
                                        f' for help.\n!ussr help')

    async def handle_happy_birthday_message(self):
        """
        Handle the incoming happy birthday message
        """

        birthday_message = 'Happy Birthday'
        for letter in birthday_message:
            await self.message.channel.send(f'{letter} {self.message.content.split()[1]}')
            time.sleep(1)

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
            'birthday': self.handle_happy_birthday_message
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
