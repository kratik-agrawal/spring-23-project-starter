"""
The module that brings it all together! We intentionally keep this as small as possible,
delegating functionality to various modules.
"""

from classv1 import ClassDef
from intbase import InterpreterBase, ErrorType
from bparser import BParser
from objectv1 import ObjectDef


class Interpreter(InterpreterBase):
    """
    Main interpreter class that subclasses InterpreterBase.
    """

    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.main_object = None
        self.class_index = {}

    def run(self, program):
        """
        Run a program (an array of strings, where each item is a line of source code).
        Delegates parsing to the provided BParser class in bparser.py.
        """
        status, parsed_program = BParser.parse(program)
        print([parsed_program])
        if not status:
            super().error(
                ErrorType.SYNTAX_ERROR, f"Parse error on program: {parsed_program}"
            )
        self.__map_class_names_to_class_defs(parsed_program)

        # instantiate main class
        invalid_line_num_of_caller = None
        self.main_object = self.instantiate(
            InterpreterBase.MAIN_CLASS_DEF, invalid_line_num_of_caller
        )

        # call main function in main class; return value is ignored from main
        self.main_object.call_method(
            InterpreterBase.MAIN_FUNC_DEF, [], invalid_line_num_of_caller
        )

        # program terminates!

    def instantiate(self, class_name, line_num_of_statement):
        """
        Instantiate a new class. The line number is necessary to properly generate an error
        if a `new` is called with a class name that does not exist.
        This reports the error where `new` is called.
        """
        if class_name not in self.class_index:
            super().error(
                ErrorType.TYPE_ERROR,
                f"No class named {class_name} found",
                line_num_of_statement,
            )
        class_def = self.class_index[class_name]
        obj = ObjectDef(
            self, class_def, self.trace_output
        )  # Create an object based on this class definition
        return obj

    def __map_class_names_to_class_defs(self, program):
        self.class_index = {}
        for item in program:
            if item[0] == InterpreterBase.CLASS_DEF:
                if item[1] in self.class_index:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Duplicate class name {item[1]}",
                        item[0].line_num,
                    )
                self.class_index[item[1]] = ClassDef(item, self)

if __name__ == "__main__":
    inter = Interpreter()
    program = ["""
    (class main
        (field int x false)
        (method int value_or_zero ((int q)) 
            (begin
            (if (< q 0)
                (print "q is less than zero")
                (return q) 
            )
            )
        )
        (method string foo ((string a) (string b)) (return (+ a b)))

        (method void main ()
            (begin
            (print (call me value_or_zero 10))  
            (print (call me value_or_zero -10)) 
            )
        )
        )

"""]
               
    program2 = ["""
    (class main
 (method void foo ((int x))
   (begin 
     (print x)
     (let ((int y 5))
          (print y)
          (set y 25)
          (print y)
     )
   )
 )
 (method void main ()
   (call me foo 10)
 )
)

"""]
                
    program3 = ["""
    (class main
 (method int i () (return))
 (method string s () (return))
 (method bool b () (return))
 (method void main ()
   (begin
      (print (call me i))
      (print (call me s))
      (print (call me b))
   )
 )
)

"""]
    program4 = ["""
(class main
 (method int foo () 
   (return "abc"))
 (method void main ()
  (call me foo)
 )
)

"""]
    inter.run(program4)