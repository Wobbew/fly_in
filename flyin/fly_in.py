from __future__ import annotations  # allows forward references
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from math import atan2, radians, degrees, cos, atan, sin, sqrt
import pygame
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
class Drone:
    """A drone in the network."""
    id: int
    zone: Zone | Link
    graph: Graph

    def next_zone(self) -> Zone | None:
        """Next zone on the cheapest path, or None if there is none."""
        end = self.graph.end
        if self.zone is end or end is None:
            return None
        step = end
        while step.previous is not self.zone:
            if step.previous is None:
                return None
            step = step.previous
        return step

    def get_connection(self, to: Zone) -> Link | None:
        """Link from the current zone to `to`, if any."""
        for link in self.zone.connections:
            if link.b == to.name:
                return link
        return None

    def move(self, used: dict[str, int]) -> bool:
        """Move one step if zone and link capacity allow it."""
        nxt = self.next_zone()
        if nxt is None:
            return False
        con = self.get_connection(nxt)
        if con is None:
            return False
        if used.get(con.name, 0) >= con.capacity:
            return False
        if nxt is not self.graph.end and len(nxt.drones) >= nxt.max_drones:
            return False
        used[con.name] = used.get(con.name, 0) + 1
        self.zone.drones.remove(self)
        nxt.drones.append(self)
        self.zone = nxt
        
        return True

@dataclass
class Zone:
    """A hub in the network."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    price: int = -1
    previous: Zone | None = None
    connections: list[Link] = field(default_factory=list)  
    drones: list[Drone] = field(default_factory=list)

    @property
    def cost(self) -> int:
        """Turns needed to enter this zone."""
        if self.zone_type is ZoneType.RESTRICTED:
            return 2
        if self.zone_type is ZoneType.PRIORITY:
            return 0.5
        return 1


@dataclass
class Link:
    """A bidirectional connection between two zones."""

    a: str
    b: str
    capacity: int = 1
    drones: list[Drone] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Connection name as used in the output format."""
        return f"{self.a}-{self.b}"

@dataclass
class Link:
    a: str
    b: str
    capacity: int = 1
    drones: list[Drone] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.a}-{self.b}"

    @staticmethod
    def midpoint(a: tuple[int, int], b: tuple[int, int]) -> tuple[float, float]:
        return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2

@dataclass
class Graph:
    """The whole map."""

    nb_drones: int = 0
    zones: dict[str, Zone] = field(default_factory=dict)
    links: dict[str, Link] = field(default_factory=dict)
    drones: list[Drone] = field(default_factory=list)
    start: Zone | None = None
    end: Zone | None = None


class Renderer:
    WIDTH, HEIGHT, MARGIN = 1000, 700, 80
    SPEED = 6  # pixels per frame

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.screen: pygame.Surface | None = None
        self.drone_img: pygame.Surface | None = None
        self.all_drones = list(graph.drones)
        self.pos = {
            d.id: pygame.Vector2(self._to_screen(d.zone.x, d.zone.y))
            for d in self.all_drones
        }

    def move_drone(self) -> None:
        """Slide every drone a bit toward the zone it is in now."""
        for Drone in self.all_drones:
            try:
                if Drone.zone.name:
                    pos = self._to_screen(Drone.zone.x, Drone.zone.y)
            except:
                a = self.graph.zones[Drone.zone.a]
                b = self.graph.zones[Drone.zone.b]
                pos = self._to_screen(*Drone.zone.midpoint((a.x, a.y), (b.x, b.y)))
            self.pos[Drone.id] = pos
        

    def _draw_drones(self) -> None:
        assert self.screen and self.drone_img
        for d in self.all_drones:
            off = pygame.Vector2((d.id % 5 - 2) * 7, (d.id // 5 % 5 - 2) * 7)
            rect = self.drone_img.get_rect(center=self.pos[d.id] + off)
            self.screen.blit(self.drone_img, rect)

    def _to_screen(self, x: int, y: int) -> tuple[int, int]:
        """Scale map coordinates into window pixels."""
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        span_x = (max(xs) - min(xs)) or 1
        span_y = (max(ys) - min(ys)) or 1
        px = self.MARGIN + (x - min(xs)) / span_x * (
            self.WIDTH - 2 * self.MARGIN)
        py = self.MARGIN + (y - min(ys)) / span_y * (
            self.HEIGHT - 2 * self.MARGIN)
        return int(px), int(py)

    @staticmethod
    def _color(name: str | None) -> pygame.Color:
        try:
            return pygame.Color(name or "white")
        except ValueError:
            return pygame.Color("gray")

    def run(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        img = pygame.image.load("drone.png").convert_alpha()
        self.drone_img = pygame.transform.smoothscale(img, (40, 40))
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_round(self.graph)
            self.screen.fill((20, 20, 30))
            self._draw_links()
            self._draw_zones()
            self.move_drone()
            self._draw_drones()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def _draw_links(self) -> None:
        assert self.screen
        for link in self.graph.links.values():
            a = self.graph.zones[link.a]
            b = self.graph.zones[link.b]
            pygame.draw.line(self.screen, (120, 120, 120),
                             self._to_screen(a.x, a.y),
                             self._to_screen(b.x, b.y),
                             width=link.capacity * 2)

    def _draw_zones(self) -> None:
        assert self.screen
        for z in self.graph.zones.values():
            pos = self._to_screen(z.x, z.y)
            pygame.draw.circle(self.screen, self._color(z.color), pos, 20)
            pygame.draw.circle(self.screen, (255, 255, 255), pos, 20, 2)


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
        zone = Zone(name, x, y, zone_type=ztype,
            color=meta.get("color"), max_drones=cap)
        if kind == "start_hub":
            if g.start:
                raise ParseError(no, "more than one start_hub")
            zone.price = 0
            g.start = zone
        elif kind == "end_hub":
            if g.end:
                raise ParseError(no, "more than one end_hub")
            g.end = zone
        g.zones[name] = zone

    def _link(self, g: Graph, rest: str, no: int) -> None:
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


def set_up_drones(g: Graph):
    for i in range(g.nb_drones):
        d = Drone(i+1, g.start, g)
        g.drones.append(d)
        g.start.drones.append(d)


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


def find_path(g: Graph) -> None:
    # reset, so it can be re-run every turn
    for z in g.zones.values():
        z.price = -1
        z.previous = None
    g.start.price = 0

    def set_price_next(z: Zone) -> None:
        for link in z.connections:
            nxt = g.zones[link.b]
            if nxt.zone_type == ZoneType.BLOCKED:
                continue
            busy = 1 if (nxt is not g.end
                         and len(nxt.drones) >= nxt.max_drones) else 0
            new_price = z.price + nxt.cost + busy
            if nxt.price == -1 or nxt.price > new_price:
                nxt.price = new_price
                nxt.previous = z
                set_price_next(nxt)

    set_price_next(g.start)


def game_round(g: Graph) -> None:
    find_path(g)
    used = {}
    moves = []
    for drone in sorted(g.drones, key=lambda d: d.zone.price, reverse=True):
        if drone.move(used):
            moves.append(f"D{drone.id}-{drone.zone.name}")
    g.drones = [d for d in g.drones if d.zone is not g.end]
    if moves:
        print(" ".join(moves))


def main() -> None:
    """Load a map and print a summary."""
    try:
        path = choose_map() if len(sys.argv) == 1 else sys.argv[1]
        graph = MapParser().parse(path)
        set_up_drones(graph)
        find_path(graph)
        renderer = Renderer(graph)
        renderer.run()
    except ParseError as e:
        print(e)


if __name__ == "__main__":
    main()