from bots.botsconfig import ID, MAX, MIN

syntax = {
    'field_sep': ',',
    'quote_char': '"',
    'charset': 'us-ascii',
    'merge': True,
    'noBOTSID': True,
}


structure = [
    {ID: 'root', MIN: 1, MAX: 999999},
]


recorddefs = {
    'root': [
        ['BOTSID', 'C', 4, 'AN'],
        ['customer_id', 'M', 6, 'AN'],
        ['po_number', 'M', 25, 'AN'],
        ['item_id', 'M', 48, 'AN'],
        ['serial_number', 'M', 48, 'AN'],
        ['customer_part_number', 'C', 48, 'AN'],
    ],
}
