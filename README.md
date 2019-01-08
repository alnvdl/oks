# Oks

Oks is a small ERP system tailor-made for a grinding wheel company in Brazil.
It has been in use for 10+ years without any hiccups at all.

It features:

- Customer/supplier management
- Inventory control
- Order, sales and manufacture management
- Accounts payable/receivable
- Several highly-customized reports

![Oks](gui/screenshot1.png)

It is written using Python 2, PyGTK and SQLite.

It was mostly developed when I (Allan) was 18 years old, before I started
college. I am proud of some parts of this project, namely the database model,
the abstractions I came up with and the overall tidiness of the code. I'm a
little ashamed by the lack of proper internationalization, poor testing (there
are only some integration tests). But this thing still works after all this
time and is still used everyday :)

## Running

Oks has only been tested in Linux. For Debian/Ubuntu systems, installing the
`python-glade2` package usually install all other dependencies:

    $ sudo apt-get install python-glade2

Then to run Oks, `cd` into the root folder and run:

    $ python oks.py

The SQLite database will be created. The user interface only supports the
Portuguese language (despite all of the actual code being in English).

The company for which Oks was developed allows the code to be published here
under the Apache 2.0 license. The icons were made by Luiz Henrique Camargo.