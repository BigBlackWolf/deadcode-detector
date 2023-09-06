"""TODOs:
- Cover with tests
- Add threading for paralell calculations
- Add progress bar
- Improve variable storage lists
- Store results in csv report
- Make arguments functionall and be available to influence execution
- Enhance the algorithms - check where modules are imported and check only those file
- Does not cover cases, when executable is imported only
"""

import io
import os
import pathlib
import re
import typing

import click

from abstract import AbstractPipeline
from utils import Attributes, CallableListParamType


class PythonPipeline(AbstractPipeline):
    context = Attributes()

    def process(self):
        self._collect_input()
        self._collect_files()
        self._collect_executable_names()
        self._count_usages()
        self._save_results()

    def report(self):
        result = len(set(self.context.callable_list) - set(self.context.found_callable_usage))
        print(f"Found {result} unused callable objects")

    def _collect_input(self):
        self.context.path = click.prompt(
            "Enter absolute path, where you project located", type=click.Path(exists=True)
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
        tree = []
        for root, _, files in os.walk(os.path.abspath(self.context.path)):
            # Ignore hidden folders
            if (nodes := root.split("/")) and (
                set(nodes) & set(self.context.ignore_paths) or nodes[-1].startswith((".", "__"))
            ):
                continue
            result = self._filter_files_by_ext(files, root)
            tree.extend(result)
        self.context.files = tree

    @staticmethod
    def _filter_files_by_ext(files: list[str], root: str, extension: str = ".py") -> list[str]:
        return ["".join((root, "/", file)) for file in files if file.endswith(extension)]

    def _collect_executable_names(self):
        generate_pattern = "|".join([f"(([\s]+)?{keyword}\ )" for keyword in ("class", "def")])
        search_pattern = rf"^({generate_pattern})(.*?(?=\())"

        for file_path in self.context.files:
            with open(file_path, "r") as file:
                executables = self._search_executables(file, search_pattern)
                self.context.callable_list.extend(executables)

    @staticmethod
    def _search_executables(file: io.TextIOWrapper, search_pattern: list[str]) -> list[str]:
        executables = []
        for line in file:
            match = re.search(search_pattern, line)
            # Ignoring magic methods
            if match and (exec_name := match.group(match.lastindex)) and not exec_name.startswith("__"):
                executables.append(exec_name)
        return executables

    # Todo: correct naming
    def _count_usages(self):
        generate_pattern = "".join([rf"(?!.*\b{keyword}\s+{{0}}\b)" for keyword in ("class", "def")])
        finall_pattern = rf"^({generate_pattern}).*\b({{0}})\b(?!\-).*$"

        search_patterns = []
        for executable in self.context.callable_list:
            pattern = finall_pattern.format(executable)
            search_patterns.append(pattern)

        for file_path in self.context.files:
            with open(file_path, "r") as file:
                self._find_substring(file, search_patterns)

    def _find_substring(self, file: io.TextIOWrapper, search_patterns: list[str]):
        for line in file:
            for pattern in search_patterns:
                if pattern in self.context.exclude_pattern:
                    continue
                match = re.search(pattern, line)
                if match and (exec_name := match.group(match.lastindex)):
                    self.context.exclude_pattern.append(pattern)
                    self.context.found_callable_usage.append(exec_name)

    def _save_results(self):
        pass


@click.command()
@click.argument("path", type=click.Path(exists=True), required=False)
def main(path):
    pipeline = PythonPipeline()
    pipeline.process()
    pipeline.report()


if __name__ == "__main__":
    main()
