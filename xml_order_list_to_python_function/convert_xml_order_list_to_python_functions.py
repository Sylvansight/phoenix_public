# converts phoenix xml order_data file into a collection of python order functions
# point order_data_file at the order_data.xml file
# output_file is the new file to create (give it a .py extension)

import xml.etree.cElementTree as ET


def clean_attrib(name_str):
    # replace characters which break function names or parameters
    # return clean string
    name_str = name_str.replace(' ', '_').replace('/', '_').replace('%', '')
    name_str = name_str.replace('(', '').replace(')', '').replace("'","").replace('from','from_').replace('.','')
    return name_str

def convert_param_datatype(datatype):
    # convert parameter datatype to python datatype
    # will be used for typing hints so user can see if nexus expects "1" or 1, True or "True" etc.
    #
    # 0 = integer
    # 1 = float
    # 2 = "string" - final version (uploaded) must have the quotes? test
    # 3 = bool strings ('True' / 'False'). upload with quotes, single quotes confirmed to work.
    #print(datatype)

    if datatype == "0":
        hint = 'int'
    elif datatype == "1":
        hint = 'float'
    elif datatype == "2":
        hint = 'str'
    elif datatype == "3":
        hint = 'bool'
    else:
        print('unknown datatype')
        quit(3)
    return hint



def convert_xml(order):
    # extract data from xml element and place into a dictionary
    # return dictionary
    order_dct = {}

    order_dct['name'] = clean_attrib(order.attrib['name'].lower())
    order_dct['id'] = order.attrib['id']
    order_dct['typeflag'] = order.attrib['typeflag']
    order_dct['tus'] = order.attrib['tus']

    order_dct['description'] = order[0].text
    order_dct['params'] = []

    for each in order[1]:
        param_name = clean_attrib(each.attrib['name'].lower())
        param_infotype = each.attrib['infotype']
        param_datatype = convert_param_datatype(each.attrib['datatype'])

        order_dct['params'].append({'name': param_name, 'infotype': param_infotype, 'datatype': param_datatype})

    return order_dct


def write_order(f, order_dict):
    # build a python function line by line
    # write the completed function to file
    # first line is going to be def name (param, param): etc
    p = ''
    r = ''
    for each in order_dict['params']:

        p += '{name}: {hint}, '.format(name=each['name'], hint=each['datatype'])
        r += each['name'] + ', '
    # print(p)
    p = p[:-2]
    r = r[:-2]

    def_str = 'def {name}({p}):'.format(name=order_dict['name'],p=p)
    print(def_str)
    desc_str = """  \"\"\"{}\"\"\"""".format(order_dict['description'])
    id_str = '  id = {}'.format(order_dict['id'])
    typeflag_str = '  typeflag = {}'.format(order_dict['typeflag'])
    tu_str = '  tus = {}'.format(order_dict['tus'])
    if r == '':
        return_list = '[id]'
    else:
        return_list = '[id, {list}]'.format(list=r)
    return_str = '  return {}'.format(return_list)

    full_string = def_str + '\n'
    full_string += desc_str + '\n\n'
    full_string += id_str + '\n'
    full_string += typeflag_str + '\n'
    full_string += tu_str + '\n\n'
    full_string += return_str + '\n\n\n'
    f.write(full_string)


def main(read_file, write_file):

    wf = open(write_file, 'w', encoding='utf-8', errors='replace')

    # parse xml, get an element and send for conversion.
    # write the converted data to file
    tree = ET.parse(read_file)
    root = tree.getroot()

    for t in root[1]:
        order_dict = convert_xml(t)
        write_order(wf, order_dict)


if __name__ == '__main__':
    order_data_file = 'order_data.xml'
    output_file = 'phoenix_orders_test.py'
    main(order_data_file, output_file)
