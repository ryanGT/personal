#Verse#:1
#Prompt:Do Not Be Anxious
#Label:ANX-1
#Reference:Matthew 6:24-25 
#Verse:``No one can serve two masters, for either he will hate the one and love the other, or he will be devoted to the one and despise the other.  You cannot serve God and money. ``Therefore I tell you, do not be anxious about your life, what you will eat or what you will drink, nor about your body, what you will put on.  Is not life more than food, and the body more than clothing?
#FontSize:footnotesize
#ExtraSpacing:-0.02

import pdb, re

refpat =  re.compile('\\((.*)\\)')

validkeys = ['Verse#','Prompt','Label','Reference','Verse','FontSize','ExtraSpacing']
rawvalidkeys = ['Verse#','Prompt','Label','Reference','Verse','size','space']
kwnames = ['num', 'prompt', 'label', 'ref', 'verse', 'fontsize', 'extraspacing']


def checktype(listin):
   """Take a list that represents one verse (i.e. not a nested list of
   lists), and check whether it is a raw verse list or one formatted
   to have key:value syntax.  If the first raw doesn't start with a
   valid key:value, it is assumed to be a raw verse."""
   firstelem = listin[0]
   for item in validkeys:
      if firstelem.find(item+':') == 0:
         return 'formatted'
   #if we made it all the way through without finding an item+':',
   #this must be a raw verse
   return 'raw'
          

class memoryverse:
   def __init__(self, ref="", verse="", prompt="",label="",fontsize="normalsize",extraspacing=0.05, num=None):
       self.ref=ref
       self.verse=verse
       self.prompt=prompt
       self.label=label
       self.fontsize=fontsize
       self.extraspacing=extraspacing
       self.num = num

   def ToTextList(self):
      outlist = []
      mylist = ['num','prompt','label','ref','verse','fontsize','extraspacing']
      txtlabels=['Verse#','Prompt','Label','Reference','Verse','FontSize','ExtraSpacing']
      for itemstr, label in zip(mylist,txtlabels):
         if hasattr(self, itemstr):
            outlist.append(label+':'+str(getattr(self,itemstr)))
      return outlist

   def __repr__(self):
       mylist = ['prompt','label','ref','verse','fontsize','extraspacing','num']

       mystring = ""
       for key in mylist:
           mystring+='%s:%s'%(key,getattr(self,key))+'\n'
       return mystring

   def ToLatex(self, colorstr=''):
       listout = []
       out = listout.append
       if self.fontsize.lower() != 'normalsize':
           print('self.fontsize='+self.fontsize)
           out('{\\'+self.fontsize)
       out('\\parbox[t][1.75in]{2.5in}{')
       out('\\raggedright{')
       out('\\begin{tabular*}{2.6in}{@{}l@{\\extracolsep{\\fill}}r}')
       out(colorstr+self.ref +' & '+colorstr+self.label)
       out('\\end{tabular*}')
       out('\\\\')
       out('\\vspace{'+str(self.extraspacing)+'in}')
       out(self.verse)
       out('}%end ragged right')
       out('\\\\')
       out('\\vspace{'+str(self.extraspacing)+'in}')
       out('\\raggedleft{')
       out(colorstr+self.ref)
       out('}%end ragged left')
       out('}%end parbox')
       if self.fontsize.lower() != 'normalsize':
           out('}%end footnotesize')
       return listout



from pytexutils import readfile


def breaklistoflists(listin):
   """Take a long list of raw verses and break it at each empty line
   into a nested list of lists."""
   listout = []
   prevind = -1
   n = 0
   N = len(listin)
   keepgoing = True
   while keepgoing and (n < N):
      try:
         nextblank = listin.index('', prevind+1)
         nextlist = listin[prevind+1:nextblank]
         prevind = nextblank
      except ValueError:
         nextlist = listin[prevind+1:]
         keepgoing = False
      if nextlist:
         listout.append(nextlist)
      n += 1
   listout = [item for item in listout if item]
   return listout


def _readfile(pathin):
   """Read in a file containing raw or formatted verses and break the
   file at blank lines.  Return a list of lists."""
   inlist = readfile(pathin)
   while inlist[-1]=='':#eliminate extra empty lines at end
       inlist.pop()

   inlist.append('')#make sure list ends in one empty line
   listoflists = breaklistoflists(inlist)
   return listoflists



def ReadRWKVerseFile(pathin):
   """This function reads a text file assumed to be a list of verses
   in the following form:

   Verse#:1
   Prompt:
   Label:FVA-1
   Reference:Deut. 7:9 
   Verse:Know therefore that the Lord your God is God, the faithful God who keeps covenant and steadfast love with those who love him and keep his commandments, to a thousand generations,
   FontSize:normalsize
   ExtraSpacing:0.05

   The verse list is parsed and a list of memoryverses is returned.
   The verses must be sepearted by a blank line in the text file.
   FontSize and ExtraSpacing are optional.  The colon on each line is
   essential.  Each item must be only one line in the text file.  Note
   that Verse# and Verse are two different things.
   """

##    f=open(pathin,'r')
##    flist=f.readlines()
##    f.close()
##    cleanlist = [item.strip() for item in flist]
##    breaklist = [n for n, line in enumerate(cleanlist) if line == '']

##    prevind = -1
##    listoflists = []
   
##    #validkeys=['Verse#','Prompt','Label','Reference','Verse','FontSize','ExtraSpacing']
##    #kwnames=['num', 'prompt', 'label', 'ref', 'verse', 'fontsize', 'extraspacing']

##    for ind in breaklist:
##        curlist = cleanlist[prevind+1:ind]
##        listoflists.append(curlist)
##        prevind = ind

##    listoflists = [item for item in listoflists if item]

   listoflists = _readfile(pathin)
   if checktype(listoflists[0]) == 'raw':#if the path really points to
                                         #a raw verse file, parse it
                                         #as such
      return parserawlistoflists(listoflists)
   listofdicts = []
   for curlist in listoflists:
       curdict = {}
       for curline in curlist:
           key, rest = curline.split(':',1)
           key = key.strip()
           rest = rest.strip()
           curdict[key] = rest
       outdict = {}
       for key, name in zip(validkeys,kwnames):
           if curdict.has_key(key):
               outdict[name]=curdict[key]
       listofdicts.append(outdict)

   verselist = [memoryverse(**curdict) for curdict in listofdicts]
   return verselist


def WriteRWKVerseFile(verselist,pathin):
   """This file takes a list of verses and writes them to a text file of the form:

   Verse#:1
   Prompt:
   Label:FVA-1
   Reference:Deut. 7:9 
   Verse:Know therefore that the Lord your God is God, the faithful God who keeps covenant and steadfast love with those who love him and keep his commandments, to a thousand generations,
   FontSize:normalsize
   ExtraSpacing:0.05
   """
   biglist=[]
   for verse in verselist:
      curlist=verse.ToTextList()
      biglist.extend(curlist)
      biglist.append('')
   bigout = []
   for line in biglist:
      if (line == '') or (line[-1] != '\n'):
         line += '\n'
      bigout.append(line)
   f = open(pathin, 'w')
   f.writelines(bigout)
   f.close()


def parserawlistoflists(listoflists):
   """Take a lists of lists and convert it to a list of memoryverse
   instances.  The first item in each list is the verse text and the
   last item is the reference.  The verse number is generated by
   enumerate."""
   listofdicts = []
   for n, curlist in enumerate(listoflists):
       curdict = {}
       curdict['Verse'] = curlist.pop(0)
       rawref = curlist.pop()
       q = refpat.search(rawref)
       if q:
          curdict['Reference'] = q.group(1)
       else:
          curdict['Reference'] = rawref
       curdict['Verse#'] = n+1
       for curline in curlist:
           key, rest = curline.split(':',1)
           key = key.strip()
           rest = rest.strip()
           curdict[key] = rest
       outdict = {}
       for key, name in zip(rawvalidkeys, kwnames):
           if curdict.has_key(key):
               outdict[name]=curdict[key]
       listofdicts.append(outdict)

   verselist = [memoryverse(**curdict) for curdict in listofdicts]

   return verselist



def readrawfile(pathin):
   """Read in a raw text file: one that contains a list of verses in
   the following format:

   verse text (persumably pasted from esv website)
   optional list of parameters like:
   space:-0.05
   size:small
   (reference)

   for example:

   For God so loved the world that He gave His only begotten Son.
   space:0.0
   size:small
   (John 3:16)

   The first element in the raw verse list must be the verse text.
   The last element must be the reference.

   Returns a list of memoryverse instances."""
##    inlist = readfile(pathin)
##    while inlist[-1]=='':#eliminate extra empty lines at end
##        inlist.pop()

##    inlist.append('')#make sure list ends in one empty line
##    listoflists = breaklistoflists(inlist)

   listoflists = _readfile(pathin)
   return parserawlistoflists(listoflists)
