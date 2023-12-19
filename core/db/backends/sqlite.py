import sqlite3
import os.path
import datetime

INTERNAL_DATE_FORMAT = "%Y-%m-%d"

TYPES_MAP = {
    "TEXT": str,
    "INTEGER": int,
    "REAL": float,
    "DATE": str,
}  # For performance reasons, it's better to deal with dates as strings


class SQLiteBackend:
    def __init__(self, dbFile=":memory:"):
        self.dbFile = dbFile
        self.connection = sqlite3.connect(
            dbFile, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self.connection.text_factory = str
        self.cursor = self.connection.cursor()
        self.update_tables_info()

    def update_tables_info(self):
        """Update the list of tables and their columns."""
        self.tables = {}
        for (table,) in self.execute_and_select_all(
            """
        SELECT name FROM sqlite_master WHERE
            name != 'sqlite_sequence' AND
            type = 'table' OR
            type = 'view'
        UNION ALL SELECT name FROM sqlite_temp_master WHERE
           name != 'sqlite_sequence' AND
            type = 'table' OR
            type = 'view'
            """
        ):
            table = str(table)
            columns = []
            for column in self.execute_and_select_all(
                "PRAGMA table_info (%s)" % table
            ):
                columns.append((column[1], TYPES_MAP[column[2]]))
            self.tables[table] = columns

    def print_table(self, table):
        """
        Print the table.
        @table: table name
        """
        print("--%s--" % table)
        for row in self.get_rows(table):
            print(row)

    def get_app_version(self):
        """
        Return the application version registered in the database.
        """
        return self.cursor.execute("PRAGMA user_version").fetchone()[0]

    def set_app_version(self, version):
        """
        Set the application version in the database.
        """
        self.cursor.execute("PRAGMA user_version = %i" % version)

    def execute_statement(self, statement, values=()):
        return self.cursor.execute(statement, values)

    def execute_script(self, script):
        self.cursor.executescript(script)

    def execute_and_select_first(self, statement, values=()):
        return self.cursor.execute(statement, values).fetchone()

    def execute_and_select_all(self, statement, values=()):
        return self.cursor.execute(statement, values).fetchall()

    def get_row(self, table, row_id):
        return self.execute_and_select_first(
            "SELECT * FROM %s WHERE row_id = ?" % table, (row_id,)
        )

    def get_rows(self, table, **values):
        statement = "SELECT * FROM %s"
        args = []
        if values:
            statement += " WHERE "
            for column, value in list(values.items()):
                if type(value) == tuple:
                    statement += "%s BETWEEN ? AND ? AND " % column
                    args.append(value[0])
                    args.append(value[1])
                else:
                    if type(value) == str and value[0] == "~":
                        value = value[1:]
                        statement += "%s LIKE ? AND " % column
                    else:
                        statement += "%s = ? AND " % column
                    args.append(value)
            statement = statement.rstrip("AND ")
        return self.execute_and_select_all(statement % table, args)

    def get_rows_in_range(self, table, column, value1, value2, select="*"):
        print("WARNING: get_rows_in_range method is deprecated!")
        statement = "SELECT %s FROM %s WHERE %s BETWEEN ? AND ?" % (
            select,
            table,
            column,
        )
        return self.execute_and_select_all(statement, (value1, value2))

    def query(self, table, resultColumn="row_id", reverse=True, **values):
        statement = "SELECT %s FROM %s" % (resultColumn, table)
        if values:
            statement += " WHERE "
            for column in list(values.keys()):
                statement += "%s LIKE ? AND " % column
            statement = statement.rstrip("AND ")
        if reverse:
            statement += " ORDER BY %s DESC" % resultColumn
        return self.execute_and_select_all(statement, list(values.values()))

    def insert(self, table, values):
        try:
            assert len(values) == len(self.tables[table])
        except AssertionError:
            raise KeyError(
                "Invalid row for table %s: %s" % (table, str(values))
            )
        placeholders = ", ".join(["?" for i in range(len(values))])
        statement = "INSERT INTO %s VALUES (%s)" % (table, placeholders)
        self.cursor.execute(statement, tuple(values))
        row_id = self.get_last_row_id()
        return row_id

    def update(self, table, row_id, new_row):
        updateColumns = ", ".join(
            [
                "%s=?" % columnName
                for columnName, columnType in self.tables[table]
            ]
        )
        statement = "UPDATE %s SET %s WHERE row_id = ?" % (
            table,
            updateColumns,
        )
        self.cursor.execute(statement, new_row + (row_id,))

    def delete(self, table, row_id):
        statement = "DELETE FROM %s WHERE row_id = ?" % table
        self.cursor.execute(statement, (row_id,))

    def delete_rows(self, table, **values):
        statement = "DELETE FROM %s"
        if values:
            statement += " WHERE "
            for column in list(values.keys()):
                statement += "%s = ? AND " % column
            statement = statement.rstrip("AND ")
        return self.execute_and_select_all(
            statement % table, list(values.values())
        )

    def get_min_and_max(self, table, column, **where):
        statement = "SELECT min(%s), max(%s) FROM %s"
        if where:
            statement += " WHERE "
            for whereColumn in list(where.keys()):
                statement += "%s = ? " % whereColumn
            return self.execute_and_select_first(
                statement % (column, column, table), list(where.values())
            )
        else:
            return self.execute_and_select_first(
                statement % (column, column, table)
            )

    def get_rows_through_child_search(
        self, table, child_table, search_col, value
    ):
        statement = (
            "SELECT * FROM %s WHERE row_id IN "
            "(SELECT pid FROM %s WHERE %s LIKE ?)"
            % (table, child_table, search_col)
        )
        return self.execute_and_select_all(statement, (value,))

    def get_last_row_id(self):
        return int(self.cursor.lastrowid)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()
        self.inserted = []
        self.updated = []
        self.deleted = []

    def close(self):
        self.commit()
        self.cursor.close()
        self.connection.execute("VACUUM")
        self.connection.close()
