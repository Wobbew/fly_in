*This project has been created as part of the 42 curriculum by <wwiedijk>.*

# Fly-in

## Description

Fly-in is a drone routing simulation. Given a map describing a network of zones and connections, the program moves a fleet of drones from a single start zone to a single end zone in as few simulation turns as possible, while respecting zone capacities, link capacities and zone movement costs.

The project contains:

- **A parser** for the map format (`nb_drones`, `start_hub`, `end_hub`, `hub`, `connection`, with `[metadata]` blocks). Any invalid input stops the program with an error message giving the line number and the cause.
- **A simulation engine** that applies the movement and occupancy rules turn by turn.
- **A pathfinding step** that computes, for every zone, its cost to reach the end zone.
- **A graphical interface** (pygame) that shows the network and animates the drones.
- **A terminal output** in the required format: one line per turn, e.g. `D1-roof1 D2-corridorA`.

### Zone types

| Type | Cost to enter | Notes |
|------|---------------|-------|
| `normal` | 1 turn | default |
| `priority` | 1 turn | preferred by the pathfinding |
| `restricted` | 2 turns | the drone waits on the link for one turn, then must arrive |
| `blocked` | n/a | can never be entered |

## Project structure

| File | Role |
|------|------|
| `fly_in.py` | Entry point: map selection, then parse, set up and run |
| `errors.py` | `ParseError`, raised for any invalid map |
| `models.py` | Data model: `ZoneType`, `Zone`, `Link`, `Drone`, `Graph` |
| `map_parser.py` | `MapParser`: reads a map file and builds a `Graph` |
| `simulation.py` | Drone setup, cost map (`find_path`) and turn processing (`game_round`) |
| `renderer.py` | `Renderer`: pygame display and main loop |
| `Makefile` | `install`, `run`, `debug`, `clean`, `fclean`, `lint`, `lint-strict` |
| `maps/` | Map files, grouped by difficulty |
| `drone.png` | Drone sprite used by the display |

## Instructions

### Requirements

- Python 3.10 or later
- `pygame` (installed by `make install`, together with `flake8` and `mypy`)
- `drone.png` in the directory the program is run from
- Map files stored as `maps/<difficulty>/<name>.txt`

### Installation and execution

```bash
make install                              # create the venv and install dependencies
make run                                  # run the program (asks you to pick a map)
make run MAP=maps/<difficulty>/<name>.txt # run a specific map directly
make debug MAP=maps/<difficulty>/<name>.txt  # run under pdb
make lint                                 # flake8 + mypy
make lint-strict                          # flake8 + mypy --strict
make clean                                # remove __pycache__ and .mypy_cache
make fclean                               # clean + remove the venv
```

Without `make`, once the dependencies are installed:

```bash
python3 fly_in.py                         # interactive map selection
python3 fly_in.py maps/<difficulty>/<name>.txt
```

### Controls

- **Space**: play one simulation turn. The turn is printed in the terminal and the drones animate to their new positions.
- **Close the window**: quit.

When every drone has reached the end zone, the window closes and the total number of turns is printed.

### Map format

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
connection: hub-roof1
connection: hub-corridorA [max_link_capacity=2]
```

Zone names cannot contain dashes or spaces. Lines starting with `#` are comments.

## Algorithm and implementation strategy

### 1. Cost map (computed once)

`find_path` assigns each zone a `price`: the cheapest cost to reach the end zone from that zone. It starts at the end zone (price 0) and propagates outwards. When a neighbour can be reached more cheaply through the current zone, its price is updated and the propagation continues from it. Blocked zones are never entered, so no path can go through them.

Zone costs used for the propagation are:

- normal: 1
- restricted: 2
- priority: 0.5

Priority zones cost 0.5 instead of 1 in the propagation, even though they take 1 turn to enter. This does not change the real turn count. It acts as a tie-breaker so that, between two routes of equal length, drones prefer the one through priority zones, as the subject asks.

Prices are computed once and cached, not recalculated every turn.

### 2. Turn simulation

Each turn (`game_round`) builds an empty link-usage counter, then lets every drone try to move, in this order:

1. Drones currently in flight toward a restricted zone go first. They must arrive this turn, so they are never delayed.
2. The remaining drones are sorted by price, lowest first, so drones closest to the end move first and free up space for the ones behind them.

A drone that is not in flight looks at all neighbours and keeps only those that:

- have a lower price than the current zone (so a drone never moves away from the goal),
- are not blocked,
- have link capacity left this turn,
- have room: `len(drones) + incoming < max_drones` (the end zone has no limit).

Among the valid neighbours it picks the one with the lowest price. If none is valid, the drone waits.

### 3. Restricted zones

When a drone chooses a restricted zone, it leaves its current zone and is placed on the link (printed as `D<ID>-<zone1>-<zone2>`). The destination's `incoming` counter is increased so that its slot is reserved while the drone is in transit. On the next turn the drone arrives unconditionally, which respects the rule that it cannot wait on the link.

### 4. Capacity rules

- Zone capacity counts both drones present and drones in transit towards the zone, so a restricted zone can never be over-filled when a drone arrives.
- Link capacity is tracked per turn in a dictionary and checked before each move.
- Drones leaving a zone free its capacity within the same turn, because drones that are closer to the end move first.

### Complexity

- Cost map: computed once, using label-correcting propagation from the end zone.
- Each turn: for each drone, the work is proportional to the number of links of its current zone, plus the sort of the drones (`O(D log D)` for `D` drones).
- Memory: `O(Z + L + D)` for zones, links and drones.

### Limitations

- The strategy is greedy and local: each drone follows the cheapest downhill route given the current state. It does not plan several turns ahead or compute disjoint paths in advance, so on very constrained maps the turn count may not be optimal.
- The propagation is recursive, so extremely long chains of zones could hit Python's recursion limit.

## Visual representation

The pygame window displays:

- **Zones** as circles filled with the colour given in the map's `color=` metadata (unknown colour names fall back to gray, a missing colour is white).
- **Links** as lines whose thickness grows with `max_link_capacity`, so bottlenecks are visible at a glance.
- **Drones** as sprites that glide smoothly between positions instead of jumping.
- **Drones in flight** toward a restricted zone are drawn at the middle of the link, which shows the 2-turn movement.
- **Several drones in one zone** are drawn with a small offset so they do not hide each other.
- The map is scaled automatically to fit the window from the zone coordinates.

Because each turn is triggered with the space bar, you can follow the simulation step by step and match what you see with the terminal output.

## Resources

### References

- Python documentation: https://docs.python.org/3/
- `dataclasses`: https://docs.python.org/3/library/dataclasses.html
- pygame documentation: https://www.pygame.org/docs/
- PEP 8 and PEP 257 (style and docstrings)
- flake8: https://flake8.pycqa.org/
- mypy: https://mypy.readthedocs.io/
- Dijkstra's shortest path algorithm and the Bellman-Ford / label-correcting family (general graph theory references)

### Use of AI

-  AI was used to discuss approaches, to help fix mypy errors, to split the code into modules, to help write this README, for brainstormings how to start it and to make a plan, and understanding how to use pygame.