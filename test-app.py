class TextManager:
    def __init__(self):
        self.history = []
        self.display_text = ""

    def set_text(self, new_text):
        self.history.append(self.display_text)  # Vorherigen Text speichern
        self.display_text = new_text

    def undo(self):
        if self.history:
            self.display_text = self.history.pop()  # Letzten Zustand wiederherstellen

# Beispiel:
tm = TextManager()
tm.set_text("Hallo")
tm.set_text("Welt")
print(tm.display_text)  # Ausgabe: Welt
tm.undo()
print(tm.display_text)  # Ausgabe: Hallo
