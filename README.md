# OSC DSL Compiler

A compiler for OpenSCENARIO 2.0-like DSL targeting enterprise network simulation.

## Overview

This compiler translates a domain-specific language (DSL) for network scenario definitions into intermediate representations (IR), execution plans, and runtime checker specifications. It is designed for **enterprise network simulation**, not autonomous driving.

**Key Principle**: The compiler produces artifacts for simulation backends - it does NOT simulate network behavior itself.

## Features

### Core Compiler Features

- **DSL Parser**: Lexer and recursive descent parser for OSC 2.0 syntax (49 keywords)
- **Semantic IR**: Structured representation of scenarios, actors, actions, constraints, events
- **Execution IR**: Backend-neutral execution plans with phases and tasks
- **Constraint IR**: Formal constraint specifications for validation
- **Action Binding**: Flexible mapping from DSL actions to backend operations (20 bindings)
- **Checker Spec**: Runtime validation and coverage specifications
- **E2E Pipeline**: Complete compilation pipeline with mock backend support

### OSC 2.0 Language Features (Sprint 11)

- **Composition Operators**: `serial()`, `parallel()`, `one_of()`
- **Labeled Phases**: Named execution phases (e.g., `phase1: serial()`)
- **Event System**: `event`, `on`, `emit`, `wait`, `until` directives
- **Constraint Modifiers**: `keep`, `keep(hard:)`, `keep(default:)`
- **Duration Parameters**: Temporal specifications (e.g., `duration: 30s`)
- **Temporal Literals**: Duration with units (`30s`, `100ms`, `5m`)

## Architecture

```text
DSL Source → Parser → AST → Semantic IR → Execution IR → Checker Spec
                                         ↓
                                    Binding Mapping
                                         ↓
                                    Backend Execution
                                         ↓
                                    Constraint Validation
                                         ↓
                                    Final Report
```

### IR Layers

1. **Syntax IR (AST)**: Close to source syntax
2. **Semantic IR**: Scenario structure, actors, actions, constraints, events, coverage
3. **Execution IR**: Phases, tasks, backend operations, acceptance rules

## Project Structure

```text
compiler/
├── parser/              # DSL parsing (OSC 2.0 Lexer + Parser)
│   ├── parser.py        # Lexer + Parser classes (49 keywords)
│   └── test.py          # Parser tests
├── ir/                  # Intermediate representations
│   ├── ast_nodes.py     # AST nodes (Scenario, Actor, Phase, Action, Event, etc.)
│   ├── semantic_ir.py   # Semantic IR + Constraint compilation
│   └── to_semantic_ir.py    # AST → Semantic IR converter
├── bindings/            # Action → backend mapping
│   ├── binding.yaml     # 20 bindings (wifi.*, aaa.*, dhcp.*, vpn.*, etc.)
│   ├── loader.py        # YAML loader
│   └── mapper.py        # Execution plan mapper
├── runtime/             # Runtime validation
│   ├── checker_spec.py  # Constraint spec definitions
│   └and validator.py     # Constraint validator (range, equality)
└── lowering/            # IR transformations & execution
    ├── e2e_execute.py   # End-to-end execution CLI
    ├── mock_backend.py  # Mock backend (20 operations)
    └── execution_trace.py  # Execution trace recorder

examples/                # OSC DSL example files
└── enterprise_wifi.osc  # Enterprise WiFi scenario (16 actions, 40 constraints)

prompts/                 # Sprint specification documents
└── sprint_11_osc_spec.md  # OSC 2.0 implementation specification
```

## DSL Example (OSC 2.0)

### Basic Scenario

```osc
scenario enterprise_wifi_session:
    worker: employee
    laptop: managed_laptop

    do serial():
        discovery: parallel():
            laptop.scan_ssid() with:
                signal_strength([-67..-55], at: end)
                ssid_found(true, at: end)

            laptop.scan_channels() with:
                channels_found([1..13], at: end)

        authentication: serial():
            laptop.associate_ap() with:
                association_status(success, at: end)

            laptop.authenticate() with:
                auth_status(success, at: end)
                auth_latency_ms([200..1500], at: end)

    cover signal_strength_range:
        target: signal_strength
        sampling: event
        min_samples: 10
```

### OSC 2.0 Event System

```osc
scenario connection_monitor:
    device: network_device

    # Event declarations
    event connection_timeout is elapsed(30s)
    event auth_complete is rise(auth_status == success)

    # Event handlers
    on @connection_timeout:
        emit(disconnected())
        call(retry_connection())

    do serial():
        device.authenticate() with:
            until @auth_complete or elapsed(10s)
```

### OSC 2.0 Composition Operators

```osc
scenario roaming_test:
    phone: mobile_device

    # one_of: execute one of the alternatives
    do one_of():
        phone.roam_to_ap1()
        phone.roam_to_ap2()
        phone.roam_to_ap3()

    # labeled phases with duration
    do test:
        phase1: serial(duration: 30s):
            phone.scan_ssid()
        phase2: parallel():
            phone.authenticate()
            phone.dhcp_discover()
```

### OSC 2.0 Constraint Modifiers

```osc
scenario performance_test:
    laptop: device

    do serial():
        laptop.authenticate() with:
            keep(auth_latency_ms in [200..1500])
            keep(hard: auth_status == success)
            keep(default: certificate_valid == true)

        laptop.connect_vpn() with:
            vpn_status(connected, at: end)
            until @vpn_ready or elapsed(60s)
```

## Semantic Model

| Concept | Description |
|---------|-------------|
| Scenario | Composition of actions and phases |
| Action | Atomic behavior (non-decomposable) |
| Actor | Entity performing actions |
| Phase | Execution unit with serial/parallel/one_of mode |
| Event | Named condition (elapsed, rise, fall, expression) |
| On Directive | Event handler (on @event: emit/wait/call) |
| Constraint | Condition over metrics (at: start/end) |
| Coverage | Sampling requirement (target, sampling, min_samples) |
| Until | Termination condition for actions |

## Execution Semantics

| Operator | Behavior |
|----------|----------|
| `serial()` | Execute children in order, wait for each to complete |
| `parallel()` | Execute children concurrently, wait for all to complete |
| `one_of()` | Execute exactly one child (random selection) |
| `with:` block | Attach constraints to action |
| `until` directive | Terminate action when condition met |

Constraint evaluation:
- Constraints evaluated at specified anchors (`at: start`, `at: end`)
- `keep` constraints: domain restrictions
- Coverage evaluated at sampling events

## Action Binding

Actions are abstract and mapped via `binding.yaml`:

```yaml
# WiFi operations
laptop.scan_ssid:
  backend: wifi.scan
  inputs: []
  outputs: [signal_strength, ssid, channel, security, frequency]

# Authentication operations  
laptop.authenticate:
  backend: aaa.authenticate
  inputs: [username, password]
  outputs: [auth_status, auth_latency_ms, auth_method, certificate_valid]

# Network operations
laptop.dhcp_discover:
  backend: dhcp.discover
  outputs: [dhcp_status, dhcp_latency_ms, ip_assigned, ip_address]

laptop.connect_vpn:
  backend: vpn.connect
  inputs: [vpn_server]
  outputs: [vpn_status, vpn_latency_ms]
```

**Current bindings (20 total)**: wifi.scan, wifi.scan_channels, wifi.associate, wifi.detect_signal, wifi.roam, aaa.authenticate, aaa.login, aaa.deauthenticate, dhcp.discover, dns.resolve, vpn.connect, proxy.connect, file.share_access, email.send, http.access, service.reconnect, network.configure, network.deploy_ap, traffic.generate.

## Generated Outputs

| File | Description |
|------|-------------|
| `ast.json` | AST representation (tree structure) |
| `semantic_ir.json` | Semantic IR (actors, phases, constraints, coverages) |
| `constraint_ir.json` | Compiled constraints (40 constraints) |
| `execution_plan.json` | Execution plan (16 bound actions) |
| `execution_trace.json` | Execution trace from backend |
| `execution_results.json` | Detailed execution results per action |
| `final_report.json` | Validation results (pass/fail, violations) |

## Quick Start

```bash
# Parse DSL and show AST
python -m compiler.parser.parser examples/enterprise_wifi.osc

# Run complete E2E pipeline
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -v

# Run with specific seed for reproducibility
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -s 42 -o output/report.json

# Output to examples/output directory
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -o examples/output/final_report.json -v
```

## Mock Backend Operations

The mock backend simulates 20 enterprise network operations:

| Domain | Operations |
|--------|------------|
| WiFi | scan, scan_channels, associate, disassociate, detect_signal, roam |
| AAA | authenticate, login, deauthenticate |
| Network | dhcp_discover, dns_resolve |
| VPN/Proxy | vpn_connect, proxy_connect |
| Services | file_share_access, email_send, http_access, service_reconnect |
| Admin | configure_router, deploy_ap, generate_traffic |

## Design Principles

1. **Correctness over completeness** - Prioritize correct IR generation
2. **Explicit IR over implicit logic** - All transformations are visible
3. **Separation of concerns** - Parsing, semantics, execution are distinct
4. **Backend decoupling** - No dependency on specific simulation backend
5. **Constraint-driven simulation** - Mock values satisfy DSL constraints

## Backend Integration

The compiler backend is designed to be replaceable:

```python
# Mock backend (current)
backend = MockBackend(seed=42)

# Real backend (ns-3, Mininet, real devices)
backend = NS3Backend(config={"script": "wifi_test.py"})
# or
backend = MininetBackend(config={...})
# or  
backend = RealDeviceBackend(config={"devices": {...}})
```

All backends must implement:
- `execute(operation: str, **kwargs) -> OperationResult`
- Return metrics that match DSL constraint names

## License

MIT