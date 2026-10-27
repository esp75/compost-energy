"""Checks that the CAD model matches the sizing model it is built from.

    .venv/bin/python -m pytest hardware/cad
"""

import pytest

cq = pytest.importorskip("cadquery")

import farm_unit as fu  # noqa: E402


@pytest.fixture(scope="module")
def parts():
    _, parts = fu.build()
    return {p["part"]: p for p in parts}


def test_tunnels_have_the_model_volume(parts):
    # inner volume equals the model's gross volume; the length is rounded up to the next 0.5 m
    inner = fu.N * fu.W * fu.H * fu.L
    assert fu.M["gross_total_m3"] <= inner < fu.M["gross_total_m3"] * 1.02


def test_beds_hold_about_the_model_inventory(parts):
    beds = sum(p["volume_m3"] for name, p in parts.items() if name.endswith("-bed"))
    assert beds == pytest.approx(fu.M["solids_per_tunnel_m3"] * fu.N, rel=0.05)


def test_skid_matches_layout(parts):
    hx = parts["HX-201-casing"]
    x0, x1, y0, y1, z0, z1 = fu.LAY.hx
    assert (hx["x_mm"], hx["y_mm"], hx["z_mm"]) == (round((x1 - x0) * 1000), round((y1 - y0) * 1000), round((z1 - z0) * 1000))


def test_every_part_is_a_valid_solid():
    assy, _ = fu.build()
    for child in assy.children:
        assert child.obj.val().isValid(), child.name


def test_buffer_tank_holds_the_study_volume(parts):
    import math
    tk = parts["TK-201-buffer"]
    assert tk["volume_m3"] == pytest.approx(fu.M["buffer_m3"], rel=0.03)
    assert fu.N == 4
