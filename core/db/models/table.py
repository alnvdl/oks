from gi.repository import Gtk as gtk


class Table(gtk.ListStore):
    def __init__(self, db, table, columns, reverse=False):
        gtk.ListStore.__init__(self, *[column[1] for column in columns])
        self.db = db
        self.table = table
        self.reverse = reverse
        self.columns = [column[0] for column in columns]
        self.column_types = [column[1] for column in columns]

        rows = self.db.execute_and_select_all("SELECT * FROM %s" % self.table)
        for row in rows:
            self.insert(0, self.map_row(row))

    def get_row_id(self, iter_):
        return self[iter_][0]

    def map_row(self, row):
        nrow = []
        i = 0
        for converter in self.column_types:
            nrow.append(converter(row[i]))
            i += 1
        return nrow

    def row_inserted(self, row):
        self.insert(0, self.map_row(row))

    def row_updated(self, new_row):
        new_row = self.map_row(new_row)
        for row in self:
            if row[0] == new_row[0]:
                iter_ = row.iter
                break

        for col in range(len(new_row)):
            self.set_value(iter_, col, new_row[col])

    def row_deleted(self, row_id):
        for row in self:
            if row[0] == row_id:
                self.remove(row.iter)
                break
