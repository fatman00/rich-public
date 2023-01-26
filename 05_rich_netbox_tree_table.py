from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree
from rich.table import Table

import pynetbox
import urllib3
from myconfig import NETBOX_URL, NETBOX_TOKEN, CLI_USERNAME, CLI_PASSWORD


# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()
console.print(NETBOX_URL, NETBOX_TOKEN, CLI_USERNAME, CLI_PASSWORD)


if __name__ == "__main__":
    # connect to netbox
    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)  # Read only token
    nb.http_session.verify = False

    #allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='cdp-update')
    allDevices = nb.dcim.devices.all()
    tree = Tree("Device Tree", guide_style="bold bright_blue")
    
    console.log("Collecting information and interfaces for all devices...")
    for device in track(allDevices):
        print(f"Collecting information for {device.name}")
        interfaces = nb.dcim.interfaces.filter(device=device)
        branch = tree.add(f"[green bold]Name: {device.name}[/green bold]")
        branch.add(f"[cyan]Interface Count: {len(interfaces)}[/cyan]")
        branch.add(f"[cyan]Platform: {device.device_type.display}[/cyan]")
        if len(interfaces):
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="bold")
            table.add_column("Type")
            table.add_column("Description")
            for int in interfaces:
                table.add_row(int.name, str(int.type), str(int.description))
            branch.add(table)
    
    console.print(tree)