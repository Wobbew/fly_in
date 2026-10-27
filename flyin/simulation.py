"""Simulation logic: drone setup, cost map and turn processing."""
import sys
from errors import ParseError
from models import Graph, Drone, Zone, ZoneType
sys.setrecursionlimit(500)


def set_up_drones(g: Graph) -> None:
    """Create the drones and place them in the start zone."""
    start = g.start
    if start is None:
        raise ParseError(0, "no start zone")
    for i in range(g.nb_drones):
        d = Drone(i + 1, start, g)
        g.drones.append(d)
        start.drones.append(d)


def find_path(g: Graph) -> None:
    """Set every zone's price to its cost to reach the end. Run once."""
    end = g.end
    if end is None:
        raise ParseError(0, "no end zone")
    end.price = 0

    def spread(z: Zone) -> None:
        """Propagate prices outwards from zone `z`."""
        for link in z.connections:
            nb = g.zones[link.other(z.name)]
            if nb.zone_type == ZoneType.BLOCKED:
                continue
            if nb.price == -1 or nb.price > z.price + z.cost:
                nb.price = z.price + z.cost
                spread(nb)

    spread(end)


def game_round(g: Graph) -> None:
    """Play one turn: move every drone and print the moves."""
    used: dict[str, int] = {}
    moves = []
    order = sorted(g.drones, key=lambda d: (d.target is None, d.zone.price))
    for drone in order:
        text = drone.move(used)
        if text:
            moves.append(text)
    g.drones = [d for d in g.drones if d.zone is not g.end]
    if moves:
        print(" ".join(moves))


def is_finished(g: Graph) -> bool:
    """Return True when every drone has reached the end zone."""
    if all(d.zone is g.end for d in g.drones):
        return True
    return False
