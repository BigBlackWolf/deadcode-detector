"""TODOs:
- Migrate to using ast
- Cover with tests

- Improve variable storage lists
- Store results in csv report
- Make arguments functionall and be available to influence execution
- Enhance the algorithms - check where modules are imported and check only those file
- Does not cover cases, when executable is imported only
"""

import ast
import io
import os
import pathlib
import re
import typing
from concurrent import futures

import click

from true_detector.abstract import AbstractPipeline
from true_detector.visitor import Visitor
from true_detector.utils import Attributes, CallableListParamType


class Node:
    value: str
    root: typing.Self = None
    children: list[typing.Self] = []

    def __init__(self, value):
        self.value = value


class PythonPipeline(AbstractPipeline):

    def __init__(self):
        self.context = Attributes()

    def process(self):
        self._collect_input()
        self._collect_files()
        analyze = self._collect_executable_names()
        results = self._count_usages(analyze)
        self._save_results(results)

    def report(self):
        result = set(self.context.callable_list) - set(self.context.found_callable_usage)
        print(f"Found {len(result)} unused callable objects")

    def _collect_input(self):
        self.context.path = click.prompt(
            "Enter path, where you project located", type=click.Path(exists=True)
        )
        if click.prompt("Do you want to check specific functions/classes usage?", default=False):
            self.context.callable_list = click.prompt(
                "Set desired names separated by ','", type=CallableListParamType()
            )
            repr_list = "\n" + ",".join(name for name in self.context.callable_list)
            click.echo(f"List of functions/classes to search:\n{repr_list}")
        if click.prompt("Do you want to add folders/files to ignore?", default=False):
            self.context.ignore_paths = click.prompt(
                "List of flies / dir, separated by ','", type=CallableListParamType()
            )

    def _collect_files(self):
        files_tree = []
        modules_tree = []
        for root, _, files in os.walk(self.context.path):
            # Ignore hidden folders
            if (nodes := root.split("/")) and (
                set(nodes) & set(self.context.ignore_paths) or nodes[-1].startswith((".", "__"))
            ):
                continue
            file_paths, modules = self._filter_files_by_ext(files, root)
            files_tree.extend(file_paths)
            modules_tree.extend(modules)
        self.context.files = files_tree
        self.context.modules = modules_tree

    @staticmethod
    def _filter_files_by_ext(files: list[str], root: str, extension: str = ".py") -> tuple[list[str], list[str]]:
        file_paths = []
        modules = []
        for file in files:
            if file.endswith(extension):
                file_path = "/".join((root, file))
                file_paths.append(file_path)

                file = file.split(extension)[0]
                module = ".".join((root, file))
                modules.append(module)
        return file_paths, modules

        return ["".join((root, "/", file)) for file in files if file.endswith(extension)]

    def _collect_executable_names(self):
        to_analyze = {}
        for file_path in self.context.files:
            executables = self._search_executables(file_path)
            if executables.get("callables", None):
                to_analyze[file_path] = self._search_executables(file_path)
        return to_analyze

    @staticmethod
    def _search_executables(file_path: str) -> dict[str, list | dict]:
        with open(file_path, "r") as file:
            code = file.read()
            try:
                tree = ast.parse(code)
            except SyntaxError:
                return {}
        visitor = Visitor()
        visitor.visit(tree)
        data = visitor.report()
        return data
    
    def _count_usages(self, analyze):
        callables = {}
        for file, data in analyze.items():
            callables[file] = data.get("callables", set())
        return callables

    def _save_results(self, results):
        print(f"Unused callables: {results}")


@click.command()
@click.argument("path", type=click.Path(exists=True), required=False)
def main(path):
    pipeline = PythonPipeline()
    pipeline.process()
    pipeline.report()


if __name__ == "__main__":
    main()
