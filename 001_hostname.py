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
    allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, tag='hostname-update')

    testbed = load("empty-testbed.yaml")

    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Netbox Name", style="bold")
    table.add_column("Device Name")
    table.add_column("Device Type", justify="right")

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
            dev.connect(log_stdout=False, learn_hostname=True, connection_timeout=10)
            version = dev.parse('show version')
        except Exception as e:
            print(e)
            continue
        device.tags = [tag for tag in device.tags if tag.name != "hostname-update"]
        device.save()
        version = version.get('version')
        hostname = version.get('hostname')
        hostname = hostname if str(device.name) == hostname else f"[red]{hostname}[/red]"
        chassis = version.get('chassis')
        chassis = f"[green]{device.device_type}[/green]" if str(device.device_type) == chassis else f"[red]{device.device_type}:{chassis}[/red]"
        table.add_row(f"{device.name}", f"{hostname}", f"{chassis}")
        if str(device.name) != hostname:
            device.name = version.get('hostname')
            devicesForUpdate.append(device)
    console.print(table)
    if Confirm.ask("Do you want to update hostnames for device?", default=True):
        [dev.save() for dev in devicesForUpdate]
        console.print("updating")