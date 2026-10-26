"""Fly-in: entry point. Picks a map, parses it and runs the simulation."""

import os
import sys

import pygame

from errors import ParseError
from map_parser import MapParser
from renderer import Renderer
from simulation import find_path, set_up_drones


def choose_map() -> str:
    """Let the user pick a map from the maps/ folder and return its path."""
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
    """Parse the map, compute the cost map and start the display."""
    try:
        path = choose_map() if len(sys.argv) == 1 else sys.argv[1]
        graph = MapParser().parse(path)
        set_up_drones(graph)
        find_path(graph)
        Renderer(graph).run()
    except ParseError as e:
        print(e)
    except (pygame.error, FileNotFoundError) as e:
        print(f"graphics error: {e}")


if __name__ == "__main__":
    main()
