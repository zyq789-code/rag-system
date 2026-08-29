## 分布式系统的 CAP 与 BASE 理论

### CAP 定理
分布式系统最多只能同时满足两个：
- **C（Consistency 一致性）**：所有节点数据一致
- **A（Availability 可用性）**：任何请求都能得到响应
- **P（Partition tolerance 分区容错性）**：网络分区时仍能工作

> 网络分区（P）在分布式环境下不可避免，所以实际是 **CP 或 AP 二选一**。
- CP：保证一致性，分区时牺牲部分可用性（如 ZooKeeper、etcd）
- AP：保证可用性，分区时数据可能暂时不一致（如 Eureka、多数缓存）

### BASE 理论（AP 的落地）
- **Basically Available**：基本可用（降级、限流）
- **Soft state**：软状态，允许中间不一致
- **Eventually consistent**：最终一致（通过异步补偿、消息队列实现）

### 在工程中的体现
- 注册中心：Eureka 偏 AP，ZooKeeper 偏 CP
- 分布式锁：强一致（CP），用 etcd/zk 或 RedLock
- 订单/库存：通常选择"最终一致"，用 MQ + 状态机补偿

> 面试延伸：能结合自己项目说清楚"哪里选了 CP、哪里选了 AP、为什么"是很大的加分项。
