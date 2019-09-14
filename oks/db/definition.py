#!/usr/bin/env python
#-*- coding:utf-8 -*-

# Version 6
database_6 = """
CREATE TABLE Companies
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE CHECK (name != ""),
type_ INTEGER,
full_name TEXT,
address TEXT,
neighborhood TEXT,
city TEXT,
state TEXT,
zip_code TEXT,
phone TEXT,
fax TEXT,
email TEXT,
cnpj TEXT,
ie TEXT,
notes TEXT
);

CREATE TABLE Inventory
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE CHECK (name != ""),
type_ INTEGER,
unit INTEGER,
quantity REAL,
price REAL,
notes TEXT
);

CREATE TABLE Operations
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
type_ INTEGER,
company TEXT CHECK (company != ""),
oid INTEGER,
date DATE,
notes TEXT,
status INTEGER
);

CREATE TABLE Products
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pid INTEGER,
IO INTEGER,
name TEXT CHECK (name != ""),
quantity REAL,
price REAL,
notes TEXT,
status INTEGER
);
 
CREATE TABLE ProductionItems
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pid INTEGER,
IO INTEGER,
name TEXT CHECK (name != ""),
quantity REAL,
name_production TEXT CHECK (name != ""),
quantity_production REAL,
density REAL,
volume REAL,
rounding REAL,
proportion_sum REAL,
notes TEXT,
status INTEGER
);

CREATE TABLE RawMaterials
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pid INTEGER,
IO INTEGER,
name TEXT CHECK (name != ""),
quantity REAL,
status INTEGER
);

CREATE TABLE ExchangeItems
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pid INTEGER,
IO INTEGER,
name TEXT CHECK (name != ""),
quantity REAL,
notes TEXT,
status INTEGER
);

CREATE TABLE Transactions
(
row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pid INTEGER,
IO INTEGER,
ddate DATE,
way TEXT,
value REAL,
notes TEXT,
status INTEGER
);

CREATE TABLE Settings
(
name TEXT,
value TEXT
);
"""

application_6 = """
CREATE TEMPORARY VIEW TransactionsView AS SELECT
    Transactions.row_id AS row_id,
    Transactions.IO AS type_,
    ddate,
    Operations.Company AS company,
    Operations.oid AS oid,
    way,
    value,
    Transactions.status AS status,
    Transactions.notes AS notes 
FROM
    Transactions, Operations
WHERE
    pid == Operations.row_id AND
    Operations.type_ != 2
ORDER BY
    Transactions.row_id;

/*
Cascade update of name on Companies
*/
CREATE TEMPORARY TRIGGER UpdateCompanyName AFTER UPDATE OF name ON Companies
    FOR EACH ROW WHEN NEW.name != OLD.name
    BEGIN
        UPDATE Operations SET company = NEW.name WHERE company == OLD.name;
    END;

/*
Cascade update of name on Inventory
*/
CREATE TEMPORARY TRIGGER UpdateInventoryName AFTER UPDATE OF name ON Inventory
    BEGIN
        UPDATE Products SET name = NEW.name WHERE name == OLD.name;
        UPDATE ProductionItems SET name = NEW.name WHERE name == OLD.name;
        UPDATE RawMaterials SET name = NEW.name WHERE name == OLD.name;
        UPDATE ExchangeItems SET name = NEW.name WHERE name == OLD.name;
    END;
    
/*
Update status on TransactionsView (updates Transactions)
*/
CREATE TEMPORARY TRIGGER ChangeTransactionStatus INSTEAD OF UPDATE OF status ON 
TransactionsView
    FOR EACH ROW WHEN NEW.status != OLD.status
    BEGIN
        UPDATE Transactions SET status = NEW.status 
        WHERE Transactions.row_id = NEW.row_id;
    END;
    
/*
Cascade update of company on Operations
This trigger doesn't perform anything, it just sends an update signal to the
Transactions table so that it can be caught by the application.
*/
CREATE TEMPORARY TRIGGER UpdateCompany AFTER UPDATE OF company ON Operations
    FOR EACH ROW
    BEGIN
        UPDATE Transactions SET pid = NEW.row_id WHERE pid == OLD.row_id;
    END;


/*
The following triggers are a nasty way to solve the lack of the update_hook 
function in the Python implementation of SQLite
*/
CREATE TEMPORARY TRIGGER InsertCompanies AFTER INSERT ON Companies
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Companies", "INSERT", NEW.row_id);
    END;

CREATE TEMPORARY TRIGGER UpdateCompanies AFTER UPDATE ON Companies
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Companies", "UPDATE", NEW.row_id);
    END;
    
CREATE TEMPORARY TRIGGER DeleteCompanies AFTER DELETE ON Companies
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Companies", "DELETE", OLD.row_id);
    END;


CREATE TEMPORARY TRIGGER InsertInventory AFTER INSERT ON Inventory
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Inventory", "INSERT", NEW.row_id);
    END;

CREATE TEMPORARY TRIGGER UpdateInventory AFTER UPDATE ON Inventory
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Inventory", "UPDATE", NEW.row_id);
    END;
    
CREATE TEMPORARY TRIGGER DeleteInventory AFTER DELETE ON Inventory
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Inventory", "DELETE", OLD.row_id);
    END;


CREATE TEMPORARY TRIGGER InsertOperations AFTER INSERT ON Operations
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Operations", "INSERT", NEW.row_id);
    END;

CREATE TEMPORARY TRIGGER UpdateOperations AFTER UPDATE ON Operations
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Operations", "UPDATE", NEW.row_id);
    END;
    
CREATE TEMPORARY TRIGGER DeleteOperations AFTER DELETE ON Operations
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Operations", "DELETE", OLD.row_id);
    END;


CREATE TEMPORARY TRIGGER InsertTransactions AFTER INSERT ON Transactions
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Transactions", "INSERT", NEW.row_id);
    END;

CREATE TEMPORARY TRIGGER UpdateTransactions AFTER UPDATE ON Transactions
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Transactions", "UPDATE", NEW.row_id);
    END;
    
CREATE TEMPORARY TRIGGER DeleteTransactions AFTER DELETE ON Transactions
    FOR EACH ROW
    BEGIN
        SELECT update_hook("Transactions", "DELETE", OLD.row_id);
    END;
    
"""
