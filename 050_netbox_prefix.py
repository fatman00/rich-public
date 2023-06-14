import pynetbox
import os
import urllib3
from myconfig import NETBOX_URL, NETBOX_TOKEN


if __name__ == "__main__":

    # Disable all SSL errors
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)  # Read only token
    nb.http_session.verify = False
    prefix = nb.ipam.ip_addresses.all()
    len(prefix)
    prefix = nb.ipam.ip_addresses.filter(parent='10.0.0.0/8', vrf_id='null') # Find all ip addresses in the 10.0.0.0/8 subnet in the global vrf
    len(prefix)
    for pre in prefix:
        pre.vrf=1 # Change the VRF to 1
        try:
            print(pre, end=' ')
            pre.save() #Save the change
        except Exception as e:
            print(e) #print error if any