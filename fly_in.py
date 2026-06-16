from __future__ import annotations  # allows forward references
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class VerticeType(Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class Graph(BaseModel):
    nb_drones: int
    Vertices: list[Vertice] = Field(default_factory=list)


class Vertice(BaseModel):
    name: str
    x: int
    y: int
    zone_type: VerticeType = VerticeType.normal
    color: Optional[str] = None
    max_drones: int = 1
    Edges: list[Edge] = Field(default_factory=list)

    @property
    def movement_cost(self) -> int:
        if self.zone_type == VerticeType.restricted:
            return 2
        return 1


class Edge(BaseModel):
    name: str
    zone_a: Vertice
    zone_b: Vertice
    max_link_capacity: int = 1


class Drone:
    def __init__(self, drone_id: str, start: Vertice) -> None:
        self.drone_id: str = drone_id
        self.current_zone: Vertice | Edge = start


def parser(name: str, Graph: Graph) -> None:
    with open(name) as f:
        for line in f:
            zone = None
            color = None
            max_drones = None
            if line[0] == '#':
                continue
            if 'nb_drones' in line:
                Graph.nb_drones = int(line.split(":")[1])
            elif 'hub' in line:
                line = line.split(': ')[1]
                line = line.strip("[]").split(" ")
                for meta in line:
                    if 'color' in meta:
                        color = meta.split("=")[1]
                    if "max_drones" in meta:
                        max_drones = meta.split('=')[1]
                    if "zone" in meta:
                        zone = meta.split("=")[1]
                Graph.Vertices.append(Vertice(line[0], x=int(line[1]), y=int(line[2]), color=color, max_drones=max_drones, zone_type=zone))
            elif line.startswith('connection'):
                pass
                





def main() -> None:
    pass

i = Graph(nb_drones=0)
parser("01_linear_path.txt", i)
print(i.nb_drones)