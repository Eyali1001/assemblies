from __future__ import annotations  # import annotations from later version of python.
# We need it here to annadiane that connectome has a method which returns itself

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Tuple, Optional, TypeVar, Mapping, Generic, Callable, Any

from ..components import BrainPart, Area, Stimulus, Connection  # imports shouldn't depend on dir
                                                                # structure. find an alternative


K_co = TypeVar('K_co', covariant=True)
V_contra = TypeVar('V_contra', contravariant=True)


class MappingProxy(Generic[K_co, V_contra]):
    def __init__(self, getter: Callable[[K_co], V_contra], setter: Callable[[K_co, V_contra], Any]):
        self._getter = getter
        self._setter = setter

    def __getitem__(self, key: K_co):
        return self._getter(key).copy()

    def __setitem__(self, key: K_co, value: V_contra):
        self._setter(key, value.copy())


# TODO: find a better name than ABCConnectome. something that other researches can understand.
# TODO 2: A method named `project` is used but it's not defined in this ABC
class ABCConnectome(metaclass=ABCMeta):
    """
    Represent the graph of connections between areas and stimuli of the brain.
    This is a generic abstract class which offer a good infrastructure for building new models of connectome.
    You should implement some of the parts which are left for private case. For example when and how the connectome
    should be initialized, how the connections are represented.

    Attributes:
        areas: List of area objects in the connectome
        stimuli: List of stimulus objects in the connectome
        connections: Dictionary from tuples of BrainPart(Stimulus/Area) and Area to some object which
        represent the connection (e.g. numpy matrix). Each connection is held ObjectProxy which will
        make the connection.
        to be saved by reference. (This makes the get_subconnectome routine much easier to implement)

    """

    def __init__(self, p, areas=None, stimuli=None):
        self.areas: List[Area] = []
        self.stimuli: List[Stimulus] = []
        self.connections: Dict[Tuple[BrainPart, Area], Connection] = {}
        self.p = p

        if areas:
            self.areas = areas
        if stimuli:
            self.stimuli = stimuli

    def add_area(self, area: Area):
        self.areas.append(area)

    def add_stimulus(self, stimulus: Stimulus):
        self.stimuli.append(stimulus)

    @property
    def winners(self) -> MappingProxy[Area, List[int]]:
        # TODO: document the use of MappingProxy - why is it needed here?
        # TODO 2: can winners be defined as a simple property? (that is, in `__init__` function)
        return MappingProxy(self._get_winners, self._set_winners)

    @abstractmethod
    def _get_winners(self, area: Area) -> List[int]:
        pass

    @abstractmethod
    def _set_winners(self, area: Area, winners: List[int]):
        pass

    @abstractmethod
    def subconnectome(self, connections: Dict[BrainPart, Area]) -> ABCConnectome:
        """
        Retrieve restriction of the connectome to specific subconnectome.
        Note that changes to the returned subconnectome should reflect in the original one. (By reference)
        :param connections: directed connections needed in the subconnectome
        :return: A connectome which is a subgraph of the self connectome, according to the mapping in connections
        """
        pass

    @abstractmethod
    def area_connections(self, area: Area) -> List[BrainPart]:
        """
        Retrieve all parts with connection to specific areas, according to the current connectome
        :param area: area which we need the connections to
        :return: List of all connections to the area
        """
        pass

    def __repr__(self):
        return f'{self.__class__.__name__} with {len(self.areas)} areas, and {len(self.stimuli)} stimuli'
