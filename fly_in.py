from __future__ import annotations  # allows forward references
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
map_path = None


class customError(Exception):
    def __init__(self, message):
        self.message = message


class ParseError(Exception):
    """Raised when the map file is invalid."""

    def __init__(self, line_no: int, message: str) -> None:
        super().__init__(f"line {line_no}: {message}")


class ZoneType(Enum):
    """Kinds of zones."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:
    """A hub in the network."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1

    @property
    def cost(self) -> int:
        """Turns needed to enter this zone."""
        return 2 if self.zone_type is ZoneType.RESTRICTED else 1


@dataclass
class Link:
    """A bidirectional connection between two zones."""

    a: str
    b: str
    capacity: int = 1

    @property
    def name(self) -> str:
        """Connection name as used in the output format."""
        return f"{self.a}-{self.b}"


@dataclass
class Graph:
    """The whole map."""

    nb_drones: int = 0
    zones: dict[str, Zone] = field(default_factory=dict)
    links: dict[frozenset[str], Link] = field(default_factory=dict)
    start: str = ""
    end: str = ""


class MapParser:
    """Parses a map file into a Graph."""

    def parse(self, path: str) -> Graph:
        """Parse the file at `path`, raising ParseError on bad input."""
        graph = Graph()
        try:
            with open(path) as f:
                lines = f.read().splitlines()
        except OSError as e:
            raise ParseError(0, f"cannot read {path}: {e}")
        first = True
        for no, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, rest = line.partition(':')
            if not sep:
                raise ParseError(no, "missing ':'")
            key, rest = key.strip(), rest.strip()
            if first and key != "nb_drones":
                raise ParseError(no, "first line must be nb_drones")
            first = False
            if key == "nb_drones":
                graph.nb_drones = self._positive(rest, no, "nb_drones")
            elif key in ("hub", "start_hub", "end_hub"):
                self._zone(graph, key, rest, no)
            elif key == "connection":
                self._link(graph, rest, no)
            else:
                raise ParseError(no, f"unknown line type '{key}'")
        if graph.nb_drones == 0:
            raise ParseError(0, "nb_drones is missing")
        if not graph.start or not graph.end:
            raise ParseError(0, "need exactly one start_hub and one end_hub")
        return graph

    @staticmethod
    def _positive(value: str, no: int, what: str) -> int:
        if not value.lstrip('+').isdigit() or int(value) <= 0:
            raise ParseError(no, f"{what} must be a positive integer")
        return int(value)

    @staticmethod
    def _split(rest: str, no: int) -> tuple[str, dict[str, str]]:
        body, bracket, meta = rest.partition('[')
        meta_dict: dict[str, str] = {}
        if bracket:
            if not meta.endswith(']'):
                raise ParseError(no, "metadata block not closed with ']'")
            for item in meta[:-1].split():
                k, eq, v = item.partition('=')
                if not eq or not k or not v:
                    raise ParseError(no, f"bad metadata '{item}'")
                meta_dict[k] = v
        return body.strip(), meta_dict

    def _zone(self, g: Graph, kind: str, rest: str, no: int) -> None:
        body, meta = self._split(rest, no)
        parts = body.split()
        if len(parts) != 3:
            raise ParseError(no, "expected: <name> <x> <y> [metadata]")
        name = parts[0]
        if '-' in name:
            raise ParseError(no, "zone names cannot contain dashes")
        if name in g.zones:
            raise ParseError(no, f"duplicate zone '{name}'")
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise ParseError(no, "coordinates must be integers")
        try:
            ztype = ZoneType(meta.get("zone", "normal"))
        except ValueError:
            raise ParseError(no, f"invalid zone type '{meta['zone']}'")
        cap = 1
        if "max_drones" in meta:
            cap = self._positive(meta["max_drones"], no, "max_drones")
        zone = Zone(name, x, y, ztype, meta.get("color"), cap)
        if kind == "start_hub":
            if g.start:
                raise ParseError(no, "more than one start_hub")
            g.start = name
        elif kind == "end_hub":
            if g.end:
                raise ParseError(no, "more than one end_hub")
            g.end = name
        g.zones[name] = zone

    def _link(self, g: Graph, rest: str, no: int) -> None:
        body, meta = self._split(rest, no)
        names = body.split('-')
        if len(names) != 2 or body.count(' ') > 0:
            raise ParseError(no, "expected: <zone1>-<zone2> [metadata]")
        a, b = names
        if a not in g.zones or b not in g.zones:
            raise ParseError(no, "connection uses an undefined zone")
        key = frozenset((a, b))
        if a == b or key in g.links:
            raise ParseError(no, "self-link or duplicate connection")
        cap = 1
        if "max_link_capacity" in meta:
            cap = self._positive(
                meta["max_link_capacity"], no, "max_link_capacity")
        g.links[key] = Link(a, b, cap)

def map_difficulty():
    difficulty = []
    folders = os.listdir('maps/')
    for folder in folders:
        if ('.' not in folder):
            difficulty.append(folder)
    return difficulty


def choose_map() -> str:
    """Let the user pick a map from the maps/ folder."""
    difficulties = sorted(d for d in os.listdir('maps/') if '.' not in d)
    for i, d in enumerate(difficulties):
        print(i, d)
    try:
        folder = difficulties[int(input("Enter: "))]
        files = sorted(
            f for f in os.listdir(f'maps/{folder}') if f.endswith('.txt'))
        for i, f in enumerate(files):
            print(i, f)
        return f'maps/{folder}/{files[int(input("Enter: "))]}'
    except (IndexError, ValueError):
        raise ParseError(0, "not a valid choice")


def main() -> None:
    """Load a map and print a summary."""
    try:
        path = choose_map() if len(sys.argv) == 1 else sys.argv[1]
        graph = MapParser().parse(path)
        print(f"{graph.nb_drones} drones, {len(graph.zones)} zones, "
              f"{len(graph.links)} links")
    except ParseError as e:
        print(e)

if __name__ == "__main__":
    main()