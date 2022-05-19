import time
import string
import operator

from rich import print
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.layout import Layout

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from collections import Counter
from itertools import chain
from pathlib import Path


class Quordle:
    def __init__(self):
        self.guesses = 9  # Guesses left
        print("[blue]Quordle Bot Initiated![/blue]")
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.get("https://www.quordle.com/")

        self.boards = [
            (self.driver.find_elements(by=By.XPATH, value="/html/body/div/div/div[2]/div[1]/div[1]/div[1]")[0],
             "/html/body/div/div/div[2]/div[1]/div[1]/div[1]"),
            (self.driver.find_elements(by=By.XPATH, value="/html/body/div/div/div[2]/div[1]/div[1]/div[2]")[0],
             "/html/body/div/div/div[2]/div[1]/div[1]/div[2]"),
            (self.driver.find_elements(by=By.XPATH, value="/html/body/div/div/div[2]/div[1]/div[2]/div[1]")[0],
             "/html/body/div/div/div[2]/div[1]/div[2]/div[1]"),
            (self.driver.find_elements(by=By.XPATH, value="/html/body/div/div/div[2]/div[1]/div[2]/div[2]")[0],
             "/html/body/div/div/div[2]/div[1]/div[2]/div[2]")
        ]
        print(f"[green]Boards detected![/green]")

        self.grid = None

        print(f"[yellow]Inputting starters...[/yellow]")
        self.type_enter("adieu")
        self.type_enter("crown")
        self.type_enter("nymph")
        self.type_enter("roast")

    def type_enter(self, text):
        actions = ActionChains(self.driver)
        actions.send_keys(text)
        actions.send_keys(Keys.RETURN)
        actions.perform()
        self.guesses -= 1
        # Check if wordle didn't accept the word
        time.sleep(0.1)  # Let deny animation play
        read_res = self.read()
        if str(read_res.data[0][9 - (self.guesses + 1)][0]) == "_":
            self.guesses += 1
            raise RuntimeError(f"Word {text} not accepted by wordle!")

    def read(self, board_no: int = 0):
        def read_classes(classes):
            possible_classes = ("bg-box-diff", "bg-box-correct")
            rich_conversion = {
                "none": "white",
                "bg-box-diff": "yellow",
                "bg-box-correct": "green"
            }
            for possible in possible_classes:
                if possible in classes:
                    return rich_conversion[possible]
            return rich_conversion["none"]

        def calc(board_path):
            read_board = []
            for _ in range(9 - self.guesses):
                row = board_path + f"/div[{_ + 1}]"
                letters = [
                    RichText(
                        self.driver.find_element(by=By.XPATH, value=row + f"/div[{letter + 1}]/div[1]").text,
                        read_classes(
                            self.driver.find_element(by=By.XPATH, value=row + f"/div[{letter + 1}]").get_attribute(
                                "class"))
                    ) for
                    letter in
                    range(5)]
                read_board.append(letters)
            for _ in range(self.guesses):
                read_board.append([RichText("_", "grey53") for letter in range(5)])
            return read_board

        if board_no == 0:
            to_return = []
            for board in self.boards:
                to_return.append(calc(board[1]))
        else:
            to_return = [calc(self.boards[board_no][1])]
        if not self.grid:
            self.grid = QuordleGrid(to_return)
        else:
            self.grid.data = to_return
        return self.grid


class RichText:
    def __init__(self, text, style, correct_bool=True):
        self.text = text
        self.style = style
        self.bool = True if style == "green" and correct_bool else False

    def __str__(self):
        return self.text

    def __bool__(self):
        return self.bool

    def __rich__(self):
        return Text(self.text, self.style)


class QuordleGrid:
    def __init__(self, data):
        self.data = data
        self.layout = Layout()
        self.layouts = ["tl", "tr", "bl", "br"]
        self.tables = []

        self.layout.split_column(
            Layout(name="upper"),
            Layout(name="lower")
        )
        self.layout["upper"].split_row(
            Layout(name="tl"),
            Layout(name="tr"),
        )
        self.layout["lower"].split_row(
            Layout(name="bl"),
            Layout(name="br"),
        )

        self.generate_tables()

    def generate_tables(self):
        self.tables = []
        for grid, layout_code in zip(self.data, self.layouts):
            table = Table(show_header=False, expand=True, show_lines=False)
            for _ in range(5):
                table.add_column("", justify="center")
            for row in grid:
                table.add_row(*[letter for letter in row])
            self.tables.append(table)
            self.layout[layout_code].update(table)
        return self.tables

    def __iter__(self):
        for _ in self.data:
            yield _

    def __rich__(self):
        print("update")
        self.generate_tables()
        return self.layout


class Logic:
    ALLOWED_CHARACTERS = set(string.ascii_letters)
    ALL_WORDS = {
        word.lower()
        for word in Path("./words.txt").read_text().splitlines()
        if len(word) == 5 and set(word) < set(string.ascii_letters)
    }

    def __init__(self, data):
        self.not_in = []
        self.wrong_pos = []
        self.correct_pos = []

        self.LETTER_COUNTER = Counter(chain.from_iterable(Logic.ALL_WORDS))
        self.LETTER_FREQUENCY = {
            character: value / self.LETTER_COUNTER.total()
            for character, value in self.LETTER_COUNTER.items()
        }

        for row in data:
            for letter, num in zip(row, range(5)):
                if letter.style == "white":
                    for correct in self.correct_pos:
                        if letter.text.lower() == correct[0]:
                            break
                    else:
                        if letter.text.lower() not in self.not_in and letter.text != '':
                            self.not_in.append(letter.text.lower())
                elif letter.style == "yellow":
                    self.wrong_pos.append(letter.text.lower())
                elif letter.style == "green":
                    for correct in self.correct_pos:
                        if correct == (letter.text.lower(), num):
                            break
                    else:
                        self.correct_pos.append((letter.text.lower(), num))

        self.words = Logic.ALL_WORDS.copy()

        print(f"not in: {self.not_in}")
        print(f"wrong_pos: {self.wrong_pos}")
        print(f"correct_pos = {self.correct_pos}")

        # Filter words
        for word in Logic.ALL_WORDS:
            l_word = list(word)
            wrong_pos_l_word = l_word
            if [i for i in self.not_in if i in l_word]:
                self.words.remove(word)
            elif [i for i in self.wrong_pos if i not in wrong_pos_l_word]:
                if word == "graph":
                    print("nah")
                    print([i for i in self.wrong_pos if i not in wrong_pos_l_word])
                    print(l_word)
                self.words.remove(word)
            elif [cor for cor in self.correct_pos if word[cor[1]] != cor[0]]:
                self.words.remove(word)

        self.words = self.sort_by_word_commonality(self.words)
        print(f"words: {self.words}")

    # https://www.inspiredpython.com/article/solving-wordle-puzzles-with-basic-python
    def calculate_word_commonality(self, word):
        score = 0.0
        for char in word:
            score += self.LETTER_FREQUENCY[char]
        return score / (5 - len(set(word)) + 1)

    # https://www.inspiredpython.com/article/solving-wordle-puzzles-with-basic-python
    def sort_by_word_commonality(self, words):
        sort_by = operator.itemgetter(1)
        return sorted(
            [(word, self.calculate_word_commonality(word)) for word in words],
            key=sort_by,
            reverse=True,
        )


if __name__ == "__main__":
    bot = Quordle()
    info = bot.read()
    with Live(bot.grid.__rich__(), refresh_per_second=50) as live:
        for grid in range(4):
            print(len(bot.grid.data))
            _word = Logic(bot.grid.data[grid]).words
            for _words in range(len(_word)):
                try:
                    bot.type_enter(_word[_words][0])
                    _data = bot.read().data
                    live.update(bot.grid.__rich__())
                    print(f"grid: {grid}")
                    print(f"row: {7 - bot.guesses}")
                    if not all(_data[grid][7 - bot.guesses]):
                        print(all(_data[grid][9 - (bot.guesses + 1)]))
                        print("listing:")
                        for _ in _data[grid][9 - (bot.guesses + 1)]:
                            print(_.text)
                        print(_word[_words])
                        continue
                    else:
                        break
                except RuntimeError:
                    continue
