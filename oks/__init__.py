import datetime
import locale

from core.db.backends.sqlite import INTERNAL_DATE_FORMAT as SQLITE_DATE_FORMAT

# Modes
MODE_MAIN = 0
MODE_REPORT = 1

# Report options
REPORT_OPTION_BOOL = 0
REPORT_OPTION_DATE = 1
REPORT_OPTION_TEXT = 2
DATE_RANGE_OPTIONS = [
    (
        "start_date",
        REPORT_OPTION_DATE,
        "Período de",
        datetime.date.today() - datetime.timedelta(weeks=4),
    ),
    ("end_date", REPORT_OPTION_DATE, "Até", datetime.date.today()),
]

# Element types
COMPANY = 0
ITEM = 1
OPERATION = 2
PRODUCT = 3
PRODUCTION_ITEM = 4
RAW_MATERIAL = 5
EXCHANGE_ITEM = 6
TRANSACTION = 7

# IO
INPUT = 1
OUTPUT = 0

# Types for categorization
TYPE_CUSTOMER_COMPANY = 0
TYPE_SUPPLIER_COMPANY = 1
TYPE_CUSTOMER_AND_SUPPLIER_COMPANY = 2
TYPE_COMPANIES_ALL = 3

TYPE_COMMON_ITEM = 0
TYPE_RAW_MATERIAL = 1
TYPE_PRODUCTION_ITEM = 2
TYPE_SERVICE = 3
TYPE_ITEMS_ALL = 4

TYPE_UNIT_PC = 0
TYPE_UNIT_KG = 1
TYPE_UNIT_L = 2
TYPE_UNITS_ALL = 3

TYPE_SALE_OPERATION = 0
TYPE_PURCHASE_OPERATION = 1
TYPE_PRODUCTION_OPERATION = 2
TYPE_EXCHANGE_OPERATION = 3
TYPE_OPERATIONS_ALL = 4

TYPE_PAYABLE_TRANSACTION = 0
TYPE_RECEIVABLE_TRANSACTION = 1
TYPE_TRANSACTIONS_ALL = 2

TYPE_STATUS_INCOMPLETE = 0
TYPE_STATUS_COMPLETE = 1
TYPE_STATUS_ALL = 2

# Labels for the types above
COMPANY_TYPES = (
    (TYPE_CUSTOMER_COMPANY, "Cliente"),
    (TYPE_SUPPLIER_COMPANY, "Fornecedora"),
    (TYPE_CUSTOMER_AND_SUPPLIER_COMPANY, "Cl. e Forn."),
    (TYPE_COMPANIES_ALL, "Todas as empresas"),
)
COMPANY_TYPES_LIST = [el[0] for el in COMPANY_TYPES]
COMPANY_TYPES_DESC = [el[1] for el in COMPANY_TYPES]

ITEM_TYPES = (
    (TYPE_COMMON_ITEM, "Item comum"),
    (TYPE_RAW_MATERIAL, "Matéria Prima"),
    (TYPE_PRODUCTION_ITEM, "Item de produção"),
    (TYPE_SERVICE, "Serviço"),
    (TYPE_ITEMS_ALL, "Todos os itens"),
)
ITEM_TYPES_LIST = [el[0] for el in ITEM_TYPES]
ITEM_TYPES_DESC = [el[1] for el in ITEM_TYPES]

ITEM_UNITS = (
    (TYPE_UNIT_PC, "Peça"),
    (TYPE_UNIT_KG, "Kilograma"),
    (TYPE_UNIT_L, "Litro"),
    (TYPE_UNITS_ALL, "Todas as unidades"),
)
ITEM_UNITS_LIST = [el[0] for el in ITEM_UNITS]
ITEM_UNITS_DESC = [el[1] for el in ITEM_UNITS]

OPERATION_TYPES = (
    (TYPE_SALE_OPERATION, "Venda"),
    (TYPE_PURCHASE_OPERATION, "Compra"),
    (TYPE_PRODUCTION_OPERATION, "Produção"),
    (TYPE_EXCHANGE_OPERATION, "Troca"),
    (TYPE_OPERATIONS_ALL, "Todas as operações"),
)
OPERATION_TYPES_LIST = [el[0] for el in OPERATION_TYPES]
OPERATION_TYPES_DESC = [el[1] for el in OPERATION_TYPES]

TRANSACTION_TYPES = (
    (TYPE_PAYABLE_TRANSACTION, "Pagamento"),
    (TYPE_RECEIVABLE_TRANSACTION, "Recebimento"),
    (TYPE_TRANSACTIONS_ALL, "Todas as transações"),
)
TRANSACTION_TYPES_LIST = [el[0] for el in TRANSACTION_TYPES]
TRANSACTION_TYPES_DESC = [el[1] for el in TRANSACTION_TYPES]

TRANSACTION_STATUS = (
    (TYPE_STATUS_INCOMPLETE, "Não completado(a)"),
    (TYPE_STATUS_COMPLETE, "Completado(a)"),
    (TYPE_STATUS_ALL, "Todos"),
)
TRANSACTION_STATUS_LIST = [el[0] for el in TRANSACTION_STATUS]
TRANSACTION_STATUS_DESC = [el[1] for el in TRANSACTION_STATUS]

# Settings
SETTINGS = {
    "DEFAULT_TRANSACTION_DEADLINE": (int, 28),
    "PRINT_FONT_NAME": (str, "monospace"),
    "PRINT_FONT_SIZE": (int, 10),
    "SELF_COMPANY": (str, "Empresa"),
    "ENABLE_INVENTORY_CONTROL": (int, 1),
}

USER_DATE_FORMAT = locale.nl_langinfo(locale.D_FMT)
INTERNAL_DATE_FORMAT = SQLITE_DATE_FORMAT


# Exceptions
class OksException(Exception):
    pass


class BadStatusError(OksException):
    pass


class InvalidCompanyError(OksException):
    text = "Empresa não cadastrada"
    secondaryText = (
        "A empresa indicada não está cadastrada.\n"
        + "Altere o nome da empresa ou cadastre-a antes."
    )


class InvalidItemError(OksException):
    text = "Item não cadastrado"
    secondaryText = (
        "Um ou mais dos itens indicados não está cadastrado.\n"
        + "Altere o nome dos itens ou cadastre-os antes."
    )


class ItemQuantityError(OksException):
    text = "Erro ao retirar item do estoque"
    secondaryText = "Não há quantidade suficiente em estoque."


class OperationEditError(OksException):
    text = "Essa operação não pode ser editada"
    secondaryText = "Uma operação concluída não pode ser editada."


class InvalidNameError(OksException):
    text = "Nome inválido"
    secondaryText = (
        "O nome de uma empresa ou item não pode estar em \n"
        + "branco e deve ser único caso esteja sendo cadastrado."
    )


class DescriptionError(OksException):
    text = "Especificação inválida"
    secondaryText = ""

    def __init__(self, msg):
        self.secondaryText = msg


class InvalidWidgetName(OksException):
    def __init__(self, widget_name):
        self.widget_name = widget_name

    def __str__(self):
        return "The widget does not exist: " + self.widget_name


class UnsupportedOutputError(OksException):
    def __init__(self, type_):
        self.type_ = type_

    def __str__(self):
        return "The given report output is not supported: " + self.type_


class SettingValueError(OksException):
    def __init__(self, setting):
        self.setting = setting

    def __str__(self):
        return "Invalid value for setting %s" % self.setting
