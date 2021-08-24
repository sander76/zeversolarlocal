"""Zever solar cli."""
import asyncio

import zeversolarlocal


def get(args):
    loop = asyncio.get_event_loop()
    address = args.ipaddress
    url = zeversolarlocal.default_url(address)

    print(f"Getting solar data from Zeversolar inverter located at {address}")
    solar_data = loop.run_until_complete(zeversolarlocal.solardata(url))
    print(solar_data)
    return solar_data
