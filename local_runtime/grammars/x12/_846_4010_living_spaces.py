from botscore.constants import ID, LEVEL, MAX, MIN

from . import segments_004010_ls_846

recorddefs = segments_004010_ls_846.recorddefs


syntax = {
    'envelope': 'x12',
    'version': '00401',
    'functionalgroup': 'IB',
}


structure = [
    {ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
        {ID: 'BIA', MIN: 1, MAX: 1},
        {ID: 'N1', MIN: 1, MAX: 200},
        {ID: 'LIN', MIN: 1, MAX: 10000, LEVEL: [
            {ID: 'QTY', MIN: 1, MAX: 99},
            {ID: 'DTM', MIN: 1, MAX: 10},
        ]},
        {ID: 'CTT', MIN: 1, MAX: 1},
        {ID: 'SE', MIN: 1, MAX: 1},
    ]},
]
