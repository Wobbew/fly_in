"""Parser for the map file format."""

from errors import ParseError
from models import Graph, Link, Zone, ZoneType


class MapParser:
    """Reads a map file and builds a Graph, or raises ParseError."""

    def parse(self, path: str) -> Graph:
        """Parse the map file at `path` and return the resulting graph."""
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
        """Convert `value` to a positive int or raise ParseError."""
        if not value.lstrip('+').isdigit() or int(value) <= 0:
            raise ParseError(no, f"{what} must be a positive integer")
        return int(value)

    @staticmethod
    def _split(rest: str, no: int) -> tuple[str, dict[str, str]]:
        """Split 'body [k=v ...]' into the body and a metadata dict."""
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
        """Parse a hub / start_hub / end_hub line and add the zone."""
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
        zone = Zone(name, x, y, zone_type=ztype,
                    color=meta.get("color"), max_drones=cap)
        if kind == "start_hub":
            if g.start:
                raise ParseError(no, "more than one start_hub")
            g.start = zone
        elif kind == "end_hub":
            if g.end:
                raise ParseError(no, "more than one end_hub")
            g.end = zone
        g.zones[name] = zone

    def _link(self, g: Graph, rest: str, no: int) -> None:
        """Parse a connection line and add the link to both zones."""
        body, meta = self._split(rest, no)
        names = body.split('-')
        if len(names) != 2 or body.count(' ') > 0:
            raise ParseError(no, "expected: <zone1>-<zone2> [metadata]")
        a, b = names
        if a not in g.zones or b not in g.zones:
            raise ParseError(no, "connection uses an undefined zone")
        name = f"{a}-{b}"
        if a == b or name in g.links or f"{b}-{a}" in g.links:
            raise ParseError(no, "self-link or duplicate connection")
        cap = 1
        if "max_link_capacity" in meta:
            cap = self._positive(
                meta["max_link_capacity"], no, "max_link_capacity")
        link = Link(a, b, cap)
        g.links[name] = link
        g.zones[a].connections.append(link)
        g.zones[b].connections.append(link)
