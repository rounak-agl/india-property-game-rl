"""The 40-space Indian board.

Space names follow the Funskool India (2008) board. Prices and rents use the
classic standard-edition structure in rupees (decision D-007).
"""

from __future__ import annotations

from dataclasses import dataclass

GO_SALARY = 200
START_CASH = 1500
JAIL_INDEX = 10
GO_TO_JAIL_INDEX = 30
JAIL_FINE = 50
MAX_HOUSES = 5  # level 5 == hotel
STATION_RENTS = (25, 50, 100, 200)
UTILITY_MULTIPLIERS = (4, 10)


@dataclass(frozen=True)
class Tile:
    idx: int
    name: str
    kind: str  # city | station | utility | tax | chance | chest | go | jail | parking | goto_jail
    group: int | None = None  # 1..8 colour groups, 9 = stations, 10 = utilities
    price: int = 0
    rents: tuple[int, ...] = ()  # base, 1..4 houses, hotel
    house_cost: int = 0
    tax: int = 0

    @property
    def buyable(self) -> bool:
        return self.kind in ("city", "station", "utility")

    @property
    def mortgage_value(self) -> int:
        return self.price // 2


STATIONS_GROUP = 9
UTILITIES_GROUP = 10

GROUP_NAMES: dict[int, str] = {
    1: "Brown",
    2: "Light Blue",
    3: "Pink",
    4: "Orange",
    5: "Red",
    6: "Yellow",
    7: "Green",
    8: "Dark Blue",
    STATIONS_GROUP: "Stations",
    UTILITIES_GROUP: "Utilities",
}

COLOR_GROUPS = tuple(range(1, 9))


def _city(idx: int, name: str, group: int, price: int, rents: tuple[int, ...], house: int) -> Tile:
    return Tile(idx, name, "city", group, price, rents, house)


TILES: tuple[Tile, ...] = (
    Tile(0, "GO", "go"),
    _city(1, "Guwahati", 1, 60, (2, 10, 30, 90, 160, 250), 50),
    Tile(2, "Community Chest", "chest"),
    _city(3, "Bhubaneshwar", 1, 60, (4, 20, 60, 180, 320, 450), 50),
    Tile(4, "Income Tax", "tax", tax=200),
    Tile(5, "Chennai Central Railway Station", "station", STATIONS_GROUP, 200),
    _city(6, "Panaji (Goa)", 2, 100, (6, 30, 90, 270, 400, 550), 50),
    Tile(7, "Chance", "chance"),
    _city(8, "Agra", 2, 100, (6, 30, 90, 270, 400, 550), 50),
    _city(9, "Vadodara", 2, 120, (8, 40, 100, 300, 450, 600), 50),
    Tile(10, "Jail / Just Visiting", "jail"),
    _city(11, "Ludhiana", 3, 140, (10, 50, 150, 450, 625, 750), 100),
    Tile(12, "Electric Company", "utility", UTILITIES_GROUP, 150),
    _city(13, "Patna", 3, 140, (10, 50, 150, 450, 625, 750), 100),
    _city(14, "Bhopal", 3, 160, (12, 60, 180, 500, 700, 900), 100),
    Tile(15, "Howrah Railway Station", "station", STATIONS_GROUP, 200),
    _city(16, "Indore", 4, 180, (14, 70, 200, 550, 750, 950), 100),
    Tile(17, "Community Chest", "chest"),
    _city(18, "Nagpur", 4, 180, (14, 70, 200, 550, 750, 950), 100),
    _city(19, "Kochi", 4, 200, (16, 80, 220, 600, 800, 1000), 100),
    Tile(20, "Free Parking", "parking"),
    _city(21, "Lucknow", 5, 220, (18, 90, 250, 700, 875, 1050), 150),
    Tile(22, "Chance", "chance"),
    _city(23, "Chandigarh", 5, 220, (18, 90, 250, 700, 875, 1050), 150),
    _city(24, "Jaipur", 5, 240, (20, 100, 300, 750, 925, 1100), 150),
    Tile(25, "New Delhi Railway Station", "station", STATIONS_GROUP, 200),
    _city(26, "Pune", 6, 260, (22, 110, 330, 800, 975, 1150), 150),
    _city(27, "Hyderabad", 6, 260, (22, 110, 330, 800, 975, 1150), 150),
    Tile(28, "Water Works", "utility", UTILITIES_GROUP, 150),
    _city(29, "Ahmedabad", 6, 280, (24, 120, 360, 850, 1025, 1200), 150),
    Tile(30, "Go To Jail", "goto_jail"),
    _city(31, "Kolkata", 7, 300, (26, 130, 390, 900, 1100, 1275), 200),
    _city(32, "Chennai", 7, 300, (26, 130, 390, 900, 1100, 1275), 200),
    Tile(33, "Community Chest", "chest"),
    _city(34, "Bengaluru", 7, 320, (28, 150, 450, 1000, 1200, 1400), 200),
    Tile(35, "Chhatrapati Shivaji Terminus", "station", STATIONS_GROUP, 200),
    Tile(36, "Chance", "chance"),
    _city(37, "Delhi", 8, 350, (35, 175, 500, 1100, 1300, 1500), 200),
    Tile(38, "Super Tax", "tax", tax=100),
    _city(39, "Mumbai", 8, 400, (50, 200, 600, 1400, 1700, 2000), 200),
)

BUYABLE_INDICES: tuple[int, ...] = tuple(t.idx for t in TILES if t.buyable)  # 28 tiles

GROUP_MEMBERS: dict[int, tuple[int, ...]] = {
    g: tuple(t.idx for t in TILES if t.group == g) for g in GROUP_NAMES
}

STATION_INDICES = GROUP_MEMBERS[STATIONS_GROUP]
UTILITY_INDICES = GROUP_MEMBERS[UTILITIES_GROUP]

assert len(TILES) == 40 and all(t.idx == i for i, t in enumerate(TILES))
assert len(BUYABLE_INDICES) == 28
