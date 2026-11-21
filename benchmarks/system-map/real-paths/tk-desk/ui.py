import tkinter as tk

from disk import store


class App:
    def wire(self):
        tk.Button(text="Salva", command=self.save)

    def save(self):
        store.put("orders")
