import os

class LHEFile(object):
    def __init__(self):
        pass

class LHEEvent(object):
    def __init__(self,eventinfo,particles):
        self.eventinfo = eventinfo
        self.particles = particles
        for p in self.particles:
            p.event = self

class LHEEventInfo(object):
    fieldnames = ['nparticles', 'pid', 'weight', 'scale', 'aqed', 'aqcd']
    def __init__(self, **kwargs):
        if not set(kwargs.keys()) == set(self.fieldnames):
            raise RuntimeError
        for k,v in kwargs.iteritems():
            setattr(self,k,v)
    
    @classmethod
    def fromstring(cls,string):
        return cls(**dict(zip(cls.fieldnames,map(float,string.split()))))
    

class LHEParticle(object):
    fieldnames = fieldnames = ['id','status','mother1','mother2','color1','color2','px','py','pz','e','m','lifetime','spin']
    def __init__(self, **kwargs):
        if not set(kwargs.keys()) == set(self.fieldnames):
            raise RuntimeError
        for k,v in kwargs.iteritems():
            setattr(self,k,v)
    
    @classmethod
    def fromstring(cls,string):
        obj = cls(**dict(zip(cls.fieldnames,map(float,string.split()))))
        return obj
    
    def mothers(self):
        mothers = []
        first_idx  =  int(self.mother1)-1
        second_idx =  int(self.mother2)-1
        for idx in set([first_idx,second_idx]):
            if idx >= 0: mothers.append(self.event.particles[idx])
        return mothers
    
def loads():
    pass
  
import xml.etree.ElementTree as ET
def readLHE(file):
    try:
        for event,element in ET.iterparse(file,events=['end']):      
            if element.tag == 'event':
                data = element.text.split('\n')[1:-1]
                eventdata,particles = data[0],data[1:]
                eventinfo = LHEEventInfo.fromstring(eventdata)
                particle_objs = []
                for p in particles:
                    particle_objs+=[LHEParticle.fromstring(p)]
                yield LHEEvent(eventinfo,particle_objs)
    
    except ET.ParseError:
        print "WARNING. Parse Error."
        return
    
import networkx as nx
import pypdt
import tex2pix
import subprocess
import shutil
def visualize(event,outputname):
    g = nx.DiGraph()
    for i,p in enumerate(event.particles):
        g.add_node(i,attr_dict=p.__dict__)
        name = pypdt.particle(p.id).name
        greek = ['gamma','nu','mu','tau','rho','Xi','Sigma','Lambda','omega','Omega','Alpha','psi','phi','pi','chi']
        for greekname in greek:
            if greekname in name:
                name = name.replace(greekname,'\\'+greekname)
        if 'susy-' in name:
            name = name.replace('susy-','\\tilde ')
        g.node[i].update(texlbl = "${}$".format(name))
    for i,p in enumerate(event.particles):
        for mom in p.mothers():
            g.add_edge(event.particles.index(mom),i)
    nx.write_dot(g,'event.dot')
    p = subprocess.Popen(['dot2tex','event.dot'], stdout = subprocess.PIPE)
    tex2pix.Renderer(texfile = p.stdout).mkpdf(outputname)
    subprocess.check_call(['pdfcrop',outputname,outputname])
    # shutil.move('event-cropped.pdf','event.pdf')
    os.remove('event.dot')