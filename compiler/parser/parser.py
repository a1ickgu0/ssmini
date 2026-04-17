"""
Lexer and Parser for OSC DSL - Simplified version.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Union
import json
import re


class TokenType(Enum):
    """Token types for the lexer."""
    # Core keywords
    SCENARIO = auto()
    DO = auto()
    SERIAL = auto()
    PARALLEL = auto()
    ONE_OF = auto()
    WITH = auto()
    COVER = auto()
    RECORD = auto()

    # Event system
    EVENT = auto()
    ON = auto()
    EMIT = auto()
    WAIT = auto()
    UNTIL = auto()
    ELAPSED = auto()
    EVERY = auto()
    RISE = auto()
    FALL = auto()
    CALL = auto()

    # Constraint system
    KEEP = auto()
    HARD = auto()
    DEFAULT = auto()
    REMOVE_DEFAULT = auto()

    # Type system
    STRUCT = auto()
    ACTOR = auto()
    ACTION = auto()
    ENUM = auto()
    INHERITS = auto()
    TYPE = auto()
    UNIT = auto()
    VAR = auto()
    LIST = auto()
    OF = auto()
    IS = auto()
    EXTERNAL = auto()
    EXPRESSION = auto()
    UNDEFINED = auto()
    ONLY = auto()

    # Method/Extension system
    DEF = auto()
    IMPORT = auto()
    EXTEND = auto()
    GLOBAL = auto()
    MODIFIER = auto()

    # Literals and identifiers
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Basic types
    BOOL = auto()
    INT = auto()
    UINT = auto()
    FLOAT = auto()
    STRING_TYPE = auto()
    SI = auto()

    # Operators
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    EQUALS = auto()
    ARROW = auto()
    AT = auto()
    RANGE_OP = auto()  # ..

    # Logical operators
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()

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
        # Core keywords
        "scenario": TokenType.SCENARIO,
        "do": TokenType.DO,
        "serial": TokenType.SERIAL,
        "parallel": TokenType.PARALLEL,
        "one_of": TokenType.ONE_OF,
        "with": TokenType.WITH,
        "cover": TokenType.COVER,
        "record": TokenType.RECORD,

        # Event system
        "event": TokenType.EVENT,
        "on": TokenType.ON,
        "emit": TokenType.EMIT,
        "wait": TokenType.WAIT,
        "until": TokenType.UNTIL,
        "elapsed": TokenType.ELAPSED,
        "every": TokenType.EVERY,
        "rise": TokenType.RISE,
        "fall": TokenType.FALL,
        "call": TokenType.CALL,

        # Constraint system
        "keep": TokenType.KEEP,
        "hard": TokenType.HARD,
        "default": TokenType.DEFAULT,
        "remove_default": TokenType.REMOVE_DEFAULT,

        # Type system
        "struct": TokenType.STRUCT,
        "actor": TokenType.ACTOR,
        "action": TokenType.ACTION,
        "enum": TokenType.ENUM,
        "inherits": TokenType.INHERITS,
        "type": TokenType.TYPE,
        "unit": TokenType.UNIT,
        "var": TokenType.VAR,
        "list": TokenType.LIST,
        "of": TokenType.OF,
        "is": TokenType.IS,
        "external": TokenType.EXTERNAL,
        "expression": TokenType.EXPRESSION,
        "undefined": TokenType.UNDEFINED,
        "only": TokenType.ONLY,

        # Method/Extension system
        "def": TokenType.DEF,
        "import": TokenType.IMPORT,
        "extend": TokenType.EXTEND,
        "global": TokenType.GLOBAL,
        "modifier": TokenType.MODIFIER,

        # Basic types
        "bool": TokenType.BOOL,
        "int": TokenType.INT,
        "uint": TokenType.UINT,
        "float": TokenType.FLOAT,
        "string": TokenType.STRING_TYPE,
        "SI": TokenType.SI,

        # Logical operators
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
        "in": TokenType.IN,

        # Special identifier
        "it": TokenType.IDENTIFIER,
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

            # Single-character tokens and multi-character operators
            else:
                token_map = {
                    "(": TokenType.LPAREN,
                    ")": TokenType.RPAREN,
                    "[": TokenType.LBRACKET,
                    "]": TokenType.RBRACKET,
                    ":": TokenType.COLON,
                    ",": TokenType.COMMA,
                    ".": TokenType.DOT,
                    "@": TokenType.AT,
                    "=": TokenType.EQUALS,
                }
                if ch in token_map:
                    tokens.append(Token(token_map[ch], ch, self.line))
                    self.advance()
                elif ch == "-" and self.peek_next() == ">":
                    # Arrow operator ->
                    self.advance()  # consume -
                    self.advance()  # consume >
                    tokens.append(Token(TokenType.ARROW, "->", self.line))
                elif ch == "." and self.peek_next() == ".":
                    # Range operator ..
                    self.advance()  # consume first .
                    self.advance()  # consume second .
                    tokens.append(Token(TokenType.RANGE_OP, "..", self.line))
                else:
                    self.advance()

        tokens.append(Token(TokenType.EOF, "", self.line))
        return tokens

    def peek_next(self) -> Optional[str]:
        """Peek at the next character after current position."""
        if self.pos + 1 >= len(self.text):
            return None
        return self.text[self.pos + 1]

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
        if self.peek() == "." and self.peek_next() and self.peek_next() != ".":
            result += self.advance()  # consume the dot
            while self.peek() and self.peek().isdigit():
                result += self.advance()
        # Handle unit suffix (e.g., 30s, 100kph, -5dBm, 10ms)
        if self.peek() and (self.peek().isalpha() or self.peek() in "_"):
            while self.peek() and (self.peek().isalnum() or self.peek() in "_"):
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
    DurationValue,
    DurationUnit,
    UntilCondition,
    EventNode,
    OnDirectiveNode,
    EmitNode,
    WaitNode,
    CallNode,
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

    def peek_next(self) -> Optional[Token]:
        """Peek at the next token after current position."""
        if self.pos + 1 >= len(self.tokens):
            return None
        return self.tokens[self.pos + 1]

    def advance(self) -> Token:
        token = self.peek()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        token = self.peek()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type} at pos {self.pos}")
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.peek().type in token_types

    def parse(self) -> ScenarioNode:
        """Parse tokens into ScenarioNode."""
        self.expect(TokenType.SCENARIO)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)

        scenario = ScenarioNode(name=name, actors=(), events=(), on_directives=())

        # Parse actors
        while self.match(TokenType.IDENTIFIER):
            if self.is_actor_decl():
                actor = self.parse_actor()
                object.__setattr__(scenario, 'actors', tuple(list(scenario.actors) + [actor]))
            else:
                break

        # Parse event declarations
        while self.match(TokenType.EVENT):
            event = self.parse_event()
            object.__setattr__(scenario, 'events', tuple(list(scenario.events) + [event]))

        # Parse on directives
        while self.match(TokenType.ON):
            on_directive = self.parse_on_directive()
            object.__setattr__(scenario, 'on_directives', tuple(list(scenario.on_directives) + [on_directive]))

        # Parse body
        if self.match(TokenType.DO):
            object.__setattr__(scenario, 'body', self.parse_do())

        # Parse cover statements
        while self.match(TokenType.COVER):
            coverage = self.parse_cover()
            object.__setattr__(scenario, 'coverages', tuple(list(scenario.coverages) + [coverage]))

        return scenario

    def parse_event(self) -> EventNode:
        """Parse event declaration: event name is condition_type(value)."""
        self.expect(TokenType.EVENT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IS)

        condition_type = "expression"
        condition_value = None

        if self.match(TokenType.ELAPSED):
            condition_type = "elapsed"
            self.advance()
            self.expect(TokenType.LPAREN)
            duration = self.parse_duration_literal()
            condition_value = duration
            self.expect(TokenType.RPAREN)
        elif self.match(TokenType.RISE):
            condition_type = "rise"
            self.advance()
            self.expect(TokenType.LPAREN)
            condition_value = self.parse_expression_until(TokenType.RPAREN)
            self.expect(TokenType.RPAREN)
        elif self.match(TokenType.FALL):
            condition_type = "fall"
            self.advance()
            self.expect(TokenType.LPAREN)
            condition_value = self.parse_expression_until(TokenType.RPAREN)
            self.expect(TokenType.RPAREN)
        elif self.match(TokenType.EVERY):
            condition_type = "every"
            self.advance()
            self.expect(TokenType.LPAREN)
            duration = self.parse_duration_literal()
            condition_value = duration
            self.expect(TokenType.RPAREN)
        else:
            # Expression-based condition
            condition_value = self.parse_expression_until(TokenType.COLON, TokenType.NEWLINE)

        return EventNode(name=name, condition_type=condition_type, condition_value=condition_value)

    def parse_on_directive(self) -> OnDirectiveNode:
        """Parse on @event: directive."""
        self.expect(TokenType.ON)
        self.expect(TokenType.AT)
        event_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)

        actions = []
        while not self.match(TokenType.EOF, TokenType.DO, TokenType.COVER, TokenType.ON, TokenType.EVENT):
            if self.match(TokenType.EMIT):
                actions.append(self.parse_emit())
            elif self.match(TokenType.WAIT):
                actions.append(self.parse_wait())
            elif self.match(TokenType.CALL):
                actions.append(self.parse_call())
            elif self.match(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.DOT:
                actions.append(self.parse_action())
            else:
                self.advance()

        return OnDirectiveNode(event_name=event_name, actions=tuple(actions))

    def parse_emit(self) -> EmitNode:
        """Parse emit directive: emit(event_name())."""
        self.expect(TokenType.EMIT)
        self.expect(TokenType.LPAREN)
        event_name = self.expect(TokenType.IDENTIFIER).value
        if self.match(TokenType.LPAREN):
            self.advance()
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.RPAREN)
        return EmitNode(event_name=event_name)

    def parse_wait(self) -> WaitNode:
        """Parse wait directive: wait @event or wait elapsed(time)."""
        self.expect(TokenType.WAIT)

        if self.match(TokenType.AT):
            self.advance()
            event_name = self.expect(TokenType.IDENTIFIER).value
            return WaitNode(event_name=event_name)
        elif self.match(TokenType.ELAPSED):
            self.advance()
            self.expect(TokenType.LPAREN)
            duration = self.parse_duration_literal()
            self.expect(TokenType.RPAREN)
            return WaitNode(elapsed_time=duration)
        else:
            # Default: wait @event_name
            event_name = self.expect(TokenType.IDENTIFIER).value
            return WaitNode(event_name=event_name)

    def parse_call(self) -> CallNode:
        """Parse call directive: call function_name(args)."""
        self.expect(TokenType.CALL)
        self.expect(TokenType.LPAREN)
        function_name = self.expect(TokenType.IDENTIFIER).value

        arguments = []
        while not self.match(TokenType.RPAREN):
            if self.match(TokenType.STRING):
                arguments.append(self.advance().value)
            elif self.match(TokenType.NUMBER):
                arguments.append(self.parse_number_value())
            elif self.match(TokenType.IDENTIFIER):
                arguments.append(self.advance().value)
            if self.match(TokenType.COMMA):
                self.advance()

        self.expect(TokenType.RPAREN)
        return CallNode(function_name=function_name, arguments=tuple(arguments))

    def parse_duration_literal(self) -> DurationValue:
        """Parse duration literal like 30s, 100ms, 5m."""
        token = self.expect(TokenType.NUMBER)
        value_str = token.value

        # Extract numeric part and unit
        unit = DurationUnit.S
        numeric_part = value_str

        for u in [DurationUnit.MS, DurationUnit.US, DurationUnit.H, DurationUnit.M, DurationUnit.S]:
            suffix = u.value
            if value_str.endswith(suffix):
                numeric_part = value_str[:-len(suffix)]
                unit = u
                break

        try:
            value = int(numeric_part)
        except ValueError:
            value = float(numeric_part)

        return DurationValue(value=value, unit=unit)

    def parse_number_value(self) -> Union[int, float]:
        """Parse a number token and return its numeric value."""
        token = self.expect(TokenType.NUMBER)
        value_str = token.value

        # Strip unit suffix if present
        for suffix in ['ms', 'us', 's', 'm', 'h', 'kph', 'dBm', 'Mbps', 'Hz', 'kHz']:
            if value_str.endswith(suffix):
                value_str = value_str[:-len(suffix)]
                break

        try:
            return int(value_str)
        except ValueError:
            return float(value_str)

    def parse_expression_until(self, *stop_tokens: TokenType) -> str:
        """Parse an expression until reaching a stop token."""
        parts = []
        while not self.match(*stop_tokens, TokenType.EOF):
            token = self.advance()
            parts.append(token.value)
        return " ".join(parts)

    def parse_cover(self) -> CoverageNode:
        """Parse cover <name>: target: <value> sampling: <type> min_samples: <n>."""
        self.expect(TokenType.COVER)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)

        target = None
        sampling = "event"
        min_samples = 1
        max_samples = None

        # Parse coverage properties
        while self.match(TokenType.IDENTIFIER):
            prop_name = self.advance().value
            self.expect(TokenType.COLON)

            if prop_name == "target":
                if self.match(TokenType.NUMBER):
                    target = self.parse_number_value()
                elif self.match(TokenType.IDENTIFIER):
                    target = self.advance().value
                else:
                    # Handle keyword-as-identifier for target
                    target = self.advance().value
            elif prop_name == "sampling":
                # Handle keyword-as-identifier (event, interval, random)
                if self.match(TokenType.IDENTIFIER, TokenType.EVENT, TokenType.ELAPSED, TokenType.EVERY):
                    sampling = self.advance().value
                else:
                    sampling = "event"  # default
            elif prop_name == "min_samples":
                min_samples = int(self.expect(TokenType.NUMBER).value)
            elif prop_name == "max_samples":
                max_samples = int(self.expect(TokenType.NUMBER).value)
            else:
                # Unknown property, skip it
                if self.match(TokenType.IDENTIFIER, TokenType.NUMBER):
                    self.advance()

        if target is None:
            raise SyntaxError(f"Coverage '{name}' missing target property")

        return CoverageNode(name=name, target=target, sampling=sampling, min_samples=min_samples, max_samples=max_samples)

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
                t3.value not in ("serial", "parallel", "one_of"))

    def parse_actor(self) -> ActorNode:
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.COLON)
        type_val = self.expect(TokenType.IDENTIFIER).value
        return ActorNode(name=name, type=type_val)

    def parse_do(self) -> PhaseNode:
        """Parse do [phase_name:] composition(): blocks."""
        self.expect(TokenType.DO)

        # Check for labeled phase at top level (e.g., "do connect:")
        phase_name = ""
        if self.match(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.COLON:
            phase_name = self.advance().value
            self.expect(TokenType.COLON)

        # Parse composition operator - may be implicit (serial by default)
        mode = "serial"
        duration = None

        if self.match(TokenType.SERIAL):
            mode = "serial"
            self.advance()
            duration = self.parse_composition_args()
            self.expect(TokenType.COLON)
        elif self.match(TokenType.PARALLEL):
            mode = "parallel"
            self.advance()
            duration = self.parse_composition_args()
            self.expect(TokenType.COLON)
        elif self.match(TokenType.ONE_OF):
            mode = "one_of"
            self.advance()
            duration = self.parse_composition_args()
            self.expect(TokenType.COLON)
        elif self.match(TokenType.IDENTIFIER):
            # Could be another label (nested phase) or composition operator name
            if self.peek().value in ("serial", "parallel", "one_of"):
                mode = self.advance().value
                duration = self.parse_composition_args()
                self.expect(TokenType.COLON)
            else:
                # It's a labeled nested phase - no explicit top-level composition
                # The top-level is implicitly serial with labeled children
                # Don't consume the label, let parse_phase_member handle it
                pass
        # If no COLON was consumed yet, check if next is COLON (implicit serial)
        elif self.match(TokenType.COLON):
            self.advance()
        # If nothing matches, use default serial with no explicit COLON

        # Parse children (actions, nested phases)
        children = []
        while not self.match(TokenType.EOF, TokenType.COVER):
            child = self.parse_phase_member()
            if child:
                children.append(child)
            else:
                # Check if we're stuck
                if self.match(TokenType.IDENTIFIER):
                    # Maybe it's a labeled phase start - try to parse it as phase member
                    break
                else:
                    self.advance()  # skip unknown token
                    if self.pos > len(self.tokens) - 2:
                        break

        return PhaseNode(name=phase_name, mode=mode, children=tuple(children), duration=duration)

    def parse_composition_args(self) -> Optional[DurationValue]:
        """Parse composition operator arguments like duration(30s)."""
        duration = None
        if self.match(TokenType.LPAREN):
            self.advance()
            # Check for duration parameter
            if self.match(TokenType.IDENTIFIER) and self.peek().value == "duration":
                self.advance()
                self.expect(TokenType.COLON)
                duration = self.parse_duration_literal()
            self.expect(TokenType.RPAREN)
        return duration

    def parse_phase_member(self) -> Optional[ASTNode]:
        """Parse a member of a phase (action, nested phase, directive)."""
        # Handle labeled nested phases
        if self.match(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.COLON:
            label = self.advance().value
            self.expect(TokenType.COLON)

            # Check what follows the label
            if self.match(TokenType.SERIAL):
                return self.parse_nested_phase(label, "serial")
            elif self.match(TokenType.PARALLEL):
                return self.parse_nested_phase(label, "parallel")
            elif self.match(TokenType.ONE_OF):
                return self.parse_nested_phase(label, "one_of")
            elif self.match(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.DOT:
                # Labeled action - create a phase with just this action
                action = self.parse_action()
                return PhaseNode(name=label, mode="serial", children=(action,))
            elif self.match(TokenType.IDENTIFIER):
                # Could be another labeled phase - end this one
                return None
            else:
                return None

        # Handle emit, wait, call directives
        if self.match(TokenType.EMIT):
            return self.parse_emit()
        if self.match(TokenType.WAIT):
            return self.parse_wait()
        if self.match(TokenType.CALL):
            return self.parse_call()

        # Handle unlabeled nested phases
        if self.match(TokenType.SERIAL):
            return self.parse_nested_phase("", "serial")
        if self.match(TokenType.PARALLEL):
            return self.parse_nested_phase("", "parallel")
        if self.match(TokenType.ONE_OF):
            return self.parse_nested_phase("", "one_of")

        # Handle action
        if self.match(TokenType.IDENTIFIER) and self.peek_next() and self.peek_next().type == TokenType.DOT:
            return self.parse_action()

        return None

    def parse_nested_phase(self, name: str, mode: str) -> PhaseNode:
        """Parse a nested phase with given name and mode."""
        self.advance()  # consume mode token
        duration = self.parse_composition_args()

        # Handle the case where there's no explicit COLON after the composition
        # e.g., "phase1: serial()" - we already consumed "phase1:" and now see "serial"
        if self.match(TokenType.COLON):
            self.expect(TokenType.COLON)

        children = []
        while not self.match(TokenType.EOF, TokenType.COVER):
            # Check for end conditions (labeled phase or action)
            if self.match(TokenType.IDENTIFIER):
                next_token = self.peek_next()
                if next_token and next_token.type == TokenType.COLON:
                    # Next labeled phase - end this one
                    break
                elif next_token and next_token.type == TokenType.DOT:
                    # Action inside this phase
                    child = self.parse_phase_member()
                    if child:
                        children.append(child)
                    else:
                        break
                elif next_token and next_token.type == TokenType.LPAREN:
                    # Constraint in action, continue
                    child = self.parse_phase_member()
                    if child:
                        children.append(child)
                    else:
                        break
                else:
                    # Unknown identifier, break
                    break
            elif self.match(TokenType.SERIAL, TokenType.PARALLEL, TokenType.ONE_OF):
                # Nested composition, end this phase
                break
            elif self.match(TokenType.EMIT, TokenType.WAIT, TokenType.CALL):
                # Directive inside this phase
                child = self.parse_phase_member()
                if child:
                    children.append(child)
                else:
                    break
            else:
                # Unknown token, try to skip
                if self.match(TokenType.COLON):
                    break  # COLON likely starts next section
                self.advance()
                if self.pos > len(self.tokens) - 2:
                    break

        return PhaseNode(name=name, mode=mode, children=tuple(children), duration=duration)

    def parse_action(self) -> ActionNode:
        """Parse action: actor.action() with: constraints."""
        actor = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.DOT)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        self.expect(TokenType.RPAREN)

        action = ActionNode(actor=actor, name=name)

        # Parse with: constraints
        if self.match(TokenType.WITH):
            self.advance()
            self.expect(TokenType.COLON)
            constraints_list = self.parse_constraints()
            object.__setattr__(action, 'constraints', tuple(constraints_list))

        return action

    def parse_constraints(self) -> list[ConstraintNode]:
        """Parse constraints in with: block."""
        constraints = []

        while not self.match(TokenType.EOF):
            # Handle until directive first (can appear without constraints)
            if self.match(TokenType.UNTIL):
                until = self.parse_until_condition()
                # Create a constraint with just the until condition
                # This is used for actions that only specify termination condition
                constraint = ConstraintNode(
                    metric="until",
                    value=None,
                    anchor=AnchorType.END,
                    until=until
                )
                constraints.append(constraint)
                continue

            # Handle keep constraints
            if self.match(TokenType.KEEP):
                constraint = self.parse_keep_constraint()
                constraints.append(constraint)
                continue

            # Handle regular constraints
            if self.match(TokenType.IDENTIFIER):
                # Check if it's an action (actor.action) - stop
                if self.peek_next() and self.peek_next().type == TokenType.DOT:
                    break
                # Check if it's a constraint modifier consumed as metric
                if self.peek().value in ("hard", "default"):
                    # Skip modifiers without keep
                    self.advance()
                    if self.match(TokenType.COLON):
                        self.advance()
                    continue
                constraint = self.parse_simple_constraint()
                constraints.append(constraint)

                # Check for until directive after constraint
                if self.match(TokenType.UNTIL):
                    until = self.parse_until_condition()
                    # Attach until to last constraint
                    if constraints:
                        last_constraint = constraints[-1]
                        constraints[-1] = ConstraintNode(
                            metric=last_constraint.metric,
                            value=last_constraint.value,
                            anchor=last_constraint.anchor,
                            until=until,
                            constraint_modifier=last_constraint.constraint_modifier
                        )
                continue

            break

        return constraints

    def parse_keep_constraint(self) -> ConstraintNode:
        """Parse keep constraint: keep(modifier: expression) or keep(expression)."""
        self.expect(TokenType.KEEP)

        constraint_modifier = None

        # Check for modifier before parentheses: keep hard: (expression)
        if self.match(TokenType.HARD):
            constraint_modifier = "hard"
            self.advance()
            if self.match(TokenType.COLON):
                self.advance()
        elif self.match(TokenType.DEFAULT):
            constraint_modifier = "default"
            self.advance()
            if self.match(TokenType.COLON):
                self.advance()

        self.expect(TokenType.LPAREN)

        # Check for modifier inside parentheses: keep(hard: expression)
        if self.match(TokenType.HARD):
            constraint_modifier = "hard"
            self.advance()
            self.expect(TokenType.COLON)
        elif self.match(TokenType.DEFAULT):
            constraint_modifier = "default"
            self.advance()
            self.expect(TokenType.COLON)

        # Parse expression - could be metric in range, or metric == value, or metric op value
        metric = self.expect(TokenType.IDENTIFIER).value

        value = None
        anchor = AnchorType.END

        # Check for comparison operators
        if self.match(TokenType.EQUALS):
            # Single = operator
            self.advance()
            # Check for another = (==)
            if self.match(TokenType.EQUALS):
                self.advance()
            if self.match(TokenType.NUMBER):
                value = self.parse_number_value()
            elif self.match(TokenType.STRING):
                value = self.advance().value
            elif self.match(TokenType.IDENTIFIER):
                value = self.advance().value
        elif self.match(TokenType.IN):
            self.advance()
            if self.match(TokenType.LBRACKET):
                self.advance()
                start = self.parse_number_value()
                if self.match(TokenType.RANGE_OP):
                    self.advance()
                elif self.match(TokenType.DOT):
                    self.advance()
                    if self.match(TokenType.DOT):
                        self.advance()
                end = self.parse_number_value()
                self.expect(TokenType.RBRACKET)
                value = RangeValue(start=start, end=end)

        self.expect(TokenType.RPAREN)

        return ConstraintNode(metric=metric, value=value, anchor=anchor, constraint_modifier=constraint_modifier)

    def parse_simple_constraint(self) -> ConstraintNode:
        """Parse simple constraint: metric(value, at: end)."""
        metric = self.advance().value

        value = None
        anchor = AnchorType.END
        constraint_modifier = None

        # Check for constraint modifier
        if metric in ("keep", "hard", "default"):
            constraint_modifier = metric
            # Re-parse as keep-style
            return self.parse_keep_constraint_from_modifier(metric)

        if self.match(TokenType.LPAREN):
            self.advance()  # consume (

            # Parse value inside parentheses
            if self.match(TokenType.STRING):
                value = self.advance().value
            elif self.match(TokenType.NUMBER):
                value = self.parse_number_value()
            elif self.match(TokenType.IDENTIFIER):
                value = self.advance().value
            elif self.match(TokenType.LBRACKET):
                self.advance()  # [
                start = self.parse_number_value()
                # Handle range operator
                if self.match(TokenType.RANGE_OP):
                    self.advance()
                elif self.match(TokenType.DOT):
                    self.advance()  # consume first dot
                    if self.match(TokenType.DOT):
                        self.advance()  # consume second dot
                end = self.parse_number_value()
                self.expect(TokenType.RBRACKET)
                value = RangeValue(start=start, end=end)

            # Parse anchor (comma at: end)
            if self.match(TokenType.COMMA):
                self.advance()  # consume comma
                if self.match(TokenType.IDENTIFIER) and self.peek().value == "at":
                    self.advance()  # consume at
                    self.expect(TokenType.COLON)  # consume :
                    anchor_value = self.advance().value  # consume end value
                    anchor = AnchorType(anchor_value)

            self.expect(TokenType.RPAREN)  # consume )

        return ConstraintNode(metric=metric, value=value, anchor=anchor, constraint_modifier=constraint_modifier)

    def parse_keep_constraint_from_modifier(self, modifier: str) -> ConstraintNode:
        """Parse keep-style constraint when modifier was consumed as metric."""
        # This handles cases where we already consumed the modifier as the metric
        # Need to parse the actual metric and value
        self.expect(TokenType.LPAREN)

        actual_metric = self.expect(TokenType.IDENTIFIER).value
        value = None
        anchor = AnchorType.END

        if self.match(TokenType.IN):
            self.advance()
            if self.match(TokenType.LBRACKET):
                self.advance()
                start = self.parse_number_value()
                if self.match(TokenType.RANGE_OP):
                    self.advance()
                elif self.match(TokenType.DOT):
                    self.advance()
                    if self.match(TokenType.DOT):
                        self.advance()
                end = self.parse_number_value()
                self.expect(TokenType.RBRACKET)
                value = RangeValue(start=start, end=end)
        elif self.match(TokenType.EQUALS):
            self.advance()
            if self.match(TokenType.NUMBER):
                value = self.parse_number_value()
            elif self.match(TokenType.STRING):
                value = self.advance().value
            elif self.match(TokenType.IDENTIFIER):
                value = self.advance().value

        self.expect(TokenType.RPAREN)

        return ConstraintNode(metric=actual_metric, value=value, anchor=anchor, constraint_modifier=modifier)

    def parse_until_condition(self) -> UntilCondition:
        """Parse until directive: until @event or until elapsed(time)."""
        self.expect(TokenType.UNTIL)

        event_name = None
        elapsed_time = None
        expression = None

        if self.match(TokenType.AT):
            self.advance()
            event_name = self.expect(TokenType.IDENTIFIER).value
        elif self.match(TokenType.ELAPSED):
            self.advance()
            self.expect(TokenType.LPAREN)
            elapsed_time = self.parse_duration_literal()
            self.expect(TokenType.RPAREN)
        else:
            # Expression-based until
            expression = self.parse_expression_until(TokenType.IDENTIFIER, TokenType.EOF)
            # Check for @event in expression
            if expression.startswith("@"):
                event_name = expression[1:]

        # Handle "or" combination
        if self.match(TokenType.OR):
            self.advance()
            # Parse second condition
            if self.match(TokenType.ELAPSED):
                self.advance()
                self.expect(TokenType.LPAREN)
                elapsed_time = self.parse_duration_literal()
                self.expect(TokenType.RPAREN)
            elif self.match(TokenType.AT):
                self.advance()
                # If we already have event_name, this is a secondary event
                pass

        return UntilCondition(event_name=event_name, elapsed_time=elapsed_time, expression=expression)


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