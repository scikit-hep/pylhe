import os

class LHEFile(object):
  def __init__(self):
    pass

class LHEEventInfo(object):
  fieldnames = ['nparticles', 'pid', 'weight', 'scale', 'aqed', 'aqcd']
  
  @classmethod
  def fromstring(cls,string):
    return dict(zip(cls.fieldnames,map(float,string.split())))
    

class LHEParticle(object):
  fieldnames = ['id','status','mother1','mother2','color1','color2','px','py','pz','e','m','lifetime','spin']
  
  def __init__(self):
    pass
  @classmethod
  def fromstring(cls,string):
    return dict(zip(cls.fieldnames,map(float,string.split())))

def loads():
  pass
  
import xml.etree.ElementTree as ET
def readLHE(file):
  try:
    for event,element in ET.iterparse('./test.events',events=['end']):      
      if element.tag == 'event':
          eventdict = {}
          data = element.text.split('\n')[1:-1]
          eventdata,particles = data[0],data[1:]
          eventdict['eventinfo']=LHEEventInfo.fromstring(eventdata)
          eventdict['particles'] = []
          for p in particles:
            eventdict['particles']+=[LHEParticle.fromstring(p)]
          yield eventdict

  except ET.ParseError:
    print "WARNING. Parse Error."
    return
