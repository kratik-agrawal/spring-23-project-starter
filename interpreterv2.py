"""
The module that brings it all together! We intentionally keep this as small as possible,
delegating functionality to various modules.
"""

from classv2 import ClassDef
from intbase import InterpreterBase, ErrorType
from bparser import BParser
from objectv2 import ObjectDef


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
        super_obj = None
        if class_def.super_class_name is not None:
            super_obj = self.instantiate(class_def.super_class_name, 0)
        obj = ObjectDef(
            self, class_def, self.trace_output, super_obj
        )  # Create an object based on this class definition
        return obj

    def __map_class_names_to_class_defs(self, program):
        self.class_index = {}
        self.children = {}
        for item in program:
            if item[0] == InterpreterBase.CLASS_DEF:
                if item[1] in self.class_index:
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Duplicate class name {item[1]}",
                        item[0].line_num,
                    )
                if item[2] == InterpreterBase.INHERITS_DEF:
                    if item[3] in self.children:
                        self.children[item[3]].append(item[1])
                    else:
                        self.children[item[3]] = [item[1]]
                    for cls in self.children.keys():
                        if item[3] in self.children[cls]:
                            self.children[cls].append(item[1])
                        
                self.class_index[item[1]] = ClassDef(item, self)
    
    def isChild(self, assumedparent, child):
        return assumedparent in self.children and child in self.children[assumedparent]

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
(class person 
  (field string name "jane")
  (method void set_name((string n)) (set name n))
  (method string get_name() (return name))
)

(class student inherits person
  (field int beers 3)
  (field string student_name "studentname")
  (method void set_beers((int g)) (set beers g))
  (method int get_beers() (return beers))
  (method person get_name() (return (new student)))
)

(class main
  (field student s null)
  (method void main () 
    (begin 
      (set s (new student))
      (print (call s get_name))
    )
  )
)

"""]
    
    program5 = ["""
    (class person
  (field string name "anonymous")
  (method void set_name ((string n)) (set name n))
  (method void say_something () (print name " says hi"))
)

(class student inherits person
  (field int student_id 0)
  (method void set_id ((int id)) (set student_id id))
  (method void say_something ()
    (begin
     (print "first")
     (call super say_something)  
     (print "second")
    )
  )
)

(class main
  (field student s null)
  (method void main ()
    (begin
      (set s (new student))
      (call s set_name "julin")   
(call s set_id 010123456)
      (call s say_something)	 
    )
  )
)

    """]

    program6 = ["""
(class main
  (method void main ()
    (call me foo (new animal) (new dog))
  )
  (method void foo ((animal a) (dog d))
    (set d a)
  )
)
(class animal
  (method void breathe () (return 1))
)
(class dog inherits animal
  (method void breathe () (return 1))
)


"""]
    inter.run(program6)