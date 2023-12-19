from oks.elements.operation import OperationElement
import oks


class RawMaterial(OperationElement):
    TYPE = oks.RAW_MATERIAL

    def __init__(self, **kwargs):
        self.name = ""
        self.quantity = 0.0
        self.row = ("name", "quantity")
        self.proportion = 0.0
        OperationElement.__init__(self, **kwargs)

    def __str__(self):
        return ""
