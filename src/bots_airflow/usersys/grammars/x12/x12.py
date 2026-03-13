from .envelope import recorddefs, structure, nextmessage


syntax = {
    'version': '00403',
}


def getmessagetype(editype, messagetype):
    if messagetype in {'850', '850004010', '85000401'}:
        return '850_ls_inbound4010'
    return None
