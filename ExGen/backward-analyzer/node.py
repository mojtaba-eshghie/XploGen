class Node(object):
    def __init__(self, func, name, attr):
        self.func = func
        self.name = name
        self.attr = attr  # record taint flag
