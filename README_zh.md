# OSC DSL 编译器

面向企业网络模拟的 OpenSCENARIO 类 DSL 编译器。

## 概述

本编译器将用于网络场景定义的领域特定语言（DSL）转换为中间表示（IR）、执行计划和运行时检查器规范。系统面向**企业网络模拟**，而非自动驾驶。

**核心原则**：编译器生成模拟后端所需的产物——它本身**不**模拟网络行为。

## 特性

- **DSL 解析器**：OSC 类语法的词法分析器和递归下降解析器
- **语义 IR**：场景、角色、动作、约束的结构化表示
- **执行 IR**：后端无关的执行计划，包含阶段和任务
- **约束 IR**：用于验证的正式约束规范
- **动作绑定**：DSL 动作到后端操作的灵活映射
- **检查器规范**：运行时验证和覆盖规格
- **端到端管道**：完整的编译管道，支持 Mock 后端

## 架构

```text
DSL 源码 → 解析器 → AST → 语义 IR → 执行 IR → 检查器规范
                              ↓
                         绑定映射
                              ↓
                         后端执行
```

### IR 层次

1. **语法 IR (AST)**：贴近源码语法
2. **语义 IR**：场景结构、角色、动作、约束、事件、覆盖
3. **执行 IR**：阶段、任务、后端操作、验收规则

## 项目结构

```text
compiler/
├── parser/              # DSL 解析
│   ├── parser.py        # 词法分析器 + 解析器类
│   └── test.py          # 解析器测试
├── semantic/            # 符号解析
│   └── symbol_table.py  # 符号表实现
├── ir/                  # 中间表示
│   ├── ast_nodes.py     # AST 节点定义
│   ├── semantic_ir.py   # 语义 IR 定义
│   ├── execution_ir.py  # 执行 IR 定义
│   ├── to_semantic_ir.py    # AST → 语义 IR 转换器
│   └── generate_execution_plan.py  # 执行计划生成器
│   └── compile_constraints.py      # 约束编译 CLI
├── bindings/            # 动作 → 后端映射
│   ├── binding.yaml     # 绑定配置
│   ├── loader.py        # YAML 加载器
│   └── mapper.py        # 动作映射器
├── runtime/             # 运行时验证
│   ├── checker_spec.py  # 检查器规范定义
│   └── validator.py     # 约束验证器
└── lowering/            # IR 变换
    ├── e2e_pipeline.py  # 端到端管道
    ├── execute_scenario.py  # 场景执行器
    ├── mock_backend.py  # Mock 后端实现
    └── execution_trace.py   # 执行跟踪记录器

examples/                # OSC DSL 示例文件
└── enterprise_wifi.osc  # 企业 WiFi 场景
```

## DSL 示例

```osc
scenario enterprise_wifi_session:
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
```

## 语义模型

| 概念 | 描述 |
|------|------|
| Scenario（场景） | 动作的组合 |
| Action（动作） | 原子行为（不可分解） |
| Actor（角色） | 执行动作的实体 |
| Event（事件） | 时间锚点（开始/结束） |
| Constraint（约束） | 对指标的条件 |
| Coverage（覆盖） | 采样要求 |

## 执行语义

- `serial()` → 有序阶段
- `parallel()` → 并发执行
- 约束在锚点处评估（`at: start`, `at: end`)
- 覆盖在采样事件处评估

## 动作绑定

动作是抽象的，通过 `binding.yaml` 进行映射：

```yaml
laptop.scan_ssid:
  backend: wifi.scan
  outputs: [signal_strength, ssid, channel]

laptop.authenticate:
  backend: aaa.authenticate
  outputs: [auth_status, auth_latency_ms]
```

## 生成的输出文件

| 文件 | 描述 |
|------|------|
| `semantic_ir.json` | 语义 IR 表示 |
| `constraint_ir.json` | 编译后的约束 |
| `execution_plan.json` | 后端执行计划 |
| `checker_spec.json` | 运行时验证规范 |
| `execution_trace.json` | 后端执行跟踪 |
| `final_report.json` | 验证结果 |

## 快速开始

```bash
# 解析 DSL 源码
python -m compiler.parser.parser examples/enterprise_wifi.osc

# 生成语义 IR
python compiler/ir/to_semantic_ir.py

# 编译约束
python compiler/ir/compile_constraints.py

# 生成执行计划
python compiler/ir/generate_execution_plan.py

# 运行端到端管道
python compiler/lowering/e2e_pipeline.py examples/enterprise_wifi.osc
```

## 设计原则

1. **正确性优于完整性** - 优先保证 IR 生成的正确性
2. **显式 IR 优于隐式逻辑** - 所有变换都是可见的
3. **关注点分离** - 解析、语义、执行彼此独立
4. **后端解耦** - 不依赖特定模拟后端

## 许可证

MIT
