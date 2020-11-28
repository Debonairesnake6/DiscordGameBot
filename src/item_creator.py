"""
This will contain all of the information about all of the items for the game.
"""


import json


class BaseItem:
    """
    This will include any basic stats about an item. The current base items are:
    Sword, Shield, Bow
    """

    def __init__(self, real_name: str, display_name: str = False, modifiers: dict = False):
        """
        This will include any basic stats about an item. The current base items are:
        Sword, Shield, Bow

        :param real_name: Name of the original item
        :param display_name: Display name of the item
        :param modifiers: Any modifiers to add to the base stats of an item
        """
        self.real_name = real_name
        if not display_name:
            self.display_name = real_name
        else:
            self.display_name = display_name

        self.stats = {
            'attack': 0,
            'defense': 0,
            'attack_speed': 0,
            'attack_range': 0,
            'extra_targets': 0,
            'heal': 0
        }
        self.modifiers = modifiers
        self.image_path = None
        self.json_object = None

        self.run_all_functions()

    def run_all_functions(self):
        """
        run all of the functions required to create an item
        """
        self.create_basic_item()
        if self.modifiers is not False:
            self.add_modifiers()
        self.load_image_path()
        self.to_json()

    def create_basic_item(self):
        """
        Create an item with it's basic stats
        """
        base_items = {
            'sword': {'attack': 5, 'defense': 1, 'attack_speed': 2, 'attack_range': 3},
            'shield': {'attack': 1, 'defense': 3, 'attack_speed': 1, 'attack_range': 1},
            'bow': {'attack': 4, 'attack_speed': 2, 'attack_range': 10}
        }
        for stat, value in base_items[self.real_name].items():
            self.stats[stat] = value

    def add_modifiers(self):
        """
        Add any additional modifiers to the base stats of the weapon
        """
        for stat, value in self.modifiers.items():
            self.stats[stat] = self.stats.get(stat, 0) + value

    def load_image_path(self):
        """
        Load the path for the image of the item
        """
        image_paths = {
            'sword': '../extra_files/icons/sword.png',
            'bow': '../extra_files/icons/bow.png'
        }
        self.image_path = image_paths[self.real_name]

    def to_json(self):
        """
        Return the object as a json serializable object
        :return:
        """
        self.json_object = json.dumps(self, default=lambda o: o.__dict__)


if __name__ == '__main__':
    sword = BaseItem('sword')
    bow = BaseItem('bow', 'Awesome Bow of Shooting', {'attack': 1})
    print()
