"""
This file will create an image from the input as a table
"""

import prettytable

from PIL import Image, ImageDraw, ImageFont


class CreateImage:
    """
    Create an image from the given input
    """
    def __init__(self, titles: list, rows: list, file_name: str, colour: list = False, convert_columns: bool = False,
                 title_colours: list = False, column_width: int = False):
        """
        Create an image from the given input

        :param titles: List of names to use for the titles of each column
        :param rows: List of rows to add to the table
        :param file_name: Name to save the file as
        :param colour: Dual array of colours to colour each word in the table
        :param convert_columns: Convert the riven rows from columns into rows
        :param title_colours: Array of colours to paint the titles with
        :param column_width: The number of columns to display horizontally
        """
        self.titles = titles
        self.rows = rows
        self.table_to_image = None
        self.file_name = file_name
        self.colour = colour
        self.convert_columns = convert_columns
        self.title_colours = title_colours
        self.column_width = column_width
        self.columns_processed = 0
        self.table_string = None
        self.title_rows = None

        # Setup and add rows to the table
        self.table = prettytable.PrettyTable()
        if not column_width:
            self.create_single_table()
        else:
            self.convert_to_multiple_tables()

        # Create the image from the table
        self.turn_into_image()
        self.save_image()

    def create_single_table(self):
        """
        Add the titles and rows
        """
        self.table.field_names = self.titles
        if self.convert_columns:
            self.rows = self.convert_columns_to_rows(self.rows)
            if self.colour:
                self.colour = self.convert_columns_to_rows(self.colour)

        for row in self.rows:
            self.table.add_row(row)

        self.table_string = self.table.get_string()

    def convert_to_multiple_tables(self):
        """
        Convert to multiple tables to have more verticality
        """
        self.title_rows = (len(self.titles) / self.column_width).__round__()
        joined_tables = self.split_and_join_tables()
        needed_width = self.get_correct_spacing()
        joined_tables = self.set_correct_spacing(joined_tables, needed_width)
        self.table_string = self.correct_borders(joined_tables)

    @staticmethod
    def correct_borders(joined_tables: str) -> str:
        """
        Fix the borders in the table

        :param joined_tables: String of tables joined together
        :return: The string of tables with fixed borders
        """
        original_table = ''
        first_row = joined_tables.split('\n')[0]
        for row in joined_tables.split('\n'):
            if ' ' not in row and row != first_row:
                original_table += first_row
            elif len(row) != len(first_row):
                row += '|'
                while len(row) < len(first_row):
                    row = f'{row[:-1]} {row[-1]}'
                original_table += row
            else:
                original_table += row
            original_table += '\n'
        original_table = original_table.strip()
        return original_table

    def get_correct_spacing(self) -> list:
        """
        Fix the spacing for different title or value widths

        :return: List of spacing needed for each column
        """
        needed_width = []
        for row in range(self.column_width):
            largest_title = max([len(title) for title in self.titles[row::self.column_width]])
            largest_value = max([len(amount) for amount in [value
                                                            for total_row, _ in enumerate(self.rows)
                                                            if total_row is not None
                                                            for value in self.rows[total_row][row::self.column_width]]])
            needed_width.append(max(largest_title, largest_value) + 2)
        return needed_width

    def set_correct_spacing(self, joined_tables: list, needed_width: list) -> str:
        """
        Set the correct amount of spacing for each column

        :param joined_tables: List of the split tables
        :param needed_width: Width needed for each column to be spaced out
        :return: Fixed tables string
        """
        for table_cnt, table in enumerate(joined_tables):
            for row in table.split('\n'):
                if ' ' not in row:
                    table = self.fix_spacing_in_row(table, row, needed_width, '+', '-')
                else:
                    table = self.fix_spacing_in_row(table, row, needed_width, '|', ' ')
            joined_tables[table_cnt] = table
        joined_tables.append(joined_tables[-1].split('\n')[0])
        joined_tables = '\n'.join(joined_tables)
        return joined_tables

    @staticmethod
    def fix_spacing_in_row(table: str, row: str, needed_width: list, delimiter: str, addition: str) -> str:
        """
        Fix the spacing in the given row

        :param table: The string of the current table
        :param row: The string of the current row
        :param needed_width: Needed width for each column
        :param delimiter: What delimiter to use
        :param addition: What to add to the row
        :return: Fixed table string
        """
        for cnt, column in enumerate(row.split(delimiter)[1:-1]):
            side = 'right'
            while len(column) < needed_width[cnt]:
                indexes = [pos for pos, char in enumerate(row) if char == delimiter]
                if side == 'left':
                    table = table.replace(row, f'{row[:indexes[cnt] + 1]}{addition}{row[indexes[cnt] + 1:]}')
                    side = 'right'
                    row = f'{row[:indexes[cnt] + 1]}{addition}{row[indexes[cnt] + 1:]}'
                else:
                    table = table.replace(row, f'{row[:indexes[cnt + 1]]}{addition}{row[indexes[cnt + 1]:]}')
                    side = 'left'
                    row = f'{row[:indexes[cnt + 1]]}{addition}{row[indexes[cnt + 1]:]}'
                column = f'{column}{addition}'
        return table

    def split_and_join_tables(self) -> list:
        """
        Split the tables based on self.column_width and join them below each other

        :return: List of the split tables
        """
        joined_tables = []
        for width in range(self.title_rows):
            table = prettytable.PrettyTable()
            table.field_names = self.titles[self.columns_processed:self.columns_processed + self.column_width]
            [table.add_row(row[self.columns_processed:self.columns_processed + self.column_width]) for row in self.rows]
            remove_border = "\n".join(table.get_string().split('\n')[:-1])
            joined_tables.append(remove_border)
            self.columns_processed += self.column_width
        return joined_tables

    def turn_into_image(self):
        """
        Turn the table into an image
        """
        if self.title_colours:
            self.table_to_image = TableToImage(self.table_string, self.colour, self.rows, self.titles,
                                               self.title_colours)
        else:
            self.table_to_image = TableToImage(self.table_string, self.colour, self.rows)

    def save_image(self):
        """
        Save the image as the given file name
        """
        self.table_to_image.img.save(self.file_name)

    def convert_columns_to_rows(self, columns: list):
        """
        Convert the given columns into rows to be able to create the image

        :param columns: List of columns to convert
        """
        fixed_rows = self.create_row_for_max_column_length(columns)
        return self.add_data_from_columns_into_rows(columns, fixed_rows)

    @staticmethod
    def create_row_for_max_column_length(columns) -> list:
        """
        Create a rows to match the longest column length in the given array

        :param columns: List of columns to create placeholder rows for
        :return: Array with rows fitting the max length of the given columns
        """
        fixed_rows = []
        for column in range(len(max(columns))):
            fixed_rows.append([])
        return fixed_rows

    @staticmethod
    def add_data_from_columns_into_rows(columns: list, fixed_rows: list):
        """
        Add the given data into the fixed_rows array

        :param columns: List of columns to convert into rows
        :param fixed_rows: Array with fixed positions converting columns into rows
        """
        for column in range(len(max(columns))):
            for row in range(len(columns)):
                try:
                    fixed_rows[column].append(columns[row][column])
                except IndexError:
                    fixed_rows[column].append('')
        return fixed_rows


class TableToImage:
    """
    Create an image from the text table given to it
    """

    def __init__(self, table: str, table_colour: list = False, original_rows: list = False, titles: list = False,
                 title_colours: list = False):
        """
        Create an image from the text table given to it

        :param table: String of table to create
        :param table_colour: Array of colour to print
        :param original_rows: Array of original rows to use for colouring
        :param titles: Name of each title if they need to be coloured
        :param title_colours: What to colour each title
        """
        self.img = None
        self.font = None
        self.draw = None
        self.processed = None
        self.row_cnt = None
        self.column_cnt = None
        self.table = table
        self.table_colour = table_colour
        self.original_rows = original_rows
        self.titles = titles
        self.title_colours = title_colours
        self.colour = None
        self.word = None
        self.colours = {
            '': (255, 255, 255),
            'red': (255, 0, 0),
            'orange': (255, 106, 0),
            'yellow': (255, 255, 0),
            'blue': (50, 150, 255),
            'green': (0, 153, 51),
            'iron': (91, 82, 83),
            'bronze': (136, 75, 48),
            'silver': (134, 158, 166),
            'gold': (201, 136, 52),
            'platinum': (62, 121, 120),
            'diamond': (131, 184, 215),
            'master': (146, 100, 182),
            'grandmaster': (214, 51, 46),
            'challenger': (255, 154, 43),
            'black': (0, 0, 0),
            'unranked': (255, 255, 255)
        }

        self.setup_image()
        if table_colour:
            self.colour_image()
        if title_colours:
            self.colour_titles()

    def setup_image(self):
        """
        Basic setup for the image to set the size, font, background colour, and all of the text in black
        """
        # Create the correct size image for the table
        rows = self.table.count('\n')
        columns = self.table.split('\n')[0].count('-') + self.table.split('\n')[0].count('+')
        self.img = Image.new('RGB', ((columns * 12) + 24, rows * 21 + 48), color=(54, 57, 63))

        # Initialize font and drawing object
        self.font = ImageFont.truetype('../extra_files/cour.ttf', 20)
        self.draw = ImageDraw.Draw(self.img)

        # Draw the table without markings
        for x in range(5):
            self.draw.text((12, 12), self.table, font=self.font, fill=(255, 255, 255))

    def colour_image(self):
        """
        Colour the image based on the array
        """
        for row_cnt, colour_row in enumerate(self.table_colour):
            self.processed = []
            for column_cnt, colour in enumerate(colour_row):
                self.row_cnt = row_cnt + 3
                self.column_cnt = column_cnt
                self.colour = colour
                self.word = self.original_rows[self.row_cnt - 3][self.column_cnt]
                self.colour_specific_word()

    def colour_titles(self):
        """
        Colour the titles based on the information given
        """
        self.processed = []
        for colour_cnt, title_colour in enumerate(self.title_colours):
            self.row_cnt = 1
            self.word = self.titles[colour_cnt]
            self.colour = title_colour
            self.colour_specific_word()

    def colour_specific_word(self):
        """
        Colour the specific word based on the row and column count
        """
        if self.colour != '':
            row_string = self.table.split('\n')[self.row_cnt]

            # If word only appears once
            if row_string.count(self.word) == 1:
                x_position = row_string.index(self.word)

            # If the word appears multiple times
            else:
                x_position = [x_pos for x_pos in range(len(row_string)) if row_string.startswith(self.word, x_pos)
                              and row_string[x_pos + len(self.word)] in [' ', '|'] and row_string[x_pos - 1] in
                              [' ', '|']][self.processed.count(self.word)]

            # Fill with black first
            for x in range(5):
                self.draw.text(((x_position * 12) + 12, (self.row_cnt * 21) + 12),
                               self.word, font=self.font,
                               fill=self.colours['black'])

            # Fill with the desired colour
            for x in range(5):
                self.draw.text(((x_position * 12) + 12, (self.row_cnt * 21) + 12),
                               self.word, font=self.font,
                               fill=self.colours[self.colour])
        self.processed.append(self.word)


if __name__ == '__main__':

    import shelve
    tmp = dict(shelve.open('../extra_files/shelves/text_to_image'))['user_info']
    new = CreateImage(tmp['titles'], tmp['rows'], tmp['file_name'], tmp['colour'], tmp['convert_columns'],
                      tmp['title_colours'], tmp['column_width'])
    new.save_image()
    print()
