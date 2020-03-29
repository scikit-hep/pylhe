from setuptools import setup, find_packages

extras_require = {
    "develop": [
        "check-manifest",
        "pyflakes",
        "pre-commit",
        "black;python_version>='3.6'",  # Black is Python3 only
        "twine",
    ],
}
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
)
