"""
This file will handle all of the interactions with the local sql database
"""

import aws
import item_creator
import json
import sqlite3


class DatabaseHandler:
    """
    Class to interact with the database
    """

    def __init__(self):
        # Populated from discord
        self.all_user_info = None
        self.user_name = None
        self.user_id = None
        self.user_object = None
        self.bot = None

        # SQL variables
        self.connection = sqlite3.connect("../extra_files/serverDatabase.db")
        self.cursor = self.connection.cursor()

        # AWS connection for uploading the game screen
        self.aws = aws.AWSHandler()

        # Messages the bot should display
        self.messages = {
            'info': [],
            'error': []
        }

    def save_user_info_to_table(self, all_user_info: dict, user_name: str, user_id: int):
        """
        Save the current user information to the database. This is automatically called at the end of execution

        :param all_user_info: Dictionary containing the user information for every user
        :param user_name: Name of the user to save the info for
        :param user_id: Id of the user to save the info for
        """
        dictionaries = ['Inventory', 'PreviousMessages']
        modified_dictionaries = [{}, {}]

        # Convert the inventory to serializable objects
        for item in all_user_info[user_name]['Inventory']:
            if type(item) == int:
                modified_dictionaries[0][item] = all_user_info[user_name]['Inventory'][item].json_object
            else:
                modified_dictionaries[0][item] = all_user_info[user_name]['Inventory'][item]

        # Change the previous messages to their id's
        for message in all_user_info[user_name]['PreviousMessages']:
            modified_dictionaries[1][message] = {'channel_id': all_user_info[user_name]['PreviousMessages'][message].channel.id,
                                                 'message_id': all_user_info[user_name]['PreviousMessages'][message].id}

        # Update the database with the most recent user info
        self.cursor.execute(f'UPDATE UserInfo SET {" = ?, ".join([column for column in all_user_info[user_name]])} = ? WHERE UID = {user_id}',
                            [all_user_info[user_name][column] for column in all_user_info[user_name] if column not in dictionaries] +
                            [json.dumps(column) for column in modified_dictionaries])
        self.connection.commit()

    # ----------------------------------------------
    # Everything here and below is for this function
    # ----------------------------------------------
    async def load_player_info(self, all_user_info: dict, user_object: object, bot: object):
        """
        Load the player's information from the database if not in memory. If the player does not exists, register them.
         NOTE: This is called before processing of any message. No need to call this afterwards.

        :param all_user_info: Dictionary containing the user information for every user
        :param user_object: An object of the user from the discord message
        :param bot: The discord bot in order to fetch previous messages based on the message id
        """
        self.save_user_info_to_class(all_user_info, user_object, bot)
        if self.user_name not in self.all_user_info:
            user_values = self.get_user_info_from_database()

            results = [[stat[0], user_values[cnt]] for cnt, stat in enumerate(self.cursor.description)]
            for stat in results:
                await self.load_user_stats_into_class(stat)

        return self.all_user_info, self.messages

    def save_user_info_to_class(self, all_user_info: dict, user_object: object, bot: object):
        """
        Save the most recent user information which come from the discord bot

        :param all_user_info: Dictionary containing the user information for every user
        :param user_object: An object of the user from the discord message
        :param bot: The discord bot in order to fetch previous messages based on the message id
        """
        self.bot = bot
        self.all_user_info = all_user_info
        self.user_object = user_object
        self.user_name = self.user_object.name
        self.user_id = self.user_object.id

    def get_user_info_from_database(self):
        """
        Pull the user information from the database

        :return: The user's information
        """
        self.all_user_info[self.user_name] = {}
        self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.user_id}')
        values = self.cursor.fetchone()

        if values is None:
            self.register_me()
            self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.user_id}')
            values = self.cursor.fetchone()

        # Only for one time use to fix old table todo remove once run per old user
        if 'Inventory' not in [column_name[0] for column_name in self.cursor.description]:
            self.update_user_info_table()
            self.cursor.execute(f'SELECT * FROM UserInfo WHERE UID={self.user_id}')
            values = self.cursor.fetchone()

        return values

    async def load_user_stats_into_class(self, stat: list):
        """
        Load the user's stats into the class with the results from the database
        """
        if stat[0] == 'Inventory':
            self.all_user_info[self.user_name]['Inventory'] = {}
            for key, value in json.loads(stat[1]).items():
                if key.isdecimal():
                    value = json.loads(value)
                    self.all_user_info[self.user_name]['Inventory'][int(key)] = item_creator.BaseItem(value['real_name'],
                                                                                                      value['display_name'],
                                                                                                      value['modifiers'])
                else:
                    self.all_user_info[self.user_name]['Inventory'][key] = value
        elif stat[0] == 'PreviousMessages':
            self.all_user_info[self.user_name]['PreviousMessages'] = {}
            for key, value in json.loads(stat[1]).items():
                channel = await self.bot.fetch_channel(value['channel_id'])
                self.all_user_info[self.user_name]['PreviousMessages'][key] = await channel.fetch_message(value['message_id'])
        else:
            self.all_user_info[self.user_name][stat[0]] = stat[1]

    def register_me(self):
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
        self.cursor.execute(f"SELECT UID FROM UserInfo WHERE UID={self.user_id}  ;")

        if self.cursor.fetchone() is None:
            self.cursor.execute(
                f"INSERT INTO UserInfo (UID, Name, isBusy, Money, LVL, EXP, HP, STAM, ATK, DEF, SPD, Location, Inventory, PreviousMessages) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, ? ,? ,? ,? ,? ,? ,?);",
                [f'{self.user_id}', f'{self.user_name.name}', 0, 0, 1, 0, 100, 10, 10, 10, 10, 'Home', '{}', '{}'])
            self.connection.commit()
            self.messages['info'].append(f'You\'ve been registered with name: {self.user_name.name} ')

    def update_user_info_table(self):
        """
        Update the user info table to get rid or old and include new columns
        """
        self.cursor.execute('ALTER TABLE UserInfo ADD COLUMN Inventory JSON')
        self.cursor.execute('ALTER TABLE UserInfo ADD COLUMN PreviousMessages JSON')
        self.cursor.execute(f'UPDATE UserInfo SET Inventory = ?, PreviousMessages = ? WHERE UID = {self.user_id}',
                            ['{}', '{}'])
        self.connection.commit()
