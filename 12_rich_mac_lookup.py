from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree
from rich.table import Table
from rich.prompt import Prompt

import argparse

import datetime
import os
import urllib3

console = Console(record=True)

def exportMAC(data):
    datadump = []
    for line in data.splitlines():
        datadump.append(line)
    return datadump

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='List all devices(from mac table) on a switch and the vendor and ip address')
    parser.add_argument('maclist', metavar='filename', type=argparse.FileType('r'), nargs='+',
                        help='One or more files with show mac address from switches with endpoints connected. \nA regex will look for a mac address and interface name on each line')
    parser.add_argument('--output')
    parser.add_argument('-a', '--arplist', type=argparse.FileType('r'), nargs=1, required=False,
                        help='File with show ip arp from the Layer 3 device')
    parser.add_argument('--csvout', type=argparse.FileType('w'), nargs=1, required=False,
                        help='File csvfile for output')
    args = parser.parse_args()
    print(f"arplist:{args.arplist}")
    for file in args.maclist:
        print(file.read())





    tree = Tree("Device Tree", guide_style="bold bright_blue")
    console.log("Collecting information and counters from devices...")
    
    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)