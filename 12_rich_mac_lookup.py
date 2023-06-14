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
import re

console = Console(record=True)

def extractMACdata(data):
    datadump = []
    for line in data.splitlines():
        ifpattern = r'(?:Fa|Gi)\s?\d+(?:\/\d+){0,2}(?:[\.:]\d+)?'
        vlanpattern = r'^\s*[0-9]{1,4}'
        macpattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
        ifmatch = re.findall(ifpattern, line)
        vlanmatch = re.findall(vlanpattern, line)
        if len(ifmatch) is not 0:
            ifmatch = ifmatch[0]
            vlanmatch = vlanmatch[0].strip()
            datadump.append([vlanmatch, ifmatch])
    return datadump

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='List all devices(from mac table) on a switch and the vendor and ip address')
    parser.add_argument('maclist', metavar='filename', type=argparse.FileType('r'), nargs='+',
                        help='One or more files with show mac address from switches with endpoints connected. \nA regex will look for a mac address and interface name on each line')
    parser.add_argument('--output')
    parser.add_argument('-a', '--arplist', type=argparse.FileType('r'), nargs=1, required=False,
                        help='File with show ip arp from the Layer 3 device')
    parser.add_argument('-if', '--ifname', type=ascii, required=False, default="(?:Fa|Gi)\s?\d+(?:\/\d+){0,2}(?:[\.:]\d+)?",
                        help='regex to match interfaces names for access ports')
    parser.add_argument('--csvout', type=argparse.FileType('w'), nargs=1, required=False,
                        help='File csvfile for output')
    args = parser.parse_args()
    print(f"arplist:{args.arplist}")
    print(f"ifname:{args.ifname}")
    newmac = []
    for file in args.maclist:
        newmac = extractMACdata(file.read())
    print(newmac)





    tree = Tree("Device Tree", guide_style="bold bright_blue")
    console.log("Collecting information and counters from devices...")
    
    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)