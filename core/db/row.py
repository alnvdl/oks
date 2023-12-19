import core.db


class Row(object):
    HAS_CHILDREN = False

    def __init__(self, **kwargs):
        self.row_id = None
        self.row = ("row_id",) + self.row
        self.children = {}
        for attr, value in list(kwargs.items()):
            setattr(self, attr, value)

    def load_child(self, child):
        pass

    def from_row(self, source):
        for n in range(len(self.row)):
            setattr(self, self.row[n], source[n])

    def copy(self, type_=core.db.COPY):
        # Force the copy to be complete if the row is new
        if self.row_id is None:
            type_ = core.db.COPY
        # Copy the row
        new = self.__class__()
        new.from_row(self.to_row())
        # If it's a new copy, reset the row_id
        if type_ == core.db.COPY:
            new.row_id = None
        # Copy the children
        for name, container in list(self.children.items()):
            dest = getattr(new, name)
            for iter_, element in container:
                dest.insert(element.copy(type_), type_)
        return new

    def to_row(self):
        return tuple([getattr(self, attr) for attr in self.row])

    def __eq__(self, other):
        return other.to_row() == self.to_row()

    # TODO: remove this
    def format_to_output(self, type_):
        pass


class ChildRow(Row):
    def __init__(self, **kwargs):
        self.pid = None
        self.IO = 0
        self.row = ("pid",) + self.row
        Row.__init__(self, **kwargs)

    def copy(self, type_=core.db.COPY):
        new = super(ChildRow, self).copy(type_)
        if type_ == core.db.COPY:
            new.pid = None
        return new


class RowWithStatus(object):
    CHANGE_STATUS_WITH_PARENT = True

    def __init__(self, row):
        self.STATUS_LOCKED = True

        self._status = 0
        self.row = row + ("status",)

    def from_row(self, source):
        self.STATUS_LOCKED = False
        super(RowWithStatus, self).from_row(source)
        self.STATUS_LOCKED = True

    def get_status(self):
        return self._status

    def set_status(self, status):
        if self.STATUS_LOCKED:
            # TODO: custom exception
            raise Exception(
                "Can't update status this way, use AppDatabase method instead"
            )
        else:
            self._status = status

    status = property(get_status, set_status)

    def toggle_status(self):
        self.STATUS_LOCKED = False
        self._status = int(not self._status)
        self.STATUS_LOCKED = True

    def copy(self, type_=core.db.COPY):
        new = super(RowWithStatus, self).copy(type_)
        # Status 0 by default if it's a new copy
        if type_ == core.db.COPY and self._status == 1:
            new.toggle_status()
        return new
