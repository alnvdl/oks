# Oks

Oks is a small ERP system tailor-made for a grinding wheel company in Brazil.
It has been in use in production for more than 15 years.

It features:

- Customer/supplier management
- Inventory control
- Order, sales and manufacturing management
- Accounts payable/receivable
- Several customizable reports

![Oks](gui/screenshot.png)

It was originally built using Python 2, PyGTK and SQLite, and has since been
updated to Python 3 and the new GTK/GI bindings.

It was mostly developed in 2008, when I (Allan) was 18 years old, before I
started attending university. It was my first real big project. I am proud of
some parts of it, namely the database model, the abstractions I came up with
and the *relative* tidiness of the code in certain parts.

I'm a little ashamed by the lack of proper testing (there are only some
integration tests) and some really questionable decisions, like having a
gigantic singleton for the GUI. But this thing still works after all these
years and is still used everyday as of 2023 :)

The user interface only supports Portuguese (despite all of the code being in
English).

The company for which Oks was developed allows the code to be published here
under the Apache 2.0 license. The icons were made by Luiz Henrique Camargo.

## Running on a desktop
On a vanilla Ubuntu 22.04 desktop, just `cd` into the root folder and run:

    $ python3 oks.py

## Running on a server
On a vanilla Ubuntu 22.04 minimal server or container, install the following
packages first:

    $ sudo apt-get install python3-gi python3-gi-cairo libgtk-3-0 \
        gir1.2-gtk-3.0 gir1.2-gtk-3.0 gir1.2-cairo gir1.2-gtk-3.0 \
        python3-cairo yaru-theme-icon evince

To avoid quirky behavior involving mnemonics in GTK 3.0 when using Broadway,
make sure to disable them with:

    mkdir -p ~/.config/gtk-3.0
    cat <<EOF > ~/.config/gtk-3.0/settings.ini
    [Settings]
    gtk-enable-mnemonics = 0
    EOF

Then start `broadwayd`:

    $ broadwayd :5

And start Oks:

    $ GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 python3 oks.py

It will be available at http://localhost:8085.
