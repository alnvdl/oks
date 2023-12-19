from core.db.row import Row
from core.output import *
import oks


class Company(Row):
    TYPE = oks.COMPANY

    def __init__(self, **kwargs):
        self.name = ""
        self.type_ = 0
        self.full_name = ""
        self.address = ""
        self.neighborhood = ""
        self.city = ""
        self.state = ""
        self.zip_code = ""
        self.phone = ""
        self.fax = ""
        self.email = ""
        self.cnpj = ""
        self.ie = ""
        self.notes = ""
        self.row = (
            "name",
            "type_",
            "full_name",
            "address",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "phone",
            "fax",
            "email",
            "cnpj",
            "ie",
            "notes",
        )

        Row.__init__(self, **kwargs)

    def make_output(self):
        company = Section("company_{0}".format(self.name), self.name)

        full_name = StringData("full_name", "Razão social", self.full_name)
        company.add_child(full_name)

        type_ = StringData("type", "Tipo", oks.COMPANY_TYPES_DESC[self.type_])
        company.add_child(type_)

        full_address = (self.address + ", " + self.neighborhood).strip(", ")
        address = StringData("address", "Endereço", full_address)
        company.add_child(address)

        zip_code = StringData("zip_code", "CEP", self.zip_code)
        company.add_child(zip_code)

        phone = StringData("phone", "Telefone(s)", self.phone)
        company.add_child(phone)

        fax = StringData("fax", "Fax", self.fax)
        company.add_child(fax)

        cnpj = StringData("cnpj", "CNPJ", self.cnpj)
        company.add_child(cnpj)

        ie = StringData("ie", "IE", self.ie)
        company.add_child(ie)

        notes = StringData("notes", "Observações", self.notes)
        company.add_child(notes)

        return company
