from copy import copy, deepcopy
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
        self.environment[symbol[1]] = (symbol[0], value)

    
if __name__ == "__main__":
    env = EnvironmentManager()
    env.set(["int", "a"], 5)
    env.set(["int", "b"], 6)
    print(env.get("a"))
    print(env.get("b"))
    env2 = deepcopy(env)
    print(env2.get("a"))
    print(env2.get("b"))

    env2.set(["int", "a"], 1)
    env2.set(["int", "b"], 2)
    env2.set(["int", "c"], 3)
    print(env.get("a"))
    print(env.get("b"))
    print(env2.get("a"))
    print(env2.get("b"))
    print(env2.get("c"))
    print(env.get("c"))