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
    for device in track(allDevices):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Device", style="bold")
        table.add_column("Sanitised ID")
        table.add_column("management_addresses")
        table.add_column("local_interface")
        table.add_column("port_id")
        table.add_column("platform")

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
        #device.save()
        neighbors = data['index'] # Interfaces from PyATS
        neighbors = neighbors.values()
        newNeighbors = []
        for neighbor in neighbors:
            # print(neighbor.get("device_id"))
            #newNeighbors = [new for new in newNeighbors if new.get("device_id") != neighbor.get("device_id")]
            if neighbor.get("device_id") not in [new.get("device_id") for new in newNeighbors]:
                newNeighbors.append(neighbor)
            
        for neighbor in newNeighbors:
            sanDeviceId = neighbor.get("device_id", "unknown").split('.')[0]
            mgmtIp = list(neighbor.get("management_addresses").keys())[0]+"/24"
            table.add_row(str(device.name), str(sanDeviceId), str(mgmtIp), neighbor.get("local_interface"), neighbor.get("port_id"), neighbor.get("platform"))
    console.print(table)   

        