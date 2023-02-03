from setuptools import setup

extras_require = {}
extras_require["lint"] = sorted({"flake8", "black"})
extras_require["test"] = sorted(
    {
        "pytest~=6.0",
        "pytest-cov>=2.5.1",
        "scikit-hep-testdata>=0.4.0",
        "pydocstyle",
    }
)
extras_require["develop"] = sorted(
    set(
        extras_require["lint"]
        + extras_require["test"]
        + ["pre-commit", "check-manifest", "tbump>=6.7.0", "twine"]
    )
)
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    extras_require=extras_require,
    use_scm_version=lambda: {"local_scheme": lambda version: ""},
)
