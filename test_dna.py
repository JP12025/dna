"""Test dna.py"""

import os
import subprocess
import pytest

base_param = [os.path.join(os.path.dirname(__file__), "dna.py")]
base_param = ["python"] + base_param

DATA_SMALL = [
    [
        os.path.join(os.getcwd(), "databases", "small.csv"),
        os.path.join(os.getcwd(), "sequences", f"{i}.txt"),
    ]
    for i in range(1, 5)
]

DATA_LARGE = [
    [
        os.path.join(os.getcwd(), "databases", "large.csv"),
        os.path.join(os.getcwd(), "sequences", f"{i}.txt"),
    ]
    for i in range(5, 21)
]

DATA_IN = DATA_SMALL + DATA_LARGE

DATA_OUT = [
    "Bob",
    "No match",
    "No match",
    "Alice",
    "Lavender",
    "Luna",
    "Ron",
    "Ginny",
    "Draco",
    "Albus",
    "Hermione",
    "Lily",
    "No match",
    "Severus",
    "Sirius",
    "No match",
    "Harry",
    "No match",
    "Fred",
    "No match",
]


@pytest.mark.parametrize(
    "input_data, expected_output",
    zip(DATA_IN, DATA_OUT),
)
def test_dna_single(input_data, expected_output):
    """Test dna.py"""
    param = base_param + input_data
    result = subprocess.run(
        param,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout == f"{expected_output}\n"
