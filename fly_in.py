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
    Edges: list[Edge] = Field(default_factory=list)


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
    zone_a: Vertice | None = None
    zone_b: Vertice | None = None
    max_link_capacity: int = 1


class Drone:
    def __init__(self, drone_id: str, start: Vertice) -> None:
        self.drone_id: str = drone_id
        self.current_zone: Vertice | Edge = start


def parser(file: str, Graph: Graph) -> None:
    with open(file) as f:
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
                        max_drones = int(meta.split('=')[1])
                    if "zone" in meta:
                        zone = VerticeType(meta.split("=")[1])
                Graph.Vertices.append(Vertice(
                    name=line[0],
                    x=int(line[1]),
                    y=int(line[2]),
                    color=color,
                    max_drones=max_drones if max_drones is not None else 1,
                    zone_type=zone if zone is not None else VerticeType.normal,
                ))
            elif 'connection' in line:
                line = line.split(': ')[1]
                line = line.split()
                Graph.Edges.append(Edge(
                    name=line[0],
                    max_link_capacity=int(line[1]) if len(line) > 1 else 1,
                ))
    for connection in Graph.Edges:
        fill_connection(Graph, connection)

def fill_connection(Graph: Graph, connection: Edge):
    name1, name2 = connection.name.split('-')
    print(name1, name2)
    for Vertice in Graph.Vertices:
        if Vertice.name == name1:
            Vertice.Edges.append(connection)
            connection.zone_a = Vertice
            print(connection.name, Vertice.name)
        if Vertice.name == name2:
            Vertice.Edges.append(connection)
            connection.zone_b = Vertice

def main() -> None:
    pass

i = Graph(nb_drones=0)
parser("01_linear_path.txt", i)
print(i.nb_drones)
print(i.Vertices[0])
