#!/usr/bin/env python3
# GCreepyr: A GUI frontend to Creepyr, A CLI Minecraft launcher/server-launcher/pack-dev-tool written in Python by Dunkmania101


# License:
"""
MIT License

Copyright (c) 2024 Duncan Brasher (Dunkmania101)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""



#import creepyr
from tkinter import Tk, Widget as TkWidget, Frame as TkFrame, Label as TkLabel, Button as TkButton, Entry as TkEntry


class MenuScreen(TkFrame):
    items: list = []
    vitems: dict = {}

    def setup(self) -> None:
        for item in self.items:
            frame = self.get_frame(item)
            frame.grid()
            self.vitems[str(item)] = frame

    def get_frame(self, item) -> TkWidget:
        return TkLabel(self, text=str(item))

    def redraw(self) -> None:
        for vitem in self.vitems.values():
            vitem.grid_forget()
        self.vitems.clear()

        self.setup()

    def add_item(self, item, index: int | None = None) -> None:
        if index is None:
            self.items.append(item)
        else:
            self.items.insert(index, item)
        self.redraw()


class GCreepyrWin(Tk):
    account = None
    instances = None

    def __init__(self, title: str = "GCreepyr") -> None:
        self.title = title
        self.destroyed = False

        Tk.__init__(self=self, className=self.get_title())
        self.wm_resizable(True, True)

        self.setup()

    def setup(self) -> None:
        self.account = AccountsScreen(self)
        self.instances = InstancesScreen(self)
        self.account.setup()
        self.instances.setup()
        self.account.grid()
        self.instances.grid(column=1, row=0)

    def get_title(self) -> str:
        return self.title

    def destroy(self) -> None:
        self.destroyed = True
        return super().destroy()


class AccountsScreen(TkFrame):
    menu = None
    login = None

    def setup(self) -> None:
        self.menu = AccountsMenuScreen(self)
        self.login = LoginScreen(self)
        self.menu.setup()
        self.menu.grid()
        self.login.setup(self.add_account)
        self.login.grid()

    def add_account(self, account) -> None:
        if account is not None:
            self.menu.add_item(account)


class AccountsMenuScreen(MenuScreen):
    pass


class LoginScreen(TkFrame):
    lblUname = None
    uname = None
    lblPasswd = None
    passwd = None
    btnAdd = None


    def setup(self, add_account) -> None:
        self.lblUname = TkLabel(self, text="Username: ")
        self.uname = TkEntry(self, name="username")
        self.lblPasswd = TkLabel(self, text="Password: ")
        self.passwd = TkEntry(self, name="password")
        self.btnAdd = TkButton(self, text="Add", command=lambda: add_account([self.uname.get(), self.passwd.get()]))
        self.lblUname.grid()
        self.uname.grid(row=0, column=1)
        self.lblPasswd.grid(row=1, column=0)
        self.passwd.grid(row=1, column=1)
        self.btnAdd.grid(row=2, column=1)


class InstancesScreen(TkFrame):
    menu = None
    dialog = None

    def setup(self) -> None:
        self.menu = InstancesMenuScreen(self)
        self.menu.setup()
        self.menu.grid()



class InstancesMenuScreen(MenuScreen):
    def setup(self) -> None:
        self.items = [1, 2, 3, 4, 5] # TODO: This is just a test. This should be populated with actual instances collected from a directory listing or something like that.
        return super().setup()

    def get_frame(self, item):
        frame = InstanceObjectFrame()
        frame.setup(item)
        return frame

class InstanceObjectFrame(TkFrame):
    instance = None
    title = None

    def setup(self, instance) -> None:
        self.instance = instance
        self.title = TkButton(self, text=str(instance))
        self.title.grid()


def main(args: list[str] = []) -> int:
    try:
        win = GCreepyrWin()
        win.mainloop()
    except:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())

