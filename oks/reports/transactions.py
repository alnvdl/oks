from core.output import *
from core.report import Report
import oks

class TransactionsReport(Report):
    OPTIONS = [("status", oks.REPORT_OPTION_BOOL,
                "Incluir transações concluídas", False)]

    def __init__(self, db):
        Report.__init__(self, db)

    def make(self, type_):
        Report.make(self)
        if self.status == True:
            status = (oks.TYPE_STATUS_INCOMPLETE, oks.TYPE_STATUS_COMPLETE)
        else:
            status = oks.TYPE_STATUS_INCOMPLETE

        transactions = self.db.cached_load(oks.TRANSACTION,
                                           IO = type_,
                                           status = status)
        total = 0.0
        operations = {}
        for transaction in transactions:
            pid = transaction.pid
            if pid not in operations:
                operations[pid] = self.db.cached_load(oks.OPERATION,
                                                      row_id = pid)
            operation = operations[transaction.pid]

            self.data.append((transaction.ddate,
                              operation.company,
                              transaction.value,
                              operation.oid,
                              transaction.way))
            total += transaction.value

        self.data.sort(key = lambda row: row[0]) # Sort by date

        if total:
            self.bits.append(CurrencyData("total", "Total", total, unit="R$"))

    def make_output(self):
        Report.make_output(self)
        return TableSection("transactions_report", self.NAME,
                            (DateData("ddate", "Vencimento"),
                             StringData("company", "Empresa"),
                             CurrencyData("value", "Valor", unit="R$"),
                             IntegerData("oid", "ID"),
                             StringData("way", "Forma")),
                            self.data, self.bits)


class PayablesReport(TransactionsReport):
    NAME = "Contas a pagar"
    DESCRIPTION = "Listagem das contas a pagar."
    def __init__(self, db):
        TransactionsReport.__init__(self, db)

    def make(self):
        TransactionsReport.make(self, oks.TYPE_PAYABLE_TRANSACTION)

class ReceivablesReport(TransactionsReport):
    NAME = "Contas a receber"
    DESCRIPTION = "Listagem das contas a receber."
    def __init__(self, db):
        TransactionsReport.__init__(self, db)

    def make(self):
        TransactionsReport.make(self, oks.TYPE_RECEIVABLE_TRANSACTION)
