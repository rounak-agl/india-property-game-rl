"""Two original 16-card decks.

Card text is written for this project; mechanics follow the standard card types
(move, collect, pay, repairs, jail). Effects are tuples interpreted by engine.py.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    id: str
    deck: str  # "chance" | "chest"
    text: str
    effect: tuple


CHANCE_CARDS: tuple[Card, ...] = (
    Card("ch01", "chance", "Board the express to GO. Collect ₹200.", ("advance", 0)),
    Card("ch02", "chance", "Wedding season in Mumbai! Advance to Mumbai.", ("advance", 39)),
    Card("ch03", "chance", "Business trip to Lucknow. Advance to Lucknow.", ("advance", 21)),
    Card("ch04", "chance", "Pilgrimage to Ludhiana. Advance to Ludhiana.", ("advance", 11)),
    Card("ch05", "chance", "Catch the next train: advance to the nearest railway station.", ("nearest", "station")),
    Card("ch06", "chance", "Catch the next train: advance to the nearest railway station.", ("nearest", "station")),
    Card("ch07", "chance", "Power cut! Advance to the nearest utility.", ("nearest", "utility")),
    Card("ch08", "chance", "Your startup got funded. Collect ₹150.", ("collect", 150)),
    Card("ch09", "chance", "Cricket match bet pays off. Collect ₹50.", ("collect", 50)),
    Card("ch10", "chance", "Missed your stop. Go back 3 spaces.", ("back", 3)),
    Card("ch11", "chance", "Caught jumping the ticket barrier. Go directly to Jail.", ("jail",)),
    Card("ch12", "chance", "Bail bond from a good lawyer. Keep this card to leave Jail free.", ("jail_card",)),
    Card("ch13", "chance", "Traffic challan. Pay ₹15.", ("pay", 15)),
    Card("ch14", "chance", "Monsoon repairs: pay ₹25 per house and ₹100 per hotel.", ("repairs", 25, 100)),
    Card("ch15", "chance", "You hosted the family reunion. Pay your opponent ₹50.", ("pay_opponent", 50)),
    Card("ch16", "chance", "Tour of the capital: advance to New Delhi Railway Station.", ("advance", 25)),
)

CHEST_CARDS: tuple[Card, ...] = (
    Card("cc01", "chest", "Take the morning train to GO. Collect ₹200.", ("advance", 0)),
    Card("cc02", "chest", "Bank interest credited. Collect ₹200.", ("collect", 200)),
    Card("cc03", "chest", "Diwali bonus! Collect ₹100.", ("collect", 100)),
    Card("cc04", "chest", "Income tax refund. Collect ₹20.", ("collect", 20)),
    Card("cc05", "chest", "Fixed deposit matures. Collect ₹100.", ("collect", 100)),
    Card("cc06", "chest", "You won second prize at the rangoli contest. Collect ₹10.", ("collect", 10)),
    Card("cc07", "chest", "Sold your old scooter. Collect ₹50.", ("collect", 50)),
    Card("cc08", "chest", "Life insurance matures. Collect ₹100.", ("collect", 100)),
    Card("cc09", "chest", "Hospital bill. Pay ₹100.", ("pay", 100)),
    Card("cc10", "chest", "School fees due. Pay ₹50.", ("pay", 50)),
    Card("cc11", "chest", "Doctor's consultation. Pay ₹50.", ("pay", 50)),
    Card("cc12", "chest", "Festival gifts from your opponent. Collect ₹50 from them.", ("collect_from_opponent", 50)),
    Card("cc13", "chest", "Municipal property tax: pay ₹40 per house and ₹115 per hotel.", ("repairs", 40, 115)),
    Card("cc14", "chest", "Court summons. Go directly to Jail.", ("jail",)),
    Card("cc15", "chest", "Friendly neighbour stands bail. Keep this card to leave Jail free.", ("jail_card",)),
    Card("cc16", "chest", "Consultancy fee received. Collect ₹25.", ("collect", 25)),
)


class Deck:
    """A shuffled deck. Jail-free cards leave the deck until they are used."""

    def __init__(self, cards: tuple[Card, ...], rng: random.Random):
        order = list(cards)
        rng.shuffle(order)
        self._cards: deque[Card] = deque(order)
        self._held: list[Card] = []

    def draw(self) -> Card:
        card = self._cards.popleft()
        if card.effect[0] == "jail_card":
            self._held.append(card)
        else:
            self._cards.append(card)
        return card

    def return_jail_card(self) -> bool:
        if not self._held:
            return False
        self._cards.append(self._held.pop())
        return True

    def __len__(self) -> int:
        return len(self._cards)
