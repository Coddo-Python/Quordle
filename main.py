from rich import print
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.panel import Panel
from rich.layout import Layout

from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


class Quordle:
    def __init__(self):
        print("[blue]Quordle Bot Initiated![/blue]")
        options = webdriver.ChromeOptions()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = webdriver.Chrome(options=options)
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

        print(f"[yellow]Inputting starters...[/yellow]")
        self.type_enter("adieu")
        self.type_enter("crown")
        self.type_enter("nymph")

        self.guesses = 6  # Guesses left

    def type_enter(self, text):
        actions = ActionChains(self.driver)
        actions.send_keys(text)
        actions.send_keys(Keys.RETURN)
        actions.perform()

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
        return QuordleGrid(to_return)


class RichText:
    def __init__(self, text, style):
        self.text = text
        self.style = style

    def __str__(self):
        return self.text

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

        for grid, layout_code in zip(self.data, self.layouts):
            table = Table(show_header=False, expand=True, show_lines=False)
            for _ in range(5):
                table.add_column("", justify="center")
            for row in grid:
                table.add_row(*[letter for letter in row])
            self.tables.append(table)
            self.layout[layout_code].update(table)

    def __iter__(self):
        for _ in self.data:
            yield _

    def __rich__(self):
        return self.layout


if __name__ == "__main__":
    bot = Quordle()
    info = bot.read()
    print(info)
