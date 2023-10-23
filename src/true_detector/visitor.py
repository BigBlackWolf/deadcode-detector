import ast


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.assignments = {}
        self.callables = set()
        self.calls = set()
        self.class_methods = {}
        self.imports = set()
        self.import_alliases = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        self.callables.add(class_name)

        for attribute in node.body:
            if isinstance(attribute, ast.Assign):
                pass  # TODO: add handler
            elif isinstance(attribute, ast.FunctionDef):
                self.callables.add(".".join([class_name, attribute.name]))
                self.class_methods[attribute.name] = attribute.lineno
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        class_method = self.class_methods.get(node.name, None)
        if not class_method or class_method != node.lineno:
            self.callables.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if hasattr(node.func, "id"):
            self.calls.add(node.func.id)
        else:
            _call = self._create_callable_path(node.func)
            self.calls.add(_call)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        targets = [name.id for name in node.targets]
        if not hasattr(node.value, "func"):
            self.generic_visit(node)
            return
        _call = self._create_callable_path(node.value.func)
        if _call in self.assignments:
            self.assignments[_call].extend(targets)
        else:
            self.assignments[_call] = targets
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for _name in node.names:
            self.imports.add(_name.name)
            if _name.asname:
                self.import_alliases[_name.asname] = _name.name
    
    def visit_ImportFrom(self, node):
        module = node.module
        for _name in node.names:
            import_name = f"{module}.{_name.name}"
            self.imports.add(import_name)
            if _name.asname:
                self.import_alliases[_name.asname] = import_name
    
    @classmethod
    def _create_callable_path(cls, func: ast.Attribute | ast.Name) -> str:
        modules = []
        while isinstance(func, ast.Attribute):
            modules.append(func.attr)
            func = func.value
        modules.append(func.id)
        return ".".join(modules[::-1])
        
    def report(self):
        used = set()
        extend = set()
        for _call in self.calls:
            if _call in self.callables:
                self.callables.remove(_call)
                used.add(_call)
            # Built-in and assignments
            # TODO: fix for assignments
            first_part = _call.split(".")[0]
            if first_part == _call and first_part not in self.imports:
                used.add(_call)
            elif first_part in self.import_alliases:
                used.add(_call)
                unaliased = _call.replace(first_part, self.import_alliases[first_part])
                extend.add(unaliased)
        self.calls -= used
        self.calls |= extend
        return {"calls": self.calls, "callables": self.callables}
