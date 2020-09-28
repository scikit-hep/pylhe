from setuptools import setup

extras_require = {
    "test": ["pytest", "pytest-cov>=2.5.1", "scikit-hep-testdata>=0.3.1", "pydocstyle"],
}
extras_require["lint"] = sorted(set(["flake8", "black;python_version>='3.6'"]))
extras_require["develop"] = sorted(
    set(
        extras_require["test"]
        + ["pre-commit", "check-manifest", "bump2version~=1.0", "twine"]
    )
)
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    extras_require=extras_require,
    use_scm_version=lambda: {"local_scheme": lambda version: ""},
)
