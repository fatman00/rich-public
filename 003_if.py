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
    allDevices = nb.dcim.devices.filter(status='active', tag='if-update')


    testbed = load("empty-testbed.yaml")

    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Netbox ID", style="bold")
    table.add_column("Interface")
    table.add_column("Type")
    table.add_column("Description")

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
        device.tags = [tag for tag in device.tags if tag.name != "sn-update"]
        #device.save()
        interfaces = interfaces.to_dict().get('info')

        nbInterface = nb.dcim.interfaces.filter(device=device)
        nbInterfaceList = list(nbInterface)
        nbInterfaceName = [i.name for i in nbInterfaceList]

        
        for interface in interfaces:
            print(interface)
            interfaceType = "other"
            if "GigabitEthernet" in interface:
                interfaceType = "1000base-t"
            if "FastEthernet" in interface:
                interfaceType = "100base-tx"
            if "TenGigabitEthernet" in interface:
                interfaceType = "10gbase-x-sfpp"
            if "TwentyFiveGigE" in interface:
                interfaceType = "25gbase-x-sfp28"
            if "FortyGigabitEthernet" in interface: 
                interfaceType = "40gbase-x-qsfpp"
            if "HundredGigE" in interface: 
                interfaceType = "100gbase-x-qsfp28"
            if "BVI" in interface:
                interfaceType = "virtual"
            if "BDI" in interface:
                interfaceType = "virtual"
            if "Vlan" in interface:
                interfaceType = "virtual"
            if "Tunnel" in interface:
                interfaceType = "virtual"
            if "Loopback" in interface:
                interfaceType = "virtual"
            if "Port-channel" in interface:
                interfaceType = "lag"
            if "." in interface:
                interfaceType = "virtual"
            if "Trans" in interface:
                interfaceType = "other"
            if interfaceType is not "other" and interface not in nbInterfaceName:
                newInterface = {}
                newInterface['device']= device.id
                newInterface['name'] = interface
                newInterface['type'] = interfaceType
                if "description" in interfaces[interface]:
                    newInterface['description'] = interfaces[interface]['description']    
                #print(nb.dcim.interfaces.create(newInterface))
                addInterfaceList.append(newInterface)
    for interface in addInterfaceList:
        table.add_row(str(interface.get('device')), interface.get('name'), interface.get('type'), interface.get('description'))
    console.print(table)
    if Confirm.ask("Do you want to update Interfaces for devices?", default=True):
        console.print(f"updating... {nb.dcim.interfaces.create(addInterfaceList)}")