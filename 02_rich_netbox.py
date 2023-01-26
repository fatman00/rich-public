from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
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

    #allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='if-update')
    allDevices = nb.dcim.devices.all()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="bold")
    table.add_column("Site")
    table.add_column("Manufacturer")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("If Count", justify="right")
    
    console.log("Collecting information and interfaces for all devices...")
    for device in track(allDevices):
        ifcount = "N/A"
        ifcount = nb.dcim.interfaces.count(device=device)
        # console.log(f"Fetching information for {device}")
        icon = ':thumbs_up:' if str(device.status) == 'Active' else ':pile_of_poo:'
        table.add_row(
            device.name, 
            device.site.name, 
            device.device_type.manufacturer.name, 
            device.device_type.model, 
            f"{str(device.status)}({icon})", 
            str(ifcount)
        )
    
    console.print(table)