from .order_lines import JsonOrdersToCsv


def main(inn, out, **kwargs):
    return JsonOrdersToCsv().main(inn=inn, out=out, **kwargs)

