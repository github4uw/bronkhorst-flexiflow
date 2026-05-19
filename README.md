# Bronkhorst Flexi-Flow Python package

Package for controlling Bronkhorst Flexi-Flow massflowcontrollers via USB-Serial.

# installing package in python project

Before installing this module make sure you have the correct access rights. If not make sure your public
ssh-key is listed in the access rights config of this repository. To verify your access rights try cloning
the repository with the ssh address. If you can access the repository in this way everything is alright.

To install this repository as a python dependency you should use pip or equivalent (uv for example). Then
go to your repository and install this project as a dependency:

```shell
$ uv pip install git+ssh://git@github.com/github4uw/bronkhorst-flexiflow.git
```

If there are no errors when running this command you should be able to include it in you python scripts.
Check the successful installation with `uv pip freeze`. This repository should then be listed in the
output.

```python
from bronkhorst_flexiflow import Bronkhorst
mfc = Bronkhorst("/dev/ttyACM0")
mfc.blink_led(3)
```
