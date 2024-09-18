import os
from lxml import etree
import json
import pprint

# define directory
os.chdir('F:\DM\Mets Files Extracted') 

#define parser
parser = etree.XMLParser(collect_ids=False, remove_comments=True)

#define namespaces
ns = {
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'mets': 'http://www.loc.gov/METS/',
    'premis': 'info:lc/xmlns/premis-v2',
    'xlink': 'http://www.w3.org/1999/xlink',
    'mods': 'http://www.loc.gov/mods/v3',
    'rts': 'http://cosimo.stanford.edu/sdr/metsrights/',
    'blprocess': 'http://bl.uk/namespaces/blprocess',
    'bl': 'http://bl.uk/namespaces/bldigitized',
    'dc': 'http://purl.org/dc/terms/',
    'odrl': 'http://www.w3.org/ns/odrl/2/'
}

#xpaths
smLinkGrp_xpath = '/mets:mets/mets:structLink/mets:smLinkGrp'
phys_xpath = '/mets:mets/mets:structMap[@TYPE="PHYSICAL"]/mets:div/mets:div'
smLocatorLink_xpath = '/mets:mets/mets:structLink/mets:smLinkGrp/mets:smLocatorLink'
structMaps_xpath = '/mets:mets/mets:structMap[@TYPE="LOGICAL"]'


class CanvasItem:
    def __init__(self, item_id):
        self.id = item_id
        self.label = "Canvas"

    def __repr__(self):
        return f'{{"id": "{self.id}", "label": "{self.label}"}}'

    
class RangeItem:
    def __init__(self, element=None):
        if element is not None:
            self.id = element.get('ID')
            self.type = 'Range'
            self.label = f'{{"en": ["{element.get("LABEL")}"]}}' if element.get('LABEL') is not None else ''
            self.items = [ CanvasItem(canvas_index) for canvas_index in get_canvas_indexes_for_log_id(self.id) ]
        else:
            raise ValueError("input must be an lxml element")   
            
        self.items = self.items + [RangeItem(element=child) for child in element.findall('mets:div', namespaces=ns)]
        
    def __repr__(self):
        return f'{{"id": "{self.id}", "type": "{self.type}", "label": {self.label}, "items": {self.items}}}'


#takes a log id and returns a list of canvas indexes for that log
def get_canvas_indexes_for_log_id(log_id):
    
    smLinkGrp = root.xpath(smLocatorLink_xpath + f'[@xlink:href="#{log_id}"]', namespaces=ns)[0].getparent()
    
    if log_id == 'log0':
        return []
    else:
        phys_list = [ smLocatorLink.attrib['{http://www.w3.org/1999/xlink}href'] for smLocatorLink in smLinkGrp.findall('mets:smLocatorLink', namespaces=ns)[1:] ]

        canvas_list = []

        for phys_id in phys_list:
            phys_id = phys_id.replace('#', '')
            phys_e = root.xpath(phys_xpath + f'[@ID="{phys_id}"]', namespaces=ns)
            canvas_index = phys_e[0].attrib["ORDER"]
            canvas_list.append(canvas_index)

        return canvas_list


#main function
def get_structures(root):
    structMap = root.xpath(structMaps_xpath, namespaces=ns)[0]
    structures = []
    for e in structMap:
        structures.append(RangeItem(e))
    return structures


# run on single file
filename = 'egerton_ms_613mets.xml'
tree = etree.parse(filename, parser)
root = tree.getroot()
structures = get_structures(root)
structure = structures[0]
print(structure)

# # directory
# for troot, dirs, files in os.walk('.'):
#     for filename in files:
#         print(filename)
#         tree = etree.parse(filename, parser)
#         root = tree.getroot()
#         structures = get_structures(root)
#         structure = structures[0]
#         print(structure)
#         print('.........................')