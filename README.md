# rich-test
Testing rich library

Create a file with the credentials called myconfig.py
```
NETBOX_URL = "https://demo.netbox.dev/"
NETBOX_TOKEN = "0123456789abcdef0123456789abcdef01234567"

# CSR1K = "sandbox-iosxe-latest-1.cisco.com"
CLI_USERNAME = "developer"
CLI_PASSWORD = "C1sco12345"
```

Use environment variables to connect to devices:
```
export PYATS_USERNAME=developer
export PYATS_PASSWORD=C1sco12345
```

Install python venv
```
apt install python3.8-venv
```

Create and activate the venv:
```
python -m venv venv
source ./venv/bin/activate
```

To update pip, run:
``` 
pip install --upgrade pip
```
And install all requirement:
```
#pip install pyats[full]
pip install -r requirements.txt
```