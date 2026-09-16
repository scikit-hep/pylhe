import h5py
import pytest

import pylhe


def test_lheh5_read_generators_warns_for_non_object_extra_attributes_json(tmp_path):
    path = tmp_path / "non-object-generator-extra-attributes.hdf5"

    with h5py.File(path, "w") as h5:
        generators = h5.create_dataset(
            "generators",
            shape=(1, 4),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
        generators.attrs["properties"] = [
            b"name",
            b"version",
            b"description",
            b"extraAttributes",
        ]
        generators[...] = [["Sherpa", "3.0.0", "description", '["not-an-object"]']]

    with (
        h5py.File(path, "r") as h5,
        pytest.warns(
            UserWarning,
            match=r"Expected JSON object for attribute, got list",
        ),
    ):
        generators = pylhe.lheh5.read_generators(h5)

    assert generators[0].extra_attributes == {}
