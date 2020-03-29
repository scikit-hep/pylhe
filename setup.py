from setuptools import setup, find_packages

extras_require = {
    "test": [
        "pytest",
        "pytest-cov>=2.5.1",
        "scikit-hep-testdata",
        "pydocstyle",
        "check-manifest",
        "flake8",
        "black;python_version>='3.6'",  # Black is Python3 only
    ],
}
extras_require["develop"] = sorted(
    set(extras_require["test"] + ["pre-commit", "twine"])
)
extras_require["complete"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="pylhe",
    version="0.0.5",
    description="small package to get structured data out of Les Houches Event files",
    author="Lukas Heinrich",
    author_email="lukas.heinrich@cern.ch",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=["networkx", "tex2pix", "pypdt"],
    extras_require=extras_require,
    dependency_links=[],
    use_scm_version=lambda: {"local_scheme": lambda version: ""},
)
