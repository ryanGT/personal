import os, copy, sys

import versepack

def findblanks(listin):
    inds = []
    for n, line in enumerate(listin):
        if line.strip()=='':
            inds.append(n)
    return inds

def readrawverse(mypath):
    f = open(mypath,'r')
    mylist = f.readlines()
    f.close()
    list2 = [item.strip() for item in mylist]
    return list2

def separaterawverses(listin):
    biglist = []
    myinds = findblanks(listin)
    prevind = 0
    for curind in myinds:
        curraw = listin[prevind:curind]
        biglist.append(curraw)
        prevind = curind+1
    biglist.append(listin[prevind:])
    bigout = [item for item in biglist if item]
    return bigout

def findref(versein):
    refind = -1
    for n, line in enumerate(versein):
        if line[0]=='(' and line[-1]==')':
            refind = n
            break
    verseout = copy.copy(versein)
    refstr=verseout.pop(refind)
    return refstr[1:-1], verseout

refdict={'2Ti':'2 Timothy','Joh':'John','Rom':'Romans','Mat':'Matthew','Psa':'Psalm','Gal':'Galations','1Co':'1 Corinthians','Jos':'Joshua'}

def parseref(refin):
    book,verseref = refin.split(' ',1)
    if refdict.has_key(book):
        return refdict[book]+' '+verseref
    else:
        return refin

def parseopts(linesin):
    keys=['space','size']
    optout = dict(zip(keys,[None]*len(keys)))
    keylines = []
    for line in linesin:
        for key in keys:
            if line.find(key+':')==0:
                keylines.append(line)
                break
    outlines = [line for line in linesin if line not in keylines]
    for keyline in keylines:
        key, value = keyline.split(':',1)
        optout[key]=value
    if optout['space']:
        optout['space']=float(optout['space'])
    return optout, outlines

def mapopts(optsin):
    mymap = {'space':'extraspacing','size':'fontsize'}
    optsout = {}
    for key, value in optsin.iteritems():
        if value is not None:
            optsout[mymap[key]] = value
    return optsout
    
## Verse#:1
## Prompt:Freedom
## Label:FREE-1
## Reference:Matthew 5:28
## Verse:But I say to you that everyone who looks at a woman with lustful intent has already committed adultery with her in his heart.

import pdb

if __name__=='__main__':
#    pathin = os.path.join('freedom','freedom2.txt')
#    pathin = os.path.join('freedom','freedom_test.txt')
    if len(sys.argv)>1:
        pathin = sys.argv[1]
    else:
        pathin = 'Gods_delight.txt'

    list1 = readrawverse(pathin)
    big1 = separaterawverses(list1)

    test1=big1[0]
    out = findref(test1)

    finalout = []

#    myprompt = 'Freedom'
    if len(sys.argv)>2:
        myprompt = sys.argv[2]
    else:
        myprompt = "God's Delight"
#    mylabel = 'freedom'
    if len(sys.argv)>3:
        mylabel = sys.argv[3]
    else:
        mylabel = 'Delight'
    myout = finalout.append
    #   def __init__(self, refin="", versein="", promptin="",labelin="",fontsizein="normalsize",extraspacingin=0.05, num=None):
    for n, mylist in enumerate(big1):
        mytup = findref(mylist)
        myref = mytup[0]
        mylines = mytup[1]
        #pdb.set_trace()
        outdict, lines2 = parseopts(mylines)
        extraopts = mapopts(outdict)
        myverse = ' '.join(lines2)
        myref = parseref(myref)
        verseopts = {'ref':myref,'verse':myverse,'prompt':myprompt,'label':mylabel+'-'+str(n+1),'num':str(n+1)}
        verseopts.update(extraopts)
        curverse = versepack.memoryverse(**verseopts)
        curlines = curverse.ToTextList()
        finalout.extend(curlines)
        myout('')
##         myout('Verse#:'+str(n+1))
##         myout('Prompt:'+myprompt)
##         myout('Label:'+mylabel+'-'+str(n+1))
##         myout('Reference:'+myref)
##         myout('Verse:'+myverse)
##         myout('')
    myout('')

#    pathout = os.path.join('freedom','freedom_out.txt')
    pathnoe, ext = os.path.splitext(pathin)
    pathout = pathnoe+'_out'+ext
    f = open(pathout,'w')
    finalout = [item +'\n' for item in finalout]
    f.writelines(finalout)
    f.close()
        
        
