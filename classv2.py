# pylint: disable=too-few-public-methods

"""
# v2
- inheritance
  (class foo inherits bar ...)
  dynamic dispatch
  polymorphism
- static typing
.  update formal params to use VariableDef instead of just strings
.  check parameter type compatability on calls
.  change syntax for method definitions to:
   (method method_name ((type1 param1) (type2 param2) ...) (statement))
.  change MethodDef class to store typename and Type.??? instead of just strings for formal params
.  create new let statement, which is just like begin except it has locals
   (let ((type1 param1 val1) (type2 param2 val2)) (statement1) (statement2))
.  update environment to scope variables by block
.  update code to ensure variables go out of scope at end of block
.  change class syntax for field definitions:
   (field type name init_value)
.  update FieldDef class to support types of fields
.  need to support class names for types
.  update variable assignments to ensure types are consistent
.  update parameter passing code to make sure actual and formal args are consistent types
   . must handle polymorphism (passing subtype to f(supertype))
.  update overload checking code to check not only by # of parameters but by types in inheritance
.  have return type for methods
.  update return code to check return type of returned value
.  add void return type for methods that don't return a value
.  update method completion code to return default value (0, False, "", null) if no returned value
.  add test cases for returning a subclass (pass) of the return type, and a superclass (fail)
.  test for duplicate formal param names and generate error
.  test for invalid param types and return types
.  propagate type to null during return and when assigned to variable so we can't compare
   a null pointer of type person to a null pointer of type robot
"""

from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, create_value, create_default_value

class VariableDef:
    # var_type is a Type() and value is a Value()
    def __init__(self, var_type, var_name, value=None):
        self.type = var_type
        self.name = var_name
        self.value = value

    def set_value(self, value):
        self.value = value


# parses and holds the definition of a member method
# [method return_type method_name [[type1 param1] [type2 param2] ...] [statement]]
class MethodDef:
    def __init__(self, method_source):
        self.line_num = method_source[0].line_num  # used for errors
        self.method_name = method_source[2]
        if method_source[1] == InterpreterBase.VOID_DEF:
            self.return_type = Type(InterpreterBase.NOTHING_DEF)
        else:
            if '@' in method_source[1]:
                val =  method_source[1]
                self.return_type = Type(val[:val.find('@')],full_name= method_source[1])
            else:
                self.return_type = Type(method_source[1])
        self.formal_params = self.__parse_params(method_source[3])
        self.code = method_source[4]

    def get_method_name(self):
        return self.method_name

    def get_formal_params(self):
        return self.formal_params

    # returns a Type()
    def get_return_type(self):
        return self.return_type

    def get_code(self):
        return self.code

    # input params in the form of [[type1 param1] [type2 param2] ...]
    # output is a set of VariableDefs
    def __parse_params(self, params):
        formal_params = []
        for param in params:
            print(param)
            if '@' in param[0]:
                var_def = VariableDef(Type(param[0][:param[0].find('@')], full_name=param[0]), param[1])
            else:
                var_def = VariableDef(Type(param[0]), param[1])
            formal_params.append(var_def)
        return formal_params


# holds definition for a class, including a list of all the fields and their default values, all
# of the methods in the class, and the superclass information (if any)
# v2 class definition: [class classname [inherits baseclassname] [field1] [field2] ... [method1] [method2] ...]
# [] denotes optional syntax
class ClassDef:
    def __init__(self, class_source, interpreter):
        self.interpreter = interpreter
        self.name = class_source[1]
        self.class_source = class_source
        self.template = False
        self.fields_and_methods_start_index = (
            self.__check_for_inheritance_and_set_superclass_info(class_source)
        )
        self.__create_field_list(class_source[self.fields_and_methods_start_index:])
        self.__create_method_list(class_source[self.fields_and_methods_start_index:])
    
    def template_instantiation(self, templated_vars):
        # print(templated_vars)
        if self.num_parameterized_types != len(templated_vars):
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "templated class with not all types " + self.name,
                
            )
        print("bo", templated_vars)
        for i, typ in enumerate(self.parameterized_types_arr):
            self.parameterized_types[typ] = templated_vars[i]

        # handle and create all fields
        self.__template_instantiation_fields(self.class_source[self.fields_and_methods_start_index:])

        # handle and create all methods
        self.__template_instantiation_methods(self.class_source[self.fields_and_methods_start_index:])
        
        # handle and check all types
    
    def __template_instantiation_fields(self, class_body):
        self.fields = []  # array of VariableDefs with default values set
        self.field_map = {}
        fields_defined_so_far = set()
        for member in class_body:
            # member format is [field typename varname default_value]
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                if member[1] in self.parameterized_types:
                    member[1] = self.parameterized_types[member[1]]
                if '@' in member[1]:
                    temp = member[1].split('@')
                    for t in temp:
                        if t in self.parameterized_types:
                            t = self.parameterized_types[t]
                    member[1] = '@'.join(temp)
                    
                var_def = self.__create_variable_def_from_field(member)
                self.fields.append(var_def)
                self.field_map[member[2]] = var_def
                fields_defined_so_far.add(member[2])

    def __template_instantiation_methods(self, class_body):
        self.methods = []
        self.method_map = {}
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                print("bob", self.parameterized_types)
                if member[1] in self.parameterized_types:
                    member[1] = self.parameterized_types[member[1]]
                for param in member[3]:
                    if param[0] in self.parameterized_types:
                        param[0] = self.parameterized_types[param[0]]
                print(member)
                method_def = MethodDef(member)
                if method_def.method_name in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + method_def.method_name,
                        member[0].line_num,
                    )
                self.__check_method_names_and_types(method_def)
                self.methods.append(method_def)
                self.method_map[method_def.method_name] = method_def
                methods_defined_so_far.add(method_def.method_name)
                
    def __check_all_types_templates(self):
        return 1
    # get the classname
    def get_name(self):
        return self.name

    # get a list of FieldDef objects for all fields in the class
    def get_fields(self):
        return self.fields

    # get a list of MethodDef objects for all methods in the class
    def get_methods(self):
        return self.methods

    # returns a ClassDef object
    def get_superclass(self):
        return self.super_class

    def __check_for_inheritance_and_set_superclass_info(self, class_source):
        if class_source[0] == InterpreterBase.TEMPLATE_CLASS_DEF:
            self.super_class = None
            self.__handle_template_class(class_source)
            return 3
        if class_source[2] != InterpreterBase.INHERITS_DEF:
            self.super_class = None
            return 2  # fields and method definitions start after [class classname ...], jump to the correct place to continue parsing
        if class_source[2] == InterpreterBase.INHERITS_DEF:
            super_class_name = class_source[3]
            self.super_class = self.interpreter.get_class_def(
                super_class_name, class_source[0].line_num
            )
            return 4  # fields and method definitions start after [class classname inherits baseclassname ...]

    def __handle_template_class(self, class_source):
        self.template = True
        self.num_parameterized_types = len(class_source[2])
        self.parameterized_types = {}
        self.parameterized_types_arr = []
        for t in class_source[2]:
            self.parameterized_types[t] = ""
            self.parameterized_types_arr.append(t)
        self.__handle_fields_template(class_source[3:])
        self.__handle_methods_template(class_source[3:])
    
    # just check for duplicates
    def __handle_fields_template(self, class_body):
        fields_defined_so_far = set()
        # print(class_body)
        for member in class_body:
            # member format is [field typename varname default_value]
            # print(member)
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                # var_def = self.__create_variable_def_from_field(member)
                # self.fields.append(var_def)
                fields_defined_so_far.add(member[2])
    
    # just check for duplicates
    def __handle_methods_template(self, class_body):
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                # method_def = MethodDef(member)
                method_name = member[2]
                if method_name in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + method_name,
                        member[0].line_num,
                    )
                methods_defined_so_far.add(method_name)

    def __create_field_list(self, class_body):
        if self.template == True:
            return
        self.fields = []  # array of VariableDefs with default values set
        self.field_map = {}
        fields_defined_so_far = set()
        for member in class_body:
            # member format is [field typename varname default_value]
            if member[0] == InterpreterBase.FIELD_DEF:
                if member[2] in fields_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate field " + member[2],
                        member[0].line_num,
                    )
                if self.template != True:
                    var_def = self.__create_variable_def_from_field(member)
                    self.fields.append(var_def)
                    self.field_map[member[2]] = var_def
                fields_defined_so_far.add(member[2])

    # field def: [field typename varname defvalue]
    # returns a VariableDef object that represents that field
    def __create_variable_def_from_field(self, field_def):
        if len(field_def) == 3:
            # print(field_def)
            if '@' in field_def[1]:
                # print(field_def[1])
                if not self.interpreter.is_valid_type(field_def[1]):
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid use of templated class"
                    )
                var_def = VariableDef(
                    Type(field_def[1][0:field_def[1].find('@')], full_name=field_def[1]), field_def[2], create_default_value(Type(field_def[1][0:field_def[1].find('@')], full_name = field_def[1]))
                )
            else:
                var_def = VariableDef(
                    Type(field_def[1]), field_def[2], create_default_value(Type(field_def[1]))
                )   
        else:
            if '@' in field_def[1]:
                # print(field_def[1])
                if not self.interpreter.is_valid_type(field_def[1]):
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid use of templated class"
                    )
                var_def = VariableDef(
                    Type(field_def[1][0:field_def[1].find('@')], full_name=field_def[1]), field_def[2], create_value(field_def[3])
                )
            else: 
                var_def = VariableDef(
                    Type(field_def[1]), field_def[2], create_value(field_def[3])
                )
        # print(var_def.type.type_name, var_def.value.type().type_name)
        if not self.interpreter.check_type_compatibility(
            var_def.type, var_def.value.type(), True
        ):
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid type/type mismatch with field " + field_def[2],
                field_def[0].line_num,
            )
        return var_def

    def __create_method_list(self, class_body):
        if self.template == True:
            return
        self.methods = []
        self.method_map = {}
        methods_defined_so_far = set()
        for member in class_body:
            if member[0] == InterpreterBase.METHOD_DEF:
                method_def = MethodDef(member)
                if method_def.method_name in methods_defined_so_far:  # redefinition
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate method " + method_def.method_name,
                        member[0].line_num,
                    )
                self.__check_method_names_and_types(method_def)
                self.methods.append(method_def)
                self.method_map[method_def.method_name] = method_def
                methods_defined_so_far.add(method_def.method_name)

    # for a given method, make sure that the parameter types are valid, return type is valid, and param names
    # are not duplicated
    def __check_method_names_and_types(self, method_def):
        # print(method_def.return_type.type_name)
        if not self.interpreter.is_valid_type(
            method_def.return_type.type_name
        ) and method_def.return_type != Type(InterpreterBase.NOTHING_DEF): #checks that return type isn't a defined type or void
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "invalid return type for method " + method_def.method_name,
                method_def.line_num,
            )
        used_param_names = set()
        for param in method_def.formal_params:
            if param.name in used_param_names:
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "duplicate formal parameter " + param.name,
                    method_def.line_num,
                )
            if not self.interpreter.is_valid_type(param.type.type_name):
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid type for parameter " + param.name,
                    method_def.line_num,
                )
