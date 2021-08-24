[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![PyPI](https://img.shields.io/pypi/v/zeversolarlocal)
[![codecov](https://codecov.io/gh/sander76/zeversolarlocal/branch/master/graph/badge.svg?token=FED6T168H0)](https://codecov.io/gh/sander76/zeversolarlocal)


# zeversolarlocal

Access solar energy data from your local Zeversolar inverter.

## installation

`pip install zeversolarlocal`

## usage

```python
import asyncio
import zeversolarlocal

loop = asyncio.get_event_loop()

def get():

    address = "192.168.1.12"  # ip address of your zeversolar inverter.
    url = zeversolarlocal.default_url(address)
    
    solar_data = loop.run_until_complete(zeversolarlocal.solardata(url))

    print(solar_data)

```

## CLI

from the commandline use:

`python -m zeversolarlocal 192.168.1.12`
