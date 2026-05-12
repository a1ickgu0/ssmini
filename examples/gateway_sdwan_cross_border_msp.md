# Gateway SD-WAN 跨境 MSP 场景说明

> 对应场景文件：`gateway_sdwan_cross_border_msp.osc`
>
> 维护约定：如果后续修改 `.osc` 场景中的角色、阶段、动作、指标或覆盖目标，需要同步更新本文档，保证产品说明与可执行场景保持一致。

## 1. 一句话说明

这个场景描述的是：佳慧 Gateway 作为跨境网络 MSP/ISP 服务商，为企业客户创建独立 SD-WAN 租户，快速接入无公网 IP 的分支站点，建立加密 Overlay 隧道，并通过 SLA 和应用策略选择跨境访问路径；当主链路质量下降时，系统能够自动告警、切换路径，并由 NOC 生成可解释的故障恢复报告。

这不是一个普通企业“自用 SD-WAN”的场景，而是一个服务商运营场景。产品要支持 Gateway 面向多个客户、多分支、多 POP、多链路进行集中交付、监控和运维。

对应 OSC 片段：

```osc
scenario gateway_sdwan_cross_border_msp:
    gateway_management: msp_decision_maker
    gateway_engineer: sdwan_network_engineer
    gateway_noc: noc_operator
    customer_it: enterprise_it_lead
    branch_cpe: sdwan_branch_cpe
    branch_user: remote_business_user
    carrier_cloud: underlay_provider
```

代码解读：

这里定义了一个名为 `gateway_sdwan_cross_border_msp` 的场景。`scenario` 后面的名字是场景标识，表示这个 DSL 文件不是描述一个单点功能，而是在描述“Gateway 跨境 SD-WAN MSP 服务”这个完整业务场景。下面的多行 `角色名: 角色类型` 是参与方声明，说明本场景会同时观察服务商、客户、分支设备、分支用户和 Underlay 供应方之间的协作。

## 2. 业务目标

本场景希望验证产品是否具备以下能力：

| 目标 | 产品可理解的含义 |
| --- | --- |
| 多租户服务准备 | Gateway 可以为不同企业客户创建隔离的服务空间，避免客户之间互相影响。 |
| 低接触分支开局 | 分支 CPE 即使没有公网 IP，也可以注册到 Gateway，并完成远程上线。 |
| 安全 Overlay 建立 | 分支与 Gateway/POP 之间可以建立加密隧道，承载跨境业务流量。 |
| 路由和业务路径可控 | 分支路由可以导入 Overlay，跨境业务访问可以按 SLA 和策略选择合适路径。 |
| 集中可视化运维 | Gateway NOC 可以看到拓扑、隧道、告警和日志关联，及时发现问题。 |
| 故障恢复可解释 | 主链路劣化后，系统能触发告警、切换路径，并输出可说明原因和处理结果的报告。 |

对应 OSC 片段：

```osc
do serial():
    service_preparation:
        parallel():
            ...

    branch_onboarding:
        serial():
            ...

    cross_border_operation:
        parallel():
            ...

    failure_recovery:
        serial():
            ...
```

代码解读：

`do serial()` 表示整体业务按顺序推进：先准备服务，再接入分支，然后进入跨境业务运行，最后模拟故障恢复。每个带冒号的名称，例如 `service_preparation:`，都是一个业务阶段。阶段内部可以继续使用 `parallel()` 或 `serial()`：`parallel()` 表示这些动作可以同时发生，`serial()` 表示动作之间存在先后依赖。

## 3. 场景角色

| 角色 | 在业务中的身份 | 关注点 |
| --- | --- | --- |
| Gateway 管理层 | 服务商决策者 | 是否能替代 Fortinet 常用运营能力、降低成本、支撑跨境服务交付。 |
| Gateway 网络工程师 | 服务建设人员 | 租户、策略、Overlay、路由、SLA 选路是否可配置、可验证、可解释。 |
| Gateway NOC | 运维团队 | 是否能集中看到客户服务状态，快速定位故障，并形成恢复闭环。 |
| 客户 IT 负责人 | 企业客户侧 IT | 分支是否稳定接入，跨境业务是否可用，故障是否有说明。 |
| 分支 CPE | 客户分支网关设备 | 是否能低接触注册、建隧道、发布路由、完成故障切换。 |
| 分支业务用户 | 远程办公或分支业务人员 | 跨境应用访问是否成功、稳定、延迟可接受。 |
| 运营商/云侧资源 | Underlay 供应方 | 承载跨境链路质量，可能出现链路劣化并触发切换。 |

对应 OSC 片段：

```osc
gateway_management: msp_decision_maker
gateway_engineer: sdwan_network_engineer
gateway_noc: noc_operator
customer_it: enterprise_it_lead
branch_cpe: sdwan_branch_cpe
branch_user: remote_business_user
carrier_cloud: underlay_provider
```

代码解读：

冒号左侧是场景里使用的角色实例名，右侧是角色类型。比如 `gateway_engineer` 是具体参与者，类型是 `sdwan_network_engineer`；`branch_cpe` 是分支设备，类型是 `sdwan_branch_cpe`。后续动作都采用 `角色.动作()` 的形式，例如 `branch_cpe.register_to_gateway()`，表示由这个角色执行某个原子动作。

## 4. 业务流程

### 4.1 服务准备

Gateway 网络工程师先完成两个准备动作：

| 动作 | 产品含义 | 成功标准 |
| --- | --- | --- |
| 创建客户租户 | 为企业客户建立独立服务空间。 | 租户状态为已创建，客户隔离检查通过。 |
| 配置 Overlay 策略 | 定义跨境业务流量如何选择路径。 | 策略处于启用状态，路径选择逻辑对运维可见。 |

这个阶段是并行执行的，含义是租户准备和策略配置可以同时推进，不必等待其中一个完成后再做另一个。

对应 OSC 片段：

```osc
service_preparation:
    parallel():
        gateway_engineer.create_customer_tenant() with:
            tenant_status(created, at: end)
            tenant_isolation_passed(true, at: end)

        gateway_engineer.configure_overlay_policy() with:
            policy_status(active, at: end)
            policy_path_visible(true, at: end)
```

代码解读：

`service_preparation:` 是服务准备阶段。里面的 `parallel()` 表示创建租户和配置 Overlay 策略可以并行完成。每个 `动作() with:` 后面跟的是验收条件。`tenant_status(created, at: end)` 的意思是动作结束时，租户状态必须是 `created`；`tenant_isolation_passed(true, at: end)` 表示租户隔离检查必须通过。

### 4.2 分支开局

分支 CPE 按顺序完成上线：

| 动作 | 产品含义 | 成功标准 |
| --- | --- | --- |
| 注册到 Gateway | 分支设备连接到服务商平台。 | 注册成功，NAT 穿越成功，不要求公网 IP，开局时间 5 到 30 分钟。 |
| 建立 Overlay 隧道 | 分支和服务商网络之间建立加密连接。 | 隧道建立成功，建立耗时 300 到 1500 毫秒，加密开启。 |
| 发布分支路由 | 分支网络被纳入 Overlay 可达范围。 | 路由导入成功，收敛耗时 500 到 2000 毫秒，没有路由泄漏。 |

这个阶段强调“低接触开局”：客户分支现场不需要复杂 IT 操作，也不要求具备公网 IP。

对应 OSC 片段：

```osc
branch_onboarding:
    serial():
        branch_cpe.register_to_gateway() with:
            branch_registration_status(success, at: end)
            nat_traversal_status(success, at: end)
            public_ip_required(false, at: end)
            onboarding_minutes([5..30], at: end)

        branch_cpe.establish_overlay_tunnel() with:
            tunnel_status(established, at: end)
            tunnel_setup_latency_ms([300..1500], at: end)
            overlay_encryption_enabled(true, at: end)

        branch_cpe.advertise_branch_routes() with:
            route_import_status(success, at: end)
            route_convergence_ms([500..2000], at: end)
            route_leak_detected(false, at: end)
```

代码解读：

`branch_onboarding:` 使用 `serial()`，表示分支开局必须按顺序完成：先注册，再建隧道，再发布路由。`[5..30]`、`[300..1500]`、`[500..2000]` 是区间约束，表示指标必须落在这个范围内。`public_ip_required(false, at: end)` 是很关键的产品假设：分支上线不能依赖公网 IP。

### 4.3 跨境业务运行

业务运行阶段同时验证三件事：

| 动作 | 产品含义 | 成功标准 |
| --- | --- | --- |
| SLA 路径选择 | 系统根据链路质量和策略选择跨境路径。 | 路径选择正确率 95% 到 100%，延迟 60 到 180 毫秒，抖动 2 到 25 毫秒，丢包 0% 到 2%。 |
| 访问跨境应用 | 分支用户访问海外或跨境业务系统。 | 访问成功，交易延迟 80 到 300 毫秒，业务可用性 99% 到 100%，吞吐 20 到 120 Mbps。 |
| NOC 监控客户服务 | 运维中心观察客户服务状态。 | 拓扑可见，隧道可见，告警健康，日志关联完整，平均发现时间 10 到 60 秒。 |

产品上，这一段证明的不只是“网络通了”，而是业务体验、路径决策和运维可视化同时成立。

对应 OSC 片段：

```osc
cross_border_operation:
    parallel():
        branch_cpe.select_sla_path() with:
            path_selection_status(correct, at: end)
            path_correctness_percent([95..100], at: end)
            latency_ms([60..180], at: end)
            jitter_ms([2..25], at: end)
            packet_loss_percent([0..2], at: end)

        branch_user.access_cross_border_app() with:
            app_access_status(success, at: end)
            transaction_latency_ms([80..300], at: end)
            business_availability_percent([99..100], at: end)
            throughput_mbps([20..120], at: end)

        gateway_noc.monitor_customer_service() with:
            topology_visible(true, at: end)
            tunnel_visible(true, at: end)
            alert_status(healthy, at: end)
            log_correlation_status(complete, at: end)
            mttd_seconds([10..60], at: end)
```

代码解读：

`cross_border_operation:` 使用 `parallel()`，表示路径选择、用户访问和 NOC 监控是在同一个业务运行窗口内同时成立的。这里不是先选路、再访问、再监控的单线流程，而是要求产品在真实运行状态下同时满足三类结果：链路质量合格、业务访问成功、运维视图完整。`at: end` 表示这些指标在动作结束时进行验收。

### 4.4 故障恢复

故障恢复阶段模拟主链路质量下降后的闭环：

| 动作 | 产品含义 | 成功标准 |
| --- | --- | --- |
| 主链路劣化 | Underlay 出现 SLA 问题。 | 主链路状态为劣化，探针检测到 SLA 违规，告警被触发。 |
| Overlay 路径切换 | 分支流量切换到健康路径。 | 切换成功，切换时间 500 到 3000 毫秒，丢包 0% 到 3%。 |
| NOC 关闭事件 | 运维完成故障处理和解释。 | 事件关闭，平均修复时间 5 到 30 分钟，生成服务报告，根因可见。 |

这个阶段对应产品中的高可用和可解释运维能力。对 Gateway 来说，客户不仅需要服务恢复，还需要知道为什么出问题、如何恢复、是否影响业务。

对应 OSC 片段：

```osc
failure_recovery:
    serial():
        carrier_cloud.degrade_primary_link() with:
            primary_link_status(degraded, at: end)
            sla_probe_status(violation_detected, at: end)
            alert_status(triggered, at: end)

        branch_cpe.failover_overlay_path() with:
            failover_status(success, at: end)
            failover_time_ms([500..3000], at: end)
            packet_loss_percent([0..3], at: end)

        gateway_noc.close_incident() with:
            incident_closed(true, at: end)
            mttr_minutes([5..30], at: end)
            service_report_generated(true, at: end)
            root_cause_visible(true, at: end)
```

代码解读：

`failure_recovery:` 使用 `serial()`，因为故障恢复存在明确因果顺序：先发生 Underlay 劣化，再执行 Overlay 切换，最后由 NOC 关闭事件。`carrier_cloud.degrade_primary_link()` 表示外部承载链路变差，不是产品主动制造业务失败；后面的 `failover_overlay_path()` 和 `close_incident()` 才是产品需要证明的恢复和解释能力。

## 5. 核心验收指标

| 指标 | 验收范围 | 产品意义 |
| --- | --- | --- |
| `tenant_isolation_passed` | true | 多租户隔离可靠，适合服务商运营多个客户。 |
| `public_ip_required` | false | 分支不需要公网 IP，降低开局门槛。 |
| `onboarding_minutes` | 5 到 30 分钟 | 分支上线效率可控。 |
| `tunnel_setup_latency_ms` | 300 到 1500 毫秒 | Overlay 隧道建立速度可接受。 |
| `route_convergence_ms` | 500 到 2000 毫秒 | 路由变化能较快生效。 |
| `path_correctness_percent` | 95% 到 100% | SLA/应用路径选择足够准确。 |
| `latency_ms` | 60 到 180 毫秒 | 跨境访问时延在可接受范围内。 |
| `packet_loss_percent` | 正常 0% 到 2%，故障切换 0% 到 3% | 正常运行和切换期间都要控制丢包。 |
| `business_availability_percent` | 99% 到 100% | 业务可用性达到服务承诺。 |
| `mttd_seconds` | 10 到 60 秒 | NOC 能快速发现故障。 |
| `failover_time_ms` | 500 到 3000 毫秒 | 故障切换速度可接受。 |
| `mttr_minutes` | 5 到 30 分钟 | 故障恢复和关闭效率可控。 |
| `root_cause_visible` | true | 故障原因可以被运维和客户理解。 |

对应 OSC 写法：

```osc
metric_name(expected_value, at: end)
metric_name([min..max], at: end)
metric_name(true, at: end)
metric_name(false, at: end)
```

代码解读：

每一行约束都由三部分组成：指标名、期望值、验收锚点。`tenant_status(created, at: end)` 表示动作结束时指标必须等于 `created`；`onboarding_minutes([5..30], at: end)` 表示动作结束时指标必须在 5 到 30 之间；`root_cause_visible(true, at: end)` 表示最终报告必须能看到根因。这里的 `at: end` 很重要，它说明这些验收不是动作开始前的前置条件，而是动作完成后的结果检查。

## 6. 覆盖目标

`.osc` 文件最后的 `cover` 部分定义了产品和测试需要长期采样关注的指标：

| 覆盖目标 | 采样对象 | 最少样本 | 说明 |
| --- | --- | --- | --- |
| 跨境业务可用性 | `business_availability_percent` | 5 | 验证跨境业务访问是否稳定。 |
| 低接触分支开局 | `onboarding_minutes` | 5 | 验证分支上线时间是否稳定可控。 |
| SLA 选路有效性 | `path_correctness_percent` | 10 | 验证路径选择是否长期准确。 |
| NOC 运维效率 | `mttr_minutes` | 5 | 验证故障恢复效率。 |
| 恢复可解释性 | `root_cause_visible` | 3 | 验证故障处理是否能输出清楚原因。 |

这些不是单次通过即可结束的指标，而是需要在多次运行中积累样本，用于证明能力稳定。

对应 OSC 片段：

```osc
cover cross_border_business_availability:
    target: business_availability_percent
    sampling: event
    min_samples: 5

cover branch_low_touch_onboarding:
    target: onboarding_minutes
    sampling: event
    min_samples: 5

cover sla_path_selection_effectiveness:
    target: path_correctness_percent
    sampling: event
    min_samples: 10

cover noc_operations_efficiency:
    target: mttr_minutes
    sampling: event
    min_samples: 5

cover recovery_explainability:
    target: root_cause_visible
    sampling: event
    min_samples: 3
```

代码解读：

`cover` 不是一次性的通过/失败条件，而是覆盖率目标。`target` 表示要长期采样观察的指标，`sampling: event` 表示在事件或动作结果产生时采样，`min_samples` 表示至少需要积累多少个样本。比如 `sla_path_selection_effectiveness` 要对 `path_correctness_percent` 至少采样 10 次，才足以说明 SLA 选路能力不是偶然通过。

## 7. 产品视角总结

这个场景可以被理解为一条完整的 SD-WAN 服务商交付链路：

1. 先为客户准备独立服务空间和路径策略。
2. 再让分支设备低接触上线，不依赖公网 IP。
3. 然后建立加密 Overlay，导入分支路由。
4. 在业务运行期间，根据 SLA 和策略选择跨境路径。
5. NOC 持续观察客户服务状态。
6. 当 Underlay 劣化时，自动触发告警和路径切换。
7. 最后由 NOC 关闭事件，并生成可解释的服务报告。

对产品规划来说，这个 `.osc` 场景不是单个功能点测试，而是一个“佳慧 Gateway 作为跨境 MSP 运营 SD-WAN 服务”的端到端验收样板。它覆盖了租户、开局、Overlay、路由、SLA 选路、业务体验、监控告警、故障切换和报告解释。

对应 OSC 总体结构：

```osc
scenario gateway_sdwan_cross_border_msp:
    <角色声明>

    do serial():
        service_preparation:
            parallel():
                <租户与策略准备>

        branch_onboarding:
            serial():
                <注册、建隧道、发布路由>

        cross_border_operation:
            parallel():
                <选路、访问、监控>

        failure_recovery:
            serial():
                <链路劣化、路径切换、事件关闭>

    cover <长期采样目标>:
        target: <关键指标>
        sampling: event
        min_samples: <样本数>
```

代码解读：

从 DSL 结构看，这个场景由三层组成：第一层是角色，说明谁参与；第二层是 `do serial()` 下的业务阶段，说明服务如何从准备走到恢复闭环；第三层是 `cover`，说明哪些指标需要长期积累样本。产品评审时可以按这三层检查：角色是否完整、流程是否覆盖真实交付、指标是否能支撑对客户承诺。
