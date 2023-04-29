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
            class_definition = ClassDefiniton(super(),class_name, methods, fields)
            self.class_map[class_name] = class_definition
        return

def get_native_type(argument):
    if type(argument) is list:
        return evaluate_expression(argument)
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
    elif argument.isdigit():
        return int(argument)
    else:
        # NEED TO DO
        # this will be a variable or classname
        return argument

def evaluate_expression(argument):
    return 0


class ClassDefiniton:
    def __init__(self, super, name, methods, fields):
        self.super = super
        self.my_name = name
        self.my_methods = methods
        self.my_fields = fields
        return 
    
    def instantiate_object(self):
        obj = ObjectDefinition(self.super)
        for name, details in self.my_methods.items():
            obj.add_method(name, details)

        for name, value in self.my_fields.items():
            obj.add_field(name, value)
        return obj
    

class ObjectDefinition:
    def __init__(self, super):
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
        method = self.obj_methods[method_name]
        if len(method['arguments']) != len(parameters):
            super().error(ErrorType.TYPE_ERROR,
                                      "Wrong number of arguments for method")
        else:
            parameter_map = {}
            for idx, val in enumerate(method['arguments']):
                parameter_map[val] = parameters[idx]
        statement = method['statement']
        result = self.__run_statement(statement, parameter_map)
        return result
    
    def __run_statement(self, statement, parameters):
        statement_type = statement[0]
        if statement_type == self.super.PRINT_DEF:
            result = self.__execute_print_statement(statement, parameters)
        elif statement_type == self.super.INPUT_INT_DEF or statement_type == self.super.INPUT_STRING_DEF:
            result = self.__execute_input_statement(statement, parameters)
        elif statement_type == self.super.CALL_DEF:
            result = self.__execute_call_statement(statement)
        elif statement_type == self.super.WHILE_DEF:
            result = self.__execute_while_statement(statement)
        elif statement_type == self.super.IF_DEF:
            result = self.__execute_if_statement(statement)
        elif statement_type == self.super.RETURN_DEF:
            result = self.__execute_return_statement(statement)
        elif statement_type == self.super.BEGIN_DEF:
            result = self.__execute_begin_statement(statement, parameters)
        elif statement_type == self.super.SET_DEF:
            result = self.__execute_set_statement(statement, parameters) 
        else:
            return 0
        #might need more
        return result
    
    def __execute_print_statement(self, statement, parameters):
        result = ""
        for arg in statement[1:]: ## ignoring the print command itself
            #need to evaluate arg
            val = get_native_type(arg)
            if val in parameters:
                val = parameters[val]
            if val in self.obj_fields:
                val = self.obj_fields[val]
            elif val == True or val == False:
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
    def __execute_set_statement(self, statement, parameters):
        # print(statement, "parameters before", parameters, "\n")
        # set_value = get_native_type(statement[2])
        set_value = statement[2]
        if statement[1] in parameters: # if the value is in parameters, make it that value
            parameters[statement[1]] = set_value 
        elif statement[1] in self.obj_fields: # if the value is in the object, make it that value
            self.obj_fields[statement[1]] = set_value
        else:
            self.super.error(ErrorType.NAME_ERROR,
                                      f"{statement}Can't Set, field or name does not exist")
            return -1023
        # print(statement, "parameters after", parameters, "\n")
    def __execute_begin_statement(self,statement, parameters):
        for s in statement[1:]:
            result = self.__run_statement(s, parameters)




if __name__ == '__main__':
    program = ['''(class main
 (field x 5)
 (method main ()
  (begin
   (set x "def")
   (print x)
   (set x 20)
   (print "here's a result " (* 3 5) " and here's a boolean" true)
   (set x true)
   (print x)
  )
 )
 (method test (a b)
  (begin
   (set a "def")
   (print a)
   (set b 20)
   (print "here's a result " (* 3 5) " and here's a boolean" true)
   (inputi x)
   (print b)
   (print x)
  )
 )
)
(class bob
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