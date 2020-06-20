import sys
from pathlib import Path
import importlib
import re
from brain import Brain


class ReadDriver:
    """
    An object representing a reader that can use several different implementations for reading
    from assemblies. The implementation is chosen by the parameter 'reader_name'.
    An automatic framework collects every class beginning with "Read" from assembly_readers
    and collects it into the dictionary. The key is the 'name' parameter of the class.

    :param reader_name: the name of the reader we've chosen to use
    """

    def __init__(self, reader_name):
        self.readers = {}
        # Path to assemblies package
        assemblies_package_path = Path(__file__).parent.absolute()
        readers = assemblies_package_path / 'assembly_readers'
        sys.path.insert(0, str(assemblies_package_path))
        for path in readers.iterdir():
            if not (path.is_file() and path.suffix == '.py'):
                continue
            m = importlib.import_module(f'{readers.name}.{path.stem}')
            for name in m.__dict__:
                val = m.__dict__[name]
                if not (re.match('Read*', name) and 'name' in val.__dict__.keys()):
                    continue
                self.readers[val.__dict__['name']] = val
        self.reader = self.readers[reader_name]

    def read(self, assembly, brain: Brain, preserve_brain: bool = False):
        """
        Read the winners from given assembly in given brain and return the result.

        :param assembly: the assembly object
        :param brain: the brain object
        :param preserve_brain: a boolean representing whether we want to change the brain state or not
        :return: the winners as read from the area that we've fired up
        """
        return self.reader.read(assembly, brain=brain, preserve_brain=preserve_brain)

    def update_hook(self, brain: Brain, assembly):
        """
        Internal hook for readers to subscribe to, allowing more elaborate read drivers.
        Called every time an assembly is changed.
        :param brain: the brain object
        :param assembly: the assembly object
        """
        if hasattr(self.reader, 'update_hook'):
            self.reader.update_hook(self, brain, assembly)
