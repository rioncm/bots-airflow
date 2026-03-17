from botscore.constants import ID, MAX, MIN

syntax = {
    'pass_all': True,
}


structure = [
    {ID: 'root', MIN: 1, MAX: 999999},
]


recorddefs = {
    'root': [
        ['BOTSID', 'C', 4, 'AN'],
        ['order_id', 'C', 20, 'AN'],
        ['sku', 'C', 48, 'AN'],
        ['quantity', 'C', 10, 'AN'],
    ],
}

