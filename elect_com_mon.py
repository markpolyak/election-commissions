import logging
import argparse
import requests
import sys
import time
import csv
from bs4 import BeautifulSoup

base_url = 'http://www.st-petersburg.vybory.izbirkom.ru/region/st-petersburg'


# extract a list of members of given election commission (any level)
def parse_commission(commission):
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
    commission_data = []
    tables = [
        [
            [
                td.get_text(strip=True) for td in tr.find_all('td')
            ]
            for tr in table.find_all('tr')
        ]
        for table in soup.find_all('table')
    ]

    for info in soup.find_all('p'):
        commission_data.append(info.get_text(strip=True))

    # commission_data[1] is address
    # commission_data[3] is phone number
    # commission_data[4] is fax
    # commission_data[5] is email
    # commission_data[6] is deadline
    # commission_data[7] is vote address (may not appear for spbizbirkom or TIK)
    # commission_data[9] is voteroom phone number (may not appear for spbizbirkom or TIK)

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
    return members_list, commission_data


# Retrieve the election commissions tree.
# Tree structure is assumed to be the following:
# level 0 (root) - regional election commission;
# level 1 - territory-level election commission;
# level 2 - district-level election commission.
def get_commissions(second_level_limit):
    params = {
        'action': 'ikTree',
        'region': '78',
        'vrn': '27820001006425',  # election commission internal id
        'id': '#'  # root tree element
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
    commission_data = []
    members_list = []
    members_list, commission_temp = parse_commission(root_element)
    commission_data.append(commission_temp)
    counter = 0

    for child in decoded_json[0]['children']:
        commission = {
            'id': child['id'],
            'name': child['text'],
            'parent': root_element['name']
        }
        logging.info("Parsing members of %s", commission['name'])
        members_temp, commission_temp = parse_commission(commission)
        members_list.extend(members_temp)
        commission_data.append(commission_temp)

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
                time.sleep(0.1)

                # parse members of lower level commission
                logging.info("Parsing members of %s", child_commission['name'])
                members_temp, commission_temp = parse_commission(child_commission)
                members_list.extend(members_temp)
                commission_data.append(commission_temp)
        else:
            logging.critical("Bad response for query with params %s", params)
            sys.exit(f"Request can not be executed. Status code: {response.status_code}")
    return members_list, commission_data


def main():
    parser = argparse.ArgumentParser(description="Election commision member list parser")
    parser.add_argument('-l', '--limit', type=int, action='store', default=None,
                        help='maximum number of territory-level commissions to parse (useful for debug purposes)')
    parser.add_argument('-o', '--output', action='store', default='members.tsv', help='output file name')
    parser.add_argument('-c', '--commissions', action='store', default='commissions.tsv',
                        help='commissions output file name')
    parser.add_argument('--loglevel', '--log', action='store', default='info',
                        help='logging level (debug, info, warning, error, critical)')

    args = parser.parse_args()

    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=numeric_level)

    logging.info('Arguments %s', args)

    members_list, commission_data = get_commissions(args.limit)
    logging.info("Saving members list to file ...")
    with open(args.output, 'w', newline='', encoding='utf-8') as out_file:
        tsv_writer = csv.DictWriter(out_file,
                                    fieldnames=['commission_name', 'parent_commission', 'member_name', 'member_status',
                                                'delegated_by'],
                                    delimiter='\t')  # , quotechar='', quoting=csv.QUOTE_NONE # doublequote=False, escapechar=' '
        tsv_writer.writeheader()
        tsv_writer.writerows(members_list)
    logging.info("Writing members done!")

    logging.info("Saving commission data to file ...")
    with open(args.commissions, 'w', newline='', encoding='utf-8') as out_commissions:
        out_commissions.write(
            "address" + "\t" + "phone_number" + "\t" + "fax" + "\t" + "email" + "\t" + "expiration_date" + "\t" + "voteroom_address" + "\t" + "voteroom_phone_number" + "\n")
        for row in commission_data:
            try:
                out_commissions.write(
                    row[1].split(':')[1] + "\t" + row[3].split(':')[1] + "\t" + row[4].split(':')[1] + "\t" +
                    row[5].split(':')[1] + "\t" + row[6].split(':')[1] + "\t" + row[7].split(':')[1] + "\t" +
                    row[9].split(':')[1] + "\n")
            except IndexError:  # regional and territory-level commissions dont have voterooms
                out_commissions.write(
                    row[1].split(':')[1] + "\t" + row[3].split(':')[1] + "\t" + row[4].split(':')[1] + "\t" +
                    row[5].split(':')[1] + "\t" + row[6].split(':')[1] + "\n")
    out_commissions.close()
    logging.info("Writing commissions done!")


if __name__ == "__main__":
    main()

