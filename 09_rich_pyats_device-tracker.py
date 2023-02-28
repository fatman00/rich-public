from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree
from rich.table import Table
from rich.prompt import Prompt

import datetime
import os
import urllib3

from genie.testbed import load
from genie.conf.base.device import Device
from quickstart import disable_console_log, make_ssh_conn, add_device


console = Console(record=True)

try:
    assert all(os.environ[env] for env in ['PYATS_USERNAME', 'PYATS_PASSWORD'])
    CLI_USERNAME = os.environ['PYATS_USERNAME']
    CLI_PASSWORD = os.environ['PYATS_PASSWORD']
except KeyError as exc:
    print("export PYATS_USERNAME=<your-login-username>")
    print("export PYATS_PASSWORD=<your-login-password>")
    print(f"ERROR: missing ENVAR: {exc}")

#console.print(NETBOX_URL, NETBOX_TOKEN, CLI_USERNAME, CLI_PASSWORD)

if __name__ == "__main__":
    # connect to netbox
    allDevices = Prompt.ask("Type Device IP/hostname", default="10.2.20.21")
    
    testbed = load("empty-testbed.yaml")

    tree = Tree("Device Tree", guide_style="bold bright_blue")
    console.log("Collecting information and counters from devices...")
    for device in track(allDevices.split()):
        branch = tree.add(f"[green bold]Name: {device}[/green bold]")
        print(f"Connecting to {device}...")
        dev = add_device(device, "ios", testbed, ip_addr=device)


        print(f"Collecting information for {device}")

        try:
            dev.connect(log_stdout=False, learn_hostname=True, connection_timeout=10)
            interface = dev.learn('interface')
            collectionTime = datetime.datetime.now()
        except Exception as e:
            error = branch.add(f"[red]Undefined error occured during CLI parsing[/red]")
            error.add(f"[red bold]{e}[/red bold]")
            print(e)
            continue
        interface = interface.to_dict()['info']
        # if True:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("name", style="bold")
        table.add_column("type")
        table.add_column("oper_status")
        table.add_column("bandwidth")
        table.add_column("counters:rate:in_rate")
        table.add_column("counters:rate:out_rate")
        for int in interface:
            type = interface[int].get('type')
            oper_status = interface[int].get('oper_status')
            bandwidth = interface[int].get('bandwidth')
            if interface[int].get('counters') == None:
                continue
            in_rate = interface[int].get('counters').get('rate').get('in_rate')
            in_rate_pct = in_rate / (bandwidth * 1000)
            out_rate = interface[int].get('counters').get('rate').get('out_rate')
            out_rate_pct = out_rate / (bandwidth * 1000)
            style = "bright_green" if oper_status == "up" else "bright_blue"
            table.add_row(int, str(type), str(oper_status), str(bandwidth), str(in_rate_pct), str(out_rate_pct), style=style)
            # branch.add(f"[cyan]Name: {int}[/cyan]")
        branch.add(table)

    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)