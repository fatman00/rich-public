
# Use rich.print to color text in the console
from rich import print
print("Hej med [bold red]mig[/bold red]")

# Use pretty to make the terminal show output in better formatting
from rich import pretty
pretty.install()
arr = ["rasmus", "er", "sej"]
arr

# Use the Console
from rich.console import Console
console = Console()
console.print("Hello", "World!")
console.print("Hello", "World!", style="bold red")
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")

# use the inspect to show information about objects
from rich import inspect
inspect(arr, methods=True)

#Log to the console
console.log("Hello from", console, "!")
test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]
console.log(test_data, log_locals=True)

# Print Emojies to the console
console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")

#Working with tables in rich
from rich.table import Table

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)

# Working with progressbar

import time
from rich.progress import track

def do_step(ms):
    time.sleep(ms*0.001)
    return f"Doing work for {ms} milliseconds"

for step in track(range(50)):
    print(do_step(step))

# Work with panels on the console
from rich.panel import Panel

names = ["Rasmus E", "Jens", "Erik"]
console.print(names, overflow="ignore", crop=False)

user_renderables = [Panel(name, expand=True) for name in names]

#Print panels in a column
from rich.columns import Columns
console.print(Columns(user_renderables))

console.print(Columns([Panel("Rasmus\nE"), Panel("Erik")]))

from rich.prompt import Prompt, Confirm
name = Prompt.ask("Enter your name", default="Demo User")
print(name)

name = Prompt.ask("Enter your name", choices=["Paul", "Jessica", "Duncan"], default="Paul")
print(name)

is_rich_great = Confirm.ask("Do you like rich?")
assert is_rich_great