from __future__ import print_function, division
import xml.etree.cElementTree as ET
from operator import itemgetter



def stripInfoFromTemplate(aTemplate):

    template = aTemplate.split(';')

    thisShip = {}
    internals = {}
    headers = template[0].split(',')
    thisShip['templateID'] = headers[0].split('=')[1]
    thisShip['templateName'] = headers[1]
    thisShip['hulls'] = headers[2]
    thisShip['hullType'] = headers[3]
    thisShip['armourPlates'] = headers[4]
    thisShip['armourType'] = headers[5]
    internals[thisShip['hullType']] = thisShip['hulls']
    internals[thisShip['armourType']] = thisShip['armourPlates']
    
    for i in range (1,len(template)):
        x = template[i].strip().replace('ShipItem=','').split(',')
        if len(x) == 2:
            internals[x[1]] = x[0]
    
    thisShip['internals'] = internals
    
    return thisShip



def getRawMats(breakdown,root):
    results = []
    for k,v in breakdown['internals'].items():
        x = getRawMatSingleItem(k,v,root)
        if not x == -1:
            results.append(x)
        for k1,v1 in x[5].items():
            y = getRawMatSingleItem(k1,float(v1) * int(x[4]),root)
            if not y == -1:
                results.append(y)

        
    return results
        
def getRawMatSingleItem(k,v,root):
    item_num = k
    itype = ''
    name = ''
    prod = ''
    amount = v
    rawMats = {}
    for rt in root:
        for item in rt:
            if str(item.attrib['key']) == item_num:
                for i in item.iter('Name'):
                    name = i.attrib['value']
                for i in item.iter('Prod'):
                    prod = i.attrib['value']            
                for i in item.iter('itype'):
                    itype = i.attrib['value']
                if not itype == '49':
                    for i in item.iter('RawMaterials'):
                        for y in i:
                            for x in y:
                                #print(x.tag,x.attrib)
                                if x.tag == 'Item':
                                    rmItem = x.attrib['value']
                                if x.tag == 'Quantity':
                                    rmCount = x.attrib['value']
                            rawMats[rmItem]=rmCount
        if not itype == '49':
            return [name,item_num,itype,prod,amount,rawMats]
        else:
            return -1
                    
                
def multiplyOresByItemCount(aList):
    newList = []
    for each in aList:

        itemCount = int(each[4])
        each[5].update((x, float(y)*itemCount) for x, y in each[5].items())
        try:
            each.extend([itemCount * int(each[3])])
            newList.append(each)
        except ValueError:
            # probably means no armour :o
            pass

    return newList

def sumAllOre(aList):
    results = {}
    for each in aList:
        if not 'production' in results.keys():
            results['production'] = int(each[6])
        else:
            results['production'] += int(each[6])
            
        for ore,v in each[5].items():
            if not ore in results.keys():
                results[ore] = float(v) 
            else:
                results[ore] += float(v)
    return results

def getItemNameType(item_num,root):

    name = ''
    itype = ''
    for rt in root:
        for item in rt:
            if str(item.attrib['key']) == item_num:
                for i in item.iter('Name'):
                    name = i.attrib['value']
                for i in item.iter('itype'):
                    itype = i.attrib['value']
                if not name == '' and not itype == '':
                    return {'name':name,'itype':itype}    

def humaniseIt(aDict,root):
    results = []
    for k,v in aDict.items():
        if not k == 'production':
            x = getItemNameType(k,root)
            #print(x)
            name = x['name']
            itype = x['itype']
            if itype == '49':
                results.append([name,k,v])
        else:
            results.append([k,'',v])
    results = sorted(results,key=itemgetter(int(1)))
    return results
        

def main(template,item_file_xml):
    from time import time
    start = time()
    breakdown = stripInfoFromTemplate(template)
    itemFile = ET.parse(item_file_xml)

    root = itemFile.getroot()
    x = getRawMats(breakdown,root)
    for dsf in x:
        print(dsf)
    y = multiplyOresByItemCount(x)
    z = sumAllOre(y)
    readable = humaniseIt(z,root)
    print('------------------------')
    for each in readable:
        print(each)
    column = 2
    print('------------------------')
    print(sum(row[column] for row in readable))
    print('time taken: {} secs'.format(time()-start))
if __name__ == '__main__':

    template = """Ship=3,Barge,50,60,0,0,25003;
ShipItem=1,100;
ShipItem=2,103;
ShipItem=5,155;
ShipItem=1,175;
ShipItem=30,180;
ShipItem=5,131;
ShipItem=10,160;"""

    item_file = 'items.xml'
    main(template,item_file)
