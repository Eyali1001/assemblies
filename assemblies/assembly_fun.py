from __future__ import annotations
from .read_driver import ReadDriver
from utils.blueprints.recordable import Recordable
from utils.implicit_resolution import ImplicitResolution
from utils.bindable import Bindable
from brain.components import Stimulus, Area, UniquelyIdentifiable
from typing import Iterable, Union, Tuple, TYPE_CHECKING, Set, Optional, Dict
from itertools import product

if TYPE_CHECKING:
    from brain import Brain
    from brain.brain_recipe import BrainRecipe

Projectable = Union['Assembly', Stimulus]

# TODO: Look at parameters as well? (Yonatan, for associate)
bound_assembly_tuple = ImplicitResolution(lambda instance, name:
                                          Bindable.implicitly_resolve_many(instance.assemblies, name, False), 'brain')


@Recordable(('merge', True), 'associate',
            resolution=ImplicitResolution(
                lambda instance, name: Bindable.implicitly_resolve_many(instance.assemblies, name, False), 'recording'))
class AssemblyTuple(object):
    """
    Wraps a tuple of assemblies with syntactic sugar, such as >> (merge).

    :param assemblies: a tuple containing the assemblies
    """

    def __init__(self, *assemblies: Assembly):
        self.assemblies: Tuple[Assembly, ...] = assemblies

    def __add__(self, other: AssemblyTuple):
        """
        In the context of AssemblyTuples, + creates a new AssemblyTuple containing the members
        of both parts.

        :param other: the other AssemblyTuple we add
        :returns: the new AssemblyTuple
        """
        assert isinstance(other, AssemblyTuple), "Assemblies can be concatenated only to assemblies"
        return AssemblyTuple(*(self.assemblies + other.assemblies))

    @bound_assembly_tuple
    def merge(self, area: Area, *, brain: Brain = None):
        return Assembly._merge(self.assemblies, area, brain=brain)

    @bound_assembly_tuple
    def associate(self, other: AssemblyTuple, *, brain: Brain = None):
        return Assembly._associate(self.assemblies, other.assemblies, brain=brain)

    def __rshift__(self, other: Area):
        """
        In the context of assemblies, >> symbolizes merge.
        Example: (within a brain context) (a1+a2+a3)>>area

        :param other: the area we merge into
        :return: the new merged assembly
        """
        assert isinstance(other, Area), "Assemblies must be merged onto an area"
        return self.merge(other)

    def __iter__(self):
        return iter(self.assemblies)


@Recordable(('project', True), ('reciprocal_project', True))
@Bindable('brain')
class Assembly(UniquelyIdentifiable, AssemblyTuple):
    """
    A representation of an assembly of neurons that can be binded to a specific brain
    in which it appears. An assembly is defined primarily by its parents - the assemblies
    and/or stimuli that were fired to create it.
    This class implements basic operations on assemblies (project, reciprocal_project,
    merge and associate) by using a reader object, which interacts with the brain directly.

    :param parents: the Assemblies and/or Stimuli that were used to create the assembly
    :param appears_in: an iterable containing every BrainRecipe in which the assembly appears
    :param area: an Area where the Assembly "lives"
    :param reader: name of a read driver pulled from assembly_readers. defaults to 'default'
    """

    def __init__(self, parents: Iterable[Projectable], area: Area,
                 appears_in: Iterable[BrainRecipe] = None, reader: str = 'default'):
        # we hash an assembly using its parents (sorted by id) and area
        # this way equivalent assemblies have the same id.
        UniquelyIdentifiable.__init__(self, uid=hash((area, *sorted(parents, key=hash))))
        AssemblyTuple.__init__(self, self)

        self.parents: Tuple[Projectable, ...] = tuple(parents)
        self.area: Area = area
        self.reader = ReadDriver(reader)
        self.appears_in: Set[BrainRecipe] = set(appears_in or [])
        for recipe in self.appears_in:
            recipe.append(self)

    def identify(self, preserve_brain=False, *, brain: Brain) -> Tuple[int, ...]:
        return self.reader.read(self, brain, preserve_brain=preserve_brain)

    @staticmethod
    def read(area, *, brain: Brain):
        assemblies: Set[Assembly] = brain.recipe.area_assembly_mapping[area]
        overlap: Dict[Assembly, float] = {}
        for assembly in assemblies:
            overlap[assembly] = len(set(area.winners) & set(assembly.identify(preserve_brain=True, brain=brain)))/area.k
        return max(overlap.keys(), key=lambda x: overlap[x])

    def _update_hook(self, *, brain: Brain):
        self.reader.update_hook(brain, self)

    def project(self, area: Area, *, brain: Brain = None, iterations: Optional[int] = None) -> Assembly:
        """
        Projects an assembly into an area.

        :param brain: the brain in which the projection happens
        :param area: the area in which the new assembly is going to be created
        :returns: resulting projected assembly
        """
        assert isinstance(area, Area), "Project target must be an Area"
        projected_assembly: Assembly = Assembly([self], area, appears_in=self.appears_in)
        if brain is not None:
            neurons = self.identify(brain=brain)

            # TODO: Eyal see my update to line after merge
            # LINE FOR AFTER MERGE WITH PERFORMANCE
            brain.connectome.winners[self.area] = neurons
            #print(isinstance(neurons,Area))
            # CURRENT TEMPORARY BOOTSTRAPPING LINE
            #brain.connectome._winners[self.area] = set(neurons)

            # Replace=True for better performance
            brain.next_round({self.area: [area]}, replace=True, iterations=iterations or brain.repeat)

            projected_assembly._update_hook(brain=brain)

        projected_assembly.bind_like(self)
        return projected_assembly

    def __rshift__(self, other: Area):
        """
        In the context of assemblies, >> represents project.
        Example: a >> A (a is an assembly, A is an area)

        :param other: the area into which we project
        :returns: the new assembly that was created
        """
        assert isinstance(other, Area), "Assembly must be projected onto an area"
        return self.project(other)

    def reciprocal_project(self, area: Area, *, brain: Brain = None) -> Assembly:
        """
        Reciprocally projects an assembly into an area,
        creating a projected assembly with strong bi-directional links to the current one.

        :param brain: the brain in which the projection occurs
        :param area: the area into which we project
        :returns: Resulting projected assembly
        """
        projected_assembly: Assembly = self.project(area, brain=brain)
        projected_assembly.project(self.area, brain=brain)
        self._update_hook(brain=brain)

        return projected_assembly

    @staticmethod
    def _merge(assemblies: Tuple[Assembly, ...], area: Area, *, brain: Brain = None) -> Assembly:
        """
        Creates a new assembly with all input assemblies as parents.
        Practically creates a new assembly with one-directional links from parents.
        ONLY CALL AS: Assembly.merge(...), as the function is invariant under input order.

        :param brain: the brain in which the merge occurs
        :param assemblies: the parents of the new merged assembly
        :param area: the area into which we merge
        :returns: resulting merged assembly
        """
        assert len(assemblies) != 0, "tried to merge with empty input"

        merged_assembly: Assembly = Assembly(assemblies, area,
                                             appears_in=set.intersection(*[x.appears_in for x in assemblies]))
        if brain is not None:
            # create a mapping from the areas to the neurons we want to fire
            area_neuron_mapping = {ass.area: set() for ass in assemblies}
            for ass in assemblies:
                area_neuron_mapping[ass.area].update(ass.identify(brain=brain))

            # update winners for relevant areas in the connectome
            for a in area_neuron_mapping:
                brain.connectome[a]._winners = area_neuron_mapping[a]

            # Replace=True for better performance
            brain.next_round({a: [area] for a in area_neuron_mapping}, replace=True, iterations=brain.repeat)
        merged_assembly.bind_like(*assemblies)
        return merged_assembly

    @staticmethod
    def _associate(a: Tuple[Assembly, ...], b: Tuple[Assembly, ...], *, brain: Brain = None) -> None:
        """
        Associates two lists of assemblies, by strengthening each bond in the
        corresponding bipartite graph.
        for simple binary operation use Assembly.associate([a],[b]).
        for each x in A, y in B, associate (x,y).
        A1 z-z B1
        A2 -X- B2
        A3 z-z B3

        :param a: first list
        :param b: second list
        """
        pairs = product(a, b)
        for x, y in pairs:
            Assembly._merge((x, y), x.area, brain=brain)  # Eyal: You omitted brain, notice that you need to specify it

    def __lt__(self, other: Assembly):
        """
        Checks that other is a child assembly of self.

        :param other: the assembly we compare against
        """
        return isinstance(other, Assembly) and other in self.parents

    def __gt__(self, other: Assembly):
        """
        Checks if self is a child assembly of other.

        :param other: the assembly we compare against
        """
        return isinstance(other, Assembly) and self in other.parents
