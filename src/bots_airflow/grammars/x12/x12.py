from .envelope import nextmessage, recorddefs, structure


syntax = {
    'version': '00403',
}


def getmessagetype(editype, messagetype):
    if messagetype in {'846', '846004010', '84600401'}:
        return '846_4010_living_spaces'
    if messagetype in {'850', '850004010', '85000401'}:
        return '850_ls_inbound4010'
    return None
