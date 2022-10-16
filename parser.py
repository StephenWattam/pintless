

from lark import Lark

json_parser = Lark(r"""
    expression: magnitude unit
               | magnitude unit_product
               | magnitude unit_division

    magnitude: SIGNED_NUMBER
    unit: CNAME

    unit_product: unit ["*" unit]+
    unit_division: unit "/" unit
                 | unit_product "/" unit
                 | unit "/" unit_product

    %import common.CNAME
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS

    """, start='expression')

text = '24 kilograms'
tree = json_parser.parse(text)
print(tree.pretty())
import code; code.interact(local=locals())