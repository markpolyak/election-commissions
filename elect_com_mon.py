import logging
import argparse
import requests
import sys
# import time
import csv
from bs4 import BeautifulSoup


base_url = 'http://www.st-petersburg.vybory.izbirkom.ru/region/st-petersburg'
reserve_url = 'http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg/ik_r/'
reserve_tree_url = 'http://www.st-petersburg.vybory.izbirkom.ru/st-petersburg/ik_r_tree/'

# extract a list of members of given election commission (any level)
def get_members(commission):
    members_list = []
    if not commission['id']:
        logging.critical("Commission id not found. Raw data is: %s", commission)
        sys.exit('No commission id')
        
    params = {
        'action': 'ik',
        'vrn': commission['id']
    }

    response = requests.get(base_url, params=params, verify=False)

    if not response.ok:
        logging.critical("Bad response for query with params %s", params)
        sys.exit(f"Request can not be executed. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'lxml')
    tables = [
        [
            [
                td.get_text(strip=True) for td in tr.find_all('td')
            ]
            for tr in table.find_all('tr')
        ]
        for table in soup.find_all('table')
    ]

    # table[0] is a placeholder
    # table[1] is a navigation block
    # table[2] has the data
    for names in tables[2]:
        if len(names) == 4:
            members_list.append(
                {
                    'commission_name': commission['name'],
                    'parent_commission': commission['parent'],
                    'member_name': names[1],
                    'member_status': names[2],
                    'delegated_by': names[3]
                }
            )
    logging.debug("Found %d members of election commission %s", len(members_list), commission['name'])
    return members_list

def get_members_reserve(commission):
    members_list = []
    if not commission['id']:
        logging.critical("Commission id not found. Raw data is: %s", commission)
        sys.exit('No commission id')
        
    params = {}    
    compose_url = reserve_url + commission['id']
    logging.debug("Composed URL: %s", compose_url)
    response = requests.get(compose_url, params=params, verify=False)
    response.encoding = response.apparent_encoding
    
    if not response.ok:
        logging.critical("Bad response for query with params %s", params)
        sys.exit(f"Request can not be executed. Status code: {response.status_code}")

    soup = BeautifulSoup(response.text, 'lxml')
    tables = [
        [
            [
                td.get_text(strip=True) for td in tr.find_all('td')
            ]
            for tr in table.find_all('tr')
        ]
        for table in soup.find_all('table')
    ]

    # table[0] is a placeholder
    # table[1] is a navigation block
    # table[2] has the data
    for names in tables[0]:
        if len(names) == 4:
            members_list.append(
                {
                    'commission_name': commission['name'],
                    'parent_commission': commission['parent'],
                    'member_name': names[1],
                    'member_status': names[2],
                    'delegated_by': names[3]
                }
            )
    logging.debug("Found %d members of election commission %s", len(members_list), commission['name'])
    return members_list

# Retrieve the election commissions tree.
# Tree structure is assumed to be the following:
# level 0 (root) - regional election commission;
# level 1 - territory-level election commission;
# level 2 - district-level election commission.
def get_reserve(second_level_limit):
    params = {
        'first': '1',
        'id2': '',
        'id': '#'
        }
    response = requests.get(reserve_tree_url, params=params, verify=False)

    if response.ok:
        decoded_json = response.json()
    else:
        logging.critical("Bad response for query with params %s", params)
        sys.exit(f"Request can not be executed. Status code: {response.status_code}")

    root_element = {
        'name': decoded_json[0]['text'],
        'parent': '',
        'id': decoded_json[0]['id']
    } 
    logging.info("Parsing root element")
    
    members_list = get_members_reserve(root_element)
    counter = 0
    
    child_counter = 0
    for child in decoded_json[0]['children']:
        commission = {
            'id': child['id'],
            'name': child['text'],
            'parent': root_element['name']
        }
        logging.info("Parsing members of %s", commission['name'])
        members_list.extend(get_members_reserve(commission))  
        
        params = {
            
            'first': '1',
            'id2': commission['id'],
            'id': '#'
        }

        # limit number of parsed territory level commissions (for debug purposes only)
        if second_level_limit and counter >= second_level_limit:
            break
        counter += 1

        # get list of lower level commissions
        compose_url = reserve_tree_url + commission['id']
        logging.debug("Composed URL: %s", compose_url)        
        response = requests.get(compose_url, params=params, verify=False)

        if response.ok:
            decoded_json = response.json()
            
            for child_item in decoded_json[0]['children'][child_counter]['children']:
                child_commission = {
                    'id': child_item['id'],
                    'name': child_item['text'],
                    'parent': commission['name'],
                }
                # TODO: might need to insert a delay here
                # time.sleep( 0.5 if int(child_commission['id']) % 10 != 0 else 3)

                # parse members of lower level commission
                logging.info("Parsing members of %s", child_commission['name'])
                members_list.extend(get_members_reserve(child_commission))
                
        else:
            logging.critical("Bad response for query with params %s", params)
            sys.exit(f"Request can not be executed. Status code: {response.status_code}")
        child_counter += 1
    return members_list        

def get_commissions(second_level_limit):
    members_list = []
    params = {
        'action': 'ikTree',
        'region': '78',
        'vrn': '27820001006425', # election commission internal id
        'id': '#'                # root tree element
    }

    response = requests.get(base_url, params=params, verify=False)
  
    if response.ok:
        decoded_json = response.json()
    else:
        logging.critical("Bad response for query with params %s", params)
        sys.exit(f"Request can not be executed. Status code: {response.status_code}")

    root_element = {
        'name': decoded_json[0]['text'],
        'parent': '',
        'id': decoded_json[0]['id']
    } 
    logging.info("Parsing root element")
    members_list = get_members(root_element)

    counter = 0

    for child in decoded_json[0]['children']:
        commission = {
            'id': child['id'],
            'name': child['text'],
            'parent': root_element['name']
        }
        logging.info("Parsing members of %s", commission['name'])
        members_list.extend(get_members(commission))
        
        params = {
            'action': 'ikTree',
            'region': '78',
            'vrn': commission['id'],
            'onlyChildren': 'true',
            'id': commission['id']
        }

        # limit number of parsed territory level commissions (for debug purposes only)
        if second_level_limit and counter >= second_level_limit:
            break
        counter += 1

        # get list of lower level commissions
        response = requests.get(base_url, params=params, verify=False)

        if response.ok:
            decoded_json = response.json()
            for child_item in decoded_json:
                child_commission = {
                    'id': child_item['id'],
                    'name': child_item['text'],
                    'parent': commission['name'],
                }
                # TODO: might need to insert a delay here
                # time.sleep( 0.5 if int(child_commission['id']) % 10 != 0 else 3)

                # parse members of lower level commission
                logging.info("Parsing members of %s", child_commission['name'])
                members_list.extend(get_members(child_commission))
        else:
            logging.critical("Bad response for query with params %s", params)
            sys.exit(f"Request can not be executed. Status code: {response.status_code}")
    return members_list


def main():
    parser = argparse.ArgumentParser(description= "Election commision member list parser")
    parser.add_argument('-l', '--limit', type=int, action='store', default=None, help='maximum number of territory-level commissions to parse (useful for debug purposes)')
    parser.add_argument('-o', '--output', action='store', default='members.tsv', help='output file name')
    parser.add_argument('-m', '--mode', action='store', default='comission', help='Using: -m *mode* Example: -m reserve Default:comission (comission, reserve)')
    parser.add_argument('-r', '--routput', action='store', default='reserve.tsv', help='Using: -r *filename.tsv* Example: -r reserve.tsv Default:reserve.tsv')
    parser.add_argument('--loglevel', '--log', action='store', default='info', help='logging level (debug, info, warning, error, critical)')
    
    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=numeric_level)

    logging.info('Arguments %s', args)
    
    if args.mode == 'reserve':
        members_list = get_reserve(args.limit);
        args.output = args.routput
    else:
        members_list = get_commissions(args.limit)
    
    logging.info("Saving members list to file ...")
    with open(args.output, 'w', newline='', encoding='utf-8') as out_file:
        tsv_writer = csv.DictWriter(out_file, fieldnames=['commission_name', 'parent_commission', 'member_name', 'member_status', 'delegated_by'], delimiter='\t') # , quotechar='', quoting=csv.QUOTE_NONE # doublequote=False, escapechar=''
        tsv_writer.writeheader()
        tsv_writer.writerows(members_list)
    
    logging.info("All done!")


if __name__ =="__main__":
    main()
