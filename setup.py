from setuptools import setup,find_packages

setup(
  name = 'pylhe',
  version = '0.0.2',
  description = 'small package to get structured data out of Les Houches Event files',
  author = 'Lukas Heinrich',
  author_email = 'lukas.heinrich@cern.com',
  packages = find_packages(),
  install_requires = [
    'networkx',
    'tex2pix',
    'pypdt'
  ]
)