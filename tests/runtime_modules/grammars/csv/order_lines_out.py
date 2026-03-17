from botscore.constants import ID, MAX, MIN

syntax = {
    'field_sep': ',',
    'quote_char': '"',
    'charset': 'utf-8',
    'merge': True,
    'noBOTSID': True,
}


structure = [
    {ID: 'root', MIN: 1, MAX: 999999},
]


recorddefs = {
    'root': [
        ['BOTSID', 'C', 4, 'AN'],
        ['order_id', 'M', 20, 'AN'],
        ['sku', 'M', 48, 'AN'],
        ['quantity', 'M', 10, 'AN'],
    ],
}

