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
    allDevices = nb.dcim.devices.filter(status='active', tag='ip-update')


    testbed = load("empty-testbed.yaml")

    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Netbox ID", style="bold")
    table.add_column("Interface")
    table.add_column("IP")

    console.log("Collecting information for all devices...")
    allDevices = list(allDevices)
    addInterfaceList = [] # The interface list to add to NB
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
            interfaces = dev.learn('interface')
        except Exception as e:
            print(e)
            continue
        device.tags = [tag for tag in device.tags if tag.name != "ip-update"]
        device.save()
        atsInterfaces = interfaces.to_dict().get('info')
        # Collect all interfaces from the device in Netbox
        nbInterface = nb.dcim.interfaces.filter(device=device)
        nbInterfaceList = list(nbInterface)
        nbInterfaceName = [i.name for i in nbInterfaceList]
        # Collect all ip addesses from the device in Netbox
        nbIps = nb.ipam.ip_addresses.filter(device=device)
        nbIpsList = list(nbIps)
        nbIpsList = [ips.display for ips in nbIpsList]
        
        addPrefixList = []
        for interface in nbInterfaceList:
            if interface.name in atsInterfaces.keys():
                if "ipv4" in atsInterfaces[interface.name].keys():
                    atsPrefix = list(atsInterfaces[interface.name]['ipv4'].keys())[0]
                    if not str(atsPrefix) in nbIpsList and atsPrefix != "dhcp_negotiated":
                        table.add_row(str(interface.device), interface.name, atsPrefix)
                        # remember to change the VRF ID to something that matches your netbox
                        newPrefix = { 'address': atsPrefix, 'assigned_object_type': 'dcim.interface', 'assigned_object_id': interface.id, 'vrf': 1}
                        addPrefixList.append(newPrefix)
    console.print(table)
    if Confirm.ask("Do you want to update interfaces for devices?", default=True):
        # console.print("not implemented")
        console.print(f"updating... {nb.ipam.ip_addresses.create(addPrefixList)}")