from bots.botsconfig import ID, MAX, MIN

syntax = {
    'pass_all': True,
}


structure = [
    {ID: 'root', MIN: 1, MAX: 999999},
]


recorddefs = {
    'root': [
        ['BOTSID', 'C', 4, 'AN'],
        ['customer_id', 'C', 20, 'AN'],
        ['location_id', 'C', 10, 'AN'],
        ['item_sku', 'C', 48, 'AN'],
        ['description', 'C', 80, 'AN'],
        ['price', 'C', 20.4, 'N'],
        ['sku_status', 'C', 1, 'AN'],
        ['sku_upc', 'C', 14, 'AN'],
        ['customer_sku', 'C', 48, 'AN'],
    ],
}
