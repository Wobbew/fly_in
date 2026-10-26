"""Data model: zones, links, drones and the graph that holds them."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ZoneType(Enum):
    """The kinds of zone a map can contain."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


# eq=False: these classes point at each other, so the default __eq__
# (used by list.remove) would compare them recursively.
@dataclass(eq=False)
class Zone:
    """A node of the graph.

    Attributes:
        price: cost to reach the end zone from here (-1 = not computed).
        drones: drones currently standing in this zone.
        incoming: drones on a link heading to this zone.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    price: float = -1
    connections: list[Link] = field(default_factory=list, repr=False)
    drones: list[Drone] = field(default_factory=list, repr=False)
    incoming: int = 0

    @property
    def cost(self) -> float:
        """Cost of entering this zone."""
        if self.zone_type is ZoneType.RESTRICTED:
            return 2
        if self.zone_type is ZoneType.PRIORITY:
            return 0.5
        return 1


@dataclass(eq=False)
class Link:
    """A bidirectional connection between two zones."""

    a: str
    b: str
    capacity: int = 1

    @property
    def name(self) -> str:
        """Name of the link, as printed in the simulation output."""
        return f"{self.a}-{self.b}"

    def other(self, zone: str) -> str:
        """Return the name of the zone at the opposite end."""
        return self.b if zone == self.a else self.a


@dataclass(eq=False)
class Drone:
    """A drone travelling from the start zone to the end zone.

    Attributes:
        link: the link the drone is on (only while in flight).
        target: the restricted zone it is heading to (only in flight).
    """

    id: int
    zone: Zone
    graph: Graph
    link: Link | None = None
    target: Zone | None = None

    def move(self, used: dict[str, int]) -> str | None:
        """Do one turn.

        Args:
            used: number of drones already using each link this turn.

        Returns:
            The text for the output line, or None if the drone waits.
        """
        # on a link: this turn it must arrive
        if self.target is not None:
            assert self.link is not None
            used[self.link.name] = used.get(self.link.name, 0) + 1
            self.target.incoming -= 1
            self.target.drones.append(self)
            self.zone = self.target
            self.target = self.link = None
            return f"D{self.id}-{self.zone.name}"

        best = None
        for link in self.zone.connections:
            nxt = self.graph.zones[link.other(self.zone.name)]
            if nxt.price == -1 or nxt.price >= self.zone.price:
                continue
            if used.get(link.name, 0) >= link.capacity:
                continue
            if (nxt is not self.graph.end
                    and len(nxt.drones) + nxt.incoming >= nxt.max_drones):
                continue
            if best is None or nxt.price < best[0].price:
                best = (nxt, link)
        if best is None:
            return None
        nxt, link = best
        used[link.name] = used.get(link.name, 0) + 1
        self.zone.drones.remove(self)
        if nxt.zone_type is ZoneType.RESTRICTED:
            # stop on the link, arrive next turn
            self.link, self.target = link, nxt
            nxt.incoming += 1
            return f"D{self.id}-{link.name}"
        nxt.drones.append(self)
        self.zone = nxt
        return f"D{self.id}-{nxt.name}"


@dataclass(eq=False)
class Graph:
    """The whole map: zones, links, drones, start and end."""

    nb_drones: int = 0
    zones: dict[str, Zone] = field(default_factory=dict)
    links: dict[str, Link] = field(default_factory=dict)
    drones: list[Drone] = field(default_factory=list)
    start: Zone | None = None
    end: Zone | None = None
