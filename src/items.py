"""
This will contain all of the information about all of the items for the game.
"""


class BaseItem:
    """
    This will include any basic stats about an item. The current base items are:
    Sword, Shield, Bow
    """

    def __init__(self, name: str, modifiers: dict = False):
        """
        This will include any basic stats about an item. The current base items are:
        Sword, Shield, Bow

        :param name: Name of the item
        :param modifiers: Any modifiers to add to the base stats of an item
        """
        self.name = name
        self.stats = {
            'attack': 0,
            'defense': 0,
            'attack_speed': 0,
            'attack_range': 0,
            'extra_targets': 0,
            'heal': 0
        }
        self.modifiers = modifiers

        self.create_basic_item()

        if modifiers is not False:
            self.add_modifiers()

    def create_basic_item(self):
        """
        Create an item with it's basic stats
        """
        base_items = {
            'sword': {'attack': 5, 'defense': 1, 'attack_speed': 2, 'attack_range': 3},
            'shield': {'attack': 1, 'defense': 3, 'attack_speed': 1, 'attack_range': 1},
            'bow': {'attack': 4, 'attack_speed': 2, 'attack_range': 10}
        }
        for stat, value in base_items[self.name].items():
            self.stats[stat] = value

    def add_modifiers(self):
        """
        Add any additional modifiers to the base stats of the weapon
        """
        for stat, value in self.modifiers.items():
            self.stats[stat] += value


if __name__ == '__main__':
    sword = BaseItem('sword')
    bow = BaseItem('bow', {'attack': 1})
    print()
