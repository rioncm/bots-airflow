from botscore.constants import ID, LEVEL, MAX, MIN

from . import segments_004010_ls_850

recorddefs = segments_004010_ls_850.recorddefs


syntax = {
    'version': '00401',
    'functionalgroup': 'PO',
}


structure = [
    {ID: 'ST', MIN: 1, MAX: 1, LEVEL: [
        {ID: 'BEG', MIN: 1, MAX: 1},
        {ID: 'REF', MIN: 2, MAX: 99999},
        {ID: 'FOB', MIN: 0, MAX: 99999},
        {ID: 'ITD', MIN: 0, MAX: 99999},
        {ID: 'DTM', MIN: 1, MAX: 10},
        {ID: 'TD5', MIN: 0, MAX: 12},
        {ID: 'N9', MIN: 0, MAX: 1000, LEVEL: [
            {ID: 'MSG', MIN: 0, MAX: 1000},
        ]},
        {ID: 'N1', MIN: 2, MAX: 200, LEVEL: [
            {ID: 'N3', MIN: 0, MAX: 2},
            {ID: 'N4', MIN: 0, MAX: 99999},
            {ID: 'PER', MIN: 0, MAX: 99999},
        ]},
        {ID: 'PO1', MIN: 1, MAX: 100000, LEVEL: [
            {ID: 'PID', MIN: 0, MAX: 1000},
            {ID: 'TD5', MIN: 0, MAX: 12},
            {ID: 'MAN', MIN: 0, MAX: 1000},
            {ID: 'N1', MIN: 0, MAX: 1},
        ]},
        {ID: 'CTT', MIN: 0, MAX: 1},
        {ID: 'SE', MIN: 1, MAX: 1},
    ]},
]
