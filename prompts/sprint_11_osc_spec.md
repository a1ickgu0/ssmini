# Sprint 11: Implement OpenSCENARIO 2.0 DSL Specification

## Overview

Based on the OpenSCENARIO 2.0 Language Reference Manual (Sections 7.1-7.7), implement a compliant DSL parser/compiler for enterprise network simulation scenarios.

**Reference**: OpenSCENARIO v2 Language Reference Manual (asam-ev.github.io/OpenSCENARIO-v2)

## Language Features to Implement

### Priority 1: Core Scenario Structure (Already Partially Implemented)

The current implementation already supports:
- `scenario` declarations
- Actor declarations (`actor: type`)
- `do serial()/parallel()` composition
- Action invocations (`actor.action()`)
- `with:` blocks for constraints
- `cover` declarations

**Enhancements needed**:
1. Support `one_of` composition operator
2. Support labeled phases (`phase_name: serial()/parallel()`)
3. Support `duration` parameter for composition operators
4. Support `until` directive in `with:` blocks

### Priority 2: Type System

Keywords to add:
```
struct, actor, action, enum, inherits, type, unit, SI
```

Type declarations:
```osc
# Physical type declaration
type speed is SI(m: 1, s: -1)

# Unit declaration
unit kph of speed is SI(m: 1, s: -1, factor: 0.277778)

# Enum declaration  
enum network_status: [disconnected, connecting, connected, error]

# Struct declaration
struct wifi_config:
    ssid: string
    security: string
    channel: uint

# Actor declaration (inheritance)
actor network_device inherits physical_object:
    mac_address: string
    ip_address: string
```

### Priority 3: Field and Variable Declarations

```osc
# Parameter declaration with default and constraints
name: type = default_value with:
    keep(constraint_expression)

# Variable declaration
var signal_log: list of signal_sample

# Sample expression
var current_signal: signal_strength = sample(signal, @scan.end)
```

### Priority 4: Constraint System Enhancement

Keywords to add:
```
keep, hard, default, remove_default
```

```osc
# Keep constraint
keep(signal_strength in [-67..-55])
keep(default: auth_latency_ms < 1000)
keep(hard: connection_status == connected)

# Remove default
remove_default(timeout_ms)
```

### Priority 5: Event System

Keywords to add:
```
event, on, emit, wait, rise, fall, elapsed, every, until
```

```osc
# Event declaration
event connection_timeout is elapsed(30s)
event signal_lost is fall(signal_strength > -80)

# On directive for event handling
on @connection_timeout:
    call(log_event())
    emit(disconnected())

# Wait directive
wait @signal_stable

# Until directive in behavior invocation
laptop.authenticate() with:
    until @auth_complete or elapsed(10s)
```

### Priority 6: Method Definitions

Keywords to add:
```
def, is, expression, external, undefined, only
```

```osc
# Expression method
def is_connected() -> bool is expression connection_status == connected

# External method
def send_packet(data: bytes) -> bool is external network.send_packet(data)

# Only expression (singleton)
def only: default_gateway is expression routers.first(it.is(gateway))
```

### Priority 7: Import and Extension

Keywords to add:
```
import, extend, global
```

```osc
# Import statement
import osc.standard
import "network_library.osc"

# Type extension
extend wifi_config:
    encryption: string

# Global parameter
global network_seed: uint = 42
```

### Priority 8: Modifier System

Keywords to add:
```
modifier, of
```

```osc
# Modifier declaration
modifier high_performance of laptop.drive:
    keep(cpu_usage < 0.8)
    on @start:
        call(set_high_power())

# Modifier application
laptop.authenticate() with:
    timeout(30s)
    retry_on_failure(max: 3)
```

### Priority 9: Coverage Enhancement

Keywords to add:
```
record, target, buckets, ignore, override
```

```osc
# Cover with target
cover(signal_strength, target: 50, range: [-80..-40], every: 10)

# Record directive
record(auth_latency, unit: ms)

# Cross coverage
cover(network_params, items: [signal, latency, throughput])

# Override
cover(override: signal_strength, target: 100)
```

### Priority 10: Expression System

Operators to support:
```
in, =>, and, or, not, .is(), .as(), .size(), .filter(), .map(), .has()
```

Range expressions:
```osc
# Range constructor
range(10, 20)
[10..20]

# In operator
keep(speed in [10..100])
```

## Lexer Changes

### New Keywords (49 total)
```python
KEYWORDS = {
    "action", "actor", "and", "as", "bool", "call", "cover", "def", "default",
    "do", "elapsed", "emit", "enum", "event", "every", "expression", "extend",
    "external", "fall", "float", "global", "hard", "if", "import", "inherits",
    "int", "is", "it", "keep", "list", "not", "of", "on", "one_of", "only",
    "or", "parallel", "range", "record", "remove_default", "rise", "scenario",
    "serial", "SI", "string", "struct", "type", "uint", "undefined", "unit",
    "until", "var", "wait", "with"
}
```

### New Operators
```python
OPERATORS = {
    "==", "!=", "<", "<=", ">", ">=", "in", "+", "-", "*", "/", "%",
    "and", "or", "not", "=>", "?", ":", "->", ".", ",", ":", "=", "@",
    "|", "(", ")", "[", "]"
}
```

### Physical Type Literals
```osc
# Physical literals (number + unit)
100kph
30s  
-5dBm
```

## Grammar Changes (EBNF Summary)

```ebnf
# Top-level
osc-file ::= import-statement* osc-declaration*

# Declarations
osc-declaration ::= 
    physical-type-declaration
    | unit-declaration
    | enum-declaration
    | struct-declaration
    | actor-declaration
    | action-declaration
    | scenario-declaration
    | modifier-declaration
    | type-extension
    | global-parameter-declaration

# Behavior specification
behavior-specification ::= on-directive | do-directive

do-directive ::= 'do' do-member
do-member ::= [label ':'] (composition | behavior-invocation | wait/emit/call)

composition ::= composition-operator '(' [args] ')' ':' do-member+ [with-block]
composition-operator ::= 'serial' | 'one_of' | 'parallel'

behavior-invocation ::= [actor '.'] behavior-name '(' [args] ')' [with-block]

# Events
event-specification ::= '@' event-path [ 'if' event-condition ]
                       | event-condition

event-condition ::= bool-expression | rise/fall/elapsed/every expressions
```

## Test Cases

### Test 1: Basic Scenario with Labels
```osc
scenario wifi_connection:
    laptop: device
    router: access_point
    
    do connect:
        phase1:
            laptop.scan_ssid() with:
                keep(signal_strength in [-67..-55])
        phase2: serial():
            laptop.associate_ap()
            laptop.authenticate() with:
                until @auth_done or elapsed(30s)
```

### Test 2: One_of Composition
```osc
scenario roaming_test:
    phone: mobile_device
    
    do one_of():
        phone.roam_to_ap1()
        phone.roam_to_ap2()
        phone.roam_to_ap3()
```

### Test 3: Event Handling
```osc
scenario connection_monitor:
    device: network_device
    
    event connection_lost is fall(device.connected)
    event timeout_reached is elapsed(60s)
    
    on @connection_lost:
        emit(alert())
        call(device.retry_connect())
    
    do parallel():
        device.run_test()
        wait @timeout_reached
```

### Test 4: Struct and Enum
```osc
enum wifi_security: [open, wpa2_psk, wpa2_ent, wpa3]

struct network_profile:
    ssid: string
    security: wifi_security
    priority: uint = 0 with:
        keep(priority in [0..10])

scenario multi_network:
    profile: network_profile
    
    do serial():
        laptop.connect(profile.ssid, profile.security)
```

### Test 5: Inheritance
```osc
actor enterprise_device inherits network_device:
    domain: string
    vpn_config: vpn_profile
    
action enterprise_device.login():
    duration: duration = 5s
    
    do serial():
        authenticate()
        connect_vpn()
```

### Test 6: Coverage with Targets
```osc
scenario performance_test:
    cover(latency_ms, target: 100, range: [0..500], every: 50,
          ignore: latency_ms < 0)
    record(throughput_mbps, unit: Mbps)
    
    cover(network_quality, items: [latency_ms, throughput_mbps, signal])
```

### Test 7: Modifier
```osc
modifier high_qos of laptop.stream:
    keep(bitrate >= 10Mbps)
    on @start:
        call(set_qos_high())

scenario video_call:
    laptop: device
    
    do serial():
        laptop.stream() with:
            high_qos()
```

### Test 8: Expressions
```osc
scenario complex_scenario:
    devices: list of network_device
    routers: list of router
    
    keep(devices.size() >= 3)
    keep(routers.has(it.is(default_gateway)))
    keep(devices.filter(it.connected).size() == devices.size())
    
    def all_connected() -> bool is expression 
        devices.filter(it.connected).size() == devices.size()
```

## Implementation Approach

1. **Phase 1**: Extend lexer with new keywords and operators
2. **Phase 2**: Extend AST node definitions for new constructs
3. **Phase 3**: Implement parser methods for new grammar elements
4. **Phase 4**: Update Semantic IR for new types
5. **Phase 5**: Update Execution IR generation
6. **Phase 6**: Add expression evaluator for complex expressions
7. **Phase 7**: Write comprehensive tests for each feature

## Notes

- Focus on enterprise network simulation domain, not autonomous driving
- Physical types may not be needed for network simulation (use standard units like ms, Mbps)
- `SI` units can be simplified
- Import mechanism can be deferred (single-file scenarios sufficient for current scope)