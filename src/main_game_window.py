"""
This file will contain all of the logic for the main game window
"""

import aws
import datetime
import random
import csv
import requests
import itertools

from discord import Embed
from PIL import Image, ImageDraw


class MainGameWindow:
    """
    Class to control the main game window
    """
    def __init__(self, user_info: dict, user_name: str, direction: str = None):
        """
        Class to control the main game window

        :param user_info: User information for the current user
        :param user_name: Username of the current user
        :param direction: The direction the player is travelling in, if any
        """
        # Bot variables
        self.user_info = user_info
        self.user_name = user_name
        self.window_name = 'Main'
        self.reactions = ['east', 'north', 'south', 'west', 'reset']

        # Travel variables
        self.embed = None
        self.direction = direction
        self.image = None
        self.location_description = None
        self.location_updated = False
        self.location_x = None
        self.location_y = None
        self.original_x = None
        self.original_y = None
        self.world_map = None

        # AWS connection for uploading the game screen
        self.aws = aws.AWSHandler()
        self.image_url = 'https://discordgamebotimages.s3.us-east-2.amazonaws.com/'

        # Messages the bot should display
        self.messages = {
            'info': [],
            'error': []
        }

    def play_game(self):
        """
        Display the map and move the player if a direction is set
        """
        self.load_user_info_into_class()
        self.perform_travel_for_user()
        self.verify_location_is_valid()
        self.create_travel_image()
        self.get_location_description()
        self.create_embed()

        return {'embed': self.embed, 'name': self.window_name, 'reactions': self.reactions, 'messages': self.messages}

    def load_user_info_into_class(self):
        """
        Load the information stored from the user's dictionary into the class
        """
        self.location_x = int(self.user_info['Location'].split('-')[0])
        self.location_y = int(self.user_info['Location'].split('-')[1])
        self.original_x = self.location_x
        self.original_y = self.location_y

    def perform_travel_for_user(self):
        """
        Make the user travel based on the specified direction
        """
        if self.direction is not None and self.direction[1] == 'Main':
            if self.direction[0] == 'north':
                self.location_y -= 1
            elif self.direction[0] == 'south':
                self.location_y += 1
            elif self.direction[0] == 'west':
                self.location_x -= 1
            elif self.direction[0] == 'east':
                self.location_x += 1

    def verify_location_is_valid(self):
        """
        Verify that the location the player moved to is an appropriate tile.
        """
        # Load the world map
        with open("../extra_files/WorldMap.csv") as csv_to_map:
            reader = csv.reader(csv_to_map, delimiter=',')
            self.world_map = list(reader)

        # Check if on map
        if not 0 <= self.location_y < len(self.world_map) \
                or not 0 <= self.location_x < len(self.world_map[self.location_y]):
            self.messages['error'].append('Invalid movement!')

        # Check if in water
        elif self.world_map[self.location_y][self.location_x] == 'W':
            self.messages['error'].append('Cannot travel into water!')

        # Save the location change if successful
        else:
            self.user_info['Location'] = f'{self.location_x}-{self.location_y}'
            self.location_updated = True

    def create_travel_image(self):
        """
        Create an image of the map based on the user's location
        """
        # Only create a new image if the location was updated or if the user has not played before
        if self.location_updated or requests.get(f'{self.image_url}{self.user_name}_overview_map.png').status_code != 200:
            self.image = Image.new('RGBA', (300, 300))
            self.draw_skybox()
            self.draw_map_locations()
            self.image.save(f'../extra_files/{self.user_name}_overview_map.png')
            self.aws.upload_image(self.user_name, 'overview_map.png')

    def draw_skybox(self):
        """
        Draw the skybox for the image which will be from a particular time of day
        """
        time_of_day = random.randint(0, 100)

        for x in range(-1, 2):
            x_offset = 100 + 100 * x
            sky = ImageDraw.Draw(self.image)
            sky.rectangle([(x_offset, 0), (x_offset + 100, 80)],
                          fill=(170 - time_of_day, 190 - time_of_day, 235 - time_of_day))

    def draw_map_locations(self):
        """
        Draw the locations of each tile on the map
        """
        tile_image_legend = {
            '0': 'clearLand',
            'H': 'home',
            'W': 'water'
        }

        # Draw a 3x3 tile of squares
        for x, y in itertools.product(range(-1, 2), range(-1, 2)):
            x_offset = 100 + x * 100
            y_offset = (y + 1) * 80
            x_tile = self.location_x + x
            y_tile = self.location_y + y

            # Check if the tile is inside of the map
            if not 0 <= y_tile < len(self.world_map) or not 0 <= x_tile < len(self.world_map[y_tile]):
                self.draw_border_tile(x_offset, y_offset)

            # Draw the player if the tile is in the center
            elif x == y == 0:
                self.draw_player_on_tile(x_offset, y_offset, x_tile, y_tile, tile_image_legend)

            # Draw the appropriate file
            else:
                self.draw_tile_image(x_offset, y_offset, x_tile, y_tile, tile_image_legend)

    def draw_border_tile(self, x_offset: int, y_offset: int):
        """
        Draw a border tile image on the specified tile

        :param x_offset: The x offset to draw the tile on
        :param y_offset: The y offset to draw the tile on
        """
        tile_image = Image.open('../extra_files/tileImages/border.png').resize((100, 160))
        background = self.image.crop([x_offset, y_offset, x_offset + 100, y_offset + 160])
        final_tile = Image.alpha_composite(background, tile_image)
        self.image.paste(final_tile, (x_offset, y_offset))

    def draw_player_on_tile(self, x_offset: int, y_offset: int, x_tile: int, y_tile: int, tile_image_legend: dict):
        """
        Draw the player in the center of the image

        :param x_offset: The x offset to draw the tile on
        :param y_offset: The y offset to draw the tile on
        :param x_tile: The x coordinate of the current tile
        :param y_tile: The y coordinate of the current tile
        :param tile_image_legend: A legend to determine what file should be used for the tile
        """
        player_image = Image.open('../extra_files/tileImages/player.png').convert('RGBA').resize((100, 160))
        tile_image = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[y_tile][x_tile]]}.png').resize((100, 160))
        background = self.image.crop([100, 80, 200, 240])
        map_image = Image.alpha_composite(background, tile_image)
        player_on_tile = Image.alpha_composite(map_image, player_image)
        self.image.paste(player_on_tile, (x_offset, y_offset))

    def draw_tile_image(self, x_offset: int, y_offset: int, x_tile: int, y_tile: int, tile_image_legend: dict):
        """

        :param x_offset: The x offset to draw the tile on
        :param y_offset: The y offset to draw the tile on
        :param x_tile: The x coordinate of the current tile
        :param y_tile: The y coordinate of the current tile
        :param tile_image_legend: A legend to determine what file should be used for the tile
        """
        tile_image = Image.open(f'../extra_files/tileImages/{tile_image_legend[self.world_map[y_tile][x_tile]]}.png').resize((100, 160))
        background = self.image.crop([x_offset, y_offset, x_offset + 100, y_offset + 160])
        final_tile = Image.alpha_composite(background, tile_image)
        self.image.paste(final_tile, ([x_offset, y_offset, x_offset + 100, y_offset + 160]))

    def get_location_description(self):
        """
        Get the description of the current location of the player
        """
        location_legend = {
            '0': 'You find yourself on clear land.',
            'H': 'You find yourself home! Home sweet home!',
            'W': 'WATER'
        }

        # If a new location was set
        if self.location_updated:
            self.location_description = location_legend[self.world_map[self.location_y][self.location_x]]

        # Otherwise use the old values
        else:
            if len(self.messages['error']) == 0:
                self.location_description = location_legend[self.world_map[self.location_y][self.location_x]]
            else:
                self.location_description = location_legend[self.world_map[self.original_y][self.original_x]]

    def create_embed(self):
        """
        Create an embed based on the player's current travel state
        """
        timestamp = int(datetime.datetime.now().timestamp())
        self.embed = Embed()
        self.embed.set_image(url=f'{self.image_url}{self.user_name}_overview_map.png?{timestamp}')
        self.embed.add_field(name='Info', value=self.location_description)
        if len(self.messages['error']) > 0:
            self.embed.add_field(name='ERROR', value='\n'.join(self.messages['error']))
