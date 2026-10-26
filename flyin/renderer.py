"""Graphical display of the simulation, built on pygame."""

import pygame

from models import Graph
from simulation import game_round, is_finished


class Renderer:
    """Draws the network and the drones, and runs the main loop."""

    WIDTH, HEIGHT, MARGIN = 1800, 1000, 80
    SPEED = 6

    def __init__(self, graph: Graph) -> None:
        """Set up the window and load the drone sprite."""
        self.graph = graph
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT))
        img = pygame.image.load("drone.png").convert_alpha()
        self.drone_img: pygame.Surface = pygame.transform.smoothscale(
            img, (40, 40))
        self.all_drones = list(graph.drones)  # keeps finished drones too
        self.pos = {
            d.id: pygame.Vector2(self._to_screen(d.zone.x, d.zone.y))
            for d in self.all_drones
        }

    def _to_screen(self, x: float, y: float) -> tuple[int, int]:
        """Convert map coordinates to pixel coordinates."""
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
        """Turn a color name into a pygame color (gray if unknown)."""
        try:
            return pygame.Color(name or "white")
        except ValueError:
            return pygame.Color("gray")

    def move_drone(self) -> None:
        """Slide each drone sprite a little towards its target position."""
        for d in self.all_drones:
            if d.target is not None:
                mx = (d.zone.x + d.target.x) / 2
                my = (d.zone.y + d.target.y) / 2
                target = pygame.Vector2(self._to_screen(mx, my))
            else:
                target = pygame.Vector2(self._to_screen(d.zone.x, d.zone.y))
            pos = self.pos[d.id]
            delta = target - pos
            if delta.length() > self.SPEED:
                pos += delta.normalize() * self.SPEED
            else:
                pos.update(target)

    def _draw_drones(self) -> None:
        """Draw every drone, slightly offset so stacked ones stay visible."""
        for d in self.all_drones:
            off = pygame.Vector2((d.id % 5 - 2) * 7, (d.id // 5 % 5 - 2) * 7)
            rect = self.drone_img.get_rect(center=self.pos[d.id] + off)
            self.screen.blit(self.drone_img, rect)

    def _draw_links(self) -> None:
        """Draw the links, thicker when their capacity is higher."""
        for link in self.graph.links.values():
            a = self.graph.zones[link.a]
            b = self.graph.zones[link.b]
            pygame.draw.line(self.screen, (120, 120, 120),
                             self._to_screen(a.x, a.y),
                             self._to_screen(b.x, b.y),
                             width=link.capacity * 2)

    def _draw_zones(self) -> None:
        """Draw the zones as circles in their map color."""
        for z in self.graph.zones.values():
            pos = self._to_screen(z.x, z.y)
            pygame.draw.circle(self.screen, self._color(z.color), pos, 20)
            pygame.draw.circle(self.screen, (255, 255, 255), pos, 20, 2)

    def run(self) -> None:
        """Main loop: SPACE plays a turn, closing the window quits."""
        rounds = 0
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if (event.type == pygame.KEYDOWN
                        and event.key == pygame.K_SPACE):
                    game_round(self.graph)
                    rounds += 1
            if is_finished(self.graph):
                running = False
                print(f"Game finished after {rounds} rounds.")
            self.screen.fill((20, 20, 30))
            self._draw_links()
            self._draw_zones()
            self.move_drone()
            self._draw_drones()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()
