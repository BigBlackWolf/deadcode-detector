import abc


class AbstractPipeline(abc.ABC):
    @abc.abstractmethod
    def process():
        ...

    @abc.abstractmethod
    def report():
        ...

    @abc.abstractmethod
    def _collect_input():
        ...

    @abc.abstractmethod
    def _collect_files():
        ...

    @abc.abstractclassmethod
    def _search_executables():
        ...

    @abc.abstractmethod
    def _collect_executable_names():
        ...

    @abc.abstractmethod
    def _count_usages():
        ...
