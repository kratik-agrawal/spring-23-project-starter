"""
Module that manages program environments. Currently a mapping from variables to values.
"""
from type_valuev1 import Type, Value


class EnvironmentManager:
    """
    The EnvironmentManager class maintains the lexical environment for a construct.
    In project 1, this is just a mapping between each variable (aka symbol)
    in a brewin program and the value of that variable - the value that's passed in can be
    anything you like. In our implementation we pass in a Value object which holds a type
    and a value (e.g., Int, 10).
    """

    def __init__(self):
        self.environment = {}
    
    def get_type(self, symbol):
        if symbol in self.environment:
            return self.environment[symbol][0]

        return None

    def get(self, symbol):
        """
        Get data associated with variable name.
        """
        if symbol in self.environment:
            return self.environment[symbol][1]

        return None

    def set(self, symbol, value):
        """
        Set data associated with a variable name.
        """
        # print(symbol)
        self.environment[symbol[1]] = (symbol[0], value)

    