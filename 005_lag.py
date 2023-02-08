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
    allDevices = nb.dcim.devices.filter(status='active', tag='lag-update')


    testbed = load("empty-testbed.yaml")

    console = Console()

    console.log("Collecting information for all devices...")
    allDevices = list(allDevices)
    updateInterfaceList = [] # The interface list to add to NB
    for device in track(allDevices):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Netbox ID", style="bold")
        table.add_column("Interface")
        table.add_column("Parent LAG")

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
        device.tags = [tag for tag in device.tags if tag.name != "lag-update"]
        device.save()
        atsInterfaces = interfaces.to_dict().get('info')
        # Collect all interfaces from the device in Netbox
        nbInterface = nb.dcim.interfaces.filter(device=device)
        nbInterfaceList = list(nbInterface)
        

        for interface in atsInterfaces:
            port_channel = atsInterfaces[interface].get('port_channel', None)
            # Only go into interfaces with with portchannel attribute and with memeber = True # {'port_channel_member': True, 'port_channel_int': 'Port-channel9'}
            if port_channel is not None and port_channel.get("port_channel_member"):
                # Get the type of the interface. If nothing is given from ATS then set to EtherChannel as we ignore it then
                interfaceType = atsInterfaces[interface].get('type', 'EtherChannel')
                # Make sure we do not update the LAG interface but only the child interfaces
                if interfaceType != 'EtherChannel' and interfaceType != 'GEChannel' and interfaceType != '10GEChannel':
                    # print(f"{interface}({atsInterfaces[interface].get('type', 'EtherChannel')}): {port_channel}")
                    # Find the netbox interface object with the interface we are working with
                    nbIntChild = [nbInt for nbInt in nbInterfaceList if nbInt.name == interface]
                    # Find the netbox interface object for the LAG parent interface
                    nbIntParent = [nbInt for nbInt in nbInterfaceList if nbInt.name == port_channel['port_channel_int']]
                    # If we have found both interfaces and the child interface has not been configured as LAG:
                    if (len(nbIntChild) and len(nbIntParent)) and nbIntChild[0].lag is None:
                        nbIntChild[0].lag = nbIntParent[0].id
                        # print(nbIntChild[0].lag)
                        updateInterfaceList.append(nbIntChild[0])


    for interface in updateInterfaceList:
        print(interface["device"]["name"], interface["name"], interface["lag"])
        table.add_row(str(interface["device"]["name"]), str(interface["name"]), str(interface["lag"]))
        
    console.print(table)
    if Confirm.ask("Do you want to update interfaces for devices?", default=True):
        # console.print("not implemented")
        console.print(f"updating... {[int.save() for int in updateInterfaceList]}")