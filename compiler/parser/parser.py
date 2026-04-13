"""
Lexer and Parser for OSC DSL - Simplified version.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
import json
import re


class TokenType(Enum):
    """Token types for the lexer."""
    SCENARIO = auto()
    DO = auto()
    SERIAL = auto()
    PARALLEL = auto()
    WITH = auto()
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    EOF = auto()


@dataclass
class Token:
    """Represents a token from the lexer."""
    type: TokenType
    value: str
    line: int


class Lexer:
    """Tokenizes input DSL string."""

    KEYWORDS = {
        "scenario": TokenType.SCENARIO,
        "do": TokenType.DO,
        "serial": TokenType.SERIAL,
        "parallel": TokenType.PARALLEL,
        "with": TokenType.WITH,
    }

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1

    def peek(self) -> Optional[str]:
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.pos < len(self.text):
            ch = self.peek()

            # Skip whitespace
            if ch in " \t\n":
                if ch == "\n":
                    self.advance()
                else:
                    self.advance()
                continue

            # Skip comments
            if ch == "#":
                while self.peek() and self.peek() != "\n":
                    self.advance()
                continue

            # Identifier or keyword
            if ch.isalpha() or ch == "_":
                value = self.read_identifier()
                token_type = self.KEYWORDS.get(value, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, value, self.line))

            # Number
            elif ch.isdigit() or ch == "-":
                value = self.read_number()
                tokens.append(Token(TokenType.NUMBER, value, self.line))

            # String
            elif ch == '"':
                value = self.read_string()
                tokens.append(Token(TokenType.STRING, value, self.line))

            # Single-character tokens
            else:
                token_map = {
                    "(": TokenType.LPAREN,
                    ")": TokenType.RPAREN,
                    "[": TokenType.LBRACKET,
                    "]": TokenType.RBRACKET,
                    ":": TokenType.COLON,
                    ",": TokenType.COMMA,
                    ".": TokenType.DOT,
                }
                if ch in token_map:
                    tokens.append(Token(token_map[ch], ch, self.line))
                    self.advance()
                else:
                    self.advance()

        tokens.append(Token(TokenType.EOF, "", self.line))
        return tokens

    def read_identifier(self) -> str:
        result = ""
        while self.peek() and (self.peek().isalnum() or self.peek() in "_-"):
            result += self.advance()
        return result

    def read_number(self) -> str:
        result = ""
        # Handle leading minus sign
        if self.peek() == "-":
            result += self.advance()
        while self.peek() and self.peek().isdigit():
            result += self.advance()
        # Handle single dot for decimal (but not .. for range)
        if self.peek() == "." and self.pos + 1 < len(self.text) and self.text[self.pos + 1] != ".":
            result += self.advance()  # consume the dot
            while self.peek() and self.peek().isdigit():
                result += self.advance()
        return result

    def read_string(self) -> str:
        self.advance()
        result = ""
        while self.peek() and self.peek() != '"':
            result += self.advance()
        self.advance()
        return result


# AST Node imports - use absolute imports from compiler package
from compiler.ir.ast_nodes import (
    ASTNode,
    ScenarioNode,
    ActorNode,
    PhaseNode,
    ActionNode,
    ConstraintNode,
    RangeValue,
    AnchorType,
    CoverageNode,
    node_to_dict,
    print_ast,
)


class Parser:
    """Parses tokens into AST - simple recursive descent."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        token = self.peek()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type}")
        return self.advance()

    def parse(self) -> ScenarioNode:
        """Parse tokens into ScenarioNode."""
        self.expect(TokenType.SCENARIO)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)

        scenario = ScenarioNode(name=name, actors=())

        # Parse actors
        while self.peek().type == TokenType.IDENTIFIER:
            if self.is_actor_decl():
                actor = self.parse_actor()
                object.__setattr__(scenario, 'actors', tuple(list(scenario.actors) + [actor]))
            else:
                break

        # Parse body
        if self.peek().type == TokenType.DO:
            object.__setattr__(scenario, 'body', self.parse_do())

        return scenario

    def is_actor_decl(self) -> bool:
        """Check if current position looks like actor: type declaration."""
        if self.pos + 2 >= len(self.tokens):
            return False
        t1 = self.tokens[self.pos]
        t2 = self.tokens[self.pos + 1]
        t3 = self.tokens[self.pos + 2]
        return (t1.type == TokenType.IDENTIFIER and
                t2.type == TokenType.COLON and
                t3.type == TokenType.IDENTIFIER and
                t3.value not in ("serial", "parallel"))

    def parse_actor(self) -> ActorNode:
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)
        type_val = self.expect(TokenType.IDENTIFIER).value
        return ActorNode(name=name, type=type_val)

    def parse_do(self) -> PhaseNode:
        """Parse do serial(): or do parallel():"""
        self.expect(TokenType.DO)

        mode = "serial"
        if self.peek().type == TokenType.IDENTIFIER:
            if self.peek().value in ("serial", "parallel"):
                mode = self.advance().value

        if self.peek().type in (TokenType.SERIAL, TokenType.PARALLEL):
            mode = self.advance().value

# Handle optional parentheses: serial() or parallel()
        if self.peek().type == TokenType.LPAREN:
            self.advance()  # skip (
            self.expect(TokenType.RPAREN)  # skip )

        self.expect(TokenType.COLON)

        # Parse children: parallel blocks or actions
        children = []
        while self.peek().type != TokenType.EOF:
            # Handle phase name like "connect:" - skip it
            if (self.peek().type == TokenType.IDENTIFIER and
                    self.pos + 1 < len(self.tokens) and
                    self.tokens[self.pos + 1].type == TokenType.COLON):
                self.advance()  # skip name
                self.expect(TokenType.COLON)  # skip colon
                continue
            if self.peek().type == TokenType.IDENTIFIER:
                if self.peek().value == "parallel":
                    children.append(self.parse_parallel())
                else:
                    children.append(self.parse_action())
            elif self.peek().type == TokenType.PARALLEL:
                children.append(self.parse_parallel())
            elif self.peek().type == TokenType.DO:
                break  # End of this do block
            else:
                self.advance()

        return PhaseNode(name="", mode=mode, children=tuple(children))

    def parse_parallel(self) -> PhaseNode:
        """Parse parallel(): block"""
        if self.peek().type == TokenType.PARALLEL:
            self.advance()
        # Handle optional parentheses
        if self.peek().type == TokenType.LPAREN:
            self.advance()  # skip (
            self.expect(TokenType.RPAREN)  # skip )
        self.expect(TokenType.COLON)

        children = []
        while self.peek().type != TokenType.EOF:
            if self.peek().type == TokenType.IDENTIFIER:
                children.append(self.parse_action())
            elif self.peek().type == TokenType.PARALLEL:
                break  # Nested parallel ends current
            elif self.peek().type == TokenType.DO:
                break
            else:
                self.advance()

        return PhaseNode(name="", mode="parallel", children=tuple(children))

    def parse_action(self) -> ActionNode:
        """Parse action: actor.action() with: constraints"""
        actor = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.DOT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)

        action = ActionNode(actor=actor, name=name)

        # Parse with: constraints
        if self.peek().type == TokenType.WITH:
            self.advance()
            self.expect(TokenType.COLON)
            constraints_list = self.parse_constraints()
            object.__setattr__(action, 'constraints', tuple(constraints_list))

        return action

    def parse_constraints(self) -> list[ConstraintNode]:
        """Parse constraints in with: block. Constraints are separated by newlines."""
        constraints = []

        while self.peek().type != TokenType.EOF and self.peek().type == TokenType.IDENTIFIER:
            metric = self.advance().value

            # Check if constraint has parentheses
            if self.peek().type == TokenType.LPAREN:
                self.advance()  # consume (
                # Parse value inside parentheses
                value = None
                if self.peek().type == TokenType.STRING:
                    value = self.advance().value
                elif self.peek().type == TokenType.NUMBER:
                    value = self.advance().value
                elif self.peek().type == TokenType.IDENTIFIER:
                    value = self.advance().value
                elif self.peek().type == TokenType.LBRACKET:
                    self.advance()  # [
                    start_str = self.advance().value
                    # Skip .. separator (two dots in range notation)
                    if self.peek().type == TokenType.DOT:
                        self.advance()  # consume first dot
                        if self.peek().type == TokenType.DOT:
                            self.advance()  # consume second dot
                    end_str = self.advance().value
                    self.expect(TokenType.RBRACKET)
                    # Convert to numbers
                    try:
                        start = int(start_str)
                    except ValueError:
                        start = float(start_str)
                    try:
                        end = int(end_str)
                    except ValueError:
                        end = float(end_str)
                    value = RangeValue(start=start, end=end)

                # Parse anchor (comma at: end)
                anchor = AnchorType.END
                if self.peek().type == TokenType.COMMA:
                    self.advance()  # consume comma
                    if self.peek().value == "at":
                        self.advance()  # consume at
                        self.expect(TokenType.COLON)  # consume :
                        anchor_value = self.advance().value  # consume end value
                        anchor = AnchorType(anchor_value)

                self.expect(TokenType.RPAREN)  # consume )
                constraints.append(ConstraintNode(metric=metric, value=value, anchor=anchor))
            else:
                # No parentheses - just metric name
                constraints.append(ConstraintNode(metric=metric, value=None, anchor=AnchorType.END))

            # Skip comma if present
            if self.peek().type == TokenType.COMMA:
                self.advance()

            # Check if next is another constraint (IDENTIFIER followed by LPAREN or LBRACKET)
            # or if it's a new action (IDENTIFIER followed by DOT)
            if self.peek().type == TokenType.IDENTIFIER:
                next_metric = self.peek().value
                # Look ahead to determine what comes next
                if self.pos + 1 < len(self.tokens):
                    next_token = self.tokens[self.pos + 1]
                    if next_token.type == TokenType.DOT:
                        # Next is a new action (actor.action), stop constraints
                        break
                    elif next_token.type == TokenType.LPAREN:
                        # Next is another constraint, continue
                        continue
                    else:
                        # Unclear, stop
                        break
            break

        return constraints


def parse(text: str) -> ScenarioNode:
    """Parse DSL text into AST."""
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def parse_file(path: str) -> ScenarioNode:
    with open(path, "r") as f:
        return parse(f.read())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        ast = parse_file(sys.argv[1])
    else:
        example = '''scenario enterprise_wifi_session:
    worker: employee
    laptop: managed_laptop

    do serial():
        connect:
            parallel():
                laptop.scan_ssid() with:
                    signal_strength([-67..-55], at: end)

                laptop.authenticate() with:
                    auth_status(success, at: end)
                    auth_latency_ms([200..1500], at: end)
'''
        ast = parse(example)

    print("=== AST Tree ===")
    print(print_ast(ast))

    print("\n=== JSON Output ===")
    print(json.dumps(node_to_dict(ast), indent=2))