from bparser import BParser
from intbase import InterpreterBase, ErrorType

class Interpreter(InterpreterBase):
    
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase’s constructor
        self.class_map = {}
        #class: ClassDefinition

    def _create_obj(self):
        return ObjectDefinition(super())
    
    def run(self, program):
        result, parsed_program = BParser.parse(program)
        if result == False:
            super().error(ErrorType.TYPE_ERROR, "Can't parse program")
            return 
        print(parsed_program)
        self.__discover_all_classes_and_track_them(parsed_program)
        class_def = self.class_map["main"]
        obj = class_def.instantiate_object()
        obj.call_method("main", [])
        # obj.call_method("test", ['1','2'])
        return
    
    def __discover_all_classes_and_track_them(self, program):
        # use this to go through the code and find all classes and such
        # find a way to map all of these and keep track of them
        
        for class_def in program:
            
            class_name = class_def[1]
            if class_name in self.class_map:
                super().error(ErrorType.TYPE_ERROR, "two classes with the same name")
                
            fields = {}
            methods = {}
            for item in class_def[2:]:
                if item[0] == super().FIELD_DEF:
                    # handle a field
                    if item[1] in fields:
                        super().error(ErrorType.NAME_ERROR,
                                      "two fields with the same name")
                    else:
                        # fields[item[1]] = get_native_type(item[2]) # parse this to native type
                        fields[item[1]] = item[2]
                elif item[0] == super().METHOD_DEF:
                    # handle a method
                    if item[1] in methods:
                        super().error(ErrorType.NAME_ERROR,
                                      "two methods with the same name")
                    else:
                        methods[item[1]] = {
                            "arguments": item[2],
                            "statement": item[3]
                        }
                else:
                
                    super().error(ErrorType.SYNTAX_ERROR,
                                      "Recieved something unexpected in class def")
            
            # print(class_name)
            # print(fields)
            # print(methods)
            # print()
            class_definition = ClassDefiniton(self,super(),class_name, methods, fields)
            self.class_map[class_name] = class_definition
        return




class ClassDefiniton:
    def __init__(self, above, super, name, methods, fields):
        self.above = above
        self.super = super
        self.my_name = name
        self.my_methods = methods
        self.my_fields = fields
        return 
    
    def instantiate_object(self):
        obj = ObjectDefinition(self.above,self.super)
        for name, details in self.my_methods.items():
            obj.add_method(name, details)

        for name, value in self.my_fields.items():
            obj.add_field(name, value)
        return obj
    

class ObjectDefinition:
    def __init__(self, above, super):
        self.interpreter = above
        self.super = super
        self.obj_fields = {}
        self.obj_methods = {}

    def add_method(self, name, details):
        self.obj_methods[name] = details

    def add_field(self, name, value):
        self.obj_fields[name] = value
    
    def call_method(self, method_name, parameters): 
        # method = self.__find_method(method_name)
        # statement = method.get_top_level_statement()
        # result = self.__run_statement(method, statement)
        if method_name not in self.obj_methods:
            self.super.error(ErrorType.NAME_ERROR,
                                      "Method does not exist")
        method = self.obj_methods[method_name]
        if len(method['arguments']) != len(parameters):
            self.super.error(ErrorType.TYPE_ERROR,
                                      f"{method_name} Method. Wrong number of arguments for method: {parameters}")
        else:
            parameter_map = {}
            for idx, val in enumerate(method['arguments']):
                parameter_map[val] = parameters[idx]
        statement = method['statement']
        result = self.__run_statement(statement, parameter_map)
        if result == "exit exit exit exit":
            return
        return result
    
    def __run_statement(self, statement, parameters):
        statement_type = statement[0]
        if statement_type == self.super.PRINT_DEF:
            result = self.__execute_print_statement(statement, parameters)
        elif statement_type == self.super.INPUT_INT_DEF or statement_type == self.super.INPUT_STRING_DEF:
            result = self.__execute_input_statement(statement, parameters)
        elif statement_type == self.super.CALL_DEF:
            result = self.__execute_call_statement(statement, parameters)
        elif statement_type == self.super.WHILE_DEF:
            result = self.__execute_while_statement(statement, parameters)
        elif statement_type == self.super.IF_DEF:
            result = self.__execute_if_statement(statement, parameters)
        elif statement_type == self.super.RETURN_DEF:
            result = self.__execute_return_statement(statement, parameters)
        elif statement_type == self.super.BEGIN_DEF:
            result = self.__execute_begin_statement(statement, parameters)
        elif statement_type == self.super.SET_DEF:
            result = self.__execute_set_statement(statement, parameters) 
        else:
            return 0
        #might need more
        return result
    
    def __execute_print_statement(self, statement, parameters):
        # print("print", statement, parameters)
        result = ""
        for arg in statement[1:]: ## ignoring the print command itself
            #need to evaluate arg
            val = self.__get_native_type(arg, parameters)
            if val == True or val == False:
                val = str(val).lower()
            result += str(val)
        self.super.output(result)

    def __execute_input_statement(self, statement, parameters):
        val = self.super.get_input()
        if statement[0] == self.super.INPUT_INT_DEF:
            val = str(val)
        else:
            val = "\"" + str(val) + "\""

        if statement[1] in parameters: # if the value is in parameters, make it that value
            parameters[statement[1]] = val 
            # print(parameters)
        elif statement[1] in self.obj_fields: # if the value is in the object, make it that value
            self.obj_fields[statement[1]] = val
            # print(self.obj_fields)
            # print(self.obj_fields)
            
    def __execute_set_statement(self, statement, parameters):
        # print(statement, "parameters before", parameters, "\n")
        # set_value = get_native_type(statement[2])
        set_value = statement[2]
        if type(statement[2]) is list:
            set_value = self.__evaluate_expression(statement[2], parameters)
        if statement[1] in parameters: # if the value is in parameters, make it that value
            parameters[statement[1]] = set_value 
        elif statement[1] in self.obj_fields: # if the value is in the object, make it that value
            self.obj_fields[statement[1]] = set_value
            # print(self.obj_fields)
        else:
            self.super.error(ErrorType.NAME_ERROR,
                                      f"{statement}Can't Set, field or name does not exist")
            return -1023
        # print(statement, "parameters after", parameters, "\n")

    def __execute_begin_statement(self,statement, parameters):
        for s in statement[1:]:
            result = self.__run_statement(s, parameters)
            if result == "exit exit exit exit":
                return
    
    def __execute_return_statement(self, statement, parameters):
        if len(statement) == 1:
            return "exit exit exit exit"
        else:
            return self.__evaluate_expression(statement[1], parameters)

    def __execute_if_statement(self, statement, parameters):
        if statement[1] != 'true' and statement[1] != 'false':
            result = self.__evaluate_expression(statement[1], parameters)
        else:
            result = statement[1]
        if result == 'true':
            result = self.__run_statement(statement[2], parameters)
            if result == "exit exit exit exit":
                return
        elif result == 'false':
            if len(statement) > 3:
                result = self.__run_statement(statement[3], parameters)
                if result == "exit exit exit exit":
                    return
        else:
            self.super.error(ErrorType.TYPE_ERROR, f"Expression \"{statement[1]}\" did not result in boolean in if statement")

    def __execute_while_statement(self, statement, parameters):
        if statement[1] != 'true' and statement[1] != 'false':
            result = self.__evaluate_expression(statement[1], parameters)
        else:
            result = statement[1]
        if result != 'true' and result != 'false':
            self.super.error(ErrorType.TYPE_ERROR, f"Expression \"{statement[1]}\" did not result in boolean in while statement")
        while result == 'true':
            result = self.__run_statement(statement[2], parameters)
            if result == "exit exit exit exit":
                return
            result = self.__evaluate_expression(statement[1], parameters)
    
    def __execute_call_statement(self, statement, parameters):
        if statement[1] == self.super.ME_DEF:
            return self.call_method(statement[2], statement[3:]) # Need to check
        elif self.__get_native_type(statement[1], parameters) is None:
            self.super.error(ErrorType.FAULT_ERROR, "Call to method of class null")
        else:
            object = self.__get_native_type(statement[1], parameters)
            return object.call_method(statement[2], statement[3:])
        

    def __var_type(self,argument):
        if type(argument) is list:
            return "expression"
        if argument[0] == '"' and argument[-1] == '"':
            return self.super.STRING_DEF
        elif argument == 'true' or  argument == 'false':
            return self.super.BOOL_DEF
        elif argument == 'null':
            return self.super.NULL_DEF
        elif argument[0] == '-':
            if argument[1:].isdigit():
                return self.super.INT_DEF
        elif argument.isdigit():
            return self.super.INT_DEF
        else:
            # NEED TO DO
            # this will be a variable or classname
            return "variable or object"
        
    def __get_native_type(self,argument, parameters):
        if type(argument) is ObjectDefinition:
            return argument
        if type(argument) is list:
            temp = self.__evaluate_expression(argument, parameters)
            return self.__get_native_type(temp, parameters)
        if argument[0] == '"' and argument[-1] == '"':
            return argument.strip("\"")
        elif argument == 'true':
            return True
        elif argument == 'false':
            return False
        elif argument == 'null':
            return None
        elif argument[0] == '-':
            if argument[1:].isdigit():
                return int(argument)
        elif argument.isdigit() :
            return int(argument)
        else:
            # NEED TO DO
            # this will be a variable or classname
            if argument in parameters:
                return self.__get_native_type(parameters[argument], parameters)
            elif argument in self.obj_fields:
                return self.__get_native_type(self.obj_fields[argument], parameters)
            else:
                self.super.error(ErrorType.NAME_ERROR,
                                      f"{argument} Does not exist.")
            return argument
    

    def __evaluate_expression(self, expression, parameters):
        operand = expression[0]
        if operand == '+' or operand == '-' or operand == '*' or operand == '/' or operand == '%':
            result = self.__handle_arithmetic(expression, parameters)
        elif operand == '!':
            result = self.__handle_not(expression, parameters)
        elif operand == '>' or operand == '<' or operand == '>=' or operand == '<=' or operand == '!=' or operand == '==':
            result = self.__handle_comparison(expression, parameters)
        elif operand == self.super.CALL_DEF:
            result = self.__execute_call_statement(expression, parameters)
        elif operand == self.super.NEW_DEF:
            if expression[1] in self.interpreter.class_map:
                class_def = self.interpreter.class_map[expression[1]]
                return class_def.instantiate_object()
            else:
                self.super.error(ErrorType.NAME_ERROR,
                                      f"{expression} Class does not exist.")
        # check if class is in class map self.above.class_map
        # if so create a class definition with class map stuff
        # and then use that class def to create a object definition
        # and then store that object definition in a variable
        # what about native type too

        else:
            result = "abc"
        
        return result

    def __handle_arithmetic(self,expression, parameters):
        operand = expression[0]
        argument1 = self.__get_native_type(expression[1], parameters)
        argument2 = self.__get_native_type(expression[2], parameters)
        if operand == '+':
            if (type(argument1) != int and type(argument1) != str) or type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} Not a compatible operation.")
            else:
                if type(argument1) == str:
                    result =  "\"" + argument1 + argument2 + "\""
                else:
                    result = argument1 + argument2
        elif operand == '-':
            if type(argument1) != int or type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} Not a compatible operation.")
            else:
                result =  argument1 - argument2
        elif operand == '*':
            if type(argument1) != int or type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} Not a compatible operation.")
            else:
                result =  argument1 * argument2
        elif operand == '/':
            if type(argument1) != int or type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} Not a compatible operation.")
            else:
                result =  argument1 / argument2
        elif operand == '%':
            if type(argument1) != int or type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} arg1 {argument1} arg2 {argument2} Not a compatible operation.")
            else:
                result =  argument1 % argument2
        # print(f"{expression} {argument1} {argument2}")
        return str(result)

    def __handle_not(self, expression, parameters):
        # if self.__var_type(expression[1]) == "variable or object":
            
        # if self.__var_type(expression[1]) != self.super.BOOL_DEF:
        #     self.super.error(ErrorType.TYPE_ERROR,
        #                               f"{expression} Not a compatible operation.")
        # else:
        if type(expression[1]) is list:
            currval = self.__evaluate_expression(expression[1], parameters)
            currval = self.__get_native_type(currval, parameters)
        else:
            currval = self.__get_native_type(expression[1], parameters)

        # print("curr", currval)
        if currval == False:
            return 'true'
        elif currval == True:
            return 'false'
        else:
            self.super.error(ErrorType.TYPE_ERROR,
                                       f"{expression} Not a compatible operation.")
            

    def __handle_comparison(self, expression, parameters):
        operand = expression[0]
        argument1 = self.__get_native_type(expression[1], parameters)
        argument2 = self.__get_native_type(expression[2], parameters)
        if type(argument1) != type(argument2):
                self.super.error(ErrorType.TYPE_ERROR,
                                      f"{expression} arg1 {argument1} arg2 {argument2} Not a compatible operation.")
        if operand == '>':
            result =  argument1 > argument2
        elif operand == '<':
            result =  argument1 < argument2
        elif operand == '>=':
            result =  argument1 >= argument2
        elif operand == '<=':
            result =  argument1 <= argument2
        elif operand == '!=':
            result =  argument1 != argument2
        elif operand == '==':
            result =  argument1 == argument2

        if result == True:
            result = 'true'
        elif result == False:
            result = 'false'
            
        return result












if __name__ == '__main__':
#     program = ['''(class main
#  (field x 5)
#  (method main ()
#   (begin
#    (print x)
#    (set x "def")
#    (print x)
#    (set x (+ 5 7))
#    (print x)
#    (print "here's a result " (* 3 5) " and here's a boolean" true)
#    (set x true)
#    (set x (+ "576" "5"))
#    (print x)
#   )
#  )
#  (method test (a b)
#   (begin
#    (set a "def")
#    (print a)
#    (set b 20)
#    (print "here's a result " (* 3 5) " and here's a boolean" true)
#    (print b)
#    (print x)
#   )
#  )
# )
# (class bob
#  (field x "abc")
#  (method main ()
#   (begin
#    (set x "def")
#    (print x)
#    (set x 20)
#    (print x)
#    (set x true)
#    (print x)
#   )
#  )
# )
# ''']

#     program = ['''(class main
#         (field x 0)
#         (method main () 
#           (begin
#            (set x (+ "abc" (+ "def" "g")))
#            (print x)
#            (set x (+ 3 (- 5 1)))
#            (set x false)
#            (if (== true x) 
#              (print "x is even")
#              (print "x is odd")
#            )
#            (set x 5)
#            (while (> 0 x ) 
#              (begin
#                (print "x is " x)
#                (set x (- x 1))
#              ) 
#            )
#            (set x (! false))  
#            (print x)     
#            (if (! (! x)) 
#              (print "lucky seven") 
#            )  
#            (if (!= x (! (! false))) (print "that's true") (print "this won't print"))    
#           )
#   )
# )
# ''']

    program = ['''(class main
 (field x "abc")
 (method main ()
  (begin
   (set x "def")
   (print x)
   (set x 20)
   (print x)
   (set x true)
   (print x)
  )
 )
)
	

''']
    interpreter = Interpreter()
    interpreter.run(program) 