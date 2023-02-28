from rich import print
from rich import pretty
from rich.console import Console
from rich.progress import track
from rich.tree import Tree
from rich.table import Table
from rich.prompt import Prompt

import pynetbox
import datetime
import os
import urllib3
from myconfig import NETBOX_URL, NETBOX_TOKEN

from genie.testbed import load
from genie.conf.base.device import Device
from quickstart import disable_console_log, make_ssh_conn, add_device


# Disable all SSL errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console(record=True)

try:
    assert all(os.environ[env] for env in ['PYATS_USERNAME', 'PYATS_PASSWORD'])
    CLI_USERNAME = os.environ['PYATS_USERNAME']
    CLI_PASSWORD = os.environ['PYATS_PASSWORD']
except KeyError as exc:
    print("export PYATS_USERNAME=<your-login-username>")
    print("export PYATS_PASSWORD=<your-login-password>")
    print(f"ERROR: missing ENVAR: {exc}")

#console.print(NETBOX_URL, NETBOX_TOKEN, CLI_USERNAME, CLI_PASSWORD)

if __name__ == "__main__":
    # connect to netbox
    siteShort = Prompt.ask("Find devices from site short", default="RAN")
    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)  # Read only token
    nb.http_session.verify = False
    # get the site object
    nbSite = nb.dcim.sites.filter(status='active', manufacturer_id=1, cf_short=siteShort)
    nbSite = list(nbSite)
    if len(nbSite) > 1:
        console.log("More than one site returned")
        quit()
    # Collecting all site switches of type cisco from the site
    allDevices = nb.dcim.devices.filter(status='active', manufacturer_id=1, role_id=4, site_id=nbSite[0].id)

    testbed = load("empty-testbed.yaml")

    tree = Tree("Device Tree", guide_style="bold bright_blue")
    console.log("Collecting information and counters for all devices...")
    for device in track(allDevices):
        branch = tree.add(f"[green bold]Name: {device.name}[/green bold]")
        deviceIp = ""
        try:
            deviceIp = str(device.primary_ip4.address).split("/")[0]
        except:
            branch.add(f"[red]Unable to connect[/red]")
        if not deviceIp is "":
            print(f"Connecting to {device.name} using IP: {deviceIp}...")
            dev = add_device(device.name, "ios", testbed, ip_addr=deviceIp)
        else:
            continue

        print(f"Collecting information for {device.name}")

        try:
            dev.connect(log_stdout=False, connection_timeout=10)
            interface = dev.learn('interface')
            collectionTime = datetime.datetime.now()
        except Exception as e:
            error = branch.add(f"[red]Undefined error occured during CLI parsing[/red]")
            error.add(f"[red bold]{e}[/red bold]")
            print(e)
            continue
        interface = interface.to_dict()['info']
        # if True:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("name", style="bold")
        table.add_column("type")
        table.add_column("oper_status")
        table.add_column("bandwidth")
        table.add_column("counters:rate:in_rate")
        table.add_column("counters:rate:out_rate")
        for int in interface:
            type = interface[int].get('type')
            oper_status = interface[int].get('oper_status')
            bandwidth = interface[int].get('bandwidth')
            if interface[int].get('counters') == None:
                continue
            in_rate = interface[int].get('counters').get('rate').get('in_rate')
            in_rate_pct = in_rate / (bandwidth * 1000)
            out_rate = interface[int].get('counters').get('rate').get('out_rate')
            out_rate_pct = out_rate / (bandwidth * 1000)
            style = "bright_green" if oper_status == "up" else "bright_blue"
            table.add_row(int, str(type), str(oper_status), str(bandwidth), str(in_rate_pct), str(out_rate_pct), style=style)
            # branch.add(f"[cyan]Name: {int}[/cyan]")
        branch.add(table)

    console.print(tree)
    # console.print(table)
    saveTimestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    CONSOLE_HTML_FORMAT = """\
    <pre style="font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">{code}</pre>
    """
    # console.save_html(f"STP-Status-{siteShort}-{saveTimestamp}.html", inline_styles=True, code_format=CONSOLE_HTML_FORMAT)