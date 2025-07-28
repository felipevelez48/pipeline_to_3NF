""" En este archivo hacemos las pruebas unitarias que definimos en el transform_to_3nf.py"""
import pytest
from scripts.transform_to_3nf import fix_encoding, clean_location, clean_schedule

@pytest.mark.parametrize(
    "dirty,clean",
    [
        ("via BeBee MÃ©xico", "via BeBee México"),
        ("Watertown, CT (+3 others)", "Watertown, CT"),
        ("Anywhere", "Remote"),
    ],
)
def test_fix_and_location(dirty, clean):
    assert clean_location(dirty) == clean

@pytest.mark.parametrize(
    "raw,expected",
    [("Full-time", "Full-Time"), ("PART time", "Part-Time"), ("Contrato", "Other")],
)
def test_clean_schedule(raw, expected):
    assert clean_schedule(raw) == expected

