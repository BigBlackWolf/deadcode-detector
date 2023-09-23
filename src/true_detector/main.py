"""TODOs:
- Cover with tests
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
from concurrent import futures

import click

from abstract import AbstractPipeline
from utils import Attributes, CallableListParamType


class PythonPipeline(AbstractPipeline):

    def __init__(self):
        self.context = Attributes()

    def process(self):
        self._collect_input()
        self._collect_files()
        with futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            self._collect_executable_names(executor)
            self._count_usages(executor)
        self._save_results()

    def report(self):
        result = set(self.context.callable_list) - set(self.context.found_callable_usage)
        print(f"Found {len(result)} unused callable objects")

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

    def _collect_executable_names(self, executor):
        generate_pattern = "|".join([fr"(([\s]+)?{keyword}\ )" for keyword in ("class", "def")])
        search_pattern = fr"^({generate_pattern})(.*?(?=\())"

        results = []
        for file_path in self.context.files:
            future = executor.submit(self._search_executables, file_path, search_pattern)
            results.append(future)

        for result in futures.as_completed(results):
            self.context.callable_list.extend(result.result())

    @staticmethod
    def _search_executables(file_path: str, search_pattern: str) -> list[str]:
        executables = []
        with open(file_path, "r") as file:
            for line in file:
                match = re.search(search_pattern, line)
                # Ignoring magic methods
                if match and (exec_name := match.group(match.lastindex)) and not exec_name.startswith("__"):
                    executables.append(exec_name.strip())
        return executables

    # Todo: correct naming
    def _count_usages(self, executor):
        generate_pattern = "".join([fr"(?!.*\b{keyword}\s+{{0}}\b)" for keyword in ("class", "def")])
        finall_pattern = fr"^({generate_pattern}).*\b({{0}})\b(?!\-).*$"

        search_patterns = []
        for executable in self.context.callable_list:
            pattern = finall_pattern.format(executable)
            search_patterns.append(pattern)

        for file_path in self.context.files:
            executor.submit(self._find_substring, file_path, search_patterns)

    def _find_substring(self, file_path: str, search_patterns: list[str]):
        with open(file_path, "r") as file:
            content = file.read()
            for pattern in search_patterns:
                if pattern in self.context.exclude_pattern:
                    continue
                match = re.search(pattern, content)
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
