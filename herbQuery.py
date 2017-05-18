# -*- coding: utf-8 -*-
"""

@author: legitz7
"""

from PyQt4 import QtGui, QtCore
import sys, os, time
import pickle, copy
import hpsyfuncs, genPDF
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras as pex

"""
QHolder is the primary search widget, providing an interface to the database.
It is a tabbed widget, and the API for individual searches are maintained as 
instances of the WQInterface class, defined next.


"""
class QHolder(QtGui.QWidget):
    def __init__(self, callsesh=None, db=None, userName='biouser', password='biouser', opMode="search"):
        super(QHolder, self).__init__()

        self.callsesh = callsesh
        self.db = db
        self.userName = userName
        self.password = password                   
        self.opMode = opMode        
        
        self.firstWQI=WQInterface(owner=self) 
        self.WQIList=[]        
        self.holderWidget=QtGui.QTabWidget()
        self.addWQI(specified=self.firstWQI)   
        
        self.hasWordExpand = False
        #self.wordExpandWidget
        self.wordExpandDictList = []
                
        
        #self.expButton=QtGui.QPushButton("Expand Checked Sequences")
        #self.allButton=QtGui.QPushButton("Select All")
        #self.noneButton=QtGui.QPushButton("Select None")
        
        #self.expButton.clicked.connect(self.expandAction)
#        self.allButton.clicked.connect(self.selAllAction)
#        self.noneButton.clicked.connect(self.selNoneAction)        
#        
        
        #botButtonList=[self.expButton]
        #lowerlayout=QtGui.QHBoxLayout()
        #for button in botButtonList:
        #    lowerlayout.addWidget(button)
            
        masterLayout=QtGui.QVBoxLayout()
        masterLayout.addWidget(self.holderWidget)
        #masterLayout.addLayout(lowerlayout)
        self.setLayout(masterLayout)
        self.setGeometry(100,100,600,400)

    #specified param allows default widget creation, while allowing user option of
    #passing custom widget
    def addWQI(self, specified=False):
        if not specified:
            thisWQI=WQInterface(owner=self)
        else:
            thisWQI=specified
            
        tabString='Query_' + str(len(self.WQIList)//2)
        self.holderWidget.addTab(thisWQI, tabString)
        self.WQIList.append(thisWQI)
        self.holderWidget.setCurrentIndex(len(self.WQIList)-1)
        
        #This is the method that converts an idlist returned from the complex query into
        #a display-tab
        
        #Note that the queryResultsTab is an entirely distinct Widget from WQInterface,
        
    def addResultsTab(self, idlist):
        querynum=len(self.WQIList) // 2 
        thisRT=queryResultsTab(idlist, querynum, owner=self)
        rtString='Results_'+str(querynum)        
        self.holderWidget.addTab(thisRT, rtString)
        self.WQIList.append(thisRT)
        self.addWQI()
        self.holderWidget.setCurrentIndex(len(self.WQIList)-2)
        
    def expandAction(self):
        1          


"""
This widget provides the central API to the database.
It has three main methods: addConditionLine() and removeConditionLine() are used 
to construct arbitrary Boolean query conditions, 
and runQuery() executes the user-generated query.

Additionally, showRegexSyntax() provides a reminder table for the regexes supported in queries
(POSIX standard???)

The construction methods operate upon instances of the queryConditionRow widget, defined subsequently.

"""        
class WQInterface(QtGui.QWidget):
    def __init__(self, owner=None):
        super(WQInterface, self).__init__()
        self.mode='virgin' # =>executed
        self.owner=owner

        self.runButton=QtGui.QPushButton('Run Query')
        self.runButton.setFixedWidth(100)
        self.runButton.clicked.connect(self.runQuery) 

        self.maxLabel=QtGui.QLabel('Max Returns')
        self.maxLabel.setFixedWidth(100)
        self.maxEntry=QtGui.QLineEdit('100')
        self.maxEntry.setFixedWidth(100)

        self.regexButton = QtGui.QPushButton('Regex Syntax')
        self.regexButton.clicked.connect(self.showRegexSyntax)
        self.regexButton.setFixedWidth(100)
        self.queryLabel=QtGui.QLabel('')
        
        
        self.conditionWidgets=[]
        self.conditionLayout=QtGui.QVBoxLayout()
        for c in self.conditionWidgets:
            self.conditionLayout.addWidget(c)


        dashlabel1=QtGui.QLabel('----------------------------')
        dashlabel2=QtGui.QLabel('----------------------------')
        dashlabel3=QtGui.QLabel('----------------------------')
        dashlabel4=QtGui.QLabel('----------------------------')
        dashlayout=QtGui.QHBoxLayout()
        dashlayout.addWidget(dashlabel1)
        dashlayout.addWidget(dashlabel2)
        dashlayout.addWidget(dashlabel3)
        dashlayout.addWidget(dashlabel4)

        self.entryWidget=queryConditionRow(owner=self)        
        
        self.rawModeBox=QtGui.QCheckBox('Use Raw SQL Query')
        self.rawModeBox.setChecked(False)
        self.rawTextEdit=QtGui.QTextEdit()
        self.rawModeBox.setFixedHeight(40)
        self.rawTextEdit.setFixedHeight(80)
        rawLayout=QtGui.QHBoxLayout()
        rawLayout.addWidget(self.rawModeBox)
        rawLayout.addWidget(self.rawTextEdit)
        
        
        self.masterLayout=QtGui.QVBoxLayout()
        self.masterLayout.addWidget(self.runButton)
#        self.masterLayout.addWidget(self.istatusbox)
        self.masterLayout.addWidget(self.maxLabel)
        self.masterLayout.addWidget(self.maxEntry)
        self.masterLayout.addWidget(self.regexButton)
        self.masterLayout.addWidget(self.queryLabel)
        self.masterLayout.addLayout(self.conditionLayout)
        self.masterLayout.addLayout(dashlayout)  
        self.masterLayout.addWidget(self.entryWidget)
        self.masterLayout.addLayout(rawLayout)
        
        
        self.setLayout(self.masterLayout)
        self.setGeometry(100,100,400,500)
        
    def addConditionLine(self, callingRow):
        #first, initialize an 'added' rowMode queryConditionRow
        newpos=len(self.conditionWidgets)
        newCondition=queryConditionRow(owner=self, rowMode='added', layoutPos=newpos)
        #grab data
        lparenthVal=str(callingRow.lParenthEntry.text()).strip()
        propNum=callingRow.propCombo.currentIndex()
        invNum=callingRow.invCombo.currentIndex()
        equalNum=callingRow.equalCombo.currentIndex()
        condVal=str(callingRow.condEntry.text()).strip()
        rparenthVal=str(callingRow.rParenthEntry.text()).strip()
        #set data
        newCondition.lParenthEntry.setText(lparenthVal)
        newCondition.propCombo.setCurrentIndex(propNum)
        newCondition.invCombo.setCurrentIndex(invNum)
        newCondition.equalCombo.setCurrentIndex(equalNum)
        newCondition.condEntry.setText(condVal)
        newCondition.condPosCombo.setCurrentIndex(callingRow.condPosCombo.currentIndex())
        newCondition.condLangCombo.setCurrentIndex(callingRow.condLangCombo.currentIndex())
        newCondition.rParenthEntry.setText(rparenthVal)
        newCondition.condStack.setCurrentIndex(callingRow.condStack.currentIndex())
        if callingRow.addConj:
            conjNum=callingRow.conjCombo.currentIndex()
            newCondition.conjCombo.setCurrentIndex(conjNum)
        self.conditionWidgets.append(newCondition)
        self.conditionLayout.addWidget(newCondition)
        

        
    def removeConditionLine(self, callingRow):
        #removeRowPos=callingRow.layoutPos
        #self.conditionLayout.removeWidget(callingRow)
        callingRow.hide()
        self.conditionWidgets.remove(callingRow)
        for pos, widget in enumerate(self.conditionWidgets):
            widget.layoutPos=pos
        self.update()
        
        
    def runQuery(self):
        #blablabla actually run the query...
        try:
            dbConn=hpsyfuncs.ppgConn(self.owner.db, self.owner.userName, passwd=self.owner.password)
            dbCursor=dbConn.cursor()
        except:
            print 'Query failed to connect to database. Apologies'
            return -1
            
    #First thing is, this command is Totally different if we are are in verbatim command mode
        if self.rawModeBox.isChecked():
            queryString=str(self.rawTextEdit.toPlainText()).strip()
            dbCursor.execute(queryString)
            qidlist=[]
            for etuple in dbCursor.fetchall():
                if etuple[0] is not None:
                    qidlist.append(etuple[0])
        else:
            #If we opt to use the GUI (ie queryConditionRows),
            #first lets check the parenthetical nesting, and assign a depth to each statement
            condLength=len(self.conditionWidgets)
            legalParens=True
            pdepth=0
            depthList=[]
            retIDList=[] #thisis where we store IDs associated w each query
            for condPos, cond in enumerate(self.conditionWidgets):
                retIDList.append([])
                lParens=str(cond.lParenthEntry.text()).count('(')
                pdepth += lParens
                depthList.append(pdepth)
                rParens=str(cond.rParenthEntry.text()).count(')')
                pdepth -= rParens
                if pdepth < 0:
                    legalParens=False
            if pdepth != 0:
                legalParens=False
            if legalParens:
                print 'parentheses legal:'
                print depthList
            else:
                print 'illegal parentheses placement'
                print depthList
                print pdepth
            #queries are evaluated one by one, from deepest to shallowest nesting, then logic is applied to the returned seqIDs for each query
            depthIndices=[]
            dmax=max(depthList)
            for d in range(dmax+1):
                dcount=depthList.count(d)
                dlist=[]
                lastd=0
                for instance in range(dcount):
                    nextd=depthList.index(d,lastd)
                    dlist.append(nextd)
                    lastd=nextd+1
                depthIndices.append(dlist)
            #final result is we have two lists: depthList gives depth of each condition, 
            #whereas depthIndices gives list of chronological conditions matching each depth
            print 'depthIndices'
            #d[-1]->d[-2]...d[0]

            for conditionPos in range(condLength):
    #THIS is the important line, ie the 
    #queryConditionRow.makeQueryString() provides the atomic SQL string creation, 
    #With All Boolean logic handled by Python!
                qPair=self.conditionWidgets[conditionPos].makeQueryString()
                qString=qPair[0]
                qVals=qPair[1]
                print 'qstring %s :\n' % (conditionPos)                
                print qString
                print 'qvals %s :\n' % (conditionPos)                
                print qVals                
                dbCursor.execute(qString, qVals)
                tupleList=dbCursor.fetchall()
                for t in tupleList:
                    if t[0] is not None: # the SQL queries we construct always return the ID as the first element of a row
                        retIDList[conditionPos].append(t[0])

            aggIDList=retIDList
            
            #ok so here, we are working back from the deepest-nested queryConditionRow,
            #and at each level of nesting we perform the specified conjunction set operations (and, or)
            #between any *contiguous QCR's at that depth. Then we pop those results up a level, and repeat until we have performed 
            #all logic operations between QCR's
            for edepth in range(len(depthIndices)-1, -1, -1):
                #working from deepest to shallowest nesting, we always do the same thing which is, 
                #i) find adjacents
                #2) perform appropriate set operation
                #3 pop up a level
                cPosList=depthIndices[edepth]
                for cpos in cPosList:
                    #is this condition part of a comparison pair at this depth?
                    if (cpos + 1) in cPosList:
                        combIDList=[]
                        if self.conditionWidgets[cpos].conjCombo.currentIndex() == 0:
                            #AND
                            for eid in retIDList[cpos]:
                                if eid in retIDList[cpos+1]:
                                    combIDList.append(eid)
                            
                        else:
                            #OR
                            for eid in retIDList[cpos]:
                                combIDList.append(eid)
                            for fid in retIDList[cpos+1]:
                                if fid not in combIDList:
                                    combIDList.append(fid)
                        aggIDList[cpos]=combIDList
                        aggIDList[cpos+1]=combIDList
                    #InterDepth aggregation (aka popping)                        
                    elif len(depthList)-cpos > 1:
                        if depthList[cpos+1] > edepth:
                            combIDList=[]
                            if self.conditionWidgets[cpos].conjCombo.currentIndex() == 0:
                                #AND
                                for eid in retIDList[cpos]:
                                    if eid in aggIDList[cpos+1]:
                                        combIDList.append(eid)
                                
                            else:
                                #OR
                                for eid in retIDList[cpos]:
                                    combIDList.append(eid)
                                for fid in aggIDList[cpos+1]:
                                    if fid not in combIDList:
                                        combIDList.append(fid)
                            aggIDList[cpos]=combIDList
                            aggIDList[cpos+1]=combIDList
                            for i in range(cpos+1, len(aggIDList)):
                                if depthList[i] > depthList[cpos]:
                                    aggIDList[cpos]=combIDList
                                else:
                                    break
            print aggIDList
            qidlist=aggIDList[0]
        qidlist=sorted(qidlist)
        print 'matches:'    
        for qid in qidlist:
            print qid
                
    # generate tableWidget from qidlist, each qidlist defaults to import-as-sandbox
    #so basically just 1 addtl gui layer separating the ImportByseqID function called here
    #from what we call in order to recreate a saved session
        self.owner.addResultsTab(qidlist)
    
    #handle displays
        self.runButton.setVisible(False)
#        self.istatusbox.setChecked(True)
#        self.istatusbox.setVisible(True)
        self.mode='executed'
       # self.owner.addDBI()
        self.update()
        
    def showRegexSyntax(self):
        print 'showRegex Button clicked!'
        self.rw=regexWidget()
        self.rw.show()        
 
#recall, that the key method of this class is the .makeQueryString(),
#which returns an SQL string. However, this method is always called from the Parent tab in which the
#queryConditionRow is embedded, since there is considerable processing involved in order to implement 
#the user-specified Boolean logic amongst multiple condition rows       
class queryConditionRow(QtGui.QWidget): #3 rowmodes: 'entry', 'added', and 'searched'
    def __init__(self, owner=None, rowMode='entry',addConj=True, layoutPos=-1):
        super(queryConditionRow,self).__init__()
        self.owner = owner
        self.addConj=addConj
        self.layoutPos=layoutPos         
        if rowMode == 'entry':
            addLabels=True
            self.layoutPos=-1
        else:
            addLabels=False
            
 
        lParenthLabel=QtGui.QLabel('(')
        propLabel=QtGui.QLabel('Property')
        invLabel=QtGui.QLabel('Invert?')
        equalLabel=QtGui.QLabel('Equality')
        condLabel=QtGui.QLabel('Condition')
        rParenthLabel=QtGui.QLabel(')')
        
        self.lParenthEntry=QtGui.QLineEdit('(')
        self.lParenthEntry.setFixedWidth(40)
        self.propCombo=QtGui.QComboBox()
        self.propCombo.currentIndexChanged.connect(self.updateCondStack)
        self.invCombo=QtGui.QComboBox()
        self.equalCombo=QtGui.QComboBox()
        
        self.condEntry=QtGui.QLineEdit()
        self.condEntry.setMinimumWidth(150)
        self.condPosCombo=QtGui.QComboBox()
        self.condPosCombo.setMinimumWidth(150)
        self.condLangCombo=QtGui.QComboBox()
        self.condLangCombo.setMinimumWidth(150)
        
        self.condStack=QtGui.QStackedWidget()
        self.condStackList=[self.condEntry, self.condPosCombo, self.condLangCombo]
        for ew in self.condStackList:
            self.condStack.addWidget(ew)
        self.condStack.setCurrentIndex(0)
        
        
        self.rParenthEntry=QtGui.QLineEdit(')')
        self.rParenthEntry.setFixedWidth(40)
        addButton=QtGui.QPushButton('Add Condition to Query')
        removeButton=QtGui.QPushButton('Remove Condition from Query')
        

        addButton.clicked.connect(self.addCondition)
        removeButton.clicked.connect(self.removeCondition)
#        propList=['Word', 'ID', 'Length', 'Language', 'Prefix','Part of Speech', 'Synonym', 'Tag']
#        eqList=['=', '<', '<=' , '>','>=','regex', 'caseless regex']
        propList=["""Common Name""", """Any Name""", """Kingdom""", """Phylum""", """Class""","""Order""", """Family""", """Genus""", """Species""", """Strains""",\
        """General Description """, """Strain Descriptions ""","""Stalk Description ""","""Leaf Description ""","""Flower Description ""","""Fruit Description ""","""Root Description """,\
        """Propagation ""","""Reproductive Season ""","""Origin ""","""Habitat ""","""Medical Traditions ""","""Medical Categories ""","""Parts Used ""","""Preparation Notes """,\
        """Compounds ""","""References ""","""Date Added ""","""Date Last Modified """, """Image Files""", """Size"""]
        #Note that we also need to provide a dictionary mapping these display variables to table variables 

        self.actualNames = ['commonname', 'allnames','pkingdom','pphylum', 'pclass', 'porder', 'pfamily', 'pgenus', 'pspecies', 'strains', 'descgen','descstrains','descstalk','descleaves','descflowers','descfruits','descroots','descprop',\
        'descseasons','origin','habitat','medtrads','medcats','medparts','prepnotes','compounds','refs','adddate','moddate','imglinks', 'descsize']

        eqList=['includes', '=', '<', '<=' , '>','>=','regex', 'caseless regex']
        invList=['', '!']
        langList=['afrikaans','czech','dutch','english', 'french', 'german' , 'greek', 'hungarian','hindi','italian', 'japanese','latin', 'portuguese','romanian','russian','spanish','turkish', 'ukranian']
        posList=['noun','verb','adjective','adverb','preposition','conjunction','pronoun', 'profanity', 'saying', 'salutation']        

        self.propList = propList

        self.propCombo.addItems(propList)
        self.equalCombo.addItems(eqList)        
        self.invCombo.addItems(invList)
        self.condLangCombo.addItems(langList)
        self.condPosCombo.addItems(posList)
        self.addConj=addConj
        self.addLabels=addLabels
        if addConj:
            conjLabel=QtGui.QLabel('Conjunction')
            self.conjCombo=QtGui.QComboBox()
            self.conjCombo.addItem('and')
            self.conjCombo.addItem('or')
            self.conjCombo.addItem('xor')
            self.conjCombo.addItem('nor')
            #should add nand for logical completeness
            labels=[ lParenthLabel, propLabel, invLabel, equalLabel, condLabel, rParenthLabel, conjLabel]        
            self.paramWidgets=[ self.lParenthEntry, self.propCombo, self.invCombo, self.equalCombo, self.condStack, self.rParenthEntry, self.conjCombo]
        else:
            labels=[lParenthLabel, propLabel, invLabel, equalLabel, condLabel, rParenthLabel]        
            self.paramWidgets=[self.lParenthEntry, self.propCombo, self.invCombo, self.equalCombo, self.condStack, self.rParenthEntry]

        qgw=QtGui.QGridLayout()
        if self.addLabels:
            labels.append(QtGui.QLabel(''))
            self.paramWidgets.append(addButton)
            for i in range(len(labels)):
                qgw.addWidget(labels[i], 0,i)
                qgw.addWidget(self.paramWidgets[i], 1, i)
            #qgw.addWidget(addButton, 1, len(labels))
  
        else:
            self.paramWidgets.append(removeButton)
            for i in range(len(self.paramWidgets)):
                qgw.addWidget(self.paramWidgets[i], 0, i)

        self.setLayout(qgw)
        self.setMaximumHeight(80)


    """
    this method currently obsolete, since all query parameters are entered manually for herbQuery
    """
    def updateCondStack(self):
        if str(self.propCombo.currentText())=='Part of Speech':
            self.condStack.setCurrentIndex(1)
        elif str(self.propCombo.currentText())=='Language':
            self.condStack.setCurrentIndex(2)
        else:
            self.condStack.setCurrentIndex(0)

    def addCondition(self):
        self.owner.addConditionLine(self)
    def removeCondition(self):
        self.owner.removeConditionLine(self)

    #note that the default option for herbQuery is actually a case-insensitive 
    # 'includes' regex. Thus, we have to format those (qval) strings somewhat differently
    def makeQueryString(self):
#       propList=['Word', 'ID', 'Length', 'Language', 'Prefix','Part of Speech', 'Synonym', 'Tag']
#        propList=["""wordname""", """wordid""", """wordlength""", """language""", """prefix""","""pos""", """synonym""", """tag"""]
#        invsyms=[""" != """, """ >= """, """ > """, """ <= """, """ < """, """ !~ """, """ !~* """]        
#        regsyms=[""" = """, """ < """, """ <= """, """ > """, """ >= """, """ ~ """, """ ~* """]        

        
        invsyms=[""" !~* """, """ != """, """ >= """, """ > """, """ <= """, """ < """, """ !~ """, """ !~* """]        
        regsyms=[""" ~* """ , """ = """, """ < """, """ <= """, """ > """, """ >= """, """ ~ """, """ ~* """]        

        #I suspect the tricky thing here will be handling 'includes' conditions
        # for arrays and pseudoranges

        header="""SELECT plantid FROM planttable WHERE """
        proppos=self.propCombo.currentIndex()
        #thisprop = self.propList[proppos]
        thisprop = self.actualNames[proppos]

        if self.invCombo.currentIndex() == 1:
            logop = invsyms[self.equalCombo.currentIndex()]
        else:
            logop = regsyms[self.equalCombo.currentIndex()]
            
        #Next we have to determine whether we are querying an array-type column
        #If so, the string must be constructed somewhat differently than the default case
        arrayTypes = ['allnames', 'nametypes','strains','descstrains','imglinks','imgcaplinks']
        numTypes = ['flowerseason', 'descsize']
        if thisprop in arrayTypes:
            header += ' %s '
            header += logop
            header += ' ANY ('
            header += thisprop
            header += ')'
        elif thisprop in numTypes:
            if thisprop == 'descsize':
                if self.equalCombo.currentIndex() == 0:
                    if self.invCombo.currentIndex() == 0:
                        header += 'descsize[1] <= %s AND descsize[2] >= %s'
                    else:
                        header += 'descsize[1] > %s OR descsize[2] < %s'
                else:
                    header += 'descsize[1] '
                    header += logop
                    header += ' %s AND descsize[2]'
                    header += logop
                    header =+ ' %s '
            elif thisprop == 'flowerseason':
                header += 'descsize[1] < %s OR descsize[2] > %s'
                if self.equalCombo.currentIndex() == 0:
                    if self.invCombo.currentIndex() == 0:
                        header += ' (flowerseason[1] <= %s AND flowerseason[2] > %s'
                    else:
                        header += 'flowerseason[1] > %s OR flowerseason[2] < %s'
                else:
                    header += 'flowerseason[1] '
                    header += logop
                    header += ' %s AND flowerseason[2]'
                    header += logop
                    header =+ ' %s '
            
        else:
            header += thisprop            
            header += logop        
            header += ' %s '
            
        #Here is where we use the stackedWidget currentIndex to determine whether we are reading a
        #QLineEdit, or grabbing a .currentText()
        csIndex=self.condStack.currentIndex()
        if csIndex == 0:
            qval =  str(self.condEntry.text()).strip() 
            #case-dependent formatting unique to herbQuery with default 'includes' regex


            if ( (self.equalCombo.currentIndex() == 0) and (thisprop not in numTypes) ):
                qval = """.*""" + qval + """.*"""
               
        elif csIndex == 1:
            qval = str(self.condPosCombo.currentText()).strip()
        else:
            qval = str(self.condLangCombo.currentText()).strip()            


        if thisprop in numTypes:
            valtuple = (qval, qval)
        else:
            valtuple = (qval,)
        try:
            maxint=int(str(self.owner.maxEntry.text()))
            maxint=str(maxint)
            header += """ LIMIT """
            header += maxint
            header += """ ;"""            
        except:
            header += """ ;"""

        print header
        return [header, valtuple]
        
        
"""                
So every query run generates one of these first, and then a new query tab
*** 2 lines below NOT APPLICABLE to the wordQuery/pyWords implementation of the database interface                
these guys have the checkbox that corresponds to the IMPORT selections for the
global DBIHolder, but also has a local selectability for partial imports of the tab results
***Ignore 2 lines above                

"""
class queryResultsTab(QtGui.QWidget):
    def __init__(self, idlist, querynum=1, owner=None):
        super(queryResultsTab,self).__init__()        
        self.idlist=idlist
        self.querynum=querynum
        self.owner=owner #note, owner here is the master TabWidget() holding this display,
                        #NOT the callingSesh responsible for the query
        self.liveEdits = []        


        self.createWidgets()
        self.layoutWidgets()
    def createWidgets(self):
        confirmedPlants = []
        for plantid in self.idlist:
            #still need to reimplement this
            plantPreview = self.makePreviewFromPlantID(plantid)
            if plantPreview is not -1:
                confirmedPlants.append(plantPreview)
        self.previewTable = QtGui.QTableWidget()
        self.previewTable.setColumnCount(6)
        propList = ["""commonname""", """pgenus""","""pspecies""","""descgen""","""adddate""","""plantid"""] 
        baseHeaders = ['Name','Latin','','Description','Date Added','ID']
        allHeaders = baseHeaders
        self.previewTable.setRowCount(len(confirmedPlants))

        for epos, epreview in enumerate(confirmedPlants):
            for ppos, param in enumerate(propList):
                try:
                    pval = epreview[param]
                    if pval is not None:
                        #Truncate General Description for preview
                        if param != "descgen":
                            qtwi=QtGui.QTableWidgetItem(str(pval))
                        else:
                            ptrunc = str(pval)
                            olength = len(ptrunc)
                            olength = min(olength, 50)
                            ptrunc = ptrunc[:50]
                            qtwi=QtGui.QTableWidgetItem(ptrunc)
                            
                    else:
                        qtwi=QtGui.QTableWidgetItem('')
                except:
                    qtwi=QtGui.QTableWidgetItem('')
                if ppos == 0:                                      
                    qtwi.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable| QtCore.Qt.ItemIsSelectable)
                    if self.owner.opMode == "edit":
                        qtwi.setCheckState(QtCore.Qt.Unchecked)                        
                    else: #"search" mode, default
                        qtwi.setCheckState(QtCore.Qt.Checked)
                        #qtwi.setFlags(QtCore.Qt.ItemIsUserCheckable)
                                                                
                self.previewTable.setItem(epos, ppos, qtwi)

        self.previewTable.setHorizontalHeaderLabels(allHeaders)
        self.previewTable.resizeColumnsToContents()
        self.ascList=[]
        for i in range(self.previewTable.columnCount()): 
            self.ascList.append(True)
            
        self.resultString='Query ' + str(self.querynum) + ' Results: ' + str(len(confirmedPlants))
        self.resLabel=QtGui.QLabel(self.resultString)
        
        self.selAllButton = QtGui.QPushButton('Select All')
        self.selNoneButton = QtGui.QPushButton('Select None')
        self.expandButton = QtGui.QPushButton('Generate PDF from Selected')
        self.editButton = QtGui.QPushButton('Edit Selection')
        self.entryupButton = QtGui.QPushButton('Move Highlighted Up')
        self.entrydownButton = QtGui.QPushButton('Move Highlighted Down')

        self.selAllButton.clicked.connect(self.selAllAction)
        self.selNoneButton.clicked.connect(self.selNoneAction)
        self.expandButton.clicked.connect(self.genPDFAction)
        self.editButton.clicked.connect(self.editEntryAction)
        self.entryupButton.clicked.connect(self.entryUp)
        self.entrydownButton.clicked.connect(self.entryDown)

        self.botbutlist = [self.selAllButton, self.selNoneButton,self.expandButton, self.entryupButton, self.entrydownButton]
        if self.owner.opMode == "edit":
            self.botbutlist.append(self.editButton)
       
        
#        confirmedWords=[] #This is where we store all successfully returned previewDicts from 
#                                # the .makePreviewFromSeqID routine
#        for wordid in self.idlist:
#            wordPreview=self.makePreviewFromWordID(wordid)
#            if wordPreview is not -1: #(error code from the makePreview routine)
#                confirmedWords.append(wordPreview)
#        self.previewTable=QtGui.QTableWidget()
#        #need to implement a language aggregator here so that we can display all relevant translations on the right side of the returned table
#        langlist = []
#        for epreview in confirmedWords:
#            for elang in epreview['translations'].keys():
#                if elang not in langlist:
#                    langlist.append(elang)
#        langlist=sorted(langlist)
#        
#        
#        self.previewTable.setColumnCount(8+len(langlist))
##        propList=["""wordname""", """wordid""", """wordlength""", """language""", """pos""", """synonym""", """tag"""]
#
#        baseHeaders=['sel','prefix','wordname','wordlength','language','pos','synonym','adddate']
#        allHeaders=baseHeaders+langlist 
#        
#         
#
#        self.previewTable.setRowCount(len(confirmedWords))
#        for epos, epreview in enumerate(confirmedWords):
#            for ppos, param in enumerate(baseHeaders):
#                if ppos > 0: # calling dict key/val by param string EXCEPT first col is selection checkbox
#                    try:
#                        pval = epreview[param]
#                        if pval is not None:
#                            qtwi=QtGui.QTableWidgetItem(str(pval))
#                        else:
#                            qtwi=QtGui.QTableWidgetItem('')
#                    except:
#                        qtwi=QtGui.QTableWidgetItem('')
#                else: #first column is just a checkbox
#                    qtwi=QtGui.QTableWidgetItem()                                        
#                    qtwi.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable)
#                    qtwi.setCheckState(QtCore.Qt.Unchecked)
#                    #qtwi.setFlags(QtCore.Qt.ItemIsUserCheckable)
#                    
#                    
#                    
#                self.previewTable.setItem(epos, ppos, qtwi)
#            for lpos, lang in enumerate(langlist):
#                if lang in epreview['translations'].keys():
#                    lval = epreview['translations'][lang]
#                else:
#                    lval=""
#                qtwi=QtGui.QTableWidgetItem(lval)
#                self.previewTable.setItem(epos, lpos+len(baseHeaders),qtwi)
#        
#       
#        self.previewTable.setHorizontalHeaderLabels(allHeaders)
#        self.previewTable.resizeColumnsToContents()
#        
#        self.ascList=[]
#        for i in range(self.previewTable.columnCount()): 
#            self.ascList.append(True)
#        
#        #add sorting and expansion routines:
#        #important reminder: need to reupdate the idlist after EVERY sort, that way any edits dont required a wordid search 
#        topheads=self.previewTable.horizontalHeader()
#        self.connect(topheads, QtCore.SIGNAL("sectionClicked(int)"), self.sortColumns)
#        expheads=self.previewTable.verticalHeader()
#        self.connect(expheads, QtCore.SIGNAL("sectionClicked(int)"), self.expandWordFromRow)
#        
#        
#        self.resultString='Query ' + str(self.querynum) + ' Results: ' + str(len(confirmedWords))
#        self.resLabel=QtGui.QLabel(self.resultString)
#        
#        self.selAllButton = QtGui.QPushButton('Select All')
#        self.selNoneButton = QtGui.QPushButton('Select None')
#        self.expandButton = QtGui.QPushButton('Expand Selected')
#
#        self.selAllButton.clicked.connect(self.selAllAction)
#        self.selNoneButton.clicked.connect(self.selNoneAction)
#        self.expandButton.clicked.connect(self.expandSelAction)
#
#        self.botbutlist = [self.selAllButton, self.selNoneButton, self.expandButton]
    def layoutWidgets(self):
        layout=QtGui.QVBoxLayout()
        layout.addWidget(self.resLabel)
        layout.addWidget(self.previewTable)
        
        buttonrow = QtGui.QHBoxLayout()
        for q in self.botbutlist:
            buttonrow.addWidget(q)
        layout.addLayout(buttonrow)
        #hlayout=QtGui.QHBoxLayout()
        #bottomButtons=[ self.selAllButton, self.selNoneButton]
        #for ebutton in bottomButtons:
        #    hlayout.addWidget(ebutton)
        #layout.addLayout(hlayout)
        self.setLayout(layout)
                
    def selAllAction(self):
        for i in range(self.previewTable.rowCount()):
            thisitem=self.previewTable.item(i,0)
            thisitem.setCheckState(QtCore.Qt.Checked)
    def selNoneAction(self):
        for i in range(self.previewTable.rowCount()):
            thisitem=self.previewTable.item(i,0)
            thisitem.setCheckState(QtCore.Qt.Unchecked)

    def entryUp(self):
        rc = self.previewTable.rowCount()
        seldrows = []
        outrows = range(rc)
        rowpair = []
        #deltaList = [0] * rc
        #Based on the rows selected, we will define a new ordering,
        #and then reassign the QTableWidgetItems via a temporary holding buffer
        for erow in outrows:
            if self.previewTable.item(erow,0).isSelected():
                seldrows.append(erow)
        if len(seldrows) > 0:
            
            #lets justdo this the easy way, max 1 row shifts
                minrow = seldrows[0]
                if minrow > 0:
                    rowpair = [minrow-1, minrow]
                elif len(seldrows) > 1:
                    if seldrows[1] > 1:
                        rowpair = [seldrows[1]-1, seldrows[1]]
        if len(rowpair) == 2:
            self.previewTable.item(rowpair[0],0).setSelected(True)
            self.previewTable.item(rowpair[1],0).setSelected(False)
            self.swapPair(rowpair)
            
    def entryDown(self):
        rc = self.previewTable.rowCount()
        seldrows = []
        outrows = range(rc)
        rowpair = []
        #deltaList = [0] * rc
        #Based on the rows selected, we will define a new ordering,
        #and then reassign the QTableWidgetItems via a temporary holding buffer
        for erow in outrows:
            if self.previewTable.item(erow,0).isSelected():
                seldrows.append(erow)
        if len(seldrows) > 0:        
                minrow = seldrows[-1]
                if minrow < (rc-1):
                    rowpair = [minrow, minrow+1]
                elif len(seldrows) > 1:
                    if seldrows[-2] < (rc-2):
                        rowpair [seldrows[-2], seldrows[-2] + 1]        
        if len(rowpair) == 2:
            self.previewTable.item(rowpair[1],0).setSelected(True)
            self.previewTable.item(rowpair[0],0).setSelected(False)
            self.swapPair(rowpair)
        
    def swapPair(self, rowpair):
        if len(rowpair) >= 2:
            rowbuf = [[],[]]
            for ecol in range(self.previewTable.columnCount()):
                rowbuf[0].append(self.previewTable.item(rowpair[0],ecol).text())
                rowbuf[1].append(self.previewTable.item(rowpair[1],ecol).text())
            rowbuf[0].append(self.previewTable.item(rowpair[0],0).checkState())
            rowbuf[1].append(self.previewTable.item(rowpair[1],0).checkState())
            
            for ecol in range(self.previewTable.columnCount()):
                self.previewTable.item(rowpair[0], ecol).setText(rowbuf[1][ecol])
                self.previewTable.item(rowpair[1], ecol).setText(rowbuf[0][ecol])
            self.previewTable.item(rowpair[0],0).setCheckState(rowbuf[1][-1])
            self.previewTable.item(rowpair[1],0).setCheckState(rowbuf[0][-1])

    
#add sorting and expansion routines:
        #important reminder: need to reupdate the idlist after EVERY sort, that way any edits dont required a wordid search         
    def sortColumns(self, sortCol):
        #so we start by making a deepcopy of .idlist, hash these entries to the column to be sorted, sort by that column, and update display according to new idlist
        idhashmap = []
        idcopy=copy.deepcopy(self.idlist)    
        floatGood=True
        for erow in range(self.previewTable.rowCount()):
            try:
                thisfloat=float(str(self.previewTable.item(erow, sortCol).text()).strip())
            except:
                floatGood=False
                break
        #now that we know whether we are sorting floats or strings, we can make a hashmap from idlist, and sort                
        for erow in range(self.previewTable.rowCount()):
            thiskey=idcopy[erow]            
            if floatGood:
                thisval=float(str(self.previewTable.item(erow, sortCol).text()).strip())
            else:
                thisval=str(self.previewTable.item(erow, sortCol).text()).strip()
            idhashmap.append([thiskey, thisval])
        #ok now that we have hashmap, we can run a sort
        if self.ascList[sortCol]:
            sortresult=sorted(idhashmap, key = lambda val : val[1] )
            self.ascList[sortCol]=False
        else:
            sortresult=sorted(idhashmap, key = lambda val : val[1], reverse = True )
            self.ascList[sortCol]=True
        #additionally, we want to subsort alphabetically by word for sets of equal sort values.
        subsorts=[]#start, length
        subOn=False
        for ss in range(1,len(sortresult)):
            if sortresult[ss][1] == sortresult[ss-1][1]:
                if subOn:
                    subsorts[-1][1]+=1
                else:
                    subsorts.append([ss-1,2])
                    subOn=True
            else:
                subOn = False
        for subsort in subsorts:
            subhash=[]
            sublist=sortresult[subsort[0]:subsort[0]+subsort[1]]
            for subrow in sublist:
                locFound=False
                thisid=subrow[0]
                #print 'thisid=%d' % (thisid)
                k=0
                while locFound == False:
                    testid=self.idlist[k]
                    if testid == thisid:
                        locFound=True
                    else:
                        k+=1                
                #print 'kfound at row = %d' % (k)                       
                wordname=str(self.previewTable.item(k,2).text()).strip()
                #print 'word=%s' % wordname 
                subhash.append([thisid, wordname])
            subhash=sorted(subhash, key = lambda sval: sval[1])
            for subpos, subrow in enumerate(subhash):
                sortresult[subsort[0]+subpos][0]=subrow[0]
        #end subsorting loops
                
        #then we grab all info from the table, and iterate through the new hashmap to post values
        newDispVals=[]
        for j in range(len(sortresult)):
            thisid=sortresult[j][0]
            locFound=False
            k=0
            thisrow=[]
            while locFound == False:
                testid=self.idlist[k]
                if testid == thisid:
                    locFound=True
                else:
                    k+=1
            for ecol in range(self.previewTable.columnCount()):
                if ecol > 0:
                    cellval=str(self.previewTable.item(k,ecol).text()).strip()
                    thisrow.append(cellval)
                else:
                    thisrow.append('')
                #else:
                 #   thisrow.append(self.previewTable.item(k, 0))
            newDispVals.append(thisrow)
        for newrow in range(len(newDispVals)):
            for newcol in range(self.previewTable.columnCount()):
                if newcol > 0:
                    qtwi = QtGui.QTableWidgetItem(newDispVals[newrow][newcol])
                #else:
                    #qtwi = newDispVals[newrow][0]
                 #   qtwi = QtGui.QTableWidgetItem(newDispVals[newrow][newcol])
                    self.previewTable.setItem(newrow, newcol, qtwi)
        newidlist=[]
        for i in range(len(sortresult)):
            newidlist.append(sortresult[i][0])
        self.idlist=newidlist
            
    def expandWordFromRow(self, wordRow):
        print 'expandWordFromRow called'
        idfromrow=self.idlist[wordRow]
        self.expandWord(idfromrow)
    
    def expandWord(self, wordid):
        #first need to get the id
        print 'wordid: %d' % (wordid)
        wordDict=self.makePreviewFromWordID(wordid)
        print 'wordDict'
        print wordDict
        
        if self.owner.hasWordExpand:
            print 'adding tab to existing expandWidget'
            self.expandWidget.addExpandTab(wordid, doneDict=wordDict)
        else:
            print 'creating new expandHolder as self.expandWidget'
            self.expandWidget=expandHolder([wordid], owner=self.owner)
            #self.owner.wordExpandWidget=self.expandWidget
            #self.owner.hasWordExpand=True
            self.expandWidget.show()
        print 'expandWord routine complete'

   
                                                            
    def expandSelAction(self):
        print 'expandSelAction called'
#        for i in range(self.previewTable.rowCount()):
#            thisitem = self.previewTable.item(i,0)
#            if thisitem.checkState == QtCore.Qt.Checked:
#                print 'checked item found at row %d' % (i)
#                self.expandWordFromRow(i)
#            if thisitem.
        
#        self.selAllButton=QtGui.QPushButton('Select All')
#        self.selNoneButton=QtGui.QPushButton('Select None')
#        self.selAllButton.clicked.connect(self.selAllAction)
#        self.selNoneButton.clicked.connect(self.selNoneAction)
        
    def genPDFAction(self):
        idList = []
        for erow in range(self.previewTable.rowCount()):
            iditem = self.previewTable.item(erow,5)
            ckitem = self.previewTable.item(erow,0)
            if ckitem.checkState() == QtCore.Qt.Checked:
                validid = str(iditem.text()).strip()
                validid = int(validid)
                idList.append(validid)
        entryCount = len(idList)        
        print('Generating PDF from %d entries' % entryCount )   
        genPDF.genPDFFromIDList(idList, db='herbdb1', uname='biouser', pw='biouser')

    def editEntryAction(self):
        entryided = False
        for erow in range(self.previewTable.rowCount()):
            testitem = self.previewTable.item(erow,0)
            if testitem.checkState() == QtCore.Qt.Checked:
                entryided = True
                iditem = self.previewTable.item(erow,5)
                validid = str(iditem.text()).strip()
                validid = int(validid)
                #now form a dict that can be used for population (identical to the one used for pdf creation...)
                dbConn = hpsyfuncs.ppgConn(dbname='herbdb1', user='biouser', passwd='biouser')
                dbCursor = dbConn.cursor()
                scrapeDict = genPDF.scrapeDataFromID(validid, dbConn, dbCursor)
                dbConn.close()                
                
                editamc = addMasterContainer(self.owner.callsesh, self.owner.db, self.owner.userName, self.owner.password, "runtime", scrapeDict )
                self.liveEdits.append(editamc)
                
        if not entryided:
            self.popup = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, "fail....", "You did not select any entries. Try Again!")
            self.popup.show()
            
            
    def makePreviewFromPlantID(self, plantid):
        getParamsString="""SELECT commonname, pgenus, pspecies, descgen, adddate, plantid FROM planttable WHERE plantid = %s ;"""
        idval=(plantid,)
        #still need to trace the params back to ancestors, to generalize this
        dbConn=hpsyfuncs.ppgConn('herbdb1', 'biouser', passwd='biouser')
        dbCursor=dbConn.cursor()
        dbCursor.execute(getParamsString, idval)
        paramVals=dbCursor.fetchone()
        dispDict={}
        fineread=True
        try:
            dispDict['commonname']=paramVals[0]
            dispDict['pgenus']=paramVals[1]
            dispDict['pspecies']=paramVals[2]
            dispDict['descgen']=paramVals[3]
            dispDict['adddate']=paramVals[4]
            dispDict['plantid']=paramVals[5]
            return dispDict
        except:
            fineread=False
            return -1
            
            
    #we are constructing a dict to be used in tabular display
    def makePreviewFromWordID(self, wordid):
        getParamsString="""SELECT prefix, wordname, wordlength, language, pos, adddate, synonym, synlist FROM wordtable WHERE wordid = %s ;"""
        idval=(wordid,)
        dbConn=hpsyfuncs.ppgConn('worddb1', 'biouser', passwd='biouser')
        dbCursor=dbConn.cursor()
        dbCursor.execute(getParamsString, idval)
        paramVals=dbCursor.fetchone()
        dispDict={}
        fineread=True
        try:
            dispDict['prefix']=paramVals[0]
            dispDict['wordname']=paramVals[1]
            dispDict['wordlength']=paramVals[2]
            dispDict['language']=paramVals[3]
            dispDict['pos']=paramVals[4]
            dispDict['adddate']=paramVals[5]
        except:
            fineread=False
            return -1
            
        #If we have loaded the 'easy' parameters into the dispDict without problem, then we proceed to grabbing synonyms.
        #since we dont naively know whether they are stored as single synonym foreign key or synlist array, we check both to 
        #produce a list of foreign ids over which we can iterate regardless
        if fineread:
            synidlist=[]
            checksyn=False
            try:
                synlist=paramVals[7]
                if len(synlist)>0:
                    synidlist=synlist
                else:
                    checksyn=True
            except:
                checksyn=True
            if checksyn:
                synidlist=[paramVals[6]]
            #ok so at this point we have an internal variable synidlist over which to iterate.
            transdict={}
            synamelist=[]
            synInfoString="""SELECT wordname, synlist FROM wordtable WHERE wordid = %s;"""
            trInfoString="""SELECT prefix, wordname, language FROM wordtable WHERE wordid = %s;"""            
            for synid in synidlist:
                s=(synid,)
                dbCursor.execute(synInfoString, s)
                sinfo=dbCursor.fetchone()
                print 'sinfo'
                print sinfo
                if sinfo is not None:
                    synamelist.append(sinfo[0])
                    if sinfo[1] is not None:
                        for trid in sinfo[1]:
                            if trid != wordid:
                                tr=(trid,)
                                dbCursor.execute(trInfoString, tr)
                                tinfo=dbCursor.fetchone()
                                if ((tinfo[0] is not None) and (len(tinfo[0]) > 0)):
                                    tstring='('+tinfo[0]+') ' + tinfo[1]
                                else:
                                    tstring = tinfo[1]
                                transdict[tinfo[2]]=tstring

            if len(synamelist) > 1:
                dispDict['synonym']=str(synamelist).strip('[').strip(']')
            elif len(synamelist) == 1:
                dispDict['synonym'] = synamelist[0]
            dispDict['translations']=transdict
            
            return dispDict

class expandHolder(QtGui.QTabWidget):
    def __init__(self, owner=None, idlist=None):
        super(expandHolder, self).__init__()
        self.owner = owner
        self.tabList=[]
        self.dictList=[]
        try:
            x=len(idlist)
            self.idList=idlist
        except:
            if idlist is None:
                self.idList=[]
            else:
                self.idList=[idlist]
        for eid in self.idList:
            self.addExpandTab(eid)
            
        if self.owner is not None:
            if self.owner.hasWordExpand == False:
                self.owner.hasWordExpand = True
            self.owner.wordExpandWidget = self
            self.owner.wordExpandDictList=self.dictList
            
    def addExpandTab(self, addid, doneDict=None):
        newtab=expandWordTab(addid, self,autoDict=doneDict)
        self.tabList.append(newtab)
        self.addTab(newtab, newtab.masterDict['wordName'])
    def killExpandTab(self, tabPos):
        if (tabPos+1)<len(self.tabList):
            self.tabList=self.tabList[:tabPos]+self.tabList[tabPos+1:]
        else:
            self.tabList = self.tabList[:-1]
    
            
class expandWordTab(QtGui.QWidget):
    def __init__(self, wordid, owner=None, autoDict=None, tabNum=0):
        super(expandWordTab, self).__init__()
        self.tabNum = tabNum
        if autoDict is not None:
            self.wordDict = autoDict
        else: #if we need to generate a param dict still, then we do it by stealing the makePreviewFromID method
                #from a dummy queryResultsTab
            ff=queryResultsTab([wordid])
            self.wordDict = ff.makePreviewFromWordID(wordid)
        self.wordDict['id']=wordid
            
        self.createWidgets()
        self.layoutWidgets()                        
        
        
    def createWidgets(self):
        #format is essentially a grid layout, with a bottom button row
        self.paramList=['prefix','wordname','wordlength','language','pos','adddate','synonym', 'etymology','tags','translations']
        self.pLabelList=[]
        for param in self.paramList:
            plabel=QtGui.QLabel(param)
            self.pLabelList.append(plabel)
        self.prefixEntry = QtGui.QLineEdit()
        self.nameEntry = QtGui.QLineEdit()
        self.lengthLabel = QtGui.QLabel()
        self.langEntry = QtGui.QLineEdit()
        self.posEntry = QtGui.QLineEdit()
        self.dateLabel = QtGui.QLabel()
        self.synEntry = QtGui.QLineEdit()
        self.etyEntry = QtGui.QLineEdit()
        self.tagsEntry = QtGui.QLineEdit()
        self.transBox = QtGui.QTableWidget()
        self.transBox.setRowCount(2)
        headerLabels=['Language','Translation']
        self.transBox.setHorizontalHeaderLabels(headerLabels)
        self.paramEntries = [self.prefixEntry, self.nameEntry, self.lengthLabel, self.langEntry,self.posEntry, self.dateLabel, self.synEntry, self.etyEntry, self.tagsEntry, self.transBox ]
        for j in range(len(self.paramList)-1):
            if self.paramList[j] in self.wordDict.keys():
                self.paramEntries[j].setText(self.wordDict[self.paramList[j]])
        if 'translations' in self.wordDict:
            try:
                self.transBox.setRowCount(len(self.wordDict['translations']))
            except:
                self.transBox.setRowCount(len(self.wordDict['translations'].keys()))
                oldTD=self.wordDict['translations']
                newTL = []
                tl0=sorted(oldTD.keys())
                for keyitem in tl0:
                    newTL.append([keyitem, oldTD[keyitem]])
                self.wordDict['translations']=newTL
            for tnum, etrans in enumerate(self.wordDict['translations']):
                qtwi=QtGui.QTableWidgetItem(etrans[0])
                qtwj=QtGui.QTableWidgetItem(etrans[1])
                self.transBox.setItem(tnum, 0, qtwi)
                self.transBox.setItem(tnum, 1, qtwj)
        self.transBox.setMaximumWidth(400)
        for j in self.paramEntries:
            j.setMaximumWidth(400)
            
        self.saveChangesButton=QtGui.QPushButton('Save Changes')
        self.killTabButton=QtGui.QPushButton('Close Tab')        
        self.saveChangesButton.clicked.connect(self.saveChangesAction)
        self.killTabButton.clicked.connect(self.killTabAction)
        self.botButtons=[self.saveChangesButton, self.killTabButton]    


    def layoutWidgets(self):
        masterlayout=QtGui.QVBoxLayout()
        topGrid=QtGui.QGridLayout()
        bottomRow=QtGui.QHBoxLayout()
        for ppos, pLabel in enumerate(self.pLabelList):
            topGrid.addWidget(pLabel, ppos, 0)
        for epos, ewidget in enumerate(self.paramEntries):
            topGrid.addWidget(ewidget, epos, 1)
        for ebutton in self.botButtons:
            bottomRow.addWidget(ebutton)
            
        
        masterlayout.addLayout(topGrid)
        masterlayout.addLayout(bottomRow)
        self.setLayout(masterlayout)
        
        
    def saveChangesAction(self):
        pass
    def killTabAction(self):
        pass
    
    
"""
Due to the large number of entry fields, it is necessary to embed this widget within a 
addMasterContainer class, consisting of a QScrollArea set to self.

Thus, parent is the enclosing addMasterContainer, and parentSesh is the usual welcomeBox session placeholder

"""    
    
class addMaster(QtGui.QWidget):
    def __init__(self, aparent= None, parentSesh = None, addMode = 'unique'):
        super(addMaster, self).__init__()
        
        #addmode can be 'unique' (default), 'replace', or 'runtime'
        self.addMode = addMode 
        #If populate(self, popDict) is called by instantiating method, 
        #self.oDict will be set to popDict, 
        #and used primarily to obtain a plantid, which is then used by the 
        #postgres API as a true PRIMARY KEY, as opposed to commonname as a proxy.        
        self.oDict = None
        
        self.addCount = 0
        self.mre = ' '        
        
        self.aparent = aparent
        self.parentSesh = parentSesh
        
        print('addMaster initialized')        
        
        self.createWidgets()
        self.layoutWidgets()
    def createWidgets(self):
        
                
        
        #row 1
        self.labelTop=QtGui.QLabel('Welcome to the herbQuery Input API, v0.1!')        
        self.acString = 'Entries this session:'
        self.acString += str(self.addCount)
        self.mreString = 'Most recent entry:'
        self.mreString += self.mre        
        
        self.labelEcount=QtGui.QLabel(self.acString)
        self.labelMre = QtGui.QLabel(self.mreString)
        #row 2
        self.labelCommon = QtGui.QLabel('Common Name')        
        self.commonEntry = QtGui.QLineEdit()


        self.oComboList = ['Ayurvedic', 'Chinese', 'European', 'Indigenous', 'Other' ]
        self.labelOnames0 = QtGui.QLabel('Other Names')        
        self.oCombo0 = QtGui.QComboBox()
        self.oEntry0 = QtGui.QLineEdit()
        
        self.labelOnames1 = QtGui.QLabel(' ')        
        self.oCombo1 = QtGui.QComboBox()
        self.oEntry1 = QtGui.QLineEdit()

        for cOption in self.oComboList:
            self.oCombo0.addItem(cOption)
            self.oCombo1.addItem(cOption)
        self.oCombo1.setCurrentIndex(1)
        
        #note that oCombo2 and 3 are NOT actually combos, but lineEdits to allow arbitrary cultural specification        
        
        self.labelOnames2 = QtGui.QLabel(' ')        
        self.oCombo2 = QtGui.QLineEdit()
        self.oEntry2 = QtGui.QLineEdit()
        
        self.labelOnames3 = QtGui.QLabel(' ')        
        self.oCombo3 = QtGui.QLineEdit()
        self.oEntry3 = QtGui.QLineEdit()        
        
        self.labelK = QtGui.QLabel('Kingdom')        
        self.labelP = QtGui.QLabel('Phylum')     
        self.labelC = QtGui.QLabel('Class')     
        self.labelO = QtGui.QLabel('Order')     
        self.labelF = QtGui.QLabel('Family')     
        self.labelG = QtGui.QLabel('Genus')     
        self.labelS = QtGui.QLabel('Classification: Species') 

        #last three labels and entries constrained by size for aesthetics
#        self.labelK.setMaximumWidth(60)     
#        self.labelP.setMaximumWidth(60)   
#        self.labelC.setMaximumWidth(60)   

        self.entryK = QtGui.QLineEdit('Plantae')
        self.entryP = QtGui.QLineEdit('')
        self.entryC = QtGui.QLineEdit('')
        self.entryO = QtGui.QLineEdit('')
        self.entryF = QtGui.QLineEdit('')
        self.entryG = QtGui.QLineEdit('')
        self.entryS = QtGui.QLineEdit('')        
#        self.entryK.setMaximumWidth(60)     
#        self.entryP.setMaximumWidth(60)  
#        self.entryC.setMaximumWidth(60) 
        
        self.labelStrains = QtGui.QLabel('Known Subspecies or Strains')        
        self.strainsEntry = QtGui.QLineEdit()
      
        self.labelGenD = QtGui.QLabel('Description: General')        
        self.genDEntry = QtGui.QTextEdit()  
        
        self.labelStrainsD = QtGui.QLabel('Description: Strains\nformat= strain1: desc1|| ... ')        
        self.strainsDEntry = QtGui.QTextEdit()    
        
        self.labelSize = QtGui.QLabel('Size range (m)')        
        self.minSizeEntry = QtGui.QLineEdit()     
        self.labelSizeColon = QtGui.QLabel('<-->')      
        self.labelSizeColon.setAlignment(QtCore.Qt.AlignHCenter)
        self.maxSizeEntry = QtGui.QLineEdit()        
        
        self.labelStalkD = QtGui.QLabel('Description: Stalk')        
        self.stalkDEntry = QtGui.QTextEdit()        
        
        self.labelRootsD = QtGui.QLabel('Description: Roots')        
        self.rootsDEntry = QtGui.QTextEdit()        
        
        self.labelLeavesD = QtGui.QLabel('Description: Leaves')        
        self.leavesDEntry = QtGui.QTextEdit()       
        
        self.labelFlowersD = QtGui.QLabel('Description: Flowers')        
        self.flowersDEntry = QtGui.QTextEdit()       
        
        self.labelFruitD = QtGui.QLabel('Description: Fruit')        
        self.fruitsDEntry = QtGui.QTextEdit()       
        
        self.labelPropD = QtGui.QLabel('Description: Propagation')        
        self.propDEntry = QtGui.QTextEdit()       
        

        self.seasonMods = ['early','mid','late']
        self.seasonMonths = ['January','February','March','April','May','June','July','August','September','October','November','December']        
        
        self.labelFseason = QtGui.QLabel('Flowering Season')        
        self.seasonMod1 = QtGui.QComboBox()
        self.season1 = QtGui.QComboBox()
        self.labelSeasonColon = QtGui.QLabel('<-->')      
        self.labelSeasonColon.setAlignment(QtCore.Qt.AlignHCenter)
        self.seasonMod2 = QtGui.QComboBox()
        self.season2 = QtGui.QComboBox()        

        for smod in self.seasonMods:
            self.seasonMod1.addItem(smod)
            self.seasonMod2.addItem(smod)            
        for smonth in self.seasonMonths:
            self.season1.addItem(smonth)
            self.season2.addItem(smonth)

        self.seasonMod1.setCurrentIndex(0)             
        self.season1.setCurrentIndex(0)    
        self.seasonMod2.setCurrentIndex(2)    
        self.season2.setCurrentIndex(11)    
        
        self.labelSeasonD = QtGui.QLabel('Seasonal Behavior')        
        self.seasonDEntry = QtGui.QTextEdit()       

        self.labelHabitat = QtGui.QLabel('Habitat')        
        self.habitatEntry = QtGui.QTextEdit()
        
        self.labelOrigin = QtGui.QLabel('Geographic Origin')        
        self.originEntry = QtGui.QLineEdit()
        
        self.labelMedtrads = QtGui.QLabel('Medical Traditions')        
        self.medtradsEntry = QtGui.QTextEdit()
        
        self.labelMedcats = QtGui.QLabel('Medical Categories')        
        self.medcatsEntry = QtGui.QLineEdit()
        
        self.labelMedparts = QtGui.QLabel('Parts Used')        
        self.medpartsEntry = QtGui.QLineEdit()
        
        self.labelPrepnotes = QtGui.QLabel('Preparation Notes')        
        self.prepEntry = QtGui.QTextEdit()
        
        self.labelCompounds = QtGui.QLabel('Notable Compounds')        
        self.compoundsEntry = QtGui.QLineEdit()
        
        self.labelRefs = QtGui.QLabel('References (use || as delim)')        
        self.refsEntry = QtGui.QLineEdit()
        
        self.addImageButton = QtGui.QPushButton('Add Image')
        self.dummyLabel = QtGui.QLabel(' ')
        self.removeImagesButton = QtGui.QPushButton('Remove Checked')
        self.imgTable = QtGui.QTableWidget()
        self.addImageButton.clicked.connect(self.getImageString)
        self.removeImagesButton.clicked.connect(self.removeChecked)
        self.imgTable.setRowCount(0)
        self.imgTable.setColumnCount(3)
        self.imgTable.setColumnWidth(0,125) 
        self.imgTable.setColumnWidth(1,325)
        self.imgTable.setColumnWidth(2,0) #hidden, only maintained for information lookup
        self.imgTable.setMaximumHeight(200) 

        #self.imgTable.setMaximumWidth(200) 
        itHeaders = ['File','Caption','Path']
        self.imgTable.setHorizontalHeaderLabels(itHeaders)
        
        
        self.addButton = QtGui.QPushButton('Add Entry')
        self.nullLabel = QtGui.QLabel(' ')
        self.clearButton = QtGui.QPushButton('Clear Form')
        self.imgupButton = QtGui.QPushButton('Selected Up')
        self.imgdownButton = QtGui.QPushButton('Selected Down')        
        self.addButton.clicked.connect(self.addEntry)
        self.clearButton.clicked.connect(self.clearForm)       
        self.imgupButton.clicked.connect(self.imgUp)
        self.imgdownButton.clicked.connect(self.imgDown)    
        
        # we really need some master mechanism for tracking all these widgets within the master GridLayout
        #format is [[(widget, w, h), ...], ... ]
        self.masterOrg = [[(self.labelTop, 1,2), (self.labelEcount, 1,2), (self.labelMre, 1,2)], [(self.labelCommon,1,1),(self.commonEntry,1,2)],[(self.labelOnames0,1,1),(self.oCombo0,1,1),(self.oEntry0,1,2) ],[(self.labelOnames1,1,1),(self.oCombo1,1,1),(self.oEntry1,1,2) ],[(self.labelOnames2,1,1),(self.oCombo2,1,1),(self.oEntry2,1,2) ],[(self.labelOnames3,1,1),(self.oCombo3,1,1),(self.oEntry3,1,2) ],\
        [(self.labelS,1,1),(self.labelG,1,1),(self.labelF,1,1),(self.labelO,1,1),(self.labelC,1,1),(self.labelP,1,1),(self.labelK,1,1)], [(self.entryS,1,1),(self.entryG,1,1),(self.entryF,1,1),(self.entryO,1,1),(self.entryC,1,1),(self.entryP,1,1),(self.entryK,1,1)],\
        [(self.labelStrains,1,1),(self.strainsEntry,1,3)],[(self.labelGenD,1,1),(self.genDEntry,3,3)],[(self.labelSize,1,1),(self.minSizeEntry,1,1),(self.labelSizeColon,1,1),(self.maxSizeEntry,1,1)],[(self.labelStrainsD,2,1),(self.strainsDEntry,3,3)],\
        [(self.labelStalkD,1,1),(self.stalkDEntry,3,3)],[(self.labelRootsD,1,1),(self.rootsDEntry,3,3)],[(self.labelLeavesD,1,1),(self.leavesDEntry,3,3)],[(self.labelFlowersD,1,1),(self.flowersDEntry,3,3)],[(self.labelFruitD,1,1),(self.fruitsDEntry,3,3)],[(self.labelPropD,1,1),(self.propDEntry,3,3)],[(self.labelFseason,1,1),(self.seasonMod1,1,1),(self.season1,1,1),(self.labelSeasonColon,1,1),(self.seasonMod2,1,1),(self.season2,1,1) ],\
        [(self.labelSeasonD,1,1),(self.seasonDEntry,3,3)],[(self.labelHabitat,1,1),(self.habitatEntry,3,3)],[(self.labelOrigin,1,1),(self.originEntry,1,2)],[(self.labelMedtrads,1,1),(self.medtradsEntry,3,3)],[(self.labelMedcats,1,1),(self.medcatsEntry,1,3)],\
        [(self.labelMedparts,1,1),(self.medpartsEntry,1,3)],[(self.labelPrepnotes,1,1),(self.prepEntry,3,3)],[(self.labelCompounds,1,1),(self.compoundsEntry,1,3)],[(self.labelRefs,1,1),(self.refsEntry,1,3)],\
        [(self.addImageButton,1,1),(self.removeImagesButton,1,1),(self.imgTable,1,5)],[(self.imgupButton,1,1),(self.imgdownButton,1,1)],[(self.addButton,1,1),(self.nullLabel,1,1),(self.clearButton,1,1)]]        
        
#        self.preLabel=QtGui.QLabel("Prefix")
#        self.nameLabel=QtGui.QLabel("Word")
#        self.langLabel=QtGui.QLabel("Language")
#        self.posLabel=QtGui.QLabel("Part of Speech")    
#        self.synLabel=QtGui.QLabel("Synonym")    
#        self.tagLabel=QtGui.QLabel("Tags")    
#        
#        self.preEntry=QtGui.QLineEdit('')
#        self.preEntry.setMinimumWidth(50)
#        self.nameEntry=QtGui.QLineEdit('')
#        self.nameEntry.setMinimumWidth(150)
#        langList=['afrikaans','czech','dutch','english', 'french', 'german' , 'greek', 'hungarian','hindi','italian', 'japanese','latin', 'portuguese','romanian','russian','spanish','turkish', 'ukranian']
#        posList=['noun','verb','adjective','adverb','preposition','conjunction','pronoun', 'profanity', 'saying', 'salutation']        
#        self.langEntry=QtGui.QComboBox()
#        self.langEntry.addItems(langList)
#        self.posEntry=QtGui.QComboBox()
#        self.posEntry.addItems(posList)
#        self.synEntry=QtGui.QLineEdit('')
#        self.synEntry.setMinimumWidth(100)
#        self.tagEntry=QtGui.QLineEdit('')
#        self.tagEntry.setMinimumWidth(100)
#               
#               
#        self.addButton=QtGui.QPushButton('Add Word')
#        self.addButton.setMaximumWidth(100)
#        self.clearButton=QtGui.QPushButton('Clear Form')
#        self.clearButton.setMaximumWidth(100)               
#        self.addButton.clicked.connect(self.addWord)
#        self.clearButton.clicked.connect(self.clearForm)
#        self.botLabel=QtGui.QLabel('Last word added: ')

    def layoutWidgets(self):
        
        self.setMinimumHeight(2000)
        mgrid = QtGui.QGridLayout()    
        mgrid.setSpacing(5)
#        mgrid.setVerticalSpacing(40)
#        mgrid.setRowMinimumHeight(0,40)
#        mgrid.setRowMinimumHeight(1,40)
#        mgrid.setRowMinimumHeight(2,40)
#        mgrid.setRowMinimumHeight(3,40)

        
        self.setLayout(mgrid)
        
        localht = 0
        for erow in self.masterOrg:
            #first identify how tall this row will be
            localwd = 0
            maxht = 1
            for ewidget in erow:
                maxht = max(maxht, ewidget[1])
            #now add the widgets
            for ewidget in erow:
                widget = ewidget[0]
                nrows = ewidget[1]
                ncols = ewidget[2]
                mgrid.addWidget(widget,localht,localwd,nrows,ncols)
                localwd += ncols
            
#            mgrid.setRowMinimumHeight(localht,40)
            localht += maxht
            
            

            
#        for i in range(mgrid.rowCount()):
#            mgrid.setRowMinimumHeight(i,40)
        
        
        
#         self.labelRow=[self.preLabel,self.nameLabel,self.langLabel,self.posLabel,self.synLabel,self.tagLabel]
#         self.entryRow=[self.preEntry,self.nameEntry,self.langEntry,self.posEntry,self.synEntry,self.tagEntry]
#         self.buttonRow=[self.addButton, self.clearButton]
#         slay = QtGui.QVBoxLayout()
#         slay.addWidget(self.topLabel)
#
#         ll=QtGui.QHBoxLayout()         
#         for i in self.labelRow:
#             ll.addWidget(i)
#         slay.addLayout(ll)
#
#         el=QtGui.QHBoxLayout()         
#         for i in self.entryRow:
#             el.addWidget(i)
#         slay.addLayout(el)
#
#         bl=QtGui.QHBoxLayout()         
#         for i in self.buttonRow:
#             bl.addWidget(i)
#         slay.addLayout(bl)
#         
#         slay.addWidget(self.botLabel)
#         self.setLayout(slay)
#         self.setGeometry(200,200,600,350)
        
        

        self.setLayout(mgrid)
        #self.show() #don't show until after embedding in parent QScrollArea

    #this method is called automatically for any addMasterContainers generated in an edit-mode database connection
    #, as the result of a successful query for an edit target
    def populate(self, popDict):
        #well just segregate this into widgetType, ie lineEdits, textEdits, and combos
        # gonna do it as a pair of dbkey:widget dictionaries, then handle the numerics manually
        # allnames+nametypes may be a lil hairy as well, and strains and their descriptions will have to be parsed from the list
        self.oDict = popDict        
        leDict = {'commonname': self.commonEntry,'pspecies': self.entryS,'pgenus': self.entryG,'pfamily': self.entryF,'porder': self.entryO,'pclass': self.entryC,'pphylum': self.entryP,'pkingdom': self.entryK,\
        'origin': self.originEntry,'medcats': self.medcatsEntry,'medparts': self.medpartsEntry,'compounds': self.compoundsEntry,'refs': self.refsEntry}
        
        teDict = {'descgen': self.genDEntry,'descroots': self.rootsDEntry,'descstalk': self.stalkDEntry,'descleaves': self.leavesDEntry,'descflowers': self.flowersDEntry,'descfruit': self.fruitsDEntry,'descprop': self.propDEntry,'descseasons': self.seasonDEntry,'medtrads': self.medtradsEntry,'prepnotes': self.prepEntry,'habitat': self.habitatEntry }
             
        for lkey in leDict.keys():
            try:
                ldata = popDict[lkey]
                if len(ldata) > 0:
                    leDict[lkey].setText(ldata)
                    leDict[lkey].setCursorPosition(0)
            except:
                pass

        for tkey in teDict.keys():
            try:
                tdata = popDict[tkey]
                if len(tdata) > 0:
                    teDict[tkey].setPlainText(tdata)
                    wcursor = teDict[tkey].textCursor()
                    wcursor.setPosition(0)
            except:
                pass
        #tobecontinued
        if "descsize" in popDict.keys():
            self.minSizeEntry.setText(str(popDict["descsize"][0]))
            self.maxSizeEntry.setText(str(popDict["descsize"][1]))             
        if "flowerseason" in popDict.keys():
            minSVal = str(popDict["flowerseason"][0]).split('.',1)             
            maxSVal = str(popDict["flowerseason"][1]).split('.',1)
            self.season1.setCurrentIndex(int(minSVal[0]))
            self.season2.setCurrentIndex(int(maxSVal[0]))              
            minSMod = int(minSVal[1])//4
            maxSMod = int(maxSVal[1])//4
            self.seasonMod1.setCurrentIndex(minSMod)
            self.seasonMod2.setCurrentIndex(maxSMod)

        combosTaken = 0
        opensTaken = 0
        for ename in popDict["allnames"]:
            print "altname: "
            print ename
            ekval = ename.split(':',1)
            if len(ekval) == 2: #this should be always, unless something has gone wrong
                nametype = ekval[0].strip()
            else: #and this is what we call a patch :)
                print "Unrecognized altname entry:"
                print ename
                nametype = 'Unknown'
                ekval.append(ekval[0]) 
            
            print "nametype"
            print nametype            
            
            if nametype in self.oComboList and combosTaken < 2:
                thisIndex = self.oComboList.index(nametype)
                if combosTaken == 0:
                    self.oCombo0.setCurrentIndex(thisIndex)
                    self.oEntry0.setText(ekval[1])
                    self.oEntry0.setCursorPosition(0)
                    combosTaken += 1
                else:
                    self.oCombo1.setCurrentIndex(thisIndex)
                    self.oEntry1.setText(ekval[1])
                    self.oEntry1.setCursorPosition(0)
                    combosTaken += 1
                    
            elif nametype not in ["Common", "Latin"] and opensTaken < 2:                
                if opensTaken == 0:
                    self.oCombo2.setText(nametype)
                    self.oEntry2.setText(ekval[1])
                    self.oCombo2.setCursorPosition(0)
                    self.oEntry2.setCursorPosition(0)
                    opensTaken += 1
                else:
                    self.oCombo3.setText(nametype)
                    self.oEntry3.setText(ekval[1])
                    self.oCombo3.setCursorPosition(0)
                    self.oEntry3.setCursorPosition(0)
                    opensTaken += 1
                    
        if "strains" in popDict.keys():
            if popDict["strains"] is not None:
                strainstring = ""
                for sno, estrain in enumerate(popDict["strains"]):
                    strainstring += estrain
                    if sno < (len(popDict["strains"])-1):
                        strainstring += ", "                
                self.strainsEntry.setText(strainstring)
                self.strainsEntry.setCursorPosition(0)
                try:
                    numdescs = len(popDict["descstrains"])
                    numprinted = 0
                    sdescstring = ""
                    #First identify if we have a General description of strains, and print that first to the descstring
                    for sdesc in popDict["descstrains"]:
                        skey = sdesc.split(':')[0].strip()
                        if skey == "General":
                            sdescstring += skey[1]
                            numprinted += 1
                            if numprinted < numdescs:
                                sdescstring += '||\n'
                        
                    for sdesc in popDict["descstrains"]:
                        skey = sdesc.split(':')[0].strip()
                        if skey != "General":
                            sdescstring += sdesc
                            numprinted += 1
                            if numprinted < numdescs:
                                sdescstring += '||\n'
                    self.strainsDEntry.setPlainText(sdescstring)
                    scur = self.strainsDEntry.textCursor()
                    scur.setPosition(0)
                except:
                    pass

                    
                    
        #load image data, if it exists. If it doesnt, take an InvalidKeyError
        try:
            for ino, eimg in enumerate(popDict["imglinks"]):
                self.addImage(eimg)
                try:
                    icaption = popDict["imgcaplinks"][ino]
                    if icaption != "NoCaption":
                        capitem = self.imgTable.item(ino,1)
                        capitem.setText(icaption)
                except:
                    pass
                
        except:
            pass

             
    def clearForm(self):
        entryList = [self.commonEntry, self.oEntry0, self.oEntry1, self.oEntry2, self.oEntry3, self.entryK, self.entryP, self.entryC, self.entryO, self.entryF, self.entryG, self.entryS,\
        self.strainsEntry, self.genDEntry, self.strainsDEntry, self.minSizeEntry, self.maxSizeEntry, self.stalkDEntry, self.rootsDEntry, self.leavesDEntry, self.flowersDEntry, self.fruitsDEntry, self.propDEntry, self.seasonDEntry,\
        self.habitatEntry, self.originEntry, self.medtradsEntry, self.medcatsEntry, self.medpartsEntry, self.prepEntry, self.compoundsEntry, self.refsEntry]
        for entry in entryList:
            entry.setText("")
#        self.preEntry.setText("")
#        self.nameEntry.setText("")
#        self.synEntry.setText("")
#        self.tagEntry.setText("")
            
    def addEntry(self):
        #construct dictionary mapping explicit SQL row names to scraped data values
        entryDict = {}
        entryDict['commonname'] = str(self.commonEntry.text()).strip()
        
        entryDict['pspecies'] = str(self.entryS.text()).strip()
        entryDict['pgenus'] = str(self.entryG.text()).strip()                
        
        entryDict['allnames'] = []        
        entryDict['nametypes'] = []
        #first scrape the explicit othernames. Then add common and Latin
        oString0 = str(self.oEntry0.text()).strip()
        if len(oString0) > 0:
            nametype = self.oComboList[self.oCombo0.currentIndex()]
            #ostrings = oString0.split(',')
            ost = nametype+':'+oString0          
            entryDict['allnames'].append(ost)
            entryDict['nametypes'].append(nametype)
                                
        oString1 = str(self.oEntry1.text()).strip()
        if len(oString1) > 0:
            nametype = self.oComboList[self.oCombo1.currentIndex()]
            ost = nametype+':'+oString1          
            entryDict['allnames'].append(ost)
            entryDict['nametypes'].append(nametype)
#            ostrings = oString1.split(',')
#            for ono, ost in enumerate(ostrings):
#                ost = ost.strip()
#                ost = nametype+':'+ost
#                ostrings[ono] = ost
#            for ost in ostrings:
#                entryDict['allnames'].append(ost)
#                entryDict['nametypes'].append(nametype)        
        
        oString2 = str(self.oEntry2.text()).strip()
        if len(oString2) > 0:
            nametype = str(self.oCombo2.text()).strip()
            if len(nametype) < 1:
                nametype = 'Other'
            ost = nametype+':'+oString2          
            entryDict['allnames'].append(ost)
            entryDict['nametypes'].append(nametype)
#            ostrings = oString1.split(',')
#            ostrings = oString2.split(',')
#            for ono, ost in enumerate(ostrings):
#                ost = ost.strip()
#                ost = nametype+':'+ost
#                ostrings[ono] = ost
#            for ost in ostrings:
#                entryDict['allnames'].append(ost)
#                entryDict['nametypes'].append(nametype)         
        
        oString3 = str(self.oEntry3.text()).strip()
        if len(oString3) > 0:
            nametype = str(self.oCombo3.text()).strip()
            if len(nametype) < 1:
                nametype = 'Other'
            ost = nametype+':'+oString3          
            entryDict['allnames'].append(ost)
            entryDict['nametypes'].append(nametype)
#            ostrings = oString1.split(',')
#            ostrings = oString3.split(',')
#            for ono, ost in enumerate(ostrings):
#                ost = ost.strip()
#                ost = nametype+':'+ost
#                ostrings[ono] = ost
#            for ost in ostrings:
#                entryDict['allnames'].append(ost)
#                entryDict['nametypes'].append(nametype) 


        comstring = 'Common:'+entryDict['commonname']
        entryDict['allnames'].append(comstring)
        entryDict['nametypes'].append('Common')  
        
        latname = 'Latin:'+entryDict['pgenus'] + ' ' + entryDict['pspecies'].lower()
        entryDict['allnames'].append(latname)
        entryDict['nametypes'].append('Latin')         

        #defined earlier, for allnames access               
#        entryDict['pspecies'] = str(self.entryS.text()).strip()
#        entryDict['pgenus'] = str(self.entryG.text()).strip()
        entryDict['pclass'] = str(self.entryF.text()).strip()        
        entryDict['porder'] = str(self.entryO.text()).strip()        
        entryDict['pfamily'] = str(self.entryC.text()).strip()
        entryDict['pphylum'] = str(self.entryP.text()).strip()
        entryDict['pkingdom'] = str(self.entryK.text()).strip()
        #dont forget to add Latin s.g name to otherNames         
        
        strains = str(self.strainsEntry.text()).strip()
        strains = strains.split(',')
        print ('strains(raw) = %s' % str(strains))
        firstStrain = strains[0]
        if len(firstStrain.strip()) > 0: 
            for sno, strain in enumerate(strains):
                strain = strain.strip()
                strains[sno] = strain
        else:
            strains = []
        
        entryDict['strains'] = strains
        # Now that we have a list of strains, we can search for strain descriptions
        confirmedSDList = []  
        sdescRaw = str(self.strainsDEntry.toPlainText()).strip()
        if ( (len(entryDict['strains']) > 0) and (len(sdescRaw)) > 0 ):
            
            sdList = sdescRaw.split('||')
            for sno, sd in enumerate(sdList):
                sd = sd.strip()
                sdList[sno] = sd
            for sd in sdList:
                kv = sd.split(':')
                skey = kv[0].strip()
                if skey in entryDict['strains']:
                    confirmedSDList.append(sd)
                else:
                    print("Unrecognized key in strain description: %s" % skey)
            
        entryDict['descstrains'] = confirmedSDList

        #numrange formatting for size-range storage
        try:
            sizelo = str(self.minSizeEntry.text()).strip()
            sizelo = float(sizelo)
            sizehi = str(self.maxSizeEntry.text()).strip()
            sizehi = float(sizehi)
            sizehi = max(sizehi, sizelo)                        
            #sizestring = 'numrange('+str(sizelo)+', '+ str(sizehi)+')'
            #entryDict['descsize'] = sizestring
            #sizeval = pex.psycopg2.extras.NumericRange(sizelo, sizehi)
            #entryDict['descsize'] = sizeval
            entryDict['descsize'] = [sizelo, sizehi]                         
        except:
            entryDict['descsize'] = ''   

        entryDict['descgen'] = str(self.genDEntry.toPlainText()).strip()             
        entryDict['descstalk'] = str(self.stalkDEntry.toPlainText()).strip()        
        entryDict['descroots'] = str(self.rootsDEntry.toPlainText()).strip()
        entryDict['descleaves'] = str(self.leavesDEntry.toPlainText()).strip()        
        entryDict['descflowers'] = str(self.flowersDEntry.toPlainText()).strip()        
        entryDict['descfruit'] = str(self.fruitsDEntry.toPlainText()).strip()
        entryDict['descprop'] = str(self.propDEntry.toPlainText()).strip()

    
        #Combo entries are (automatically, thanks Python) converted to floats for numrange specification
        seasonlo = self.season1.currentIndex()
        seasonlo += 0.4 * self.seasonMod1.currentIndex()
        
        seasonhi = self.season2.currentIndex()
        seasonhi += 0.4 * self.seasonMod2.currentIndex()

        seasonhi = max(seasonhi, seasonlo)   
        entryDict['flowerseason'] = [seasonlo, seasonhi]
        #seasonstring = 'numrange('+str(seasonlo)+', '+ str(seasonhi)+')'
        #entryDict['flowerseason'] = seasonstring
    
        entryDict['descseasons'] = str(self.seasonDEntry.toPlainText()).strip()        
        entryDict['habitat'] = str(self.habitatEntry.toPlainText()).strip()
        entryDict['origin'] = str(self.originEntry.text()).strip()
        entryDict['medcats'] = str(self.medcatsEntry.text()).strip()
        entryDict['medtrads'] = str(self.medtradsEntry.toPlainText()).strip()        
        entryDict['medparts'] = str(self.medpartsEntry.text()).strip()        
        entryDict['prepnotes'] = str(self.prepEntry.toPlainText()).strip()
        entryDict['compounds'] = str(self.compoundsEntry.text()).strip()        
        entryDict['refs'] = str(self.refsEntry.text()).strip()        

        imgPathList = []
        imgCapList = []
        imgCount = self.imgTable.rowCount()
        for imgno in range(imgCount):
            pathitem = self.imgTable.item(imgno,2)
            capitem = self.imgTable.item(imgno,1)
            pathstring = str(pathitem.text()).strip()
            capstring = str(capitem.text()).strip()
            if len(capstring) == 0:
                capstring = "NoCaption"
            imgPathList.append(pathstring)
            imgCapList.append(capstring)
            
        entryDict['imglinks'] = imgPathList
        entryDict['imgcaplinks'] = imgCapList   

        badkeys=[]
        for eitem in entryDict.keys():
            if len(entryDict[eitem]) < 1:
                badkeys.append(eitem)
        for ekey in badkeys:
            entryDict.pop(ekey)

        ##This is how we track whether an Add request is coming from edit mode, 
        ##or on a form filled from scratch
        #
        ##Note that if we are in edit mode, an update.v.new MessageBox is handled here rather than in 
        ##the addPlantFromDict() method, to enforce hpsyfuncs' independence from any GUI requirements.

        #actually- fuck it, default overwrite. too tired to deal with custom widgets and function splitting

        if self.oDict is not None:
            entryDict['plantid'] = self.oDict['plantid']
            self.addMode = 'override'

            
        print 'scraped entryDict: '
        for eitem in entryDict.keys():
            print ("%s: %s" % (eitem, str(entryDict[eitem])))
        
         #still need to reimplement this in db/user-independent fashion, but currently too lazy to trace the path of the relevant session variables
        retStat=hpsyfuncs.addPlantFromDict(entryDict, self.aparent.db, self.aparent.userName, self.aparent.password, self.addMode)
        if retStat:
            print('successful upload of herb %s to database: %s!' % (entryDict['commonname'],self.aparent.db))
            #update labels
            self.addCount += 1
            acs = self.acString.split(':')
            acs = acs[0]
            acs = acs + ': ' + str(self.addCount)
            self.acString = acs
            self.labelEcount.setText(self.acString)

            lastname = entryDict['commonname']
            mre = self.mre.split(':')
            mre = mre[0] + ': ' + lastname
            self.mreString = mre
            self.labelMre.setText(self.mreString)

        else:
            print('database connection failed with credentials= db: %s, user: %s, pw: %s  :(' % (self.aparent.db, self.aparent.userName, self.aparent.password))

    def getImageString(self):
            qfd = QtGui.QFileDialog()
            qfd.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
            qfd.setFileMode(QtGui.QFileDialog.ExistingFile)
            imgFilePath = str(qfd.getOpenFileName()).strip()
            if len(imgFilePath) > 3:
                self.addImage(imgFilePath)
        
    def addImage(self, imgSource="userDialog"):
 
        imgFilePath = imgSource 
        print('imgFilePath = ')
        print imgFilePath
        imgName = imgFilePath.split('/')
        imgName = imgName[-1]
        
        itwi = QtGui.QTableWidgetItem(imgName)
#        itwi.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable)
        itwi.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
        itwi.setCheckState(QtCore.Qt.Unchecked)

        ctwi = QtGui.QTableWidgetItem(" ")
        ctwi.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable)
        
        ptwi = QtGui.QTableWidgetItem(imgFilePath)
        
        rowCount = self.imgTable.rowCount()
        self.imgTable.insertRow(rowCount)
        self.imgTable.setItem(rowCount,0,itwi)
        self.imgTable.setItem(rowCount,1,ctwi)
        self.imgTable.setItem(rowCount,2,ptwi)
    
    
    def removeChecked(self):
        rowCount = self.imgTable.rowCount()
        for erow in range(rowCount-1,-1,-1):
            twi = self.imgTable.item(erow,0)
            if twi.checkState() == QtCore.Qt.Checked:
                self.imgTable.removeRow(erow)
    
    
#        if retStat>0:
#            botText='Last word added: %s' % (wordDict['wordname'])
#        else:
#            botText='Error adding word: %s' % (wordDict['wordname'])
#        
    def imgUp(self):
        rc = self.imgTable.rowCount()
        seldrows = []
        outrows = range(rc)
        rowpair = []
        #deltaList = [0] * rc
        #Based on the rows selected, we will define a new ordering,
        #and then reassign the QTableWidgetItems via a temporary holding buffer
        for erow in outrows:
            if self.imgTable.item(erow,0).isSelected():
                seldrows.append(erow)
        if len(seldrows) > 0:
            
            #lets justdo this the easy way, max 1 row shifts
                minrow = seldrows[0]
                if minrow > 0:
                    rowpair = [minrow-1, minrow]
                elif len(seldrows) > 1:
                    if seldrows[1] > 1:
                        rowpair = [seldrows[1]-1, seldrows[1]]
        if len(rowpair) == 2:
            self.imgTable.item(rowpair[0],0).setSelected(True)
            self.imgTable.item(rowpair[1],0).setSelected(False)
            self.swapPair(rowpair)
            
    def imgDown(self):
        rc = self.imgTable.rowCount()
        seldrows = []
        outrows = range(rc)
        rowpair = []
        #deltaList = [0] * rc
        #Based on the rows selected, we will define a new ordering,
        #and then reassign the QTableWidgetItems via a temporary holding buffer
        for erow in outrows:
            if self.imgTable.item(erow,0).isSelected():
                seldrows.append(erow)
        if len(seldrows) > 0:        
                minrow = seldrows[-1]
                if minrow < (rc-1):
                    rowpair = [minrow, minrow+1]
                elif len(seldrows) > 1:
                    if seldrows[-2] < (rc-2):
                        rowpair [seldrows[-2], seldrows[-2] + 1]        
        if len(rowpair) == 2:
            self.imgTable.item(rowpair[1],0).setSelected(True)
            self.imgTable.item(rowpair[0],0).setSelected(False)
            self.swapPair(rowpair)
        
    def swapPair(self, rowpair):
        if len(rowpair) >= 2:
            rowbuf = [[],[]]
            for ecol in range(self.imgTable.columnCount()):
                rowbuf[0].append(self.imgTable.item(rowpair[0],ecol).text())
                rowbuf[1].append(self.imgTable.item(rowpair[1],ecol).text())
            rowbuf[0].append(self.imgTable.item(rowpair[0],0).checkState())
            rowbuf[1].append(self.imgTable.item(rowpair[1],0).checkState())
            
            for ecol in range(self.imgTable.columnCount()):
                self.imgTable.item(rowpair[0], ecol).setText(rowbuf[1][ecol])
                self.imgTable.item(rowpair[1], ecol).setText(rowbuf[0][ecol])
            self.imgTable.item(rowpair[0],0).setCheckState(rowbuf[1][-1])
            self.imgTable.item(rowpair[1],0).setCheckState(rowbuf[0][-1])
                    

    def addWord(self):
        wordDict={}
        wordDict['prefix']=str(self.preEntry.text()).strip()
        wordDict['wordname']=str(self.nameEntry.text()).strip()
        wordDict['language']=str(self.langEntry.currentText()).strip()
        wordDict['pos']=str(self.posEntry.currentText()).strip()
        syntext =str(self.synEntry.text()).strip()
        if ',' in syntext:
            wordDict['synlist']=syntext.split(',')
        else:
            wordDict['synlist']=syntext.split(';')
        tagtext=str(self.tagEntry.text()).strip()
        if ',' in tagtext:
            wordDict['taglist']=tagtext.split(',')
        else:
            wordDict['taglist']=tagtext.split(';')
        maxlong=0
        for t in wordDict['taglist']:
            cc=0
            for tc in t:
                if tc.isalnum():
                    cc+=1
            if cc>0:
                maxlong=cc
                break
        if maxlong < 1:
            wordDict['taglist']=""
            
        retStat=hpsyfuncs.addWordFromDict(wordDict)
        if retStat>0:
            botText='Last word added: %s' % (wordDict['wordname'])
        else:
            botText='Error adding word: %s' % (wordDict['wordname'])
        self.botLabel.setText(botText)

class addMasterContainer(QtGui.QWidget):
    def __init__(self, sparent = None, db=None, userName='biouser', password='biouser', opMode="addOnly", popDict = None):
        super(addMasterContainer, self).__init__()
        print('addMasterContainer initialized')        
        
        self.sparent = sparent
        self.db = db
        self.userName = userName
        self.password = password        
        self.opMode = opMode
        self.popDict = popDict

        titlestring = "herbQuery session with user: " + userName + " connected to " + db + " in "
        if popDict is not None:
            titlestring += "Edit Mode"
        else:
            titlestring += "Add Mode"
        self.setWindowTitle(titlestring)
        
        self.setMinimumHeight(700)
        self.setMinimumWidth(700)
        
        self.addMaster = addMaster(self, self.sparent)
        self.scrollArea = QtGui.QScrollArea()
        #self.scrollArea.setFixedHeight(300)
        self.scrollArea.setWidget(self.addMaster)     
        #self.scrollArea.setWidgetResizable(False)
        #self.scrollArea.widget.show()
                
        
        dummyLayout = QtGui.QVBoxLayout()
        dummyLayout.addWidget(self.scrollArea)        
        
        self.setLayout(dummyLayout)     
        
        #and finally, handle the case of preloading info for editing result of search query in edit mode
        if self.popDict is not None:
            self.addMaster.populate(self.popDict)
        
        self.show()

class regexWidget(QtGui.QWidget):
    def __init__(self):
        super(regexWidget, self).__init__()
        #print 'regexWidget initialized'
        self.createWidgets()
        self.layoutWidgets()
        
    def createWidgets(self):
        self.welcomeLabel=QtGui.QLabel('Regex Syntax: Tcl on PostgreSQL')
        self.reList=[['^','string beginning'],["$","string end"],["[a,b,c]","any of a, b, c"],["[1-4]","1, 2, 3, or 4"],["[^0-5]","NOT 0-5"],["|","logical or"],["a*","0 or more occurrences of 'a'"],["a+","1 or more occurrences of 'a'"],["a?","0 or 1 occurrences of 'a'"],["a{3}","exactly 3 occurrences of 'a'"],["a{2,5}","between 2 and 5 occurrences of 'a'"],[".","any single character"],["\d","and digit"],["\s","space"],["\w","any alnum"],["\D","any nondigit"],["\m","WORD beginning"],["\M","WORD end"],["(ab.)","subexpression: treat as char"],["""\\2""","back-reference to second subexpression"]]
        self.reTable=QtGui.QTableWidget()
        self.reTable.setColumnCount(2)
        self.reTable.setRowCount(len(self.reList))
        for i,item in enumerate(self.reList):
            qtwi = QtGui.QTableWidgetItem(item[0])
            qtwj = QtGui.QTableWidgetItem(item[1])
            self.reTable.setItem(i,0,qtwi)
            self.reTable.setItem(i,1,qtwj)
        self.reTable.resizeColumnsToContents()
    def layoutWidgets(self):
        thelayout=QtGui.QVBoxLayout()
        thelayout.addWidget(self.welcomeLabel)
        thelayout.addWidget(self.reTable)
        self.setLayout(thelayout)
        self.setGeometry(300,150,400,600)
 

class attemptDBCreateWidget(QtGui.QWidget):
    def __init__(self, parentW):
        super(attemptDBCreateWidget, self).__init__()

        self.parentW = parentW
        
        dbNameLabel = QtGui.QLabel('New Database Name:')
        self.dbNameEntry = QtGui.QLineEdit()
        self.dbNameEntry.setMinimumWidth(40)
        
        dbOwnerLabel = QtGui.QLabel('New Database Owner:')
        self.dbOwnerEntry = QtGui.QLineEdit('biouser')
        self.dbOwnerEntry.setMinimumWidth(40)        
        
        self.acButton = QtGui.QPushButton('Create Database')
        self.acButton.clicked.connect(self.attemptCreation)
        self.statusLabel = QtGui.QLabel("")
        
        hl1 = QtGui.QHBoxLayout()
        hl2 = QtGui.QHBoxLayout()   
        hl3 = QtGui.QHBoxLayout()  
        ml = QtGui.QVBoxLayout()
        
        hl1.addWidget(dbNameLabel)
        hl1.addWidget(self.dbNameEntry)
 
        hl2.addWidget(dbOwnerLabel)
        hl2.addWidget(self.dbOwnerEntry)
       
        hl3.addWidget(self.acButton)
        hl3.addWidget(self.statusLabel)

        ml.addLayout(hl1)
        ml.addLayout(hl2)
        ml.addLayout(hl3)

        self.setLayout(ml)        
    """
    scrape username and pword from 
    """    
    def attemptCreation(self):
        try:
            userName = self.parentW.userEntry.text()
            userName = str(userName).strip()            
            
            pw = self.parentW.pwEntry.text()
            pw = str(pw).strip()  
            
            print userName
            print pw            
            
            masterConn = hpsyfuncs.ppgConn(dbname='postgres', user=userName, host='localhost', passwd=pw)
        except:
            print('insufficient credentials for db creation')
            self.close()
            return -1
        try:
            masterConn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = masterConn.cursor()
            existsString = """ SELECT datname FROM pg_database;"""
            cur.execute(existsString)
            print "dbname redundancy_query executed"
            oldDBs = cur.fetchall()
            #print "foundDBs:"
            #print oldDBs
            
            newDBString = self.dbNameEntry.text()
            newDBString = str(newDBString).strip()
            newOwner = self.dbOwnerEntry.text()
            newOwner = str(newOwner).strip()
            print newDBString
            print newOwner

            nameExists = False
            print ('oldTuples:')
            for oldTuple in oldDBs:
                print oldTuple
                #print oldTuple[0]
                if newDBString == oldTuple[0]:
                    self.statusLabel.setText('Proposed database already exists. Please choose original name')
                    nameExists = True
                    return -2
            if not nameExists:
                
                makeDBString = ' CREATE DATABASE "' + newDBString + '";' 
                ownString= 'ALTER DATABASE "' + newDBString +  '" OWNER TO "' + newOwner + '";'  
                try:
                    cur.execute(makeDBString)
                    
                    #At this point, we are in the psql system as pseudosudo, 
                    #and so we actually go ahead and create the table structure
                    #but first we need to login to our new database, in order to define its table structure
                    
                    try:
                        newDBConn = hpsyfuncs.ppgConn(dbname=newDBString, user=userName, host='localhost', passwd=pw)
                        newDBCur = newDBConn.cursor()                   
                        hpsyfuncs.makePlantDBTables(newDBConn, newDBCur)
                        newDBConn.close()
                        print('new DB table instantiated')
                        masterConn.commit()
                    except:
                        print('Creation of new db table structure failed. check secondary login, and hpsyfuncs makeTables method')                        
                        
                        
                    try:
                        cur.execute(ownString)
                        masterConn.commit()
                        hpsyfuncs.ppgClose(masterConn)
                        print 'master Connection closes successfully'
                        
                        """now we just need to update the config file, and its associated information
                        stored in both parent widgets. we will do this slightly differently depending on whether 
                        ownership assignment was successful, or threw an error, in which case we leave postgres as owner
                        """
                        newTuple = (newDBString, newOwner, 'localhost', 'biouser')
                        self.updateConfigFile(newTuple)

                        return 1
                    except:
                        self.statusLabel.setText('failed newDB ownership assignment.')
                        hpsyfuncs.ppgClose(masterConn)       
                    #since the db still initialized OK, we still update the config file, but owner is postgres and pw is secret                        
                        newTuple = (newDBString, 'postgres', 'localhost', 'pp')
                        self.updateConfigFile(newTuple)
                        
                        return -3
                except:
                    self.statusLabel.setText('failed DB initialization string')
                    hpsyfuncs.ppgClose(masterConn)                    
                    return -4
        except:
            self.statusLabel.setText("unidentified DB initialization error")
            return -5

    def updateConfigFile(self, newTuple):
        print ('updateConfigFile initialized')
        configLines = self.parentW.parent.configLines
        configFile = self.parentW.parent.configFile
        
        goodUpdate = False
        for lineno, line in enumerate(configLines):
            print('line %d : %s', (lineno, line))
            kvsplit = line.split(':',1)
            if 'dbs' in kvsplit[0]:
                valstring = kvsplit[1].strip()
                if valstring[0] == '[' and valstring[-1] == ']' :
                    valList = eval(valstring)
                    valList.append(newTuple)
                    newvalstring = str(valList)
                    newdbline = kvsplit[0]+':'+newvalstring
                    configLines[lineno] = newdbline
                    goodUpdate = True
                    print 'goodUpdate of db List:'
                    print(newdbline)
                    break
                else:
                    print( 'unidentified formatting from configFile: %s', (configFile) )
                    print line
        # rewrite config file with our new info, and update parent widgets accordingly
        if goodUpdate:
            #should be redundant, since list stored as pointer
            self.parentW.parent.configLines = configLines
            f=open(configFile, 'w')
            for cline in configLines:
                lstring = cline + '\n'
                f.write(lstring)
            f.close()
            #now update the widgets... what all does this entail?            
            #actually should only need to update combo box
            newComboString = newTuple[0]
            self.parentW.dbCombo.addItem(newComboString)
            
        else:
            print 'unknown error. please check config file and reload program.'
        self.close()

"""
When a user specifies their desired action within the welcomeBox widget, 
this widget is generated, allowing the user to select the database that they would like to access

"""

class dbSelectWidget(QtGui.QWidget):
    def __init__(self, parent, mode):
        super(dbSelectWidget, self).__init__()
        #print 'dbSelectWidget initiated'
        self.parent = parent
        self.mode = mode

        mainLString = "Select database to " + self.mode + " herbs"
        self.mainLabel = QtGui.QLabel(mainLString)
        self.mainLabel.setFixedHeight(20)
    
        ulabel = QtGui.QLabel('Username:')
        plabel = QtGui.QLabel('Password:')
        self.userEntry = QtGui.QLineEdit('biouser')
        self.pwEntry = QtGui.QLineEdit('biouser')
        
        self.dbCombo = QtGui.QComboBox()
        self.proceedButton = QtGui.QPushButton('Proceed')
        self.dbs = []
        #populate dbCombo with known databases
        for eline in self.parent.configLines:
            print(eline)
            kv=eline.split(':', 1)
            key=kv[0].strip()
            if key == 'dbs':
                vals=kv[1].strip()
                print 'vals=' + vals
                if vals[0] == '[' and vals[-1] == ']' :
                    vals = eval(vals) # convert to list if valid list
                    for edb in vals:
                        self.dbs.append(edb)
                            
                break
        self.dbs.append( ('new', 'biouser', 'localhost', 'biouser'))
        for edb in self.dbs:
            self.dbCombo.addItem(edb[0])
        

        self.proceedButton.clicked.connect(self.attemptConnection)

        grid = QtGui.QGridLayout()
        #lowerhalf = QtGui.QVBoxLayout()
        masterlay = QtGui.QVBoxLayout()

        grid.addWidget(ulabel, 0, 0)        
        #grid.addWidget(ulabel, 1, 0)
        grid.addWidget(plabel, 1, 0)
        grid.addWidget(self.userEntry, 0, 1)
        grid.addWidget(self.pwEntry, 1, 1)
       


        
        #lowerhalf.addWidget(self.dbCombo)
        #lowerhalf.addWidget(self.proceedButton)
        
        masterlay.addWidget(self.mainLabel)
        masterlay.addWidget(self.dbCombo)
        masterlay.addLayout(grid)
        masterlay.addWidget(self.proceedButton)
        #masterlay.addLayout(lowerhalf)
        
        self.setLayout(masterlay)
        self.setGeometry(300,300,300,300)



        """
        Control flow of the attemptConnection function:
        1. Verify that the database exists. 
        If it does not exist, then we should initialize a new one using hpsyfuncs
        If it does exist, attempt a logon connection.
        
        """
        
    def attemptConnection(self):
        whichDB = self.dbCombo.currentIndex()
        # new db
        if whichDB == (len(self.dbs) - 1):
            self.acdbw = attemptDBCreateWidget(self)
            self.acdbw.show()
        else:
            
            dbname = str(self.dbCombo.itemText(whichDB)).strip()
            uname =  str(self.userEntry.text()).strip()           
            pw = str(self.pwEntry.text()).strip()
            print('db,uname,pw:(%s,%s,%s)' % (dbname, uname, pw))
            goodConn =True
            try:
                testConn = hpsyfuncs.ppgConn(dbname, uname, passwd=pw)
                if testConn != -1:
                    hpsyfuncs.ppgClose(testConn)
                else:
                    goodConn = False
            except:
                goodConn = False
                
            if goodConn:               
                if self.mode == "add":
                    adm = addMasterContainer(self.parent, dbname, uname, pw, "addOnly")
                    self.adm= adm
                    self.parent.addWidgets.append(adm)
                    self.adm.show()
                else:
                    if self.mode == "search":
                        qh = QHolder(self.parent, dbname, uname, pw, "search")
                    else:
                        qh = QHolder(self.parent, dbname, uname, pw, "edit")
                    self.qh = qh
                    self.parent.searchWidgets.append(qh)
                    self.qh.show()

                self.close()
            else:
                self.failbox = QtGui.QMessageBox(QtGui.QMessageBox.NoIcon, 'Connection Failure', 'Credentials did not result in successful logon.\nPlease double-check your username and password')
                self.failbox.show()
    
        
"""
This is the initial widget generated upon master script execition from terminal/interpreter
Its simplicity reflects the idea that there are only two tasks the user may engage in:
searches, and adds. Edits are handled as an available subroutine for handling
query results.


It is worth noting, that instantiation of this widget triggers a search for configuration information, primarily pertaining to
the location and login credentials of any/all databases. 
If no database records exist, the user will be prompted to initialize a database via the
intercepting dbSelectWidget (defined above) before proceeding to any search/add/edit functionality.

This initialization routine comprises the first ~50 lines of the instantiation script,
followed 


A button corresponds to both search and add, and clicking any of these triggers the appropriate widget generation

The welcomeBox widget is the central placeholder for the session, and is thus not destroyed after an option is selected,
so that a user can enjoy all of these functions within a single session
(and also access multiple databases within a single session, if so inclined.


"""        
class welcomeBox(QtGui.QWidget):
    def __init__(self):
        super(welcomeBox, self).__init__()
        self.searchWidgets = []
        self.addWidgets = []
        #default location for configHQ is the executable directory. Identify this directory.
        self.configFile=''
        execDir=os.path.realpath(sys.argv[0])
        execDir=execDir.rsplit('/', 1)
        execDir=execDir[0]
        """ if no hqConfig file is found, additionally check the directory from which the script was executed
        in case separate users have separate configs. 
        If not found, write a default config file in the executable directory. 
        
        """
        execDirFiles = os.listdir(execDir)
        if "hqConfig" in execDirFiles:
            self.configFile=execDir+'/hqConfig'
            f=open(self.configFile, 'r')
            self.configLines=f.readlines()
            f.close()
            
        else:
            userDir = os.getcwd()
            userDir = userDir.rsplit('/', 1)
            userDir = userDir[0]
            userDirFiles = os.listdir(userDir)
            if "hqConfig" in userDirFiles:
                self.configFile=userDir+'/hqConfig'
                f=open(self.configFile, 'r')
                configLines=f.readlines()
                f.close()
            else:
                dbDirLoc = execDir + '/db/'   
                imgDirLoc = execDir + '/imgs/'   
                try:
                    os.mkdir(dbDirLoc)
                except:
                    pass
                try:
                    os.mkdir(imgDirLoc)
                except:
                    pass
                    
                defaultParams = [('dbDir', './db/'),('imgDir', './imgs/'), ('dbs', [] )]                
                
                self.configFile=execDir+'/hqConfig'
                f=open(self.configFile, 'w')
                for dp in defaultParams:
                    dpstring = dp[0] + ':'+ str(dp[1]) + '\n'
                    f.write(dpstring)
                f.close()
                f=open(self.configFile, 'r')
                configLines = f.readlines()
        try:        
            self.configLines = configLines             
        except:
            pass
        
        #Now that configuration information has been located, we can proceed to setup the widget
            
        self.hiLabel=QtGui.QLabel('Welcome to herbQuery v0.1!')
        #self.hiLabel=QtGui.QLabel(str(self.configLines))
        self.searchButton=QtGui.QPushButton('Search Herbs')
        self.addButton=QtGui.QPushButton('Add Herbs')
        self.editButton=QtGui.QPushButton('Edit Herbs')        
        
#        self.searchButton.clicked.connect(self.searchAction)
#        self.addButton.clicked.connect(self.addAction)
#        self.editButton.clicked.connect(self.editAction)     
        self.searchButton.clicked.connect(self.selectDB_search)
        self.addButton.clicked.connect(self.selectDB_add)
        self.editButton.clicked.connect(self.selectDB_edit)          
        
        
        lay=QtGui.QVBoxLayout()
        lay.addWidget(self.hiLabel)        
        lay.addWidget(self.searchButton)
        lay.addWidget(self.addButton)
        lay.addWidget(self.editButton)        
        
        self.setLayout(lay)
        #self.setGeometry(300,300,200,200)

    def selectDB_search(self):
        #print('selectDB_search')
        self.sw=dbSelectWidget(self, "search")
        self.sw.show()
        
    def selectDB_add(self):
        self.sw=dbSelectWidget(self, "add")
        self.sw.show()        
        
    def selectDB_edit(self):
        self.sw=dbSelectWidget(self, "edit")
        self.sw.show()


#**** note these methods are currently unutilized, since search/add widget initialization
    #is handed after database selection by dbSelectWidget!
        
#    def searchAction(self):
#        self.qh=QHolder(self)
#        self.qh.show()
#    def addAction(self):
#        self.ab=addMasterContainer(self)
#        self.ab.show()
#    def editAction(self):
#        self.ed=QHolder()
#        self.ed.show()            
            
            
            
""""
This is the main loop triggered upon execition of the script.
It uses the standard PyQt4 structure and syntax.
"""            
def runWordQuery():
    app = QtGui.QApplication(sys.argv)
    wq = welcomeBox()
    #rect = QApplication.desktop().availableGeometry()
    #form.resize(int(rect.width() * 0.6), int(rect.height() * 0.9))
    wq.show()
    #app.exec_()   
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    runWordQuery() 