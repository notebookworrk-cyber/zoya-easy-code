"""Tree-walking interpreter for executing Zoya AST nodes."""

from __future__ import annotations

import os
from typing import Any

from .ast import (
    Assign,
    AssignAttr,
    AssignIndex,
    ASTNode,
    BinOp,
    Block,
    Boolean,
    Break,
    Call,
    ClassDef,
    Continue,
    Dict_,
    EnumDef,
    ForEach,
    ForLoop,
    Function,
    GetAttr,
    Ident,
    If,
    Import,
    Index,
    Input,
    InterfaceDef,
    InterpolatedString,
    Lambda,
    List_,
    Loop,
    MethodCall,
    Number,
    Pass,
    Print,
    Return,
    Slice,
    String,
    Switch,
    Throw,
    Try,
    UnaryOp,
    While,
)
from .builtins import BUILTIN_FUNCTIONS, DICT_METHODS, LIST_METHODS, STRING_METHODS
from .environment import Environment
from .errors import (
    BreakException,
    ContinueException,
    ReturnException,
    RuntimeError_,
    ZoyaAttributeError,
    ZoyaIndexError,
    ZoyaNameError,
    ZoyaRuntimeError,
    ZoyaTypeError,
    ZoyaZeroDivisionError,
)


class ZoyaFunction:
    def __init__(self, decl: Function | Lambda, env: Environment) -> None:
        self.decl = decl
        self.env = env
        self.name = getattr(decl, "name", "")

    def __repr__(self) -> str:
        return f"<function {self.name}>" if self.name else "<lambda>"


class ZoyaModule:
    def __init__(self, name: str, functions: dict[str, Any]) -> None:
        self.name = name
        self.__dict__.update(functions)

    def __repr__(self) -> str:
        return f"<module {self.name}>"


class ZoyaClass:
    def __init__(
        self,
        name: str,
        parent: ZoyaClass | None,
        methods: dict[str, ZoyaFunction],
        env: Environment,
    ) -> None:
        self.name = name
        self.parent = parent
        self.methods = methods
        self.env = env

    def create_instance(self, args: list[Any], interp: Interpreter) -> ZoyaInstance:
        instance = ZoyaInstance(self)
        if "init" in self.methods:
            interp._call_function_internal(self.methods["init"], instance, args)
        return instance

    def __repr__(self) -> str:
        return f"<class {self.name}>"


class ZoyaInstance:
    def __init__(self, klass: ZoyaClass) -> None:
        self.klass = klass
        self._fields: dict[str, Any] = {}

    def _find_method(self, name: str) -> ZoyaFunction | None:
        k = self.klass
        while k is not None:
            if name in k.methods:
                return k.methods[name]
            k = k.parent
        return None

    def __contains__(self, item: Any) -> bool:
        return item in self._fields

    def __repr__(self) -> str:
        return f"<instance of {self.klass.name}>"


class ZoyaSuper:
    def __init__(self, instance: ZoyaInstance, klass: ZoyaClass) -> None:
        self._instance = instance
        self._klass = klass

    def __repr__(self) -> str:
        return f"<super of {self._klass.name}>"


class ZoyaEnumObj:
    def __init__(self, name: str, variants: list[str]) -> None:
        self._name = name
        for i, v in enumerate(variants):
            setattr(self, v, i)

    def __repr__(self) -> str:
        return f"<enum {self._name}>"


class ZoyaInterfaceObj:
    def __init__(self, name: str, methods: list[str]) -> None:
        self._name = name
        self._methods = methods

    def __repr__(self) -> str:
        return f"<interface {self._name}>"


class Interpreter:
    def __init__(self, file: str = "") -> None:
        self.global_env = Environment()
        self.current_env = self.global_env
        self.file = file
        self._init_builtins()

    def _init_builtins(self) -> None:
        from .builtins import register_builtins

        register_builtins(self.global_env)

    def interpret(self, node: ASTNode, env: Environment | None = None) -> Any:
        if env is not None:
            self.current_env = env
        return self._eval(node)

    def _eval(self, node: ASTNode) -> Any:
        line = getattr(node, "line", 0)
        col = getattr(node, "col", 0)

        if isinstance(node, Number):
            return node.value

        if isinstance(node, String):
            return node.value

        if isinstance(node, Boolean):
            return node.value

        if isinstance(node, InterpolatedString):
            result = ""
            for part in node.parts:
                if isinstance(part, str):
                    result += part
                elif isinstance(part, tuple):
                    expr_node, fmt = part
                    val = self._eval(expr_node)
                    try:
                        result += format(val, fmt)
                    except (ValueError, TypeError):
                        result += str(val)
                else:
                    val = self._eval(part)
                    result += str(val)
            return result

        if isinstance(node, Ident):
            name = node.name
            if self.current_env.has(name):
                return self.current_env.get(name)
            raise ZoyaNameError(name=name, line=line, col=col, file=self.file)

        if isinstance(node, Assign):
            val = self._eval(node.expr)
            self.current_env.set(node.name, val)
            return val

        if isinstance(node, AssignIndex):
            obj = self._eval(node.obj)
            index = self._eval(node.index)
            val = self._eval(node.expr)
            if isinstance(obj, list) and isinstance(index, int) or isinstance(obj, dict):
                obj[index] = val
            else:
                raise RuntimeError_(
                    "Cannot assign to index of this type", line=line, col=col, file=self.file
                )
            return val

        if isinstance(node, AssignAttr):
            obj = self._eval(node.obj)
            val = self._eval(node.expr)
            if isinstance(obj, ZoyaInstance):
                obj._fields[node.attr] = val
            else:
                setattr(obj, node.attr, val)
            return val

        if isinstance(node, BinOp):
            op = node.op
            if op == "AND":
                return self._truthy(self._eval(node.left)) and self._truthy(self._eval(node.right))
            if op == "OR":
                return self._truthy(self._eval(node.left)) or self._truthy(self._eval(node.right))

            left = self._eval(node.left)
            right = self._eval(node.right)

            if op == "POW":
                return left**right
            if op == "MOD":
                return left % right
            if op == "PLUS":
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)
                return left + right
            if op == "MINUS":
                return left - right
            if op == "MUL":
                return left * right
            if op == "DIV":
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    if right == 0:
                        raise ZoyaZeroDivisionError(
                            "Division by zero", line=line, col=col, file=self.file
                        )
                    return left / right
                raise RuntimeError_("Division requires numbers", line=line, col=col, file=self.file)
            if op == "FLOORDIV":
                if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                    if right == 0:
                        raise ZoyaZeroDivisionError(
                            "Division by zero", line=line, col=col, file=self.file
                        )
                    return left // right
                raise RuntimeError_("Division requires numbers", line=line, col=col, file=self.file)
            if op == "GT":
                return left > right
            if op == "LT":
                return left < right
            if op == "EQ":
                return left == right
            if op == "NE":
                return left != right
            if op == "GTE":
                return left >= right
            if op == "LTE":
                return left <= right
            if op == "IN":
                return left in right if hasattr(right, "__contains__") else False
            if op == "NOT_IN":
                return left not in right if hasattr(right, "__contains__") else True
            if op == "IS":
                return left is right
            if op == "IS_NOT":
                return left is not right
            raise RuntimeError_(f"Unknown operator: {op}", line=line, col=col, file=self.file)

        if isinstance(node, UnaryOp):
            expr = self._eval(node.expr)
            if node.op == "NOT":
                return not self._truthy(expr)
            if node.op == "MINUS":
                return -expr
            raise RuntimeError_(
                f"Unknown unary operator: {node.op}", line=line, col=col, file=self.file
            )

        if isinstance(node, Print):
            val = self._eval(node.expr)
            print(val)
            return val

        if isinstance(node, Input):
            prompt = ""
            if node.prompt is not None:
                prompt = str(self._eval(node.prompt))
            try:
                return input(prompt)
            except (EOFError, KeyboardInterrupt):
                return ""

        if isinstance(node, Block):
            result = None
            for stmt in node.statements:
                result = self._eval(stmt)
            return result

        if isinstance(node, If):
            cond = self._truthy(self._eval(node.cond))
            if cond:
                return self._eval_block(node.body)
            elif node.else_body is not None:
                return self._eval_block(node.else_body)
            return None

        if isinstance(node, While):
            result = None
            while self._truthy(self._eval(node.cond)):
                try:
                    result = self._eval_block(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        if isinstance(node, Loop):
            count = self._eval(node.count)
            if not isinstance(count, (int, float)):
                raise RuntimeError_(
                    "Loop count must be a number", line=line, col=col, file=self.file
                )
            result = None
            for _ in range(int(count)):
                try:
                    result = self._eval_block(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        if isinstance(node, ForLoop):
            return self._eval_for_loop(node)

        if isinstance(node, ForEach):
            return self._eval_for_each(node)

        if isinstance(node, Switch):
            return self._eval_switch(node)

        if isinstance(node, Try):
            return self._eval_try(node)

        if isinstance(node, Throw):
            val = self._eval(node.expr)
            if isinstance(val, str):
                raise ZoyaRuntimeError(val, line=line, col=col, file=self.file)
            raise ZoyaRuntimeError(str(val), line=line, col=col, file=self.file)

        if isinstance(node, Match):
            return self._eval_match(node)

        if isinstance(node, EnumDef):
            enum_obj = ZoyaEnumObj(node.name, node.variants)
            self.current_env.set(node.name, enum_obj)
            return enum_obj

        if isinstance(node, ClassDef):
            return self._eval_class_def(node)

        if isinstance(node, InterfaceDef):
            interface_obj = ZoyaInterfaceObj(node.name, node.methods)
            self.current_env.set(node.name, interface_obj)
            return interface_obj

        if isinstance(node, Break):
            raise BreakException()

        if isinstance(node, Continue):
            raise ContinueException()

        if isinstance(node, Pass):
            return None

        if isinstance(node, Function):
            func = ZoyaFunction(node, self.current_env)
            self.current_env.set(node.name, func)
            return func

        if isinstance(node, Lambda):
            return ZoyaFunction(node, self.current_env)

        if isinstance(node, Call):
            return self._call_function(node)

        if isinstance(node, GetAttr):
            obj = self._eval(node.obj)
            if isinstance(obj, ZoyaInstance):
                m = obj._find_method(node.attr)
                if m is not None:
                    return m
                if node.attr in obj._fields:
                    return obj._fields[node.attr]
                raise ZoyaAttributeError(
                    f"'{obj.klass.name}' has no attribute '{node.attr}'",
                    line=line,
                    col=col,
                    file=self.file,
                )
            if isinstance(obj, ZoyaSuper):
                parent = obj._klass.parent
                if parent is None:
                    raise RuntimeError_(
                        f"super: '{obj._klass.name}' has no parent",
                        line=line,
                        col=col,
                        file=self.file,
                    )
                if node.attr in parent.methods:
                    return parent.methods[node.attr]
                raise ZoyaAttributeError(
                    f"super: '{parent.name}' has no attribute '{node.attr}'",
                    line=line,
                    col=col,
                    file=self.file,
                )
            return getattr(obj, node.attr)

        if isinstance(node, MethodCall):
            return self._call_method(node)

        if isinstance(node, Return):
            val = None
            if node.expr is not None:
                val = self._eval(node.expr)
            raise ReturnException(val)

        if isinstance(node, List_):
            return [self._eval(elem) for elem in node.elements]

        if isinstance(node, Dict_):
            result: dict[Any, Any] = {}
            for key_node, val_node in node.pairs:
                key = self._eval(key_node)
                val = self._eval(val_node)
                result[key] = val
            return result

        if isinstance(node, Index):
            obj = self._eval(node.obj)
            index = self._eval(node.index)
            if isinstance(obj, (list, tuple, str)):
                return obj[int(index)]
            if isinstance(obj, dict):
                return obj[index]
            raise ZoyaIndexError(
                f"Cannot index {type(obj).__name__}", line=line, col=col, file=self.file
            )

        if isinstance(node, Slice):
            obj = self._eval(node.obj)
            start = self._eval(node.start) if node.start else None
            stop = self._eval(node.stop) if node.stop else None
            step = self._eval(node.step) if node.step else None
            return obj[start:stop:step]

        if isinstance(node, Import):
            return self._handle_import(node)

        raise RuntimeError_(
            f"Unknown AST node: {type(node).__name__}", line=line, col=col, file=self.file
        )

    def _eval_block(self, block: ASTNode) -> Any:
        if isinstance(block, Block):
            result = None
            for stmt in block.statements:
                result = self._eval(stmt)
            return result
        return self._eval(block)

    def _eval_for_loop(self, node: ForLoop) -> None:
        if node.init is not None:
            self._eval(node.init)
        result = None
        while True:
            if node.cond is not None:
                if not self._truthy(self._eval(node.cond)):
                    break
            try:
                result = self._eval_block(node.body)
            except BreakException:
                break
            except ContinueException:
                if node.update is not None:
                    self._eval(node.update)
                continue
            if node.update is not None:
                self._eval(node.update)
        return result

    def _eval_for_each(self, node: ForEach) -> None:
        iterable = self._eval(node.iterable)
        result = None
        if isinstance(iterable, (list, tuple, str)) or hasattr(iterable, "__iter__"):
            for item in iterable:
                self.current_env.set(node.var, item)
                try:
                    result = self._eval_block(node.body)
                except BreakException:
                    break
                except ContinueException:
                    continue
        else:
            raise RuntimeError_(
                f"Cannot iterate over '{type(iterable).__name__}'",
                line=node.line,
                col=node.col,
                file=self.file,
            )
        return result

    def _eval_switch(self, node: Switch) -> Any:
        val = self._eval(node.expr)
        result = None
        matched = False
        for case_expr, case_body in node.cases:
            case_val = self._eval(case_expr)
            if val == case_val:
                matched = True
                result = self._eval_block(case_body)
        if not matched and node.default_body is not None:
            result = self._eval_block(node.default_body)
        return result

    def _eval_try(self, node: Try) -> Any:
        result = None
        try:
            result = self._eval_block(node.try_body)
        except (ZoyaRuntimeError, ZoyaTypeError, RuntimeError_) as e:
            for catch in node.catches:
                func_env = Environment(self.current_env)
                if catch.var is not None:
                    func_env.define(catch.var, str(e))
                old_env = self.current_env
                self.current_env = func_env
                try:
                    result = self._eval_block(catch.body)
                except ReturnException as ret:
                    result = ret.value
                finally:
                    self.current_env = old_env
                break
            if not node.catches:
                raise
        except Exception as e:
            if not isinstance(e, (BreakException, ContinueException, ReturnException)):
                for catch in node.catches:
                    func_env = Environment(self.current_env)
                    if catch.var is not None:
                        func_env.define(catch.var, str(e))
                    old_env = self.current_env
                    self.current_env = func_env
                    try:
                        result = self._eval_block(catch.body)
                    except ReturnException as ret:
                        result = ret.value
                    finally:
                        self.current_env = old_env
                    break
            else:
                raise
        finally:
            if node.final_body is not None:
                self._eval_block(node.final_body)
        return result

    def _eval_match(self, node: Match) -> Any:
        val = self._eval(node.expr)
        for pattern, body in node.arms:
            if val == self._eval(pattern):
                return self._eval(body)
        if node.else_arm is not None:
            return self._eval(node.else_arm)
        return None

    def _eval_class_def(self, node: ClassDef) -> Any:
        parent: ZoyaClass | None = None
        if node.parent is not None:
            parent_obj = self.current_env.get(node.parent)
            if not isinstance(parent_obj, ZoyaClass):
                raise RuntimeError_(
                    f"'{node.parent}' is not a class", line=node.line, col=node.col, file=self.file
                )
            parent = parent_obj

        class_env = Environment(self.current_env)
        old_env = self.current_env
        self.current_env = class_env
        try:
            self._eval_block(node.body)
        finally:
            self.current_env = old_env

        methods: dict[str, ZoyaFunction] = {}
        for key, val in class_env._vars.items():
            if isinstance(val, ZoyaFunction):
                methods[key] = val

        if parent is not None:
            for key, val in parent.methods.items():
                if key not in methods:
                    methods[key] = val

        klass = ZoyaClass(node.name, parent, methods, class_env)
        self.current_env.set(node.name, klass)
        return klass

    def _call_function(self, call: Call) -> Any:
        callee = self._eval(call.callee)

        if isinstance(callee, ZoyaModule):
            if hasattr(callee, "_call"):
                return callee._call(call.args, self)
            raise RuntimeError_(
                f"'{callee.name}' is not callable", line=call.line, col=call.col, file=self.file
            )

        builtin_name = ""
        if isinstance(call.callee, Ident):
            builtin_name = call.callee.name
            if builtin_name in BUILTIN_FUNCTIONS:
                fn = BUILTIN_FUNCTIONS[builtin_name]
                args = [self._eval(arg) for arg in call.args]
                return fn(*args)

        if isinstance(callee, ZoyaFunction):
            return self._call_function_internal(callee, None, call.args)

        if isinstance(callee, ZoyaClass):
            instance = ZoyaInstance(callee)
            if "init" in callee.methods:
                self._call_function_internal(callee.methods["init"], instance, call.args)
            return instance

        if callable(callee):
            args = [self._eval(arg) for arg in call.args]
            return callee(*args)

        raise RuntimeError_(
            f"'{callee}' is not callable", line=call.line, col=call.col, file=self.file
        )

    def _call_function_internal(
        self, func: ZoyaFunction, instance: ZoyaInstance | None, arg_nodes: list[ASTNode]
    ) -> Any:
        positional_nodes: list[ASTNode] = []
        named_kwargs: dict[str, ASTNode] = {}

        for arg in arg_nodes:
            if isinstance(arg, NamedArg):
                named_kwargs[arg.name] = arg.value
            else:
                positional_nodes.append(arg)

        positional_args: list[Any] = [self._eval(a) for a in positional_nodes]
        named_evaled: dict[str, Any] = {k: self._eval(v) for k, v in named_kwargs.items()}

        func_env = Environment(func.env)

        if instance is not None:
            func_env.define("this", instance)
            func_env.define("super", ZoyaSuper(instance, instance.klass))

        params = func.decl.params
        defaults = func.decl.defaults if hasattr(func.decl, "defaults") else []

        param_filled: set[int] = set()

        for i, param in enumerate(params):
            if param in named_evaled:
                func_env.define(param, named_evaled[param])
                param_filled.add(i)

        pos_idx = 0
        for i, param in enumerate(params):
            if i in param_filled:
                continue
            if pos_idx < len(positional_args):
                func_env.define(param, positional_args[pos_idx])
                pos_idx += 1
            elif i < len(defaults) and defaults[i] is not None:
                func_env.define(param, self._eval(defaults[i]))
            else:
                func_name = getattr(func, "name", "") or "anonymous"
                raise RuntimeError_(
                    f"Missing argument for parameter '{param}' in function '{func_name}'",
                    line=getattr(func.decl, "line", 0),
                    col=getattr(func.decl, "col", 0),
                    file=self.file,
                )

        old_env = self.current_env
        self.current_env = func_env
        try:
            return self._eval_block(func.decl.body)
        except ReturnException as ret:
            return ret.value
        finally:
            self.current_env = old_env

    def _call_method(self, mc: MethodCall) -> Any:
        obj = self._eval(mc.obj)
        args = [self._eval(arg) for arg in mc.args]
        method = mc.method

        if isinstance(obj, ZoyaModule) and hasattr(obj, method):
            fn = getattr(obj, method)
            if callable(fn):
                return fn(*args)
            return fn

        if isinstance(obj, ZoyaInstance):
            func = obj._find_method(method)
            if func is not None:
                return self._call_function_internal(func, obj, mc.args)
            if method in obj._fields:
                field = obj._fields[method]
                if callable(field):
                    return field(*args)
                return field
            raise ZoyaAttributeError(
                f"'{obj.klass.name}' has no method '{method}'",
                line=mc.line,
                col=mc.col,
                file=self.file,
            )

        if isinstance(obj, ZoyaSuper):
            parent = obj._klass.parent
            if parent is None:
                raise RuntimeError_(
                    "super: no parent class", line=mc.line, col=mc.col, file=self.file
                )
            if method in parent.methods:
                func = parent.methods[method]
                return self._call_function_internal(func, obj._instance, mc.args)
            raise ZoyaAttributeError(
                f"super: '{parent.name}' has no method '{method}'",
                line=mc.line,
                col=mc.col,
                file=self.file,
            )

        if isinstance(obj, str) and method in STRING_METHODS:
            return STRING_METHODS[method](obj, *args)

        if isinstance(obj, list) and method in LIST_METHODS:
            return LIST_METHODS[method](obj, *args)

        if isinstance(obj, dict) and method in DICT_METHODS:
            return DICT_METHODS[method](obj, *args)

        if hasattr(obj, method):
            fn = getattr(obj, method)
            if callable(fn):
                return fn(*args)
            return fn

        raise ZoyaAttributeError(
            f"'{type(obj).__name__}' has no method '{method}'",
            line=mc.line,
            col=mc.col,
            file=self.file,
        )

    def _handle_import(self, node: Import) -> Any:
        path = node.path
        alias = node.alias or path

        try:
            import importlib

            py_module = importlib.import_module(f"zoya.stdlib.{path}")
            if hasattr(py_module, "load_module"):
                module = py_module.load_module(self)
                self.current_env.set(alias, module)
                return module
        except ImportError:
            pass

        if path in BUILTIN_FUNCTIONS:
            return BUILTIN_FUNCTIONS[path]

        zoya_file = path
        if not zoya_file.endswith(".zoya"):
            zoya_file += ".zoya"

        search_dirs = [
            os.path.dirname(os.path.abspath(self.file)) if self.file else os.getcwd(),
            os.path.join(os.path.dirname(__file__), "stdlib"),
            os.getcwd(),
        ]

        for search_dir in search_dirs:
            full_path = os.path.join(search_dir, zoya_file)
            if os.path.exists(full_path):
                from .lexer import tokenize
                from .parser import parse

                with open(full_path) as f:
                    source = f.read()
                tokens = tokenize(source, full_path)
                ast = parse(tokens, full_path)
                old_file = self.file
                self.file = full_path
                import_env = Environment(self.global_env)
                try:
                    self._eval_block(ast)
                finally:
                    self.file = old_file
                module_obj = ZoyaModule(alias, {})
                for key, val in import_env._vars.items():
                    if not key.startswith("_") and key not in BUILTIN_FUNCTIONS:
                        setattr(module_obj, key, val)
                self.current_env.set(alias, module_obj)
                return module_obj

        raise RuntimeError_(
            f"Module '{path}' not found", line=node.line, col=node.col, file=self.file
        )

    def _truthy(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict, tuple)):
            return len(value) > 0
        return bool(value)


def interpret(ast: Block, file: str = "") -> Any:
    interp = Interpreter(file)
    return interp._eval_block(ast)


def run(source: str, file: str = "") -> Any:
    from .lexer import tokenize
    from .parser import parse

    tokens = tokenize(source, file)
    ast = parse(tokens, file)
    return interpret(ast, file)
