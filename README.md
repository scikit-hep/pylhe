#pylhe

small and thin python interface to Les Houches Event (LHE) files.

extra: visualization of hard process

    import pylhe
    for e in pylhe.readLHE('myevents.lhe'):
      print e['eventinfo']
      for particle e['particles']:
        print particle
