from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree

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

    #allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='if-update')
    allDevices = nb.dcim.devices.all()
    tree = Tree("Device Tree", guide_style="bold bright_blue")
    
    console.log("Collecting information and interfaces for all devices...")
    for device in track(allDevices):
        print(f"Collecting information from {device.name}")
        interfaces = nb.dcim.interfaces.filter(device=device)
        branch = tree.add(f"[green bold]Name: {device.name}[/green bold]")
        branch.add(f"[cyan dim]Interface Count: {len(interfaces)}[/cyan dim]")
        for int in interfaces:
            branch.add(f"{int.name}")
    
    console.print(tree)