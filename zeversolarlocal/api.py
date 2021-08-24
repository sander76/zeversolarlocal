"""zeversolarlocal API"""

from dataclasses import dataclass
from typing import Optional

import httpx

DAILY_ENERGY_IDX = 12
CURRENT_POWER_INDEX = 11


@dataclass
class SolarData:
    daily_energy: float  # kiloWatthour
    current_power: int  # Watt


def _convert_to_string(data: bytes) -> str:
    return data.decode(encoding="utf-8")


def _parse_content(incoming: str) -> SolarData:
    """Parse incoming data from the inverter.

    Incoming data is a string in form of:
    1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error

    0 1      2               3         4            5             6       7      8 9        10         11   12  13  14
    """

    data = incoming.split()
    try:
        _daily_energy = float(data[DAILY_ENERGY_IDX])
        _current_power = int(data[CURRENT_POWER_INDEX])
    except (ValueError, IndexError) as err:
        raise ZeverError(err) from None
    else:
        return SolarData(_daily_energy, _current_power)


class HttpxClient:
    def __init__(self) -> None:
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient()
        return self.client

    async def __aexit__(self, exc_type, exc, tb):
        if self.client:
            await self.client.aclose()
        if exc_type:
            raise ZeverError(exc)


async def httpx_get_client(url: str, timeout=2) -> bytes:
    try:
        async with httpx.AsyncClient() as client:
            data = await client.get(url, timeout=timeout)
    except httpx.TimeoutException:
        raise ZeverError(
            "Connection to Zeversolar inverter timed out. %s", url
        ) from None
    return data.content


def default_url(ipaddress: str):
    """Return the default url based on the provided ip address
    Address only ie. 192.168.1.3"""

    return f"http://{ipaddress}/home.cgi"


async def solardata(url: str, client=None) -> SolarData:
    """Query the local zever solar inverter for new data.

    Raises:
        A ZeverError when unable to fetch data.
    """
    if client is None:
        client = httpx_get_client

    data = await client(url)

    return _parse_content(_convert_to_string(data))


class ZeverError(Exception):
    """Parsing problem"""
