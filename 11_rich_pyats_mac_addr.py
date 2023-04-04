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

# Create a dict from the variables added.
def createDict(*args):
     return dict(((k, eval(k)) for k in args))


if __name__ == "__main__":
    # connect to netbox
    allDevices = Prompt.ask("Type Device IP/hostname", default="10.36.20.120")
    #allDevices = Prompt.ask("Type Device IP/hostname", default="10.50.20.10")
    
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
            macs = dev.parse('show mac address-table')
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
        
        allVlans = macs.get('mac_table').get('vlans')
        vlanKeys = [key for key in allVlans.keys() if key != 'all']

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("interface", style="bold")
        table.add_column("mac_address")
        table.add_column("entry_type")
        table.add_column("vlan_id")
        table.add_column("vendor_code")

        for key in vlanKeys:
            for mac_addr in allVlans.get(key).get('mac_addresses').values():
                # print(mac_addr.get('mac_address'))
                interface = list(mac_addr.get('interfaces', "none").keys())[0]
                mac_address = mac_addr.get('mac_address')
                entry_type = mac_addr.get('entry_type')
                vlan_id = key
                vendor_code = "N/A"
                table.add_row(str(interface), str(mac_address), str(entry_type), str(vlan_id), str(vendor_code))
        
        branch.add(table)

    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)