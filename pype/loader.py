'''loader'''

from typing import Optional
from core import loader, parser
from pype import builtins_, exprs, func, params, statements, vals


def load(input_str: str) -> statements.Block:
    '''load from a string'''

    def load_statement(result: parser.Result) -> statements.Statement:
        def load_expr(result: parser.Result) -> exprs.Expr:
            def load_ref(result: parser.Result) -> exprs.Ref:
                return exprs.Ref(loader.get_token_value(result))

            def load_path(result: parser.Result) -> exprs.Path:
                def load_path_part(result: parser.Result) -> exprs.Path.Part:
                    def load_path_part_member(result: parser.Result) -> exprs.Path.Member:
                        return exprs.Path.Member(loader.get_token_value(result['path_part_member_name', 1]))

                    def load_path_part_call(result: parser.Result) -> exprs.Path.Call:
                        return exprs.Path.Call(exprs.Args([exprs.Arg(load_expr(expr)) for expr in result['expr']]))

                    return loader.factory({
                        'path_part_member': load_path_part_member,
                        'path_part_call': load_path_part_call,
                    })(result)

                root = load_expr(result['path_root', 1])
                parts = [load_path_part(part) for part in result['path_part']]
                return exprs.Path(root, parts)

            def load_literal(result: parser.Result) -> exprs.Literal:
                def load_int_literal(result: parser.Result) -> vals.Val:
                    return builtins_.Int.for_value(int(loader.get_token_value(result)))

                return exprs.Literal(loader.factory({
                    'int_literal': load_int_literal
                })(result))

            def load_binary_operation(result: parser.Result) -> exprs.BinaryOperation:
                operator = exprs.BinaryOperation.Operator(
                    loader.get_token_value(result['binary_operator', 1]))
                lhs, rhs = [load_expr(operand)
                            for operand in result['operand', 2]]
                return exprs.BinaryOperation(operator, lhs, rhs)

            return loader.factory({
                'ref': load_ref,
                'path': load_path,
                'literal': load_literal,
                'binary_operation': load_binary_operation,
            })(result)

        def load_expr_statement(result: parser.Result) -> statements.ExprStatement:
            return statements.ExprStatement(load_expr(result['expr', 1]))

        def load_assignment(result: parser.Result) -> statements.Assignment:
            name = loader.get_token_value(result['assignment_name', 1])
            value = load_expr(result['assignment_value', 1])
            return statements.Assignment(name, value)

        def load_return_statement(result: parser.Result) -> statements.Return:
            if 'return_value' in result:
                return statements.Return(load_expr(result['return_value', 1]))
            return statements.Return(None)

        def load_func_decl(result: parser.Result) -> func.Decl:
            def load_params(result: parser.Result) -> params.Params:
                def load_param(result: parser.Result) -> params.Param:
                    return params.Param(loader.get_token_value(result))
                return params.Params([load_param(param) for param in result['param']])

            name = loader.get_token_value(result['func_name', 1])
            params_ = load_params(result['func_params', 1])
            body = load_block(result['func_body', 1])
            return func.Decl(name, params_, body)

        def load_class_decl(result: parser.Result) -> statements.Class:
            name = loader.get_token_value(result['class_name', 1])
            body = load_block(result['class_body', 1])
            return statements.Class(name, body)

        return loader.factory({
            'expr_statement': load_expr_statement,
            'assignment': load_assignment,
            'return_statement': load_return_statement,
            'func_decl': load_func_decl,
            'class_decl': load_class_decl,
        })(result)

    def load_block(result: parser.Result) -> statements.Block:
        return statements.Block([load_statement(statement) for statement in result['statement']])

    return load_block(loader.load_parser(r'''
        _ws = "\w+";
        id = "[_a-zA-Z][_a-zA-Z0-9]*";
        int = "[1-9][0-9]*";

        root => block;
        block => statement+;
        statement => class_decl | func_decl | return_statement | assignment | expr_statement;
        expr_statement => expr ";";
        expr => binary_operation | operand;
        operand => path | ref | literal;
        path => path_root path_part+;
        path_root => ref | literal;
        path_part => path_part_member | path_part_call;
        path_part_member => "." path_part_member_name;
        path_part_member_name => id;
        path_part_call => "(" (expr ("," expr)*)? ")";
        ref => id;
        assignment => assignment_name "=" assignment_value ";";
        assignment_name => id;
        assignment_value => expr;
        literal => int_literal;
        int_literal => int;
        func_decl => "def" func_name func_params "{" func_body "}";
        func_name => id;
        func_params => params;
        func_body => block;
        params => "(" (param ("," param)*)? ")";
        param => id;
        return_statement => "return" return_value? ";";
        return_value => expr;
        binary_operation => operand binary_operator operand;
        binary_operator => "+" | "-" | "*" | "/";
        class_decl => "class" class_name "{" class_body "}";
        class_name => id;
        class_body => block;
    ''').apply(input_str))


def eval_(input_str: str, scope: Optional[vals.Scope] = None) -> vals.Val:
    '''eval a set of statements and return the value of the last one'''
    if scope is None:
        scope = vals.Scope.default()
    statements_ = list(load(input_str))
    for statement in statements_[:-1]:
        statement.eval(scope)
    if isinstance(statements_[-1], statements.ExprStatement):
        return statements_[-1].value.eval(scope)
    statements_[-1].eval(scope)
    return builtins_.none


if __name__ == '__main__':
    scope = vals.Scope.default()
    while True:
        try:
            result = eval_(input('>'), scope)
            if result != builtins_.none:
                print(result)
        except Exception as error:
            print(f'error: {error}')
