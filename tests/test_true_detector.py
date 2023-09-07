from click.testing import CliRunner
import pytest
import os

from true_detector.main import PythonPipeline, main
from true_detector.abstract import AbstractPipeline


@pytest.fixture
def pipeline() -> PythonPipeline:
    pipeline = PythonPipeline()
    pipeline.context.path = "tests/data"
    assert isinstance(pipeline, AbstractPipeline)
    return pipeline


def test_collect_files(pipeline: PythonPipeline):
    pipeline._collect_files()
    assert len(pipeline.context.files) == 1
    assert pipeline.context.files[0].endswith("py_tests.py")


def test_collect_executable_names(pipeline: PythonPipeline):
    pipeline._collect_files()
    pipeline._collect_executable_names()
    assert len(pipeline.context.callable_list) == 9
    