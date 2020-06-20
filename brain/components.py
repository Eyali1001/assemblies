from __future__ import annotations
import math
from typing import Optional, Union, TYPE_CHECKING
import uuid
from uuid import UUID

if TYPE_CHECKING:
    from .brain import Brain

from utils.bindable import Bindable, bindable_property


class UniquelyIdentifiable:
    hist = {}

    def __init__(self, uid=None):
        self._uid: UUID = uuid.uuid4()
        if uid is not None and uid in UniquelyIdentifiable.hist:
            self._uid = UniquelyIdentifiable.hist[uid]
        elif uid is not None:
            UniquelyIdentifiable.hist[uid] = self._uid

    def __hash__(self):
        return hash(self._uid)

    def __eq__(self, other):
        return type(self) == type(other) and self._uid == getattr(other, '_uid', None)


@Bindable('brain')
class Area(UniquelyIdentifiable):
    def __init__(self, n: int, k: Optional[int] = None, beta: float = 0.01):
        super(Area, self).__init__()
        self.beta: float = beta
        self.n: int = n
        self.k: int = k if k is not None else int(n ** 0.5)

        if k == 0:
            self.k = math.sqrt(n)

    @bindable_property
    def winners(self, *, brain: Brain):
        return brain.winners[self]

    @bindable_property
    def support(self, *, brain: Brain):
        return brain.support[self]

    @bindable_property
    def active_assembly(self, *, brain: Brain):
        from assemblies.assembly_fun import Assembly
        return Assembly.read(self, brain=brain)

    def __repr__(self):
        return f"Area(n={self.n}, k={self.k}, beta={self.beta})"


class Stimulus(UniquelyIdentifiable):
    def __init__(self, n: int, beta: float = 0.05):
        super(Stimulus, self).__init__()
        self.n = n
        self.beta = beta

    def __repr__(self):
        return f"Stimulus(n={self.n}, beta={self.beta})"


class OutputArea(Area):
    def __init__(self, n: int, beta: float):
        super(OutputArea, self).__init__(n=n, beta=beta)

    def __repr__(self):
        return f"OutputArea(n={self.n}, beta={self.beta})"


BrainPart = Union[Area, Stimulus, OutputArea]


class Connection:
    def __init__(self, source: BrainPart, dest: BrainPart, synapses=None):
        self.source: BrainPart = source
        self.dest: BrainPart = dest
        self.synapses = synapses if synapses is not None else {}

    @property
    def beta(self):
        if isinstance(self.source, Stimulus):
            return self.dest.beta
        return self.source.beta

    def __getitem__(self, key: int):
        return self.synapses[key]

    def __setitem__(self, key: int, value: float):
        self.synapses[key] = value

    def __repr__(self):
        return f"Connection(synapses={self.synapses!r})"
