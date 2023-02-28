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
    allDevices = Prompt.ask("Type Device IP/hostname", default="10.36.20.120")
    
    testbed = load("empty-testbed.yaml")

    tree = Tree("Device Tree", guide_style="bold bright_blue")
    console.log("Collecting information and counters from devices...")
    for device in track(allDevices.split()):
        branch = tree.add(f"[green bold]Device IP: {device}[/green bold]")
        print(f"Connecting to {device}...")
        dev = add_device(device, "iosxe", testbed, ip_addr=device)


        print(f"Collecting information for {device}")

        try:
            dev.connect(log_stdout=False, learn_hostname=True, connection_timeout=10)
            deviceTracking = dev.parse('show device-tracking database details')
            #interface = dev.learn('interface') # Maybee not needed
            version = dev.parse('show version')
            version = version.get('version')
            hostname = version.get('hostname')
            collectionTime = datetime.datetime.now()
        except Exception as e:
            error = branch.add(f"[red]Undefined error occured during CLI parsing[/red]")
            error.add(f"[red bold]{e}[/red bold]")
            print(e)
            continue
        branch.add(f"[bold]Name: {hostname}[/bold]")
        #interface = interface.to_dict()['info']
        # if True:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("interface", style="bold")
        table.add_column("dev_code")
        table.add_column("network_layer_address")
        table.add_column("link_layer_address")
        table.add_column("vlan_id")
        table.add_column("mode")
        table.add_column("vendor_code")
        table.add_column("state")
        for entry in deviceTracking.get('device').values():
            interface = entry.get('interface')
            dev_code = entry.get('dev_code')
            network_layer_address = entry.get('network_layer_address')
            link_layer_address = entry.get('link_layer_address')
            vlan_id = entry.get('vlan_id')
            mode = entry.get('mode')
            state = entry.get('state')
            style = "bright_green" if state == "REACHABLE" else "bright_blue"
            table.add_row(str(interface), str(dev_code), str(network_layer_address), str(link_layer_address), str(vlan_id), str(mode), str("None"), str(state), style=style)
            # branch.add(f"[cyan]Name: {int}[/cyan]")
        branch.add(table)

    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)