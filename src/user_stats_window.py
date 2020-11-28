"""
This class handles the user stats window
"""

import aws
import text_to_image


class UserStatsWindow:
    """
    This class handles the user stats window
    """
    def __init__(self):
        self.user_info = None
        self.user = None
        self.aws = aws.AWSHandler()

    def create_user_stat_table(self, width: int = False):
        """
        Create the pretty table version of the user's stats

        :param width: The size of the column width if specified
        """
        if not width:
            width = 3
        ignored_columns = ['UID', 'Name', 'isBusy']
        text_to_image.CreateImage(titles=[title for title in self.user_info[self.user].keys() if title not in ignored_columns],
                                  rows=[[str(value) for title, value in self.user_info[self.user].items()
                                         if title not in ignored_columns]],
                                  file_name=f'../extra_files/{self.user}_user_info.jpg',
                                  column_width=width)
        self.aws.upload_image(self.user, 'user_info.jpg')
