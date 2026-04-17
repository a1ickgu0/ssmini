# OSC DSL 编译器

面向企业网络模拟的 OpenSCENARIO 2.0 类 DSL 编译器。

## 概述

本编译器将用于网络场景定义的领域特定语言（DSL）转换为中间表示（IR）、执行计划和运行时检查器规范。系统面向**企业网络模拟**，而非自动驾驶。

**核心原则**：编译器生成模拟后端所需的产物——它本身**不**模拟网络行为。

## 特性

### 核心编译器特性

- **DSL 解析器**：OSC 2.0 语法的词法分析器和递归下降解析器（49 关键字）
- **语义 IR**：场景、角色、动作、约束、事件的结构化表示
- **执行 IR**：后端无关的执行计划，包含阶段和任务
- **约束 IR**：用于验证的正式约束规范
- **动作绑定**：DSL 动作到后端操作的灵活映射（20 个绑定）
- **检查器规范**：运行时验证和覆盖规格
- **端到端管道**：完整的编译管道，支持 Mock 后端

### OSC 2.0 语言特性（Sprint 11）

- **组合操作符**：`serial()`、`parallel()`、`one_of()`
- **标记阶段**：命名执行阶段（如 `phase1: serial()`）
- **事件系统**：`event`、`on`、`emit`、`wait`、`until` 指令
- **约束修饰符**：`keep`、`keep(hard:)`、`keep(default:)`
- **时长参数**：时序规格（如 `duration: 30s`）
- **时序字面量**：带单位的时长（`30s`、`100ms`、`5m`）

## 架构

```text
DSL 源码 → 解析器 → AST → 语义 IR → 执行 IR → 检查器规范
                              ↓
                         绑定映射
                              ↓
                         后端执行
                              ↓
                         约束验证
                              ↓
                         最终报告
```

### IR 层次

1. **语法 IR (AST)**：贴近源码语法
2. **语义 IR**：场景结构、角色、动作、约束、事件、覆盖
3. **执行 IR**：阶段、任务、后端操作、验收规则

## 项目结构

```text
compiler/
├── parser/              # DSL 解析（OSC 2.0 词法分析器 + 解析器）
│   ├── parser.py        # 词法分析器 + 解析器类（49 关键字）
│   └── test.py          # 解析器测试
├── ir/                  # 中间表示
│   ├── ast_nodes.py     # AST 节点（Scenario, Actor, Phase, Action, Event 等）
│   ├── semantic_ir.py   # 语义 IR + 约束编译
│   └── to_semantic_ir.py    # AST → 语义 IR 转换器
├── bindings/            # 动作 → 后端映射
│   ├── binding.yaml     # 20 个绑定（wifi.*、aaa.*、dhcp.*、vpn.* 等）
│   ├── loader.py        # YAML 加载器
│   └── mapper.py        # 执行计划映射器
├── runtime/             # 运行时验证
│   ├── checker_spec.py  # 约束规范定义
│   └── validator.py     # 约束验证器（范围、相等）
└── lowering/            # IR 变换 & 执行
    ├── e2e_execute.py   # 端到端执行 CLI
    ├── mock_backend.py  # Mock 后端（20 个操作）
    └── execution_trace.py  # 执行跟踪记录器

examples/                # OSC DSL 示例文件
└── enterprise_wifi.osc  # 企业 WiFi 场景（16 动作、40 约束）

prompts/                 # Sprint 规范文档
└── sprint_11_osc_spec.md  # OSC 2.0 实现规范
```

## DSL 示例（OSC 2.0）

### 基本场景

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

### OSC 2.0 事件系统

```osc
scenario connection_monitor:
    device: network_device

    # 事件声明
    event connection_timeout is elapsed(30s)
    event auth_complete is rise(auth_status == success)

    # 事件处理器
    on @connection_timeout:
        emit(disconnected())
        call(retry_connection())

    do serial():
        device.authenticate() with:
            until @auth_complete or elapsed(10s)
```

### OSC 2.0 组合操作符

```osc
scenario roaming_test:
    phone: mobile_device

    # one_of：执行其中一个选项
    do one_of():
        phone.roam_to_ap1()
        phone.roam_to_ap2()
        phone.roam_to_ap3()

    # 带时长参数的标记阶段
    do test:
        phase1: serial(duration: 30s):
            phone.scan_ssid()
        phase2: parallel():
            phone.authenticate()
            phone.dhcp_discover()
```

### OSC 2.0 约束修饰符

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

## 语义模型

| 概念 | 描述 |
|------|------|
| Scenario（场景） | 动作和阶段的组合 |
| Action（动作） | 原子行为（不可分解） |
| Actor（角色） | 执行动作的实体 |
| Phase（阶段） | 执行单元，带 serial/parallel/one_of 模式 |
| Event（事件） | 命名条件（elapsed、rise、fall、expression） |
| On Directive（On 指令） | 事件处理器（on @event: emit/wait/call） |
| Constraint（约束） | 对指标的条件（at: start/end） |
| Coverage（覆盖） | 采样要求（target、sampling、min_samples） |
| Until | 动作的终止条件 |

## 执行语义

| 操作符 | 行为 |
|--------|------|
| `serial()` | 按顺序执行子节点，等待每个完成 |
| `parallel()` | 并发执行子节点，等待全部完成 |
| `one_of()` | 执行恰好一个子节点（随机选择） |
| `with:` 块 | 为动作附加约束 |
| `until` 指令 | 条件满足时终止动作 |

约束评估：
- 约束在指定锚点处评估（`at: start`、`at: end`）
- `keep` 约束：域限制
- 覆盖在采样事件处评估

## 动作绑定

动作是抽象的，通过 `binding.yaml` 进行映射：

```yaml
# WiFi 操作
laptop.scan_ssid:
  backend: wifi.scan
  inputs: []
  outputs: [signal_strength, ssid, channel, security, frequency]

# 认证操作
laptop.authenticate:
  backend: aaa.authenticate
  inputs: [username, password]
  outputs: [auth_status, auth_latency_ms, auth_method, certificate_valid]

# 网络操作
laptop.dhcp_discover:
  backend: dhcp.discover
  outputs: [dhcp_status, dhcp_latency_ms, ip_assigned, ip_address]

laptop.connect_vpn:
  backend: vpn.connect
  inputs: [vpn_server]
  outputs: [vpn_status, vpn_latency_ms]
```

**当前绑定（共 20 个）**：wifi.scan、wifi.scan_channels、wifi.associate、wifi.detect_signal、wifi.roam、aaa.authenticate、aaa.login、aaa.deauthenticate、dhcp.discover、dns.resolve、vpn.connect、proxy.connect、file.share_access、email.send、http.access、service.reconnect、network.configure、network.deploy_ap、traffic.generate。

## 生成的输出文件

| 文件 | 描述 |
|------|------|
| `ast.json` | AST 表示（树结构） |
| `semantic_ir.json` | 语义 IR（角色、阶段、约束、覆盖） |
| `constraint_ir.json` | 编译后的约束（40 约束） |
| `execution_plan.json` | 执行计划（16 绑定动作） |
| `execution_trace.json` | 后端执行跟踪 |
| `execution_results.json` | 每个动作的详细执行结果 |
| `final_report.json` | 验证结果（通过/失败、违规） |

## 快速开始

```bash
# 解析 DSL 并显示 AST
python -m compiler.parser.parser examples/enterprise_wifi.osc

# 运行完整端到端管道
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -v

# 使用指定种子以确保可复现性
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -s 42 -o output/report.json

# 输出到 examples/output 目录
python compiler/lowering/e2e_execute.py examples/enterprise_wifi.osc -o examples/output/final_report.json -v
```

## Mock 后端操作

Mock 后端模拟 20 个企业网络操作：

| 领域 | 操作 |
|------|------|
| WiFi | scan、scan_channels、associate、disassociate、detect_signal、roam |
| AAA | authenticate、login、deauthenticate |
| 网络 | dhcp_discover、dns_resolve |
| VPN/代理 | vpn_connect、proxy_connect |
| 服务 | file_share_access、email_send、http_access、service_reconnect |
| 管理 | configure_router、deploy_ap、generate_traffic |

## 设计原则

1. **正确性优于完整性** - 优先保证 IR 生成的正确性
2. **显式 IR 优于隐式逻辑** - 所有变换都是可见的
3. **关注点分离** - 解析、语义、执行彼此独立
4. **后端解耦** - 不依赖特定模拟后端
5. **约束驱动模拟** - Mock 值满足 DSL 约束

## 后端集成

编译器后端设计为可替换：

```python
# Mock 后端（当前）
backend = MockBackend(seed=42)

# 真实后端（ns-3、Mininet、真实设备）
backend = NS3Backend(config={"script": "wifi_test.py"})
# 或
backend = MininetBackend(config={...})
# 或
backend = RealDeviceBackend(config={"devices": {...}})
```

所有后端必须实现：
- `execute(operation: str, **kwargs) -> OperationResult`
- 返回与 DSL 约束名称匹配的指标

## 许可证

MIT