from __future__ import annotations  # allows forward references
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional
import os
import pygame
map_path = None


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


# from typing import Callable
# import pygame


# class Button:
#     """A clickable button with an associated action.

#     Args:
#         rect: The clickable area of the button.
#         label: Text displayed on the button.
#         color: Background color name.
#         on_click: Function called with no arguments when clicked.
#     """

#     def __init__(
#         self,
#         rect: pygame.Rect,
#         label: str,
#         color: str,
#         on_click: Callable[[], None],
#     ) -> None:
#         self.rect = rect
#         self.label = label
#         self.color = color
#         self.on_click = on_click

#     def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
#         """Draw this button onto the given surface.

#         Args:
#             surface: The pygame surface to draw on.
#             font: The font used to render the button label.
#         """
#         pygame.draw.rect(surface, pygame.Color(self.color), self.rect, border_radius=8)
#         text_surface = font.render(self.label, True, pygame.Color("white"))
#         text_rect = text_surface.get_rect(center=self.rect.center)
#         surface.blit(text_surface, text_rect)

#     def handle_event(self, event: pygame.event.Event) -> None:
#         """Trigger on_click if this button was clicked.

#         Args:
#             event: The pygame event to check.
#         """
#         if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#             if self.rect.collidepoint(event.pos):
#                 self.on_click()


# class Screen:
#     """Manages the pygame window, buttons, and the main loop."""

#     def __init__(self) -> None:
#         pygame.init()
#         self.surface = pygame.display.set_mode((800, 600))
#         self.font = pygame.font.SysFont(None, 32)
#         self.buttons: list[Button] = []
#         self.background_color = pygame.Color("black")

#     def add_button(
#         self,
#         name: str,
#         color: str,
#         x: int,
#         y: int,
#         on_click: Callable[[], None],
#         width: int = 160,
#         height: int = 50,
#     ) -> Button:
#         rect = pygame.Rect(x, y, width, height)
#         button = Button(rect, name, color, on_click)
#         self.buttons.append(button)
#         return button

#     def clear_buttons(self) -> None:
#         """Remove all currently registered buttons (e.g. when changing screens)."""
#         self.buttons.clear()

#     def run(self) -> None:
#         """Run the main event loop until the window is closed."""
#         running = True
#         while running:
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     running = False
#                 for button in self.buttons:
#                     button.handle_event(event)
#             if map_path is not None:
#                 map_setup(self)
#             self.surface.fill(self.background_color)
#             for button in self.buttons:
#                 button.draw(self.surface, self.font)
#             pygame.display.flip()

#         pygame.quit()
def map_setup(s: Screen):
    global map_path
    print(map_path)

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


def set_map_path(path: str, s: Screen):
    s.clear_buttons()
    global map_path
    map_path = path

def map_difficulty():
    difficulty = []
    folders = os.listdir('maps/')
    for folder in folders:
        if ('.' not in folder):
            difficulty.append(folder)
    return difficulty


def map_list(path: str, s: Screen):
    s.clear_buttons()
    maps = []
    files = os.listdir('maps/' + path)
    for file in files:
        if file.endswith('.txt'):
            maps.append(file)
    for map in maps:
        s.add_button(map, "blue", 320, 250 + maps.index(map) * 70, lambda f=map: set_map_path(path + "/" + f, s))
        pygame.display.flip()

def choose_map(s: Screen):
    difficulty = map_difficulty()
    for level in difficulty:
        s.add_button(level, "blue", 320, 250 + difficulty.index(level) * 70, lambda p=level: map_list(p, s))
        pygame.display.flip()




def main() -> None:
    s = Screen()
    choose_map(s)
    s.run()


main()