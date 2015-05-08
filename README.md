#pylhe

small and thin python interface to read Les Houches Event (LHE) files.

extra: graphical visualization of event.

    import pylhe
    for e in pylhe.readLHE('myevents.lhe'):
      print e['eventinfo']
      for particle e['particles']:
        print particle

example:
http://nbviewer.ipython.org/github/lukasheinrich/pylhe/blob/master/zpeak.ipynb
