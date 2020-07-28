"""
Contains all functionality around inventory management within the game
"""
from PIL import Image, ImageDraw


class CreateInventoryImage:
    """
    Create an image based on the items in the inventory of a player
    """

    def __init__(self, file_name: str, columns: int = 4, rows: int = 4, highlight: int = 0, items: dict = False):
        """
        Create an image based on the items in the inventory of a player. The file path starts in the extra_files folder.

        :param file_name: What name to save the file as
        :param columns: Number of columns to display
        :param rows: Number of rows to display
        :param highlight: Which cell to highlight as selected
        :param items: Items in the player's inventory to display
        """

        self.file_name = f'../extra_files/{file_name}'
        self.item_box_size = 90
        self.border = 10
        self.columns = columns
        self.rows = rows
        self.highlight = highlight
        self.items = items
        self.item_locations = []
        self.image = None

        self.create_entire_image()

    def create_entire_image(self):
        """
        Every function ran to create the end resulting image
        """
        x, y = self.create_basic_image()
        self.add_empty_item_slots(x, y)
        self.highlight_cell()
        self.add_items()
        self.image.save(self.file_name)

    def create_basic_image(self):
        """
        Create the basic image with the standard colours
        """
        x = int(self.item_box_size * self.columns + self.border * 2)
        y = int(self.item_box_size * self.rows + self.border * 2)

        self.image = Image.new('RGBA', (x, y))
        ImageDraw.Draw(self.image).rectangle([(0, 0), (x, y)], fill=(26, 9, 0))
        return x, y

    def add_empty_item_slots(self, x: int, y: int):
        """
        Add cells for each item to be placed in

        :param x: Width of the image in pixels
        :param y: Height of the image in pixels
        """
        x = x - (self.border * 2)
        y = y - (self.border * 2)
        for row in range(self.rows):
            for column in range(self.columns):
                x_min = int(self.border + (x / self.columns * column))
                y_min = int(self.border + (y / self.rows * row))
                x_max = int(self.border + (x / self.columns * (column + 1)))
                y_max = int(self.border + (y / self.rows * (row + 1)))
                self.item_locations.append([x_min, y_min, x_max, y_max])
                ImageDraw.Draw(self.image).rectangle([(x_min, y_min), (x_max, y_max)], fill=(50, 50, 50))
                ImageDraw.Draw(self.image).rectangle([(x_min + 2, y_min + 2), (x_max - 2, y_max - 2)], fill=(77, 26, 0))

    def highlight_cell(self):
        """
        Highlight a particular cell that is selected
        """
        x_min = self.item_locations[self.highlight][0]
        y_min = self.item_locations[self.highlight][1]
        x_max = self.item_locations[self.highlight][2]
        y_max = self.item_locations[self.highlight][3]
        ImageDraw.Draw(self.image).rectangle([(x_min, y_min), (x_max, y_max)], fill=(255, 255, 255))
        ImageDraw.Draw(self.image).rectangle([(x_min + 2, y_min + 2), (x_max - 2, y_max - 2)], fill=(77, 26, 0))

    def add_items(self):
        """
        Add items from the player's inventory to be displayed in the image
        """
        icon_width = self.item_locations[0][2] - self.item_locations[0][0] - 10
        icon_height = self.item_locations[0][3] - self.item_locations[0][1] - 10

        for position, item_object in self.items.items():
            item_icon = Image.open(item_object.image_path)
            item_icon = item_icon.resize([icon_width, icon_height])
            x_min = int(self.item_locations[position][0] + (self.border / 2))
            y_min = int(self.item_locations[position][1] + (self.border / 2))
            x_max = int(self.item_locations[position][2] - (self.border / 2))
            y_max = int(self.item_locations[position][3] - (self.border / 2))
            self.image.paste(item_icon, [x_min, y_min, x_max, y_max], item_icon)


if __name__ == '__main__':
    from src import item_manager
    CreateInventoryImage(file_name='test.png', columns=4, rows=4, highlight=10, items={
        0: item_manager.BaseItem('bow', 'Awesome Bow of Shooting', {'attack': 1}),
        3: item_manager.BaseItem('sword', 'Pointy Stick', {'attack': 2}),
        9: item_manager.BaseItem('sword', 'Big Knife', {'friends': -2}),
        7: item_manager.BaseItem('bow', 'Twig and String', {'attack_range': -5}),
        14: item_manager.BaseItem('bow', 'Deluxe Master 3001', {'attack_speed': 6}),
    })
