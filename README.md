#pylhe

small and thin python interface to read Les Houches Event (LHE) files.

extra: graphical visualization of event.

    import pylhe
    for e in pylhe.readLHE('myevents.lhe'):
      print e.eventinfo.weight
      for particle in e.particles:
        print 'vector: px: {}, py: {}, pz: {}, e: {}'.format(particle.px,particle.py,particle.py,particle.e)

example:
http://nbviewer.ipython.org/github/lukasheinrich/pylhe/blob/master/zpeak.ipynb
