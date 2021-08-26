"""zeversolarlocal API"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

_LOGGER = logging.getLogger(__name__)
DAILY_ENERGY_IDX = 12
CURRENT_POWER_INDEX = 11
INVERTER_ID = 10


@dataclass
class SolarData:
    daily_energy: float  # kiloWatthour
    current_power: int  # Watt


def _convert_to_string(data: bytes) -> str:
    return data.decode(encoding="utf-8")


def _parse_content(incoming: bytes) -> SolarData:
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
        _LOGGER.error("Unable to parse incoming data %s", incoming)
        raise ZeverError(err) from None
    else:
        return SolarData(_daily_energy, _current_power)


def _parse_zever_id(incoming: bytes) -> str:
    data = incoming.split()
    try:
        return _convert_to_string(data[10])
    except (ValueError, IndexError) as err:
        _LOGGER.error("Unable to parse incoming data %s", incoming)
        raise ZeverError(err) from None


class ClientAdapter(ABC):
    """http client base adapter."""

    @abstractmethod
    async def get(self, url, timeout=2) -> bytes:
        """Return the url response data."""
        ...


class HttpxClient(ClientAdapter):
    """Httpx client adapter"""

    async def get(self, url, timeout=2) -> bytes:
        try:
            async with httpx.AsyncClient() as client:
                data = await client.get(url, timeout=timeout)
        except httpx.TimeoutException:
            raise ZeverTimeout(
                f"Connection to Zeversolar inverter timed out. {url}"
            ) from None
        return data.content


def default_url(ip_address: str):
    """Return the default url based on the provided ip address
    Address only ie. 192.168.1.3"""

    return f"http://{ip_address}/home.cgi"


async def solardata(url: str, client: ClientAdapter = None) -> SolarData:
    """Query the local zever solar inverter for new data.

    Raises:
        ZeverError when data is incorrect.
        ZeverTimeout when connecting to the inverter times out.
            For example when the invertor is off as there is no sun to
            power the invertor.
    """
    if client is None:
        client = HttpxClient()

    data = await client.get(url)

    return _parse_content(data)


async def inverter_id(url: str, client: ClientAdapter = None) -> str:
    if client is None:
        client = HttpxClient()

    data = await client.get(url)

    return _parse_zever_id(data)


class ZeverError(Exception):
    """Parsing problem"""


class ZeverTimeout(ZeverError):
    """The inverter is powered by its own solar energy.

    No sun means no power and the inverter is off.
    When queried while off, this error will be raised.
    """
