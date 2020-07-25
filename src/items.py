"""
This will contaion all of the information about all of the items for the game
"""


def create_item(name: str, modifiers: dict = False):
    """
    This will create an item based on the given name

    :param name: Name of the item
    :param modifiers: Any modifiers to add to the base stats of an item
    """
    base_items = {
        'sword': {'attack': 5, 'defense': 1, 'attack_speed': 2, 'attack_range': 3},
        'shield': {'attack': 1, 'defense': 3, 'attack_speed': 1, 'attack_range': 1},
        'bow': {'attack': 4, 'attack_speed': 2, 'attack_range': 10}
    }
    name = name
    modifiers = modifiers
    item_stats = base_items[name]

    # Add modifiers
    for stat, value in modifiers.items():
        item_stats[stat] += value

    # Create the Item

    item = BaseItem()


class BaseItem:
    """
    This will include any basic stats about an item
    """

    def __init__(self, name: str, attack: int = 0, defense: int = 0, attack_speed: int = 0, attack_range: int = 0,
                 extra_targets: int = 0, heal: int = 0):
        """
        This will include any basic stats about an item

        :param name: Name of the item
        :param attack: Attack damage
        :param defense: Dense stat
        :param attack_speed: How often the item can attack
        :param attack_range: Range of the item
        :param extra_targets: How many additional targets the item will damage
        :param heal: How much the item will heal
        """
        self.name = name
        self.attack = attack
        self.defense = defense
        self.attack_speed = attack_speed
        self.attack_range = attack_range
        self.extra_targets = extra_targets
        self.heal = heal
