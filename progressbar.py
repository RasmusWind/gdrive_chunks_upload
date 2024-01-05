class ProgressBar:
    def __init__(self, title, current_progress, total, print_state):
        self._title = title
        self._total = total
        self.current_progress = current_progress
        self._print_state = print_state
        if self._print_state:
            self.print_bar()

    @property
    def current_progress(self):
        return self._current_progress

    @current_progress.setter
    def current_progress(self, value):
        self._current_progress = value
        self._percent = 100 * (value / float(self._total))
        self._bar = chr(9608) * int(self._percent) + chr(9617) * (100 - int(self._percent))

    def print_bar(self):
        print(f"\r{self._bar} {self._percent:.2f}% {self._title}", end="\r")
        if int(self._percent) == 100:
            print()

    def increment_progress(self, amount=1):
        self.current_progress = self.current_progress + amount
        if self._print_state:
            self.print_bar()