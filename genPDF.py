import subprocess, random, sys, os
import hpsyfuncs

#note, we will need to use a temp directory so that we can get rid of all
#the latex metadata after the deed is done


#masterParams = ['plantid','commonname','allnames','nametypes','pkingdom','pphylum','pclass','porder','','','','','','','','','','','','','','','','','','','','','','']
#masterParams = ['commonname','allnames','nametypes','pkingdom','pphylum','pclass','porder']
mParams = ['plantid','commonname','allnames','nametypes','pkingdom','pphylum','pclass','porder','pfamily','pgenus','pspecies','strains','descstrains','descsize','descstalk','descleaves','descflowers','descfruit','descroots','descprop','descgen','flowerseason','descseasons','origin','habitat','medtrads','medcats','medparts','prepnotes','compounds','refs','imglinks','imgcaplinks']


def reverseMe(astring):
    sout=''
    for eind in range(len(astring)):
        rind = -1-eind
        thischar = astring[rind]
        sout += thischar
    return sout

def dispPDF(pdfFile):
    subprocess.Popen(["evince", pdfFile])

def compileTex(texFile):
    texDir = texFile.split('/')
    texDir = texDir[:-1]
    slash = '/'
    texDir = slash.join(texDir)
    oldDir = os.getcwd()
    os.chdir(texDir)
    try:
        subprocess.call(["pdflatex" , texFile])
        os.chdir(oldDir)
        #pdflatex doesnt allow output filename specification, 
        #so we must calculate it
#        texroot = reverseMe(texFile)
#        texroot = texroot.split('.',1)
#        texroot = texroot[0]
#        texroot = reverseMe(texroot)
        texroot = texFile[:-3]
        outPDF = texroot + 'pdf'
        return outPDF
    except:
        return -1

    
def artString(inDict):
    
    #First apply Latex paragraph formatting to any string that will accept it. Since pdf is output only, we don't have
    #to worry about disastrous feedback loops
#    for inVal in inDict.values():
#        try:
#            inVal.replace('\n\n', '\\\\\n\n')
#        except:
#            pass
    
    topImgs = []
    sideImgs = []
    slash = '/'
    try:
        for ino, eimg in enumerate(inDict["imglinks"]):
            imgSuffix = eimg.split(slash)
            imgSuffix = imgSuffix[-1]
            
            if inDict["imgcaplinks"][ino] != "NoCaption":
                sideImgs.append([imgSuffix, inDict["imgcaplinks"][ino] ])
            else:
                topImgs.append(imgSuffix)
    except:
        pass
    print 'topImgs: '
    print topImgs
    astring = r'\chapter*{'
    astring += inDict['commonname']
    astring +='}\n'

    if len(topImgs) > 0:
        astring += r"""\begin{picture}(12,0)(0,-3)
\put(0,0){\includegraphics[height=0.1\textheight]{"""
        astring += topImgs[0]
        astring += '} '
        if len(topImgs) > 1:
            for ti in topImgs[1:]:
                astring += r'\hfill \includegraphics[height=0.1\textheight]{'
                astring += ti
                astring += '}' 
        astring += '}\n'
        astring += r'\end{picture}'
        astring += '\n'
    astring += '\n'
    astring += r'\vspace*{-1cm}'
    astring += '\n'
     
    #Now we have to parse the entries into subsections and tables. joy!
    #alternative names
    latname = ''
    for eno, ealt in enumerate(inDict['allnames']):
        ekval =ealt.split(':')
        etype = ekval[0].strip()
        if etype == 'Latin':    
            latname = ekval[1].strip()
            
        elif etype != "Common":
            astring += r'\subsection*{'
            if len(ekval)>1:
                astring += ekval[1].strip()
            else:
                print "bad allnames inDict:"
                print inDict
                astring = ekval[0].strip()
                print astring                
            astring += '('
            astring += etype
            astring += ')}\n'
    #Latin name
    if len(latname) > 0:
        #latname = latname[0].upper() + latname[1:].lower()
        #When we add the float figure, LATEX absolutely loses its mind
        #in regard to spacing between the latin name, so we have to 
        #override its immensely oversolved and horrifically irritating insistences.
        
        astring += r'{\LARGE\emph{'
        astring += inDict['pgenus']
        astring += r'\hspace*{0.2cm}'
        astring += inDict['pspecies'].lower()
        astring += '}}\n'
        
    astring += r'\vspace*{12pt}'
    astring += '\n'
    
    #Before we enter the main text, we'll go ahead and place our float figures,
    #so that there is as much use of the left-justified phylogeny specs as possible    
    if len(sideImgs) > 0:
        astring += r'\begin{wrapfigure}{r}{0.2\textwidth}'
        astring += '\n'
        for sideImg in sideImgs:

            astring += r'\includegraphics[width=0.2\textwidth]{'
            astring += sideImg[0]
            astring += '}\n'
            astring += r'\begin{flushleft}'
            astring += '\n'
            astring += r'{\scriptsize ' 
            astring += sideImg[1]
            astring += '}\n'
            astring += r'\end{flushleft}'
            astring += '\n'
            astring += r'\vfill'
            astring += '\n'
        astring += r'\end{wrapfigure}'
        astring += '\n\n'

    #Phylogeny
    astring += r'\begin{description}'
    astring += '\n'
    for pcat in ['pkingdom', 'pphylum', 'pclass', 'porder', 'pfamily', 'pgenus', 'pspecies']:
        try:
            ebool = len(inDict[pcat])
            if ebool:
                plabel = pcat[1].upper() + pcat[2:]
                astring += r'\item['
                astring += plabel
                astring += r'] \emph{'
                astring += inDict[pcat]
                astring += '}\n'
                
        except:
            pass
    astring += r'\end{description}'
    astring += '\n'    
    #If strains, display as subsequent {description} list , undetectable from \item in primary list
    try:
        strainlist = inDict['strains']
        sbool = len(strainlist)
        if sbool:
            astring += r'\begin{description}'
            astring += '\n'
            astring += r'\item[Subspecies:]'
            for sno, subsp in enumerate(inDict['strains']):
                astring += r'\emph{'
                astring += subsp                
                if sno < (sbool-1):
                    astring += '}, '
                else:
                    astring += '}\n'
                    
            astring += r'\end{description}'
            astring += '\n'            
    except:
        pass
    
    astring += r'\section*{Descriptions}'
    astring += '\n'
    
    
    
    #general description precedes strain descriptions, and is mandatory
    astring += r'\subsection*{General}'
    astring +='\n'    
    astring += inDict['descgen']
    astring += '\n'
    
    
    for gcat in [['origin','Geographic Origin'],['habitat','Habitat']]:    
        try:
            thisdata = inDict[gcat[0]]
            if len(thisdata) > 0:
                astring += r'\subsubsection*{'
                astring += gcat[1]
                astring += '}\n'
                astring += thisdata
                astring += '\n'
        except:
            pass    
    
    
    #now check for strain descriptions
    try:
        sdlist = inDict['descstrains']
        sbool = len(max(sdlist))
        if sbool:
            astring += r'\subsection*{Strains}'
            astring +='\n'              
            for dno, sdesc in enumerate(sdlist):
                #for each valid strain description, look up header, and define a subsubsection
                if len(sdesc) > 0:
                    #need to split val from key, formatted this way in db for extra link security
                    sdesc = sdesc.split(':',1)
                    skey = sdesc[0].strip()
                    sval = sdesc[1].strip()
                    astring += r'\subsubsection*{'
                    #astring += inDict['strains'][dno]
                    astring += skey
                    astring += '}\n'
                    astring += sval
                    astring += '\n'
            astring += '\n'

    except:
        pass
   
    #Next up, handling the two numranges (descsize and flowerseason)
    astring += r'\subsection*{Anatomy and Biology}'
    astring += '\n'
    astring += r'\begin{description}'
    astring += '\n'        
        
    try:
        #descsize first, since simpler
        sizelist = inDict['descsize']
        minsize = str(sizelist[0])
        maxsize = str(sizelist[1])

        astring += r'\item[Typical Size:] '
        astring += minsize
        if maxsize != minsize:
            astring += ' --- '
            astring += maxsize
        astring += ' m\n'

        #after size description written, parse and write season info
        seasonlist = inDict['flowerseason']
        minseason = str(seasonlist[0])
        maxseason = str(seasonlist[1])     

        snameList = ['January','February','March','April','May','June','July','August','September','October','November','December']
        smodList = ['early', '', 'late']

        minparams = minseason.split('.', 1)
        minmod = int(minparams[1]) // 4
        minsname = smodList[minmod] + ' '
        minsname += snameList[int(minparams[0])]
        
        maxparams = maxseason.split('.', 1)
        maxmod = int(maxparams[1]) // 4
        maxsname = smodList[maxmod] + ' '
        maxsname += snameList[int(maxparams[0])]

               
        astring += r'\item[Flowering Season:] '
        astring += minsname
        if maxsname != minsname:
            astring += ' --- '
            astring += maxsname
        astring += '\n'
            
    except:
        pass
    
    astring += r'\end{description}'
    astring += '\n'      
    

    
    #and then we break into the major description \subsection{} loop
    #Q: would each species monograph be better cast as a chapter?
    for dcat in [['descroots','Roots'],['descstalk','Stalk'],['descleaves','Leaves'],['descflowers','Flowers'],['descfruit','Fruit'],['descprop','Propagation'],['descseasons','Seasonal Behaviour']]: #Medical info to be formatted subsequently
        try:
            thisdata = inDict[dcat[0]]
            #print dcat[1]
            #print thisdata
            if len(thisdata) > 0:
                astring += r'\subsubsection*{'
                astring += dcat[1]
                astring += '}\n'
                astring += thisdata
                astring += '\n'
        except:
            pass

    astring += r'\section*{Medical Properties}'
    astring += '\n\n'
    for mcat in [['medtrads','Traditional Uses']]:
        try:
            thisdata = inDict[mcat[0]]
            if len(thisdata) > 0:
                astring += r'\subsection*{'
                astring += mcat[1]
                astring += '}\n'
                astring += thisdata
                astring += '\n'
        except:
            pass
    #Treat the one-liners as a description-style list
    astring += r'\subsection*{}'
    astring += '\n'
    astring += r'\begin{description}'
    astring += '\n'     
    for ecat in [['medcats','Medical Categories'],['medparts','Parts Used'],['compounds','Notable Compounds']]:
        try:
            edat = inDict[ecat[0]]
            if len(edat) > 0:
                astring += r'\item['
                astring += ecat[1]
                astring += ':]'
                astring += edat    
                astring += '\n'                            
        except:
            pass
                   
    astring += r'\end{description}'
    astring += '\n'        
    for mcat in [['prepnotes','Preparation Notes']]:
        try:
            thisdata = inDict[mcat[0]]
            if len(thisdata) > 0:
                astring += r'\subsection*{'
                astring += mcat[1]
                astring += '}\n'
                astring += thisdata
                astring += '\n'
        except:
            pass
        
        
#can enforce nice reference formatting later    
    refdat = inDict['refs']
    try:
        refdat = refdat.split('||')
        astring += r'\subsection*{References}'
        astring += '\n'
        astring += r'\begin{enumerate}'
        astring += '\n'

        for eref in refdat:
            astring += r'\item '
            astring += eref
            astring += '\n'
            
        astring += r'\end{enumerate}'
        astring += '\n'
    except:
        pass
    astring += '\n\n'
    
    return astring

def createTex(dataDicts, fout, template='defaultTemplate'):
    print ('createTex initiated')

    if template == 'defaultTemplate':
        
        #determine graphicspath statement for the preamble
        imgdirs = []
        slash='/'
        for edict in dataDicts:
            if "imglinks" in edict.keys():
                if edict["imglinks"] is not None:
                    for eimg in edict["imglinks"]:
                        esplit = eimg.split(slash)
                        edir = slash.join(esplit[:-1]) + slash
                        if edir not in imgdirs:
                            imgdirs.append(edir)        
                
        theader = r"""\documentclass{report}
\usepackage[top=1.0cm, bottom=1.5cm, left=1.0cm, right=1.0cm]{geometry}
\usepackage{wrapfig}
\usepackage{graphicx}
\graphicspath{"""
        for edir in imgdirs:
            theader += '{'
            theader += edir
            theader += '}'
        theader += '}\n'
        theader += r"""\usepackage[compact]{titlesec}
\titleformat*{\section}{\Huge\bfseries}
\titleformat*{\section}{\huge\bfseries}
\titleformat*{\subsection}{\Large\bfseries}
\setlength{\parindent}{0.0cm}
\setlength{\unitlength}{1.0cm}
\begin{document}
"""

        tfooter = r"""\end{document}        
"""
        template = [theader, tfooter]      
    
    
    
    ttList = []
    ttList.append(template[0])
    for edict in dataDicts:
        outString = artString(edict)
        ttList.append(outString)
    ttList.append(template[-1])
    f=open(fout, 'w')
    for tstring in ttList:
        f.write(tstring)
    f.close()
    return fout

def scrapeDataFromID(thisid, conn, cur):

    #unfortunately, we have to declare params explicitly to associate return values with their column
    dataDict = {}
#    queryString = """SELECT """
    nParams = len(mParams)

    queryString = """SELECT """
    queryString += mParams[0]
    for mi in mParams[1:]:
        queryString += """, """
        queryString += mi
        

    queryString += """ FROM planttable WHERE plantid = %s  ;"""
    qval = (thisid,)
    cur.execute(queryString, qval)
    paramVals = cur.fetchone()
    nvals = len(paramVals)
    #print 'paramVals=:'
    #print paramVals
    for i in range(min(nParams, nvals)):
        
        dataDict[mParams[i]] = paramVals[i]

    print 'dataDict=:'
    print dataDict
    
    return dataDict

def genPDFFromIDList(idlist,db='herbdb1', uname='biouser', pw='biouser', template=None, fileName = 'rand'):

    if fileName == 'rand':
        
        fstring = 'queryResult_'
        for i in range(10):
            rchar = random.randint(65,90)
            rchar = chr(rchar)
            fstring += rchar
        fstring += '.tex'
        
    else:
        fstring = fileName
        
    if '/' not in fstring:
        execDir=os.path.realpath(sys.argv[0])
        execDir=execDir.rsplit('/', 1)
        execDir=execDir[0]
        
        pdfDir = execDir + '/pdfs'   
        tempDir = pdfDir + '/temp'
        ls_execDir= os.listdir(execDir)
        if "pdfs" not in ls_execDir:
            os.mkdir(pdfDir)
        ls_pdfDir = os.listdir(pdfDir)
        if 'temp' not in ls_pdfDir:
            os.mkdir(tempDir)
        fpath = tempDir + '/' + fstring
    else:
        fpath = fstring
    
    

    dbConn = hpsyfuncs.ppgConn(db, uname, passwd=pw)
    dbCursor = dbConn.cursor()
    scrapeDicts=[]
    for eid in idlist:
        scrapeDict = scrapeDataFromID(eid, dbConn, dbCursor)
        scrapeDicts.append(scrapeDict)
    dbConn.close()

  
    #commented for modular debugging
    newtex = createTex(scrapeDicts, fpath)
    newpdf = compileTex(newtex)
    if newpdf != -1:
        dispPDF(newpdf)
        
        
        
        
    