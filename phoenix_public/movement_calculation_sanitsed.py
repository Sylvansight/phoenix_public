from __future__ import print_function
import xml.etree.ElementTree as ET
import networkx as nx

def quadToA(aNum):
    #convert 1-4 to A-D and return
    return{'1':'A'
           ,'2':'B'
           ,'3':'G'
           ,'4':'D'}[aNum]

def generateSingleSystemNodes(sysNum,G):
    for quad in ('A','B','G','D'):
        for ring in range(1,16):
            G.add_node(str(sysNum)+'_' + quad + str(ring),{'type':0})
    return G

def generateSingleSystemEdges(sysNum,G,ISR):
    sysNum = str(sysNum)
    for ring in range(1,16):
        ring = str(ring)
        G.add_edge(sysNum +'_'+'A' + ring,sysNum +'_'+'B'+ ring,'AB',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'B' + ring,sysNum +'_'+'A'+ ring,'BA',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'A' + ring,sysNum +'_'+'D'+ ring,'AD',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'D' + ring,sysNum +'_'+'A'+ ring,'DA',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'B' + ring,sysNum +'_'+'G'+ ring,'BG',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'G' + ring,sysNum +'_'+'B'+ ring,'GB',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'G' + ring,sysNum +'_'+'D'+ ring,'GD',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        G.add_edge(sysNum +'_'+'D' + ring,sysNum +'_'+'G'+ ring,'DG',
                   {'weight':int(ring)*ISR,'type':'OQ-ring'})
        for quad in ('A','B','G','D'):
            if not ring == '15':
                G.add_edge(str(sysNum)+ '_' + quad + str(ring),str(sysNum) +'_'+
                            quad +str((int(ring) + 1)),'IO',
                            {'weight':ISR,'type':'OQ-quad'})
    for ring in range(15,1,-1):
        for quad in ('A','B','G','D'):
            if not ring == '1':
                G.add_edge(str(sysNum)+ '_' + quad + str(ring),str(sysNum) +'_'+
                            quad +str((int(ring) - 1)),'OI',
                            {'weight':ISR,'type':'OQ-quad'})
              
    return G

def extractSysFromFileDir(aFile,G,ISR,jumpTU,orbitTime):
    #extract system links and distances from systems.xmlS
    #return list of [sourceSystem, destingationSystem, distance (1-4)]
    sysLinks = {}
    tree = ET.parse(aFile)
    root = tree.getroot()
    for each in root:
        for system in each:
            G = generateSingleSystemNodes(system.attrib['id'],G)
            G = generateSingleSystemEdges(system.attrib['id'],G,ISR)
            for cb in system:
                if cb.tag == 'link':
                    if system.attrib['id'] in sysLinks.keys():
                        sysLinks[system.attrib['id']].append(
                            [cb.attrib['sys_id'],cb.attrib['dist']])
                    else:
                        sysLinks[system.attrib['id']] = []
                        sysLinks[system.attrib['id']].append(
                            [cb.attrib['sys_id'],cb.attrib['dist']])
                elif cb.tag == 'cbody':
                    oqNode = system.attrib['id'] + '_' + quadToA(
                        cb.attrib['quad']) + cb.attrib['ring']
                    
                    if not cb.attrib['type'] in ('5','6'): 
                        cbNode = system.attrib['id'] + '_' + cb.attrib['id']
                        G.add_node(cbNode,{'type':cb.attrib['type']})
                        G.add_edge(cbNode,oqNode, 'CO',
                                   {'weight':int(orbitTime),'type':'Orbit'})
                        G.add_edge(oqNode,cbNode, 'OC',
                                   {'weight':int(orbitTime),'type':'Orbit'})
                    
                    else:
                        # nav hazard (5 or 6), all edges IN get weight:400
                        hazEdges = G.in_edges(oqNode,data=True)
                        for  u,v,d  in hazEdges:
                            d['weight'] = 400   
                        # set type for oqnode
                        G.node[oqNode]['type'] = cb.attrib['type']
    return {'sysLinks':sysLinks}

def flattenSystems(aDir):
    #recurse through system links list, to flatten
    # ie each system connected to all single jump destinations with weight of 1 
    # Venice connects to Yank etc
    # load results into set in numerical order to save deduping later
    # looks a bit ugly - probably a more elegant way of doing this.
    flatList = set()
    #### direct links '''
    for k,v in aDir.items():
      for link in v:
        jumpsLeft = 4
        flatList.add((k,link[0]))
        jumpsLeft -= int(link[1])
#indirect 1 ###################################     
        if jumpsLeft > 0:
          tempJumpsLeft = jumpsLeft
          for sublink1 in aDir[link[0]]:
            jumpsLeft = tempJumpsLeft
            if not sublink1[0] == k:
              if jumpsLeft - int(sublink1[1]) > -1 :
                flatList.add((k,sublink1[0]))
                jumpsLeft -= int(sublink1[1])
                tempJumpsLeft2 = jumpsLeft
# indirect 2  #####################              
                if jumpsLeft > 0:
                  for sublink2 in aDir[sublink1[0]]:
                    jumpsLeft = tempJumpsLeft2
                    if not sublink2[0] == k:
                      if jumpsLeft - int(sublink2[1]) > -1 :
                        flatList.add((k,sublink2[0]))
                        jumpsLeft -= int(sublink2[1])
                        tempJumpsLeft3 = jumpsLeft
# last loop ##############################################
                        if jumpsLeft > 0:
                          for sublink3 in aDir[sublink2[0]]:
                            jumpsLeft = tempJumpsLeft3
                            if not sublink3[0] == k:
                              if jumpsLeft - int(sublink3[1]) > -1 :
                                flatList.add((k,sublink3[0]))                                                                                             
    return flatList

def addLinksBetweenSystems(G,aList,jumpTU):
    # aList is full of tuples of systems ('123','456')
    # go through them, for each pair generate edges for all OQ in rings 10-15
    
    #############################
    # extra weight for in / out in certain systems
    originalJumpTU = jumpTU
    jumpMods = getJumpSystemMultipliers()
    
    
    for each in aList:
        #print(each)
        s1 = each[0]
        s2 = each[1]
        for quad in ('A','B','G','D'):
            for ring in range(10,16):
                jumpTU = originalJumpTU
                attrDict = {'type':'Jump','weight':jumpTU}
                ring = str(ring)
                startNode = s1 +'_' + quad + ring
                endNode = s2 + '_' + quad + ring
                edgeKey = s1 + '|'+ s2
                if s1 in jumpMods.keys():
                    jumpTU *= jumpMods[s1]['jumpOut']
                    attrDict = {'type':'Jump','weight':jumpTU,'TU_override':jumpTU}
                G.add_edge(startNode, endNode,edgeKey, attrDict)
                edgeKey = s2 + '|'+ s1
                if s2 in jumpMods.keys():
                    jumpTU *= jumpMods[s2]['jumpIn']
                    attrDict = {'type':'Jump','weight':jumpTU,'TU_override':jumpTU}
                G.add_edge(endNode, startNode,edgeKey, attrDict)
    return G

def adjustJumpWeightsIntoHazards(G):
    for each in G.nodes_iter(data=True):
        #print(each[1]['type'])
        if int(each[1]['type']) in (5,6):
            hazEdges = G.in_edges(each[0],data=True)
            for  u,v,d  in hazEdges:
                d['weight'] = 400   
    return G

def moreWeightForPinchPoints(G):
    # amend this function if you wish to avoid  certain routes
    # for example, to avoid routing via through ring 10 of venice
    # 
    
    # example usage:
    #    badOQ = ['124_A10','124_B10','124_G10','124_D10']
     
    badOQ = ['124_G9']
     
    for each in G.nodes_iter():
        if each in badOQ:
            pinchpointEdges = G.in_edges(each,data=True)
            for u,v,d in pinchpointEdges:
                d['weight'] = 250
    return G
        
def getJumpSystemMultipliers():
    # add systems with non-standard jump multipliers to this dict
    sysJumpMod = {'124': {'jumpIn': 1.0
                         ,'jumpOut': 1.0
                            }
                }

    return sysJumpMod
    

#               

def addSGLinks(G):
    # common SG
    soloSG = '121_8434'
    noctollisSG = '61_5069'
    valhallaSG = '103_1600'
    
  
    #####
    # weight 200 so not prioritised over slightly slower jumps
    attrDict = {'type':'SG','weight':200}
    G.add_edge(soloSG,valhallaSG,'121|103',attrDict)
    G.add_edge(valhallaSG,soloSG,'103|121',attrDict)
    G.add_edge(valhallaSG,noctollisSG,'103|61',attrDict)
    G.add_edge(noctollisSG,valhallaSG,'61|103',attrDict)
    G.add_edge(soloSG,noctollisSG,'121|61',attrDict)
    G.add_edge(noctollisSG,soloSG,'61|121',attrDict)
    return G

def addWHLinks(G):    
    # Caribbean <-> Varitang
    # caribbeanWG = '6_3318'
    # varitangWH = '9_7637'
    # attrDict = {'type':'WH','weight':200}
    # G.add_edge(caribbeanWG,varitangWH,'6|9',attrDict)
    # G.add_edge(varitangWH,caribbeanWG,'9|6',attrDict)

    # yank -> halo
    yankWH = '146_3102'
    agripetaWH = '198_9890'
    attrDict = {'type':'WH','weight':200}
    G.add_edge(yankWH,agripetaWH,'146|198',attrDict)
    G.add_edge(agripetaWH,yankWH,'198|146',attrDict)       
    
    ## london <-> crossley
    ## unstable and dangerous due to AM
    ## more weight
    #londonWH = '41_565'
    #crossleyWH = '99_2231'
    #attrDict = {'type':'WH','weight':5000}
    #G.add_edge(londonWH,crossleyWH,'41|99',attrDict)
    #G.add_edge(crossleyWH,londonWH,'99|41',attrDict)     
    
    
    return G

    
def allSystems(ISR,jumpTU,orbitTime,useSG,useWH):
    G=nx.MultiDiGraph()
    x = extractSysFromFileDir('systems.xml',G,ISR,jumpTU,orbitTime)['sysLinks']
    sysEdges = flattenSystems(x)
    G = addLinksBetweenSystems(G,sysEdges,jumpTU)
    G = adjustJumpWeightsIntoHazards(G)
    G = moreWeightForPinchPoints(G)
    if str(useSG) == '1':
        G = addSGLinks(G)
    if str(useWH) == '1':
        G = addWHLinks(G)
    #for each in G.nodes(data=True):
    #   print(each)
    
    return G

def calculateTUfromEdges(G,edgesinpath,ISR,jumpTU,orbitTime,officerBonus,
                         efficiency,whNav):
    # Does not yet account for systems with multipliers for jump in/out
    TU = 0
    eff = float(100)/float(efficiency)
    #print('eff: {}'.format(eff))
    jump = int((int(jumpTU) - (int(officerBonus)*int(jumpTU)/100)) * eff)
    #print('jump: {}'.format(jump))
    if whNav == 1:
        whTU = 50
    else:
        whTU = 100
    
    for u,v in edgesinpath:
        if 'TU_override' in G[u][v].items()[0][1].keys():
            TU += G[u][v].items()[0][1]['TU_override']
        else:
            moveType = G[u][v].items()[0][1]['type']
            if moveType == 'Jump':
                TU += jump
            if moveType == 'OQ-quad':
                TU += int(float(ISR)*eff)
            if moveType == 'OQ-ring':
                r = u.split('_')[1][1:]
                TU += int(float(r)*float(ISR)*eff)
                #print(str(int(float(r)*float(ISR)*eff)))
            if moveType == 'Orbit':
                TU += int(float(orbitTime)*eff)
            if moveType == 'WH':
                TU += int(float(whTU)*eff)
            if moveType == 'SG':
                TU += int(float(100)*eff)        
    #print('TU: {}'.format(TU))
    return TU


def getPath(startSysNum,startSysOQ,endSysNum,endSysOQ,ISR,jumpTU,
                    orbitTime,efficiency,officerBonus,useSG,useWH,whNav):
    # startSysNum - system of origin
    # startSysOQ  - A15, B3 or a known body number like '975'
    # endSysNum - destination
    # endSysOQ  - A15, B3 or a known body number like '975'
    # ISR drives (1 to 4)
    # tuJump - ('50' or '100'
    # orbitTime - ships orbital speed
    # efficiency - (1 to 150)
    # officerBonus - (0,5,10,15 or 20)
    # useSG - 0 = no, 1 = yes
    # useWH - 0 = no, 1 = yes
    # whNav - 0 = no, 1 = yes
    
    G = allSystems(ISR,jumpTU,orbitTime,useSG,useWH)
    start = str(startSysNum) + '_' + str(startSysOQ)
    end = str(endSysNum) + '_' + str(endSysOQ)
    try:
        path = nx.dijkstra_path(G,source=start,target=end)
        edgesinpath=zip(path[0:],path[1:])
        totalWeight = 0
        TU = calculateTUfromEdges(G,edgesinpath,ISR,jumpTU,orbitTime
                                    ,officerBonus,efficiency,whNav)
        for u,v in edgesinpath:
            totalWeight += G[u][v].items()[0][1]['weight']
            #print(u,v,G[u][v])
        return{'TU':TU,'route':edgesinpath,'G':G}
    except nx.exception.NetworkXNoPath:
        return -1

if __name__ == '__main__':
    from time import time
    ########################################################################
    startSysNum = '146'
    startSysOQ = 'G15'   # OQ or planetID
    endSysNum = '124'
    endSysOQ = 'G15'    # OQ or planetID
    ISR = 4
    jumpTU = 50
    orbitTime = 20
    officerBonus = 0 #0,5,10,15,20
    efficiency = 100
    useSG = 0
    useWH = 1
    whNav = 1
    #########################################################################
    start = time()
    x = getPath(startSysNum, startSysOQ, endSysNum, endSysOQ, ISR, jumpTU, orbitTime, efficiency, officerBonus,useSG,useWH,whNav)
    end =  time() - start
    if not x == -1:
        for u,v in x['route']:
            print(u,v,x['G'][u][v].items())
        print('------------------------------')
        print('TU: {}'.format(x['TU']))
    else:
        print('No Route Found')
    print('------------------------------')
    print('time taken: {}'.format(end))
    
    
