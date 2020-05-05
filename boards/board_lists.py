"Generates a list of boards from current directory"
import csv
import os
import os.path as path
from collections import namedtuple

BoardFile = namedtuple("BoardFile", "name data image")

def get_data_from_csv(file):
    "Generates dict for board from csv"
    data = {}
    for row in csv.reader(file):
        data[int(row[0])] = int(row[1])
    return data


def board_list():
    "Generate list of boards from directories in this folder"
    boards_dir = path.dirname(__file__)
    boards = []
    for directory in os.listdir(boards_dir):
        if not path.isdir(path.join(boards_dir, directory)):
            continue
        data_file = path.join(boards_dir, directory, "board.csv")
        if not path.isfile(data_file):
            continue
        with open(data_file) as board:
            data = get_data_from_csv(board)
        name = directory
        image_path = path.join(boards_dir, directory, "board.jpg")
        if not path.isfile(image_path):
            image_path = None
        boards.append(BoardFile(name, data, image_path))
    return boards


BOARDS = board_list()
