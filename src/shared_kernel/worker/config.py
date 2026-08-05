from dataclasses import dataclass

from ..config.topology import Queue


@dataclass(frozen=True)
class ConsumerConfig:
    queues: list[Queue]
    prefetch_count: int = 100
