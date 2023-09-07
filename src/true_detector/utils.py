import re
import typing
from dataclasses import dataclass, field

import click


@dataclass(slots=True)
class Attributes:
    path: str = None
    callable_list: typing.Optional[list[str]] = field(default_factory=list)
    ignore_paths: typing.Optional[list[str]] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    found_callable_usage: typing.Optional[list[str]] = field(default_factory=list)
    exclude_pattern: typing.Optional[list[str]] = field(default_factory=list)


class CallableListParamType(click.ParamType):
    name = "callable_list"
    pattern = r"([a-zA-Z0-9\,\_\-])+"
    regexp = re.compile(pattern)

    def convert(
        self,
        value: str,
        param: typing.Optional["Parameter"],
        ctx: typing.Optional["Context"],
    ) -> list[str]:
        try:
            if value != self.regexp.match(value).group(0):
                raise AttributeError()
            names = set(value.split(","))
            if "" in names:
                names.remove("")
            if not names:
                raise ValueError()
            return list(names)
        except AttributeError:
            self.fail(f"Value {value!r} doesn't match pattern {self.pattern}", param, ctx)
        except ValueError:
            self.fail(f"Input is incorrect", param, ctx)
