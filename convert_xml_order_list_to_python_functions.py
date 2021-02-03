# converts phoenix xml order_data file into a collection of python order functions
# point order_data_file at the order_data.xml file
# output_file is the new file to create (give it a .py extension) 



import xml.etree.cElementTree as ET




def clean_attrib(name_str):
    name_str = name_str.replace(' ', '_').replace('/', '_').replace('%', '')
    name_str = name_str.replace('(', '').replace(')', '').replace("'","").replace('from','from_').replace('.','')
    return name_str

def convert_xml(order):
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
        param_datatype = each.attrib['datatype']

        order_dct['params'].append({'name': param_name, 'infotype': param_infotype, 'datatype': param_datatype})

    return order_dct

def write_order(f, order_dict):
    # first line is going to be def name (param, param):
    param_count = len(order_dict['params'])
    p = ''
    for each in order_dict['params']:
        p += each['name'] + ', '
    p = p[:-2]

    def_str = 'def {name}({p}):'.format(name=order_dict['name'],p=p)
    desc_str = """  \"\"\"{}\"\"\"""".format(order_dict['description'])
    id_str = '  id = {}'.format(order_dict['id'])
    typeflag_str = '  typeflag = {}'.format(order_dict['typeflag'])
    tu_str = '  tus = {}'.format(order_dict['tus'])
    if p == '':
        return_list = '[id]'
    else:
        return_list = '[id, {p}]'.format(p=p)
    return_str = '  return {}'.format(return_list)

    # print(def_str)
    # print(desc_str)
    # print(id_str)
    # print(typeflag_str)
    # print(tu_str)
    # print(return_str)
    full_string = def_str + '\n'
    full_string += desc_str + '\n\n'
    full_string += id_str + '\n'
    full_string += typeflag_str + '\n'
    full_string += tu_str + '\n\n'
    full_string += return_str + '\n\n\n'

    print(full_string)

    f.write(full_string)


def main(read_file, write_file):

    wf = open(write_file, 'w', encoding='utf-8', errors='replace')

    # parse xml, get an element and send for conversion
    tree = ET.parse(read_file)
    root = tree.getroot()

    for t in root[1]:
        order_dict = convert_xml(t)
        #for k, v in order_dict.items():
        #    print(k, v)
        write_order(wf, order_dict)


if __name__ == '__main__':
    order_data_file = 'order_data.xml'
    output_file = 'phoenix_orders_test.py'
    main(order_data_file, output_file)
