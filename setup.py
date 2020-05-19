from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent.resolve()
with open(Path(this_directory).joinpath("README.md"), encoding="utf-8") as readme_md:
    long_description = readme_md.read()

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
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scikit-hep/pylhe",
    project_urls={
        "Source": "https://github.com/scikit-hep/pylhe",
        "Tracker": "https://github.com/scikit-hep/pylhe/issues",
    },
    author="Lukas Heinrich",
    author_email="lukas.heinrich@cern.ch",
    license="Apache",
    keywords="physics lhe",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=["networkx", "tex2pix", "pypdt"],
    extras_require=extras_require,
    dependency_links=[],
    use_scm_version=lambda: {"local_scheme": lambda version: ""},
)
