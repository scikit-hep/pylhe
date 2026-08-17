See the [Scikit-HEP Developer introduction][skhep-dev-intro] for a detailed description of best practices for developing Scikit-HEP packages.

[skhep-dev-intro]: https://scikit-hep.org/developer/intro

# Installing pylhe

First create a fork of the `pylhe` repository on GitHub, then clone your fork locally and change into the `pylhe` directory:

```bash
# fork scikit-hep/vector
git clone https://github.com/<your_github_username>/pylhe.git
cd pylhe
```

# Setting up a development environment

You can set up a development environment by running:

```bash
pipx install hatch
hatch env create dev
hatch shell dev
```

# Post setup activate of pre-commit

You should prepare pre-commit, which will help you by checking that commits pass required checks:

```bash
pre-commit install # Will install a pre-commit hook into the git repo
```

You can also/alternatively run `pre-commit run` (changes only) or `pre-commit run --all-files` to check even without installing the hook.

# Testing

Use PyTest to run the unit checks:

```bash
pytest
```

# Documentation

In order to produce the documentation webpage locally, you can run the following commands:

```bash
cd docs
hatch run docs:make html
```

Now find the generated documentation in `docs/build/html/index.html`.
You can also run `hatch run docs:make clean` to remove the generated files.
