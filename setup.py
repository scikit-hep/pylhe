from setuptools import setup,find_packages

extras_require = {
    'develop': [
        'pre-commit',
        'black;python_version>="3.6"',  # Black is Python3 only
        'twine',
    ],
}
extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(
  name = 'pylhe',
  version = '0.0.4',
  description = 'small package to get structured data out of Les Houches Event files',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.ch',
  packages = find_packages(),
  install_requires = [
    'networkx',
    'tex2pix',
    'pypdt'
  ],
    extras_require=extras_require,
)
