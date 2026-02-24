# FILE: scene/world.py
from __future__ import annotations
from dataclasses import dataclass, field
from core.geometry.vec3 import Vec3
from scene.entities import Player, Block, STEVE_GEOMETRY, ALEX_GEOMETRY

@dataclass
class World:
    player_a: Player
    player_b: Player
    blocks: dict[tuple[int, int, int], Block] = field(default_factory=dict)
    ground_y: int = 0

    def clone(self) -> "World":
        a = Player(
            name=self.player_a.name,
            pos=Vec3(self.player_a.pos.x, self.player_a.pos.y, self.player_a.pos.z),
            width=float(self.player_a.width),
            height=float(self.player_a.height),
            eye=float(self.player_a.eye),
            model=str(self.player_a.model),
            geometry=str(self.player_a.geometry),
        )
        b = Player(
            name=self.player_b.name,
            pos=Vec3(self.player_b.pos.x, self.player_b.pos.y, self.player_b.pos.z),
            width=float(self.player_b.width),
            height=float(self.player_b.height),
            eye=float(self.player_b.eye),
            model=str(self.player_b.model),
            geometry=str(self.player_b.geometry),
        )
        w = World(a, b, ground_y=int(self.ground_y))
        w.blocks = dict(self.blocks)
        return w

    def solid_block_keys(self) -> set[tuple[int, int, int]]:
        return set(self.blocks.keys())

    def all_block_aabbs(self) -> list:
        return [b.aabb() for b in self.blocks.values()]

    def add_block(self, x: int, y: int, z: int, manual: bool = True) -> None:
        key = (int(x), int(y), int(z))
        self.blocks[key] = Block(key[0], key[1], key[2], manual=bool(manual))

    def remove_block(self, x: int, y: int, z: int) -> None:
        key = (int(x), int(y), int(z))
        if key in self.blocks:
            del self.blocks[key]

    def set_player_pos(self, who: str, pos: Vec3) -> None:
        if who == "A":
            self.player_a.pos = pos
            self._ensure_support_under(self.player_a)
        else:
            self.player_b.pos = pos
            self._ensure_support_under(self.player_b)

    def rebuild_supports(self) -> None:
        self._ensure_support_under(self.player_a)
        self._ensure_support_under(self.player_b)

    def cleanup_unused_auto_supports(self) -> None:
        required = self._required_support_keys()
        to_delete: list[tuple[int, int, int]] = []
        for k, b in self.blocks.items():
            if b.manual:
                continue
            if k not in required:
                to_delete.append(k)
        for k in to_delete:
            del self.blocks[k]

    def _required_support_keys(self) -> set[tuple[int, int, int]]:
        req: set[tuple[int, int, int]] = set()
        for p in (self.player_a, self.player_b):
            fx = int(p.pos.x)
            fz = int(p.pos.z)
            fy = int(p.pos.y)
            top = fy - 1
            for y in range(top, self.ground_y - 1, -1):
                req.add((fx, int(y), fz))
        return req

    def _ensure_support_under(self, p: Player) -> None:
        fx = int(p.pos.x)
        fz = int(p.pos.z)
        fy = int(p.pos.y)
        top = fy - 1
        for y in range(top, self.ground_y - 1, -1):
            key = (fx, int(y), fz)
            if key not in self.blocks:
                self.blocks[key] = Block(key[0], key[1], key[2], manual=False)

    @staticmethod
    def default_world() -> "World":
        a = Player("A", Vec3(3.5, 0.0, 1.5), model="Steve", geometry=STEVE_GEOMETRY)
        b = Player("B", Vec3(1.5, 2.0, 3.5), model="Alex", geometry=ALEX_GEOMETRY)
        w = World(a, b)
        w.rebuild_supports()
        return w