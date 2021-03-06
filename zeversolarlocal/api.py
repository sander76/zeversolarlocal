"""zeversolarlocal API"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import httpx

_LOGGER = logging.getLogger(__name__)
DAILY_ENERGY_IDX = 12
CURRENT_POWER_INDEX = 11
INVERTER_ID = 10


@dataclass
class SolarData:
    """Solar data returned from the inverter API."""

    daily_energy: float  # kiloWatthour
    current_power: int  # Watt


def _convert_to_string(data: bytes) -> str:
    return data.decode(encoding="utf-8")


def fix(data: bytes) -> bytes:
    """Return correct floating point representation.

    All incoming daily energy is incoming as floating point rounded off by
    two decimals. However, there is a bug:

    10.05 gets reported as 10.5. Which is wrong.
    10.5 is reported is 10.50 which is correct.
    """
    if (
        data[-2] == 46
    ):  # checks for char(46) meaning the "." character as dec separator.
        return data[0:-1] + b"0" + data[-1:]
    return data


def _parse_content(incoming: bytes) -> SolarData:
    """Parse incoming data from the inverter.

    Incoming data is a string in form of:
    1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error

    0 1      2               3         4            5             6       7      8 9        10         11   12  13  14
    """

    data = incoming.split()
    try:
        _daily_energy = float(fix(data[DAILY_ENERGY_IDX]))
        _current_power = int(data[CURRENT_POWER_INDEX])
    except (ValueError, IndexError) as err:
        raise ZeverError(err) from err
    else:
        return SolarData(_daily_energy, _current_power)


def _parse_zever_id(incoming: bytes) -> str:
    data = incoming.split()
    try:
        return _convert_to_string(data[INVERTER_ID])
    except (ValueError, IndexError) as err:
        raise ZeverError(err) from err


class ClientAdapter(ABC):
    """http client base adapter."""

    @abstractmethod
    async def get(self, url: str, timeout: int = 2) -> bytes:
        """Return the url response data."""


class HttpxClient(ClientAdapter):
    """Httpx client adapter"""

    async def get(self, url: str, timeout: int = 2) -> bytes:
        """Return a client request."""
        try:
            async with httpx.AsyncClient() as client:
                data = await client.get(url, timeout=timeout)
        except httpx.TimeoutException:
            raise ZeverTimeout(
                f"Connection to Zeversolar inverter timed out. {url}"
            ) from None
        return data.content


def default_url(ip_address: str) -> str:
    """Return the default url based on the provided ip address
    Address only ie. 192.168.1.3"""

    return f"http://{ip_address}/home.cgi"


def client_factory(client: Optional[ClientAdapter]) -> ClientAdapter:
    """Return a ClientAdapter instance."""
    if client is None:
        return HttpxClient()
    return client


async def solardata(
    url: str, client: Optional[ClientAdapter] = None, timeout: int = 2
) -> SolarData:
    """Query the local zever solar inverter for new data.
    Returns:
        SolarData. Dataclass containing solar data.
    Raises:
        ZeverError when data is incorrect.
        ZeverTimeout when connecting to the inverter times out.
            For example when the inverter is off as there is no sun to
            power the inverter.
    """
    client = client_factory(client)

    data = await client.get(url, timeout=timeout)
    _LOGGER.debug("incoming: %s", data)

    return _parse_content(data)


async def inverter_id(
    url: str, client: Optional[ClientAdapter] = None, timeout: int = 2
) -> str:
    """Query the local zever solar inverter for the id of the inverter.

    Returns:
        String of the zever inverter id.

    Raises:
        ZeverError when data is incorrect.
        ZeverTimeout when connecting to the inverter times out.
            For example when the inverter is off as there is no sun to
            power the inverter.
    """
    client = client_factory(client)

    data = await client.get(url, timeout=timeout)

    return _parse_zever_id(data)


class ZeverError(Exception):
    """General Zever problem"""


class ZeverTimeout(ZeverError):
    """The inverter is powered by its own solar energy.

    No sun means no power and the inverter is off.
    When queried while off, this error will be raised.
    """
