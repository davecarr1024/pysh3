'''loader'''

from typing import Mapping, Optional
from core import loader, parser
from pype import builtins_, exprs, func, vals


def load(input_str: str) -> exprs.Namespace:
    '''load an expr from a string'''

    def load_param(result: parser.Result) -> exprs.Param:
        return exprs.Param(loader.get_token_value(result))

    def load_params(result: parser.Result) -> exprs.Params:
        return exprs.Params([load_param(param) for param in result['param']])

    def load_arg(result: parser.Result) -> exprs.Arg:
        return exprs.Arg(load_expr(result))

    def load_args(result: parser.Result) -> exprs.Args:
        return exprs.Args([load_arg(expr) for expr in result['expr']])

    def load_func_decl(result: parser.Result) -> exprs.Expr:
        name = loader.get_token_value(result.where_one(
            parser.Result.rule_name_is('func_name')))
        params = load_params(result.where_one(
            parser.Result.rule_name_is('func_params')))
        body = [load_expr(expr) for expr in result.where_one(
            parser.Result.rule_name_is('func_body'))['statement']]
        return exprs.Assignment(name, exprs.Literal(func.Func(name, params, body)))

    def load_ref(result: parser.Result) -> exprs.Expr:
        return exprs.Ref(loader.get_token_value(result))

    def load_literal(result: parser.Result) -> exprs.Expr:
        def load_int_literal(lit: parser.Result) -> exprs.Expr:
            return exprs.Literal(builtins_.Int.for_value(int(loader.get_token_value(lit))))

        return loader.factory({
            'int_literal': load_int_literal,
        })(result)

    def load_assignment(result: parser.Result) -> exprs.Expr:
        return exprs.Assignment(
            loader.get_token_value(result.where_one(
                parser.Result.rule_name_is('assignment_name'))),
            load_expr(result.where_one(
                parser.Result.rule_name_is('assignment_value')))
        )

    def load_namespace(result: parser.Result) -> exprs.Namespace:
        return exprs.Namespace([load_expr(statement) for statement in result['statement']])

    def load_return_statement(result: parser.Result) -> exprs.Expr:
        if 'return_value' in result:
            return func.Return(
                load_expr(
                    result.where_one(parser.Result.rule_name_is('return_value'))))
        return func.Return(None)

    def load_call(result: parser.Result) -> exprs.Expr:
        object_ = load_expr(result.where_one(
            parser.Result.rule_name_is('call_object')))
        args = load_args(result.where_one(
            parser.Result.rule_name_is('call_args')))
        return exprs.Call(object_, args)

    def load_binary_operation(result: parser.Result) -> exprs.Expr:
        methods: Mapping[str, str] = {
            '+': '__add__',
            '-': '__sub__',
            '*': '__mul__',
            '/': '__div__',
        }
        lhs, rhs = (load_expr(operand) for operand in result['operand', 2])
        operator = loader.get_token_value(result['binary_operator', 1])
        method = methods[operator]
        return exprs.Call(exprs.Member(lhs, method), exprs.Args([exprs.Arg(rhs)]))

    def load_class_decl(result: parser.Result) -> exprs.Expr:
        name = loader.get_token_value(result['class_name', 1])
        body = [load_expr(expr) for expr in result['class_body', 1]['expr']]
        return exprs.Assignment(name, exprs.Class(name, body))

    load_expr = loader.factory({
        'ref': load_ref,
        'assignment': load_assignment,
        'literal': load_literal,
        'func_decl': load_func_decl,
        'return_statement': load_return_statement,
        'call': load_call,
        'binary_operation': load_binary_operation,
        'class_decl': load_class_decl,
    })

    return load_namespace(loader.load_parser(r'''
        _ws = "\w+";
        id = "[_a-zA-Z][_a-zA-Z0-9]*";
        int = "[1-9][0-9]*";

        root => statement+;
        statement => class_decl | func_decl | ((return_statement | assignment | expr) ";");
        expr => binary_operation | operand;
        operand => call | ref | literal;
        ref => id;
        assignment => assignment_name "=" assignment_value;
        assignment_name => id;
        assignment_value => expr;
        literal => int_literal;
        int_literal => int;
        func_decl => "def" func_name func_params "{" func_body "}";
        func_name => id;
        func_params => params;
        func_body => statement*;
        params => "(" (param ("," param)*)? ")";
        param => id;
        return_statement => "return" return_value?;
        return_value => expr;
        call => call_object call_args;
        call_object => ref;
        call_args => args;
        args => "(" (expr ("," expr)*)? ")";
        binary_operation => operand binary_operator operand;
        binary_operator => "+" | "-" | "*" | "/";
        class_decl => "class" class_name "{" class_body "}";
        class_name => id;
        class_body => statement*;
    ''').apply(input_str))


def eval_(input_str: str, scope: Optional[vals.Scope] = None) -> vals.Val:
    '''eval a set of statements and return the value of the last one'''
    scope = scope or vals.Scope.default()
    return [
        expr.eval(scope)
        for expr in load(input_str).body
    ][-1].value
