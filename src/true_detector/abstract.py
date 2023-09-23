import abc


class AbstractPipeline(abc.ABC):
    @abc.abstractmethod
    def process(self):
        ...

    @abc.abstractmethod
    def report(self):
        ...

    @abc.abstractmethod
    def _collect_input(self):
        ...

    @abc.abstractmethod
    def _collect_files(self):
        ...

    @abc.abstractstaticmethod
    def _search_executables(*args):
        ...

    @abc.abstractmethod
    def _collect_executable_names(self):
        ...

    @abc.abstractmethod
    def _count_usages(self):
        ...
