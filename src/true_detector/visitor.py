import ast


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.stats = {"class_methods": {}, "callables": set(), "calls": set(), "assignments": {}}

    def visit_ClassDef(self, node):
        class_name = node.name
        self.stats["callables"].add(class_name)

        for attribute in node.body:
            if isinstance(attribute, ast.Assign):
                pass  # TODO: add handler
            elif isinstance(attribute, ast.FunctionDef):
                self.stats["callables"].add(".".join([class_name, attribute.name]))
                self.stats["class_methods"][attribute.name] = attribute.lineno
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        class_method = self.stats["class_methods"].get(node.name, None)
        if not class_method or class_method != node.lineno:
            self.stats["callables"].add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        if hasattr(node.func, "id"):
            self.stats["calls"].add(node.func.id)
        else:
            _call = self._create_callable_path(node.func)
            self.stats["calls"].add(_call)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        targets = [name.id for name in node.targets]
        if not hasattr(node.value, "func"):
            self.generic_visit(node)
            return
        _call = self._create_callable_path(node.value.func)
        if _call in self.stats["assignments"]:
            self.stats["assignments"][_call].extend(targets)
        else:
            self.stats["assignments"][_call] = targets
        self.generic_visit(node)
    
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
        for _call in self.stats["calls"]:
            if _call in self.stats["callables"]:
                self.stats["callables"].remove(_call)
                used.add(_call)
            # Built-in, import calls and assignments
            # TODO: fix for assignments and imports
            elif _call.split(".")[0] == _call:
                used.add(_call)
        self.stats["calls"] -= used
        self.stats.pop("class_methods")
        self.stats.pop("assignments")
        return self.stats
