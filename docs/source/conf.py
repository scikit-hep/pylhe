# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import re
from datetime import datetime

# we use toml to read pyproject.toml
# the python provided toml parser does not support older python versions
import toml

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
try:
    info = toml.load("../../pyproject.toml")
except FileNotFoundError:
    info = toml.load("pyproject.toml")
project = info["project"]["name"]
current_year = datetime.now().year
copyright = f"{current_year}, The Scikit-HEP admins"
# Handle multiple authors
authors_list = info.get("authors", [])
author_names = [a.get("name", "") for a in authors_list if "name" in a]
author = ", ".join(author_names)
version = re.sub("^", "", os.popen("git describe --tags").read().strip())
rst_epilog = f""".. |project| replace:: {project} \n\n"""

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.doctest",
    "sphinx_math_dollar",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
]
nb_execution_mode = "off"
templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Patterns of URLs to ignore
linkcheck_ignore = [
    # Currently, down or blocking
    r"https?://allcontributors\.org/.*",
    # Often interrupted service
    r"https?://.*\.hepforge\.org/.*",
]
