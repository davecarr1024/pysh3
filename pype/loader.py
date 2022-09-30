'''loader'''

from core import loader, parser
from pype import builtins_, exprs, func, funcs


def load(input_str: str) -> exprs.Expr:
    '''load an expr from a string'''

    def load_param(result: parser.Result) -> funcs.Param:
        return funcs.Param(loader.get_token_value(result))

    def load_params(result: parser.Result) -> funcs.Params:
        return funcs.Params([load_param(param) for param in result['param']])

    def load_func(result: parser.Result) -> exprs.Expr:
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
            return exprs.Literal(builtins_.Int(value=int(loader.get_token_value(lit))))

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

    def load_namespace(result: parser.Result) -> exprs.Expr:
        return exprs.Namespace([load_expr(statement) for statement in result['statement']])

    def load_return_statement(result: parser.Result) -> exprs.Expr:
        if 'return_value' in result:
            return func.Return(load_expr(result.where_one(parser.Result.rule_name_is('return_value'))))
        return func.Return(None)

    load_expr = loader.factory({
        'ref': load_ref,
        'assignment': load_assignment,
        'literal': load_literal,
        'func': load_func,
        'return_statement': load_return_statement,
    })

    return load_namespace(loader.load_parser(r'''
        _ws = "\w+";
        id = "[_a-zA-Z][_a-zA-Z0-9]*";
        int = "[1-9][0-9]*";

        root => statement+;
        statement => func | ((return_statement | assignment | expr) ";");
        expr => ref | literal;
        ref => id;
        assignment => assignment_name "=" assignment_value;
        assignment_name => id;
        assignment_value => expr;
        literal => int_literal;
        int_literal => int;
        func => "def" func_name func_params "{" func_body "}";
        func_name => id;
        func_params => params;
        func_body => statement*;
        params => "(" param ("," param)* ")";
        param => id;
        return_statement => "return" return_value?;
        return_value => expr;
    ''').apply(input_str))
