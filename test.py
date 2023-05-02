class_map = {}

class_map["abc"] = {}
class_map["abc"]["methods"] = {}
class_map["abc"]["fields"] = {}


fields = {
    "a": 5,
    "b": 43,
    "c": 343,
    "g": "abc"
}

# for name, value in fields.items():
#     print(name, value)

def get_native_type(argument):
    if argument[0] == '"' and argument[-1] == '"':
        return argument.strip("\"")
    
print(type(get_native_type('"20"')))