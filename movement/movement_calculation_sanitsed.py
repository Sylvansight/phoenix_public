from __future__ import print_function
import xml.etree.cElementTree as ET
import networkx as nx

def quadToA(aNum):
    # convert 1-4 to A-D and return
    return{'1':'A'
           , '2':'B'
           , '3':'G'
           , '4':'D'}[aNum]

def generateSingleSystemNodes(sysNum, G):
    for quad in ('A', 'B', 'G', 'D'):
        for ring in range(1, 16):
            aNode = str(sysNum) + '_' + quad + str(ring)
            G.add_node(aNode, type=0)
    return G

def generateSingleSystemEdges(sysNum, G, ISR):
    sysNum = str(sysNum)
    for ring in range(1, 16):
        ring = str(ring)
        G.add_edge(sysNum + '_' + 'A' + ring, sysNum + '_' + 'B' + ring, key='AB',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'B' + ring, sysNum + '_' + 'A' + ring, key='BA',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'A' + ring, sysNum + '_' + 'D' + ring, key='AD',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'D' + ring, sysNum + '_' + 'A' + ring, key='DA',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'B' + ring, sysNum + '_' + 'G' + ring, key='BG',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'G' + ring, sysNum + '_' + 'B' + ring, key='GB',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'G' + ring, sysNum + '_' + 'D' + ring, key='GD',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        G.add_edge(sysNum + '_' + 'D' + ring, sysNum + '_' + 'G' + ring, key='DG',
                   weight=(int(ring) * ISR),values={'type':'OQ-ring'})
        for quad in ('A', 'B', 'G', 'D'):
            if not ring == '15':
                G.add_edge(str(sysNum) + '_' + quad + str(ring), str(sysNum) + '_' + 
                            quad + str((int(ring) + 1)), key='IO',
                            weight=ISR,values={'type':'OQ-quad'} )
    for ring in range(15, 1, -1):
        for quad in ('A', 'B', 'G', 'D'):
            if not ring == '1':
                G.add_edge(str(sysNum) + '_' + quad + str(ring), str(sysNum) + '_' + 
                            quad + str((int(ring) - 1)), key='OI',
                            weight=ISR, values={'type':'OQ-quad'})
              
    return G

def extractSysFromFileDir(aFile, G, ISR, jumpTU, orbitTime):
    # extract system links and distances from systems.xmlS
    # return list of [sourceSystem, destingationSystem, distance (1-4)]
    sysLinks = {}
    tree = ET.parse(aFile)
    root = tree.getroot()
    for each in root:
        for system in each:
            G = generateSingleSystemNodes(system.attrib['id'], G)
            G = generateSingleSystemEdges(system.attrib['id'], G, ISR)
            for cb in system:
                if cb.tag == 'link':
                    if system.attrib['id'] in sysLinks.keys():
                        sysLinks[system.attrib['id']].append(
                            [cb.attrib['sys_id'], cb.attrib['dist']])
                    else:
                        sysLinks[system.attrib['id']] = []
                        sysLinks[system.attrib['id']].append(
                            [cb.attrib['sys_id'], cb.attrib['dist']])
                elif cb.tag == 'cbody':
                    oqNode = system.attrib['id'] + '_' + quadToA(
                        cb.attrib['quad']) + cb.attrib['ring']
                    
                    if not cb.attrib['type'] in ('5', '6'): 
                        cbNode = system.attrib['id'] + '_' + cb.attrib['id']
                        G.add_node(cbNode, type=cb.attrib['type'])
                        G.add_edge(cbNode, oqNode, name='CO',
                                   weight=int(orbitTime), values={'type':'Orbit'})
                        G.add_edge(oqNode, cbNode, name='OC',
                                    weight=int(orbitTime), values={'type':'Orbit'})
                    
                    else:
                        # nav hazard (5 or 6), all edges IN get weight:400
                        hazEdges = G.in_edges(oqNode, data=True)
                        for  u, v, d  in hazEdges:
                            d['weight'] = 400   
                        # set type for oqnode
                        G.node[oqNode]['type'] = cb.attrib['type']
    return {'sysLinks':sysLinks}

def flattenSystems(aDir):
    # recurse through system links list, to flatten
    # ie each system connected to all single jump destinations with weight of 1 
    # Venice connects to Yank etc
    # load results into set in numerical order to save deduping later
    # looks a bit ugly - probably a more elegant way of doing this.
    flatList = set()
    #### direct links '''
    for k, v in aDir.items():
      for link in v:
        jumpsLeft = 4
        flatList.add((k, link[0]))
        jumpsLeft -= int(link[1])
#indirect 1 ###################################     
        if jumpsLeft > 0:
          tempJumpsLeft = jumpsLeft
          for sublink1 in aDir[link[0]]:
            jumpsLeft = tempJumpsLeft
            if not sublink1[0] == k:
              if jumpsLeft - int(sublink1[1]) > -1 :
                flatList.add((k, sublink1[0]))
                jumpsLeft -= int(sublink1[1])
                tempJumpsLeft2 = jumpsLeft
# indirect 2  #####################              
                if jumpsLeft > 0:
                  for sublink2 in aDir[sublink1[0]]:
                    jumpsLeft = tempJumpsLeft2
                    if not sublink2[0] == k:
                      if jumpsLeft - int(sublink2[1]) > -1 :
                        flatList.add((k, sublink2[0]))
                        jumpsLeft -= int(sublink2[1])
                        tempJumpsLeft3 = jumpsLeft
# last loop ##############################################
                        if jumpsLeft > 0:
                          for sublink3 in aDir[sublink2[0]]:
                            jumpsLeft = tempJumpsLeft3
                            if not sublink3[0] == k:
                              if jumpsLeft - int(sublink3[1]) > -1 :
                                flatList.add((k, sublink3[0]))                                                                                             
    return flatList

def addLinksBetweenSystems(G, aList, jumpTU):
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
                    jumpTU *= jumpMods[s1]['jumpIn']
                    
                    attrDict = {'type':'Jump','TU_override':jumpTU}
                    
                
                edgeKey = s2 + '|'+ s1
                if s2 in jumpMods.keys():
                    jumpTU *= jumpMods[s2]['jumpOut']
                    attrDict = {'type':'Jump','TU_override':jumpTU}
                    
                   
                G.add_edge(endNode, startNode,key=edgeKey,weight=jumpTU, values=attrDict)
    return G


def adjustJumpWeightsIntoHazards(G):
    for each in G.nodes(data=True):
        # print(each[1]['type'])
        if int(each[1]['type']) in (5, 6):
            hazEdges = G.in_edges(each[0], data=True)
            for  u, v, d  in hazEdges:
                d['weight'] = 400   
    return G

def moreWeightForPinchPoints(G):
    # amend this function if you wish to avoid  certain routes
    # for example, to avoid routing via through ring 10 of venice
    # 
    
    # example usage:
    #    badOQ = ['124_A10','124_B10','124_G10','124_D10']
     
    badOQ = ['30_G10','30_A10','30_B10','30_D10']
     
    for each in G.nodes():
        if each in badOQ:
            pinchpointEdges = G.in_edges(each, data=True)
            for u, v, d in pinchpointEdges:
                d['weight'] = 500
    return G
        
def getJumpSystemMultipliers():
    # add systems with non-standard jump multipliers to this dict
    sysJumpMod = {'124': {'jumpIn': 1.0
                         , 'jumpOut': 1.0
                            }
                }

    return sysJumpMod
    



def addSGLinks(G):
    # common SG
    soloSG = '121_8434'
    noctollisSG = '61_5069'
    valhallaSG = '103_1600'
    
    wt = 200
    #####
    # weight 200 so not prioritised over slightly slower jumps
    attrDict = {'type':'SG'}
    G.add_edge(soloSG, valhallaSG, key='121|103', weight=wt,values=attrDict)
    G.add_edge(valhallaSG, soloSG, key='103|121',  weight=wt,values=attrDict)
    G.add_edge(valhallaSG, noctollisSG, key='103|61',  weight=wt,values=attrDict)
    G.add_edge(noctollisSG, valhallaSG, key='61|103', weight=wt,values=attrDict)
    G.add_edge(soloSG, noctollisSG, key='121|61', weight=wt,values=attrDict)
    G.add_edge(noctollisSG, soloSG, key='61|121', weight=wt,values=attrDict)
    return G

def addWHLinks(G):    
    wt = 500
    attrDict = {'type':'WH'}
    # Caribbean <-> Varitang
    # caribbeanWG = '6_3318'
    # varitangWH = '9_7637'
    
    # G.add_edge(caribbeanWG,varitangWH,'6|9',values=attrDict)
    # G.add_edge(varitangWH,caribbeanWG,'9|6',values=attrDict)

    # yank -> halo
    yankWH = '146_3102'
    agripetaWH = '198_9890'
    
    G.add_edge(yankWH, agripetaWH, key='146|198',weight=wt, values = attrDict)
    G.add_edge(agripetaWH, yankWH, key='198|146',weight=wt, values = attrDict)      
    
    # # london <-> crossley
    # # unstable and dangerous due to AM
    # # more weight
    # londonWH = '41_565'
    # crossleyWH = '99_2231'
    # G.add_edge(londonWH,crossleyWH,'41|99',values ={'type':'WH','weight':5000})
    # G.add_edge(crossleyWH,londonWH,'99|41',values ={'type':'WH','weight':5000})     
    
    
    return G

    
def allSystems(ISR, jumpTU, orbitTime, useSG, useWH):
    G = nx.MultiDiGraph()
    x = extractSysFromFileDir('systems.xml', G, ISR, jumpTU, orbitTime)['sysLinks']
    sysEdges = flattenSystems(x)
    G = addLinksBetweenSystems(G, sysEdges, jumpTU)
    G = adjustJumpWeightsIntoHazards(G)
    G = moreWeightForPinchPoints(G)
   
    if str(useSG) == '1':
        G = addSGLinks(G)
    if str(useWH) == '1':
        G = addWHLinks(G)
    # for each in G.nodes(data=True):
    #   print(each)
    
    return G

def calculateTUfromEdges(G, edgesinpath, ISR, jumpTU, orbitTime, officerBonus,
                         efficiency, whNav):
    # Does not yet account for systems with multipliers for jump in/out
    TU = 0
    eff = float(100) / float(efficiency)
    # print('eff: {}'.format(eff))
    jump = int((int(jumpTU) - (int(officerBonus) * int(jumpTU) / 100)) * eff)
    # print('jump: {}'.format(jump))
    if whNav == 1:
        whTU = 50
    else:
        whTU = 100
    
    for u, v in edgesinpath:
        #print(G[u][v].items()[0][1])
        if 'TU_override' in G[u][v].items()[0][1]['values'].keys():
            TU += G[u][v].items()[0][1]['values']['TU_override']
        else:
            #print(G[u][v].items()[0][1])
            moveType = G[u][v].items()[0][1]['values']['type']
            if moveType == 'Jump':
                TU += jump
            if moveType == 'OQ-quad':
                TU += int(float(ISR) * eff)
            if moveType == 'OQ-ring':
                r = u.split('_')[1][1:]
                TU += int(float(r) * float(ISR) * eff)
                # print(str(int(float(r)*float(ISR)*eff)))
            if moveType == 'Orbit':
                TU += int(float(orbitTime) * eff)
            if moveType == 'WH':
                TU += int(float(whTU) * eff)
            if moveType == 'SG':
                TU += int(float(100) * eff)        
    # print('TU: {}'.format(TU))
    return TU


def getPath(startSysNum, startSysOQ, endSysNum, endSysOQ, ISR, jumpTU,
                    orbitTime, efficiency, officerBonus, useSG, useWH, whNav):
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
    
    G = allSystems(ISR, jumpTU, orbitTime, useSG, useWH)
    start = str(startSysNum) + '_' + str(startSysOQ)
    end = str(endSysNum) + '_' + str(endSysOQ)
    try:
        path = nx.dijkstra_path(G, source=start, target=end)
        edgesinpath = zip(path[0:], path[1:])
        totalWeight = 0
        TU = calculateTUfromEdges(G, edgesinpath, ISR, jumpTU, orbitTime
                                    , officerBonus, efficiency, whNav)
        for u, v in edgesinpath:
            totalWeight += G[u][v].items()[0][1]['weight']
            # print(u,v,G[u][v])
        return{'TU':TU, 'route':edgesinpath, 'G':G}
    except nx.exception.NetworkXNoPath:
        return -1

if __name__ == '__main__':
    from time import time
    ########################################################################
    startSysNum = '121'
    startSysOQ = 'B15'  # OQ or planetID
    endSysNum = '124'
    endSysOQ = 'B15'  # OQ or planetID
    ISR = 4
    jumpTU = 50
    orbitTime = 20
    officerBonus = 0  # 0,5,10,15,20
    efficiency = 100
    useSG = 1
    useWH = 1
    whNav = 1
    #########################################################################
    start = time()
    x = getPath(startSysNum, startSysOQ, endSysNum, endSysOQ, ISR, jumpTU, orbitTime, efficiency, officerBonus, useSG, useWH, whNav)
    end = time() - start
    if not x == -1:
        for u, v in x['route']:
            print(u, v, x['G'][u][v].items())
        print('------------------------------')
        print('TU: {}'.format(x['TU']))
    else:
        print('No Route Found')
    print('------------------------------')
    print('time taken: {}'.format(end))
    
    
