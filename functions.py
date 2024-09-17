import os
from lxml import etree
from collections import Counter
import pprint

pp = pprint.PrettyPrinter(indent=4)

# define directory
os.chdir('F:\DM\Mets Files Extracted') 

#define parser
parser = etree.XMLParser(collect_ids=False, remove_comments=True)

#define namespace dict
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

#returns the text contents of the description element 
def get_description(root):
    description_path = '/mets:mets/mets:amdSec/mets:sourceMD/mets:mdWrap/mets:xmlData/blprocess:processMetadata/blprocess:description'
    description = root.xpath(desc_path, namespaces=ns)
    return description[0].text

#returns a dict of original image filenames : canvas labels
def map_canvas_labels(root):
    label_dict = {}

    imagefile_xpath = '/mets:mets/mets:fileSec/mets:fileGrp[@USE="Original"]/mets:fileGrp[@USE="Image"]/mets:file'
    fptr_xpath = '/mets:mets/mets:structMap/mets:div/mets:div/mets:fptr'

    #Iterate over image files referenced in METS
    for file in root.xpath(imagefile_xpath, namespaces=ns):
        file_id = file.attrib['ID']

        #get the original file location
        location = file[0].attrib['{http://www.w3.org/1999/xlink}href']

        #find fptr element with file_id as attrib
        fptr = root.xpath(fptr_xpath + f'[@FILEID="{file_id}"]', namespaces=ns)[0]

        #get its parent
        parent = fptr.getparent()

        #get label from parent
        label = parent.attrib['ORDERLABEL']

        #push location:label pair to dict
        label_dict[location] = label

    return label_dict

#returns rights statement
def get_rights(root):
    rights_xpath = '/mets:mets/mets:amdSec/mets:rightsMD/mets:mdWrap/mets:xmlData/odrl:policy/dc:rights'
    rights = root.xpath(rights_xpath, namespaces=ns)
    return rights[0].text

#returns a dict with range label as key and a list of canvas indexes as value
def get_ranges(root):

    range_dict = {}
    phys_xpath = '/mets:mets/mets:structMap[@TYPE="PHYSICAL"]/mets:div/mets:div'
    log_xpath = '/mets:mets/mets:structMap[@TYPE="LOGICAL"]/mets:div/mets:div'

    smLinkGrps = root.xpath("/mets:mets/mets:structLink/mets:smLinkGrp", namespaces=ns)
    if len(smLinkGrps) > 1:
        #iterate over Link Groups if there's more than 1 (first is for whole entity so skip)
        for smLinkGrp in smLinkGrps[1:]:
            
            #get log id and use it to look up log label
            log_id = smLinkGrp[0].attrib['{http://www.w3.org/1999/xlink}href']
            log_id = log_id.replace('#', '')
            log = root.xpath(log_xpath + f'[@ID="{log_id}"]', namespaces=ns)
            if not len(log):
                print('not found')
                return
            range_label = log[0].attrib["LABEL"]
            range_dict[range_label] = []
            
            #iterate through phys IDs for that log group and look up its order value (i.e. index)
            for smLocatorLink in smLinkGrp[1:]:
                if '{http://www.w3.org/1999/xlink}href' in smLocatorLink.attrib:
                    phys_id = smLocatorLink.attrib['{http://www.w3.org/1999/xlink}href']
                    phys_id = phys_id.replace('#', '')
                    phys = root.xpath(phys_xpath + f'[@ID="{phys_id}"]', namespaces=ns)
                    index = phys[0].attrib["ORDER"]
                    
                    #add to dict for that log group
                    range_dict[range_label].append(index)

    return range_dict

# define structure class that is the same as IIIF spec

class Structure:
    def __init__(self, element=None, id: str = None, type: str = None, label: str = None, items: list = None):
        if element is not None:
            # If an lxml element is provided, extract its attributes
            self.id = element.get('ID')
            self.type = element.get('type')
            self.label = element.get('LABEL', "")  # Default to empty string if label is not provided
            self.items = [
                Structure(element=child) for child in element.findall('mets:div', namespaces=ns)
            ]
        else:
            # Otherwise, use the provided arguments
            if type not in ['range', 'canvas']:
                raise ValueError("type must be either 'range' or 'canvas'")
            self.id = id
            self.type = type
            self.label = label if label is not None else ""
            self.items = items if items is not None else []

    def add_item(self, structure):
        if not isinstance(structure, Structure):
            raise TypeError("Items must be instances of the Structure class")
        self.items.append(structure)
        
    def __repr__(self):
        return f"id={self.id}, type={self.type}, label={self.label}, items={self.items})"


def get_structures(root):
    structMaps_xpath = '/mets:mets/mets:structMap[@TYPE="LOGICAL"]'
    structMap = root.xpath(structMaps_xpath, namespaces=ns)[0]
    structures = []
    
    for e in structMap:
        structures.append(Structure(e))
        
    #iterate over structures and lookup canvas index for each image
        
    return structures


#use
#e.g.:
# for troot, dirs, files in os.walk('.'):
#     for file in files:
    
#         tree = etree.parse(file, parser)
#         root = tree.getroot()

#         rights = get_rights(root)