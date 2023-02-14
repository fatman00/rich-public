from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree
from rich.table import Table
from rich.prompt import Prompt
from rich.prompt import Confirm

import pynetbox
import os
import urllib3
from myconfig import NETBOX_URL, NETBOX_TOKEN

from genie.testbed import load
from genie.conf.base.device import Device
from quickstart import disable_console_log, make_ssh_conn, add_device


# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

try:
    assert all(os.environ[env] for env in ['PYATS_USERNAME', 'PYATS_PASSWORD'])
    CLI_USERNAME = os.environ['PYATS_USERNAME']
    CLI_PASSWORD = os.environ['PYATS_PASSWORD']
except KeyError as exc:
    print("export PYATS_USERNAME=<your-login-username>")
    print("export PYATS_PASSWORD=<your-login-password>")
    print(f"ERROR: missing ENVAR: {exc}")

if __name__ == "__main__":
    # connect to netbox
    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)  # Read only token
    nb.http_session.verify = False

    # Collecting all site switches of type cisco with the right tag
    #allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='if-update')
    allDevices = nb.dcim.devices.filter(status='active', tag='cdp-update')


    testbed = load("empty-testbed.yaml")

    console = Console()

    console.log("Collecting information for all devices...")
    allDevices = list(allDevices)
    newCables = []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Device", style="bold")
    table.add_column("local_interface")
    table.add_column("Connection")
    table.add_column("port_id")
    table.add_column("device_id")
    table.add_column("NB Device")

    for device in track(allDevices):

        deviceIp = ""
        try:
            deviceIp = str(device.primary_ip4.address).split("/")[0]
        except:
            console.log(f"[red]Unable to connect[/red]")
        if not deviceIp is "":
            print(f"Connecting to {device.name} using IP: {deviceIp}...")
            dev = add_device(device.name, "ios", testbed, ip_addr=deviceIp)
        else:
            continue

        print(f"Collecting information for {device.name}")

        try:
            dev.connect(log_stdout=False, learn_hostname=True, connection_timeout=10)
            data = dev.parse('show cdp neighbors detail')
        except Exception as e:
            print(e)
            continue
        device.tags = [tag for tag in device.tags if tag.name != "cdp-update"]
        device.save()
        neighbors = data['index'] # Interfaces from PyATS
        neighbors = neighbors.values()

        nbLocalInterface = nb.dcim.interfaces.filter(device=device)
        nbLocalInterfaceList = list(nbLocalInterface)
        nbLocalInterfaceName = [i.name for i in nbLocalInterfaceList]

        nbNeighbors = []
        for neighbor in neighbors:
            # Get the first part of the name without DNS suffix
            sanDeviceId = neighbor.get("device_id", "unknown").split('.')[0]
            # Find the local interface object from netbox
            nbLocalInt = [nbInt for nbInt in nbLocalInterfaceList if nbInt.name == neighbor.get("local_interface")]
            #Get the remove device object from netbox
            neiDev = nb.dcim.devices.get(name=sanDeviceId)
            # Get the connection if the interface has been connected
            cableData = dict(nbLocalInt[0]).get("cable")['display'] if dict(nbLocalInt[0]).get("cable") is not None else f"[green]{dict(nbLocalInt[0]).get('cable')}[/green]"
            #nbPort = f'[green]{neighbor.get("port_id", "unknown")}[/green]' if dict(nbLocalInt[0]).get("cable") is None else f'{neighbor.get("port_id", "unknown")}'
            if neiDev is None:
                table.add_row(str(device.name), f"{nbLocalInt[0].name}(None)", str("<None>"),  neighbor.get("port_id", "unknown"), sanDeviceId,  "<Not Found>")
                continue
            nbPortID = 0
            nbPort = ""
            #If we dont have a cable in the local interface everything is fine
            if dict(nbLocalInt[0]).get("cable") is None:
                nbLocalInterface = nb.dcim.interfaces.get(device=neiDev, name=neighbor.get("port_id"))
                nbPortID = nbLocalInterface.id
                nbPort = f'[green]{neighbor.get("port_id", "unknown")}({nbPortID})[/green]'
                # >>> nb.dcim.cables.create(a_terminations=[{"object_type": "dcim.interface", "object_id": 68861}], b_terminations=[{"object_type": "dcim.interface", "object_id": 68946}])
                # GigabitEthernet1/0/7 <> GigabitEthernet1/2
                cable = {
                    "a_terminations": [{"object_type": "dcim.interface", "object_id": nbLocalInt[0].id}],
                    "b_terminations": [{"object_type": "dcim.interface", "object_id": nbPortID}]
                }
                newCables.append(cable)
            elif dict(nbLocalInt[0]).get("cable") is not None:
                # If we have a cable in local interface and neighbor if name is the same
                if dict(nbLocalInt[0]).get("link_peers")[0].get("display") == neighbor.get("port_id"):
                    nbPort = f'[blue]{neighbor.get("port_id", "unknown")}[/blue]'
                # Else we have an error
                else:
                    nbPort = f'[red]{neighbor.get("port_id", "unknown")}[/red]'
            nbRow = f"[blue]{neiDev.name}({neiDev.id})[/blue]" if sanDeviceId in neiDev.name else f"[red]{neiDev.name}({neiDev.id})[/red]"
            table.add_row(str(device.name), f"{nbLocalInt[0].name}({nbLocalInt[0].id})", str(cableData),  nbPort, sanDeviceId,  nbRow)

    console.print(table)
    if Confirm.ask(f"Do you want to update cables({len(newCables)}) for devices?", default=True):
        # console.print("not implemented")
        console.print(f"updating...")
        for cable in newCables:
            try:
                nb.dcim.cables.create(cable)
            except Exception as e:
                print(e)
                continue

        