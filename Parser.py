from ASTNodeDefs import *
from typing import List, Tuple, Union
import re

"""
For Project 2, you are free to implement it based on your own Project 1 solution.

This is one of solutions to Project 1 for your reference.
If you choose to use this code, please make sure to understand it fully and adapt it to Project 2 requirements.
"""

class Lexer:
    """
    The Lexer (also known as a tokenizer or scanner) is responsible for breaking
    the raw source code string into a stream of meaningful tokens.
    """

    def __init__(self, code: str):
        self.code = code
        self.tokens: List[Tuple[str, str]] = []  # List of (token_type, token_value)
        self.token_specs = [
            ("ASSIGN", r":="),
            ("SEMICOLON", r";"),
            ("PUT", r"Put\b"),
            ("LPAREN", r"\("),
            ("RPAREN", r"\)"),
            ("IF", r"if\b"),
            ("THEN", r"then\b"),
            ("ELSE", r"else\b"),
            ("END", r"end\b"),
            ("WHILE", r"while\b"),
            ("LOOP", r"loop\b"),
            ("FOR", r"for\b"),
            ("IN", r"in\b"),
            ("RANGE", r"\.\."),
            ("OR", r"or\b"),
            ("AND", r"and\b"),
            ("EQ", r"="),
            ("NEQ", r"/="),
            ("LEQ", r"<="),
            ("GEQ", r">="),
            ("LT", r"<"),
            ("GT", r">"),
            ("PLUS", r"\+"),
            ("MINUS", r"-"),
            ("TIMES", r"\*"),
            ("DIVIDE", r"/"),
            ("MOD", r"mod\b"),
            ("INTEGER", r"[0-9]+"),
            ("BOOL", r"(True|False)\b"),
            ("INTEGER_TYPE", r"Integer\b"),
            ("BOOLEAN_TYPE", r"Boolean\b"),
            ("VAR", r"var\b"),
            ("ID", r"[a-zA-Z_][a-zA-Z0-9_]*"),
            ("COLON", r":"),
            ("SKIP", r"\s+"),  # Skip over white space
            ("MISMATCH", r"."),  # Any other character
        ]
        self.token_regex = re.compile(
            "|".join(f"(?P<{pair[0]}>{pair[1]})" for pair in self.token_specs)
        )

    def tokenize(self) -> List[Tuple[str, str]]:
        """
        Tokenizes the input code into a list of tokens.
        Each token is represented as a tuple (token_type, token_value).
        """
        for mo in self.token_regex.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "SKIP":
                continue
            elif kind == "MISMATCH":
                raise RuntimeError(f"Unexpected character: {value}")
            else:
                self.tokens.append((kind, value))
        self.tokens.append(("EOF", ""))  # End-of-file token
        return self.tokens


class Parser:
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0  # Current position in the token list
        self.invalid = False
        self.scopes = [{}]

    # methods to handle the scope
    def in_scope(self): 
        self.scopes.append({})
                                                # updated the parsing methods with the scopes  
    def out_scope(self):
        self.scopes.pop()

    def declare(self, name, var_type):
        if name in self.scopes[-1]:
            self.invalid = True
            return False
        self.scopes[-1][name] = var_type
        return True

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def current_token(self) -> Tuple[str, str]:
        # Returns the current token without consuming it
        return self.tokens[self.pos]

    def advance(self) -> None:
        # Advances to the next token
        self.pos += 1

    def expect(self, token_type: str) -> Tuple[str, str]:
        # Consumes the current token if it matches the expected type and returns it
        current_type, current_value = self.current_token()
        if current_type == token_type:
            self.advance()
            return (current_type, current_value)
        else:
            raise RuntimeError(
                f"Expected token type {token_type}, got type {current_type}"
            )

    def parse(self) -> ASTNode:
        block = self.parse_block()
        self.expect("EOF")
        self.type_check(block)
        if self.invalid:
            return Error()
        return block

    def parse_block(self) -> Block:
        statements = []
        while (
            self.current_token()[0] != "EOF"
            and self.current_token()[0] != "END"
            and self.current_token()[0] != "ELSE"
        ):
            stmt = self.parse_statement()
            statements.append(stmt)
        return Block(statements)

    def parse_statement(self) -> Union[Assign, Put, If, WhileLoop, ForLoop]:
        current_type, _ = self.current_token()
        if current_type == "ID":
            return self.parse_assign()
        elif current_type == "PUT":
            return self.parse_put()
        elif current_type == "IF":
            return self.parse_if()
        elif current_type == "WHILE":
            return self.parse_while()
        elif current_type == "FOR":
            return self.parse_for()
        elif current_type == "VAR":      # Adding the new case for variable declaration
            return self.parse_declaration()
        else:
            raise RuntimeError(f"Unexpected token type in statement: {current_type}")

    def parse_assign(self) -> Assign:
        _, id_value = self.expect("ID")
        identifier = Identifier(id_value)
        self.expect("ASSIGN")
        expr = self.parse_expr()
        self.expect("SEMICOLON")
        return Assign(identifier, expr)

    def parse_put(self) -> Put:
        self.expect("PUT")
        self.expect("LPAREN")
        expr = self.parse_expr()
        self.expect("RPAREN")
        self.expect("SEMICOLON")
        return Put(expr)

    def parse_if(self) -> If:
        self.expect("IF")
        condition = self.parse_expr()
        self.expect("THEN")
        then_block = self.parse_block()
        else_block = None
        if self.current_token()[0] == "ELSE":
            self.expect("ELSE")
            else_block = self.parse_block()
        self.expect("END")
        self.expect("IF")
        self.expect("SEMICOLON")
        return If(condition, then_block, else_block)

    def parse_while(self) -> WhileLoop:
        self.expect("WHILE")
        condition = self.parse_expr()
        self.expect("LOOP")
        body = self.parse_block()
        self.expect("END")
        self.expect("LOOP")
        self.expect("SEMICOLON")
        return WhileLoop(condition, body)

    def parse_for(self) -> ForLoop:
        self.expect("FOR")
        _, id_value = self.expect("ID")
        iterator = Identifier(id_value)
        self.expect("IN")
        start_expr = self.parse_expr()
        self.expect("RANGE")
        end_expr = self.parse_expr()
        self.expect("LOOP")
        body = self.parse_block()
        self.expect("END")
        self.expect("LOOP")
        self.expect("SEMICOLON")
        return ForLoop(iterator, start_expr, end_expr, body)

    def parse_expr(self) -> ASTNode:
        # parse the first conjunction before 'or'
        result = self.parse_conjunction()
        # if there are more conjunctions
        if self.current_token()[0] == "OR":
            temp: List[ASTNode] = []
            temp.append(result)
            while self.current_token()[0] == "OR":
                self.expect("OR")
                temp.append(self.parse_conjunction())
            result = Or(temp)
        return result

    def parse_conjunction(self) -> ASTNode:
        # parse the first comparison before 'and'
        result = self.parse_comparison()
        # if there are more comparisons
        if self.current_token()[0] == "AND":
            temp: List[ASTNode] = []
            temp.append(result)
            while self.current_token()[0] == "AND":
                self.expect("AND")
                temp.append(self.parse_comparison())
            result = And(temp)
        return result

    def parse_comparison(self) -> ASTNode:
        # parse the first term before comparison operators
        result = self.parse_term()
        # if there is a comparison operator
        comparison_operators = ["EQ", "NEQ", "LT", "GT", "LEQ", "GEQ"]
        current_type, current_value = self.current_token()
        if current_type in comparison_operators:
            self.advance()
            right_term = self.parse_term()
            result = Comparison(result, current_value, right_term)
        return result

    def parse_term(self) -> ASTNode:
        # parse the first factor before term operators
        result = self.parse_factor()
        # if there are more factors
        term_operators = ["PLUS", "MINUS"]
        current_type, current_value = self.current_token()
        if current_type in term_operators:
            temp_factors: List[ASTNode] = []
            temp_operators: List[str] = []
            temp_factors.append(result)
            while current_type in term_operators:
                temp_operators.append(current_value)
                self.advance()
                next_factor = self.parse_factor()
                temp_factors.append(next_factor)
                current_type, current_value = self.current_token()
            result = Term(temp_factors, temp_operators)
        return result

    def parse_factor(self) -> ASTNode:
        # parse the first primary before factor operators
        result = self.parse_primary()
        # if there are more primaries
        factor_operators = ["TIMES", "DIVIDE", "MOD"]
        current_type, current_value = self.current_token()
        if current_type in factor_operators:
            temp_primaries: List[ASTNode] = []
            temp_operators: List[str] = []
            temp_primaries.append(result)
            while current_type in factor_operators:
                temp_operators.append(current_value)
                self.advance()
                next_primary = self.parse_primary()
                temp_primaries.append(next_primary)
                current_type, current_value = self.current_token()
            result = Factor(temp_primaries, temp_operators)
        return result

    def parse_primary(self) -> ASTNode:
        current_type, current_value = self.current_token()
        if current_type == "INTEGER":
            self.advance()
            return Integer(current_value)
        elif current_type == "BOOL":
            self.advance()
            return Boolean(current_value)
        elif current_type == "ID":
            self.advance()
            return Identifier(current_value)
        elif current_type == "LPAREN":
            self.expect("LPAREN")
            expr = self.parse_expr()
            self.expect("RPAREN")
            return expr
        else:
            raise RuntimeError(f"Unexpected token type in primary: {current_type}")
    
    # I started this with the code given by you guys because I didnt know if my code was 100% right yet.
    def parse_declaration(self):  
        if self.current_token()[0] == "VAR":
            self.expect("VAR")
            if self.current_token()[0] == "ID":
                var_name = self.current_token()[1]
                self.expect("ID")
                if self.current_token()[0] == "COLON":
                    self.expect("COLON")
                    # Here we check for the type of the variable 
                    if self.current_token()[0] == "INTEGER_TYPE":
                        self.expect("INTEGER_TYPE")
                        var_type = Type("Integer")
                    elif self.current_token()[0] == "BOOLEAN_TYPE":
                        self.expect("BOOLEAN_TYPE")
                        var_type = Type("Boolean")
                    initial_expression = None           # defaulting to None in case there is no initialization
                    if self.current_token()[0] == "ASSIGN":
                        self.expect("ASSIGN")
                        initial_expression = self.parse_expr()
                    self.expect("SEMICOLON")
                    return Decl(Identifier(var_name), var_type, initial_expression)
        
    def type_check(self, node):
        if isinstance(node, Integer):
            return "Integer"
        
        elif isinstance(node, Boolean):
            return "Boolean"

        elif isinstance(node, Identifier):  
            var_type = self.lookup(node.name)     # here we use the lookup helper to look up the variable in the symbol table

            if var_type is None: 
                self.invalid = True         # var not declared yet
                return None
            return var_type 
        
        elif isinstance(node, Decl):
            if node.initial_value is not None:
                expr_type = self.type_check(node.initial_value)
                if expr_type != node.var_type.type_name:
                    self.invalid = True
            self.declare(node.identifier.name, node.var_type.type_name)
            
        elif isinstance(node, Assign):
            var_type = self.lookup(node.identifier.name)
            if var_type is None:                                 # again checking if the variable exists
                self.invalid = True
                return None
            expr_type = self.type_check(node.expression)
            if expr_type != var_type:
                self.invalid = True

        elif isinstance(node, Put):
            self.type_check(node.expression)

        elif isinstance(node, If):
            cond_type = self.type_check(node.condition)
            if cond_type != "Boolean":
                self.invalid = True
            self.in_scope() 
            self.type_check(node.then_block)
            self.out_scope() 
            if node.else_block is not None:
                self.in_scope()
                self.type_check(node.else_block)
                self.out_scope()

        elif isinstance(node, ForLoop):
            start_type = self.type_check(node.start_expr)
            end_type = self.type_check(node.end_expr)
            if start_type != "Integer" or end_type != "Integer":
                self.invalid = True                                   # I moved all the scopes for the type_checker to handle
            self.in_scope()                                           # this will 100% cause a merge conflict, I gotta accept the branch changes
            self.declare(node.iterator.name, "Integer") 
            self.type_check(node.body)
            self.out_scope() 
        
        elif isinstance(node, WhileLoop):
            cond_type = self.type_check(node.condition)
            if cond_type != "Boolean":
                self.invalid = True
            self.in_scope() 
            self.type_check(node.body)
            self.out_scope() 
        
        elif isinstance(node, Block):
            for stmt in node.statements:
                self.type_check(stmt)

        elif isinstance(node, Or):
            for conj in node.conjunctions:
                t = self.type_check(conj)
                if t != "Boolean":
                    self.invalid = True
            return "Boolean"
        
        elif isinstance(node, And):
            for comp in node.comparisons:
                t = self.type_check(comp)
                if t != "Boolean":
                    self.invalid = True
            return "Boolean"
        
        elif isinstance(node, Comparison):
            left_type = self.type_check(node.left)
            right_type = self.type_check(node.right)
            if left_type != "Integer" or right_type != "Integer":
                self.invalid = True
            return "Boolean"
        
        elif isinstance(node, Term):
            for factor in node.factors:
                t = self.type_check(factor)
                if t != "Integer":
                    self.invalid = True
            return "Integer"
        
        elif isinstance(node, Factor):
            for primary in node.primaries:
                t = self.type_check(primary)
                if t != "Integer":
                    self.invalid = True
            return "Integer"