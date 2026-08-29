## Redis 分布式锁的实现与注意事项

### 基础实现（SETNX + 过期时间）
```lua
SET lock_key client_id NX EX 30
```
- NX：仅当 key 不存在时设置（互斥）
- EX：过期时间（防死锁）
- value 存唯一 client_id（如 UUID），释放时校验是自己持有的锁

### 释放锁必须用 Lua 保证原子
```lua
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
```
> 防止：A 的锁过期后 B 拿到锁，A 却把 B 的锁删了（误删别人的锁）。

### 注意点
- 锁过期时间要大于业务执行时间，否则业务未完成锁就释放（可用看门狗续期）
- 主从切换时锁可能丢失（主节点宕机前未同步），RedLock 或引入 zk/etcd 可缓解
- 生产更常用 Redisson：自带看门狗自动续期、可重入

> 面试延伸：分布式锁的三大坑——死锁（必须过期时间）、误删（必须校验 client_id）、续期（业务超时）。
