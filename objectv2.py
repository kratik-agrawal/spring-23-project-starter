"""
Module handling the operations of an object. This contains the meat
of the code to execute various instructions.
"""

from env_v1 import EnvironmentManager
from intbase import InterpreterBase, ErrorType
from type_valuev1 import create_value
from type_valuev1 import Type, Value
from copy import deepcopy

class ObjectDef:
    STATUS_PROCEED = 0
    STATUS_RETURN = 1
    STATUS_NAME_ERROR = 2
    STATUS_TYPE_ERROR = 3

    def __init__(self, interpreter, class_def, trace_output, super_class = None):
        self.interpreter = interpreter  # objref to interpreter object. used to report errors, get input, produce output
        self.class_def = class_def  # take class body from 3rd+ list elements, e.g., ["class",classname", [classbody]]
        self.trace_output = trace_output
        self.super_class = super_class
        self.__map_fields_to_values()
        self.__map_method_names_to_method_definitions()
        self.__create_map_of_operations_to_lambdas()  # sets up maps to facilitate binary and unary operations, e.g., (+ 5 6)

    def call_method(self, method_name, actual_params, line_num_of_caller):
        """
        actual_params is a list of Value objects (all parameters are passed by value).

        The caller passes in the line number so we can properly generate an error message.
        The error is then generated at the source (i.e., where the call is initiated).
        """
        if method_name not in self.methods:
            # print(self.super_class)
            if self.super_class is not None:
                # print("hi")
                return self.super_class.call_method(method_name, actual_params, line_num_of_caller)
            else:
                self.interpreter.error(
                    ErrorType.NAME_ERROR,
                    "unknown method " + method_name,
                    line_num_of_caller,
                )
        method_info = self.methods[method_name]
        if len(actual_params) != len(method_info.formal_params):
            if self.super_class is not None:
                return self.super_class.call_method(method_name, actual_params, line_num_of_caller)
            else:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "invalid number of parameters in call to " + method_name,
                    line_num_of_caller,
                )
        env = (
            EnvironmentManager()
        )  # maintains lexical environment for function; just params for now

        # NEED TO CHECK VALUES FOR ACTUAL VS EXPECTING IN FORMAL - NAME ERROR
        for formal, actual in zip(method_info.formal_params, actual_params):
            if actual.type() == Type.CLASS and self.__get_type(formal[0]) == actual.type():
                if formal[0] != actual.value().class_def.name and self.interpreter.isChild(formal[0], actual.value().class_def.name) == False:
                    if self.super_class is not None:
                        return self.super_class.call_method(method_name, actual_params, line_num_of_caller)
                    else:
                        self.interpreter.error(
                            ErrorType.NAME_ERROR,
                            "method call with wrong parameter types " + formal[0],
                            line_num_of_caller,
                        )
            if self.__get_type(formal[0]) != actual.type():
                if self.super_class is not None:
                    return self.super_class.call_method(method_name, actual_params, line_num_of_caller)
                else:
                    self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "method call with wrong parameter types " + formal,
                        line_num_of_caller,
                    )
            env.set(formal, actual)

        # since each method has a single top-level statement, execute it.
        status, return_value = self.__execute_statement(env, method_info.code)

        # NEED TO DO RETURN TYPE CHECKING - TYPE ERROR
        # For Void methods make sure it doesnt return anything
        if method_info.method_return_type == InterpreterBase.VOID_DEF:
            # print(status, return_value.type())
            if status == ObjectDef.STATUS_RETURN and return_value.type() != Type.NOTHING:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "returning something to a void method " + method_info.method_name + method_info.method_return_type,
                    line_num_of_caller,
                )
            return Value(Type.NOTHING, None)
        
        # For all other methods make sure return type, if returning is correct
        # if the method explicitly used the (return expression) statement to return a value, then return that
        # value back to the caller if it is the correct type
        # print(status, return_value.type())
        # print("return val", return_value.type(), return_value.value().class_def.name)
        if status == ObjectDef.STATUS_RETURN and return_value.type() != Type.NOTHING:
            if self.__get_type(method_info.method_return_type) != return_value.type():
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "wrong return type for method ",
                    line_num_of_caller,
                )
            if return_value.type() == Type.CLASS:
                if return_value.value() != None and method_info.method_return_type != return_value.value().class_def.name:
                    if self.interpreter.isChild(method_info.method_return_type, return_value.value().class_def.name) == False:
                        self.interpreter.error(
                            ErrorType.TYPE_ERROR,
                            "wrong return type for method ",
                            line_num_of_caller,
                        )    
            
            return return_value

        # NEED TO DO DEFAULT RETURN VALUES
        # The method didn't explicitly return a value, so handle default values
        if method_info.method_return_type == InterpreterBase.INT_DEF:
            return create_value("0")
        elif method_info.method_return_type == InterpreterBase.BOOL_DEF:
            return create_value("false")
        elif method_info.method_return_type == InterpreterBase.STRING_DEF:
            return create_value("\"\"")
        elif self.__get_type(method_info.method_return_type) == Type.CLASS:
            return create_value("null")
        
        return Value(InterpreterBase.NOTHING_DEF)

    def __execute_statement(self, env, code):
        """
        returns (status_code, return_value) where:
        - status_code indicates if the next statement includes a return
            - if so, the current method should terminate
            - otherwise, the next statement in the method should run normally
        - return_value is a Value containing the returned value from the function
        """
        if self.trace_output:
            print(f"{code[0].line_num}: {code}")
        tok = code[0]
        if tok == InterpreterBase.BEGIN_DEF:
            return self.__execute_begin(env, code)
        if tok == InterpreterBase.SET_DEF:
            return self.__execute_set(env, code)
        if tok == InterpreterBase.IF_DEF:
            return self.__execute_if(env, code)
        if tok == InterpreterBase.CALL_DEF:
            return self.__execute_call(env, code)
        if tok == InterpreterBase.WHILE_DEF:
            return self.__execute_while(env, code)
        if tok == InterpreterBase.RETURN_DEF:
            return self.__execute_return(env, code)
        if tok == InterpreterBase.INPUT_STRING_DEF:
            return self.__execute_input(env, code, True)
        if tok == InterpreterBase.INPUT_INT_DEF:
            return self.__execute_input(env, code, False)
        if tok == InterpreterBase.PRINT_DEF:
            return self.__execute_print(env, code)
        if tok == InterpreterBase.LET_DEF:
            return self.__execute_let(env,code)

        self.interpreter.error(
            ErrorType.SYNTAX_ERROR, "unknown statement " + tok, tok.line_num
        )

    # (begin (statement1) (statement2) ... (statementn))
    def __execute_begin(self, env, code):
        for statement in code[1:]:
            status, return_value = self.__execute_statement(env, statement)
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return
        return ObjectDef.STATUS_PROCEED, None

    # (call object_ref/me methodname param1 param2 param3)
    # where params are expressions, and expresion could be a value, or a (+ ...)
    # statement version of a method call; there's also an expression version of a method call below
    def __execute_call(self, env, code):
        return ObjectDef.STATUS_PROCEED, self.__execute_call_aux(
            env, code, code[0].line_num
        )

    # (set varname expression), where expresion could be a value, or a (+ ...)
    def __execute_set(self, env, code):
        val = self.__evaluate_expression(env, code[2], code[0].line_num)
        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # (return expression) where expresion could be a value, or a (+ ...)
    def __execute_return(self, env, code):
        if len(code) == 1:
            # [return] with no return expression
            return ObjectDef.STATUS_RETURN, create_value(InterpreterBase.NOTHING_DEF)
        return ObjectDef.STATUS_RETURN, self.__evaluate_expression(
            env, code[1], code[0].line_num
        )

    # (print expression1 expression2 ...) where expresion could be a variable, value, or a (+ ...)
    def __execute_print(self, env, code):
        output = ""
        for expr in code[1:]:
            # TESTING NOTE: Will not test printing of object references
            term = self.__evaluate_expression(env, expr, code[0].line_num)
            val = term.value()
            typ = term.type()
            if typ == Type.BOOL:
                val = "true" if val else "false"
            # document - will never print out an object ref
            output += str(val)
        self.interpreter.output(output)
        return ObjectDef.STATUS_PROCEED, None

    # (inputs target_variable) or (inputi target_variable) sets target_variable to input string/int
    def __execute_input(self, env, code, get_string):
        inp = self.interpreter.get_input()
        if get_string:
            val = Value(Type.STRING, inp)
        else:
            val = Value(Type.INT, int(inp))

        self.__set_variable_aux(env, code[1], val, code[0].line_num)
        return ObjectDef.STATUS_PROCEED, None

    # helper method used to set either parameter variables or member fields; parameters currently shadow
    # member fields
    def __set_variable_aux(self, env, var_name, value, line_num):
        # parameter shadows fields
        if value.type() == Type.NOTHING:
            self.interpreter.error(
                ErrorType.TYPE_ERROR, "can't assign to nothing " + var_name, line_num
            )
        param_val = env.get(var_name)
        if param_val is not None:
            if value.type() != param_val.type():
               self.interpreter.error(
                ErrorType.TYPE_ERROR, "set of wrong type " + var_name, line_num
            ) 
            # print(value.value().class_def.name, env.get_type(var_name))
            if value.type() == Type.CLASS and (value.value().class_def.name != env.get_type(var_name) \
                                               and self.interpreter.isChild(env.get_type(var_name), value.value().class_def.name) == False):
                self.interpreter.error(
                    ErrorType.TYPE_ERROR, "set variable doesn't apply to poly", line_num
                )
            env.set([param_val.type(), var_name], value)
            return

        if var_name not in self.fields:
            self.interpreter.error(
                ErrorType.NAME_ERROR, "unknown variable " + var_name, line_num
            )
        for fld in self.class_def.get_fields():
            if fld.field_name == var_name:
                field_type = fld.field_type
        print(value.type(), value.value(), self.class_def.get_fields(), self.fields[var_name].type(), self.fields[var_name].value())
        if value.type() == Type.CLASS and (value.value().class_def.name != field_type \
                                               and self.interpreter.isChild(field_type, value.value().class_def.name) == False):
                self.interpreter.error(
                    ErrorType.TYPE_ERROR, "set variable doesn't apply to poly", line_num
                )
        if self.fields[var_name].type() != value.type():
            self.interpreter.error(
                ErrorType.TYPE_ERROR, "set of wrong type field " + var_name, line_num
            ) 
        self.fields[var_name] = value

    # (if expression (statement) (statement) ) where expresion could be a boolean constant (e.g., true), member
    # variable without ()s, or a boolean expression in parens, like (> 5 a)
    def __execute_if(self, env, code):
        condition = self.__evaluate_expression(env, code[1], code[0].line_num)
        if condition.type() != Type.BOOL:
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                "non-boolean if condition " + ' '.join(x for x in code[1]),
                code[0].line_num,
            )
        if condition.value():
            status, return_value = self.__execute_statement(
                env, code[2]
            )  # if condition was true
            return status, return_value
        if len(code) == 4:
            status, return_value = self.__execute_statement(
                env, code[3]
            )  # if condition was false, do else
            return status, return_value
        return ObjectDef.STATUS_PROCEED, None

    # (while expression (statement) ) where expresion could be a boolean value, boolean member variable,
    # or a boolean expression in parens, like (> 5 a)
    def __execute_while(self, env, code):
        while True:
            condition = self.__evaluate_expression(env, code[1], code[0].line_num)
            if condition.type() != Type.BOOL:
                self.interpreter.error(
                    ErrorType.TYPE_ERROR,
                    "non-boolean while condition " + ' '.join(x for x in code[1]),
                    code[0].line_num,
                )
            if not condition.value():  # condition is false, exit loop immediately
                return ObjectDef.STATUS_PROCEED, None
            # condition is true, run body of while loop
            status, return_value = self.__execute_statement(env, code[2])
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
            
    # (let (vars) (statements)... ) where vars are local variables and statements is like begin statement
    def __execute_let(self, env, code):
        #needs to do
        envLocal = deepcopy(env)
        local_vars = set()
        for var in code[1]:
            if var[1] in local_vars:
                self.interpreter.error(
                        ErrorType.NAME_ERROR,
                        "duplicate local vars " + var[1]
                    )
            #check if type of value is fine
            #add to envLocal
            determined_value = create_value(var[2])
            expected_type = self.__get_type(var[0])
            if determined_value.type() != expected_type:
                self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "trying to set value of local var to wrong type " 
                    )
            envLocal.set(var[0:2],determined_value)
            local_vars.add(var[1])
        for statement in code[2:]:
            status, return_value = self.__execute_statement(envLocal, statement)
            if status == ObjectDef.STATUS_RETURN:
                return (
                    status,
                    return_value,
                )  # could be a valid return of a value or an error
        # if we run thru the entire block without a return, then just return proceed
        # we don't want the calling block to exit with a return
        return ObjectDef.STATUS_PROCEED, None

    # given an expression, return a Value object with the expression's evaluated result
    # expressions could be: constants (true, 5, "blah"), variables (e.g., x), arithmetic/string/logical expressions
    # like (+ 5 6), (+ "abc" "def"), (> a 5), method calls (e.g., (call me foo)), or instantiations (e.g., new dog_class)
    def __evaluate_expression(self, env, expr, line_num_of_statement):
        if not isinstance(expr, list):
            # locals shadow member variables
            if expr == InterpreterBase.ME_DEF:
                return Value(Type.CLASS, self)
            val = env.get(expr)
            if val is not None:
                return val
            if expr in self.fields:
                return self.fields[expr]
            # need to check for variable name and get its value too
            value = create_value(expr)
            if value is not None:
                return value
            self.interpreter.error(
                ErrorType.NAME_ERROR,
                "invalid field or parameter " + expr,
                line_num_of_statement,
            )

        operator = expr[0]
        if operator in self.binary_op_list:
            operand1 = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            operand2 = self.__evaluate_expression(env, expr[2], line_num_of_statement)
            if operand1.type() == operand2.type() and operand1.type() == Type.INT:
                if operator not in self.binary_ops[Type.INT]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to ints",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.INT][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.STRING:
                if operator not in self.binary_ops[Type.STRING]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to strings",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.STRING][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.BOOL:
                if operator not in self.binary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to bool",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.BOOL][operator](operand1, operand2)
            if operand1.type() == operand2.type() and operand1.type() == Type.CLASS:
                if operator not in self.binary_ops[Type.CLASS]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid operator applied to class",
                        line_num_of_statement,
                    )
                return self.binary_ops[Type.CLASS][operator](operand1, operand2)
            # error what about an obj reference and null
            self.interpreter.error(
                ErrorType.TYPE_ERROR,
                f"operator {operator} applied to two incompatible types",
                line_num_of_statement,
            )
        if operator in self.unary_op_list:
            operand = self.__evaluate_expression(env, expr[1], line_num_of_statement)
            if operand.type() == Type.BOOL:
                if operator not in self.unary_ops[Type.BOOL]:
                    self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "invalid unary operator applied to bool",
                        line_num_of_statement,
                    )
                return self.unary_ops[Type.BOOL][operator](operand)

        # handle call expression: (call objref methodname p1 p2 p3)
        if operator == InterpreterBase.CALL_DEF:
            return self.__execute_call_aux(env, expr, line_num_of_statement)
        # handle new expression: (new classname)
        if operator == InterpreterBase.NEW_DEF:
            return self.__execute_new_aux(env, expr, line_num_of_statement)

    # (new classname)
    def __execute_new_aux(self, _, code, line_num_of_statement):
        obj = self.interpreter.instantiate(code[1], line_num_of_statement)
        return Value(Type.CLASS, obj)

    # this method is a helper used by call statements and call expressions
    # (call object_ref/me methodname p1 p2 p3)
    def __execute_call_aux(self, env, code, line_num_of_statement):
        # determine which object we want to call the method on
        obj_name = code[1]
        if obj_name == InterpreterBase.ME_DEF:
            obj = self
        elif obj_name == InterpreterBase.SUPER_DEF:
            obj = self.super_class
        else:
            obj = self.__evaluate_expression(
                env, obj_name, line_num_of_statement
            ).value()
        # prepare the actual arguments for passing
        if obj is None:
            self.interpreter.error(
                ErrorType.FAULT_ERROR, "null dereference", line_num_of_statement
            )
        actual_args = []
        for expr in code[3:]:
            actual_args.append(
                self.__evaluate_expression(env, expr, line_num_of_statement)
            )
        return obj.call_method(code[2], actual_args, line_num_of_statement)

    def __map_method_names_to_method_definitions(self):
        self.methods = {}
        for method in self.class_def.get_methods():
            self.methods[method.method_name] = method

    def __map_fields_to_values(self):
        self.fields = {}
        for field in self.class_def.get_fields():
            determined_value = create_value(field.default_field_value)
            expected_value = self.__get_type(field.field_type)
            # print(field.field_type, field.default_field_value, determined_value.type(), expected_value)
            if determined_value.type() != expected_value:
                self.interpreter.error(
                        ErrorType.TYPE_ERROR,
                        "trying to set value of field to wrong type " 
                    )
            self.fields[field.field_name] = determined_value

    def __create_map_of_operations_to_lambdas(self):
        self.binary_op_list = [
            "+",
            "-",
            "*",
            "/",
            "%",
            "==",
            "!=",
            "<",
            "<=",
            ">",
            ">=",
            "&",
            "|",
        ]
        self.unary_op_list = ["!"]
        self.binary_ops = {}
        self.binary_ops[Type.INT] = {
            "+": lambda a, b: Value(Type.INT, a.value() + b.value()),
            "-": lambda a, b: Value(Type.INT, a.value() - b.value()),
            "*": lambda a, b: Value(Type.INT, a.value() * b.value()),
            "/": lambda a, b: Value(
                Type.INT, a.value() // b.value()
            ),  # // for integer ops
            "%": lambda a, b: Value(Type.INT, a.value() % b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.STRING] = {
            "+": lambda a, b: Value(Type.STRING, a.value() + b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
            ">": lambda a, b: Value(Type.BOOL, a.value() > b.value()),
            "<": lambda a, b: Value(Type.BOOL, a.value() < b.value()),
            ">=": lambda a, b: Value(Type.BOOL, a.value() >= b.value()),
            "<=": lambda a, b: Value(Type.BOOL, a.value() <= b.value()),
        }
        self.binary_ops[Type.BOOL] = {
            "&": lambda a, b: Value(Type.BOOL, a.value() and b.value()),
            "|": lambda a, b: Value(Type.BOOL, a.value() or b.value()),
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }
        self.binary_ops[Type.CLASS] = {
            "==": lambda a, b: Value(Type.BOOL, a.value() == b.value()),
            "!=": lambda a, b: Value(Type.BOOL, a.value() != b.value()),
        }

        self.unary_ops = {}
        self.unary_ops[Type.BOOL] = {
            "!": lambda a: Value(Type.BOOL, not a.value()),
        }

    def __get_type(self, type):
        if type == "bool":
            return Type.BOOL
        elif type == "int":
            return Type.INT
        elif type == "string":
            return Type.STRING
        elif type == "void":
            return Type.VOID
        else:
            if type in self.interpreter.class_index:
                return Type.CLASS
            
        return Type.NOTHING
        #handle class stuff here?