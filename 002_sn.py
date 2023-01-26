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
    allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='sn-update')

    testbed = load("empty-testbed.yaml")

    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Netbox Name", style="bold")
    table.add_column("Device Type")
    table.add_column("Netbox S/N")
    table.add_column("Device S/N", justify="right")

    console.log("Collecting information and STP for all devices...")
    allDevices = list(allDevices)
    devicesForUpdate = []
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
            dev.connect(log_stdout=False, connection_timeout=10)
            platform = dev.learn('platform')
        except Exception as e:
            print(e)
            continue
        device.tags = [tag for tag in device.tags if tag.name != "sn-update"]
        device.save()
        chassis_sn = platform.chassis_sn
        chassis_sn = device.serial if str(device.serial) == chassis_sn else f"[red]{chassis_sn}[/red]"
        chassis = platform.chassis
        chassis = f"[green]{device.device_type}[/green]" if str(device.device_type) == chassis else f"[red]{device.device_type}:{chassis}[/red]"
        table.add_row(f"{device.name}", f"{chassis}", f"{device.serial}", f"{chassis_sn}")
        if str(device.serial) != platform.chassis_sn:
            device.serial = platform.chassis_sn
            devicesForUpdate.append(device)
    console.print(table)
    if Confirm.ask("Do you want to update Serial for device?", default=True):
        [dev.save() for dev in devicesForUpdate]
        console.print("updating")