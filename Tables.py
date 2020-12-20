''' IMPORTS '''

import asyncio
from sys import executable
import discord
import re
import traceback

from gspread.utils import rowcol_to_a1


import Database
import Logger
from Logger import log
import Support
from Support import simple_bot_response



''' CONSTANTS '''

aliases = ["", ]
table_length = 1000



''' CLASSES '''

class Table:
    def __init__(self, range=None, guild_id=None, workbook_key=None, worksheet_id=None, left_aligned=[], right_aligned=[], centered=[], no_markdown_cols=[], no_markdown_rows=[], table_style="multi_markdown", cells=[]):
        self.range = a1_to_numeric(range) if range else None
        self.guild_id = guild_id
        self.workbook_key = workbook_key
        self.worksheet_id = worksheet_id

        self.cells = cells # this is from the gspread.range
        self.cell_values = self.get_cell_values() if cells else None

        # style options
        self.left_aligned = [a1_to_numeric(r) for r in left_aligned]
        self.right_aligned = [a1_to_numeric(r) for r in right_aligned]
        self.centered = [a1_to_numeric(r) for r in centered]

        self.no_markdown_cols = [a1_to_numeric(r) for r in no_markdown_cols] # these are overwritten by multi_markdown style
        self.no_markdown_rows = [a1_to_numeric(r) for r in no_markdown_rows] # these also need to be corrected for offset, B:C should be 0 and 1 not 2 and 3

        self.table_style = table_style
    # end __init__


    def get_cells(self):
        gc = Support.get_g_client()
        workbook = gc.open_by_key(self.workbook_key)
        worksheet = [ws for ws in workbook.worksheets() if str(ws.id) == self.worksheet_id]
        worksheet = worksheet[0] if worksheet else None

        if not worksheet or not self.range:
            return None
            
        first_row = self.range[0][1]
        first_col = self.range[0][0]
        last_row = self.range[1][1] if self.range[1][1] != "_" else worksheet.row_count
        last_col = self.range[1][0] if self.range[1][0] != "_" else worksheet.col_count

        return worksheet.range(first_row, first_col, last_row, last_col)
    # end get_table


    def get_cell_values(self):
        values = []

        row = [self.cells[0]]
        for cell in self.cells[1:]:

            if cell.row != row[-1].row:
                values.append([c.value for c in row])
                row = [cell]

            else:
                row.append(cell)

        values.append([c.value for c in row])
        return values
    # end get_cell_values

    def get_table_displays(self):
        """
            styles: multi_markdown, single_markdown, plain
            if single line markdown, ability to not markdown specific columns
            ability to not markdown specific rows
        """

        is_multi_markdown = self.table_style == "multi_markdown" # everything surroudned by ```
        is_single_markdown = self.table_style == "single_markdown" # individual rows surroudned by `

        numeric_range = self.range
        col_offset = numeric_range[0][0]
        row_offset = numeric_range[0][1] 


        ## GET MAX WIDTHS ##

        col_max_widths = [0] * len(self.cell_values[0])
        for row in self.cell_values:
            for i, value in enumerate(row):
                col_max_widths[i] = len(value) if len(value) > col_max_widths[i] else col_max_widths[i]


        ## CREATE TABLES ##

        tables = [""]
        tables[-1] += "```" if is_multi_markdown else ""

        for i, row in enumerate(self.cell_values): # loop rows
            
            line = []
            for j, value in enumerate(row): # loop cols in row
                v = ""
                if row_col_in_range(i + row_offset, j + col_offset, self.left_aligned): # left align
                    v = value.ljust(col_max_widths[j], " ")

                if row_col_in_range(i + row_offset, j + col_offset, self.right_aligned): # right align
                    v = value.rjust(col_max_widths[j], " ")

                if row_col_in_range(i + row_offset, j + col_offset, self.centered): # center
                    v = value.center(col_max_widths[j], " ")

                if (
                    is_single_markdown and 
                    not row_col_in_range(i + row_offset, j + col_offset, self.no_markdown_cols)
                ): # wrap in ``, once wrapped later, it will reverse the effect
                    v = f"`{v}`"

                line.append(v)


            line = f"{'|' if is_multi_markdown else ' '}".join(line)


            if (
                is_single_markdown and
                row_col_in_range(i + row_offset, 1, self.no_markdown_rows)
            ): # remove ` if no markdown row
                line = line.replace("`", "")

            
            line = f"{line}\n"
                
            
            if len(tables[-1] + line) < table_length: # yes, new table = new message
                tables[-1] += line

            else:
                tables[-1] += "```" if is_multi_markdown else ""
                tables.append("```" if is_multi_markdown else "")
                tables[-1] += line

        tables[-1] += "```" if is_multi_markdown else ""
        
        return tables

    # end get_table_displays
# end Table



''' FUNCTIONS '''

async def main(message, args, author_perms):
    """
        @Phyner _command_
    """

# end main


def row_col_in_range(row, col, numeric_ranges):
    """
        numeric_range is A1:B10 >> [[1, 1], [2, 10]]
    """

    in_ranges = []
    for numeric_range in numeric_ranges:
        if numeric_range == "all":
            return True

        if numeric_range == "none":
            return False

        in_ranges.append(
            row >= numeric_range[0][1] and
            (numeric_range[1][1] == "_" or row <= numeric_range[1][1]) and
            col >= numeric_range[0][0] and
            (numeric_range[1][0] == "_" or col <= numeric_range[1][0])
        )

    return any(in_ranges)
# end row_col_in_range


def a1_to_numeric(a1_range):
    """
        A1:B10 >> [[1, 1], [2, 10]]
        A:B >> [[1, 1], [2, _]]
        A:1 >> [[1, 1], [1, 1]]
        A: >> [[1, 1], [1, _]]
        _ is to end
    """


    if a1_range in ["all", "none"]:
        return a1_range


    range = [[0, 0], [0, 0]]
    a1_cells = f"{a1_range.upper()}:".split(":")[:2] # A1 >> A1: >> [A1, ''], A1:A10 >> A1:A10: >> [A1, A10]


    for i, cell in enumerate(a1_cells): 


        ## GET COLS ##

        col = re.findall(r"([A-Z]+)", cell)

        if col: # letters in cell
            for j, letter in enumerate(col[0][::-1]): # reverse letters so 26 ^ j works out easier
                range[i][0] += (ord(letter) - ord("A") + 1) * (26 ** j) # C - A + 1 = 3 * the digit, i.e. 3 * (26 ** 1) if 2nd digit

        elif i == 0: # if first cell, col = A, or 1
            range[i][0] = 1

        else: # if second cell, col = first cell's col
            range[i][0] = "_"


        ## GET ROWS ## 

        row = re.findall(r"(\d+)", cell)

        if row: # row given
            range[i][1] = int(row[0])

        elif i == 0: # if first cell row = 1
            range[i][1] = 1

        else: # if second cell, row = _
            range[i][1] = "_"


    if range[1][0] != "_" and range[1][0] < range[0][0]: # switcherro if right col is bigger than left and not 0
        t = range[0][0]
        range[0][0] = range[1][0]
        range[1][0] = t

    if range[1][1] != "_" and range[1][1] < range[0][1]: # same as above but for rows
       t = range[0][1]
       range[0][1] = range[1][1]
       range[1][1] = t

    return range
# end a1_to_numeric


def numeric_to_a1(numeric_range):
    """
        [[1, 1], [2, 10]] >> A1:B10
        [[1, 1], [2, 0]] >> A0:B0
    """

    if numeric_range in ["all", "none"]:
        return numeric_range

    a1_range = ""
    for cell in numeric_range:
    
        ## GET COL ##

        col = cell[0]
        col_letters = ""
        while True:
            if col < 26: # single letter column
                col_letters += chr(col + ord("A") - 1)
                break

            # 53 >> BA
            r = col % 26 # 53 % 26 = 1, or A
            col_letters += chr(r + ord("A") - 1) # the remainder is the letter
            col = (col // 26) # 53 // 26 = 2, so last letter is A

        # end while

        a1_range += f"{col_letters[::-1]}{cell[1]}:" # reverse col and append the row


    return a1_range[:-1] # rids the extra :
# end numeric_to_a1


def get_table_from_entry(entry):
    return Table (
        guild_id=int(entry[0]),

        range=entry[1],
        workbook_key=entry[2],
        worksheet_id=entry[3],

        left_aligned=entry[4].split(","),
        right_aligned=entry[5].split(","),
        centered=entry[6].split(","),

        no_markdown_cols=entry[7].split(","),
        no_markdown_rows=entry[8].split(","),

        table_style=entry[9],

    )
# end get_table_from_entry


def get_tables(guild_id="%%"):
    db = Database.connect_database()
    db.cursor.execute(f"""
        SELECT * FROM Tables
        WHERE guild_id LIKE '{guild_id}'
    ;""")
    db.connection.close()
    return [get_table_from_entry(entry) for entry in db.cursor.fetchall()]
# end Tables


tables = get_tables(guild_id=789181254120505386)
table = tables[0]
table.cells = table.get_cells()
table.cell_values = table.get_cell_values()
tables = table.get_table_displays()
[print(f"{table}\n---\n") for table in tables]