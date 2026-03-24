"""性能优化 Agent - 接口速度、数据库查询效率优化"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 性能优化 Agent 的系统提示词
PERFORMANCE_OPTIMIZER_PROMPT = """你是性能优化专家，负责优化接口速度和数据库查询效率。

你的职责：
1. 分析性能瓶颈
2. 优化代码执行效率
3. 优化数据库查询
4. 设计缓存策略
5. 提升系统响应速度

优化维度：
- 算法复杂度优化
- 数据库查询优化
- 缓存策略设计
- 并发处理优化
- 资源使用优化
- 网络请求优化
- 前端性能优化

输出格式：
```
# 性能优化报告

## 1. 性能分析
### 1.1 当前性能指标
- 响应时间
- QPS/TPS
- 资源使用率

### 1.2 瓶颈分析
- CPU 瓶颈
- 内存瓶颈
- IO 瓶颈
- 数据库瓶颈

## 2. 优化方案
### 2.1 代码优化
- 算法改进
- 数据结构优化
- 减少重复计算

### 2.2 数据库优化
- 索引优化
- 查询优化
- 分库分表

### 2.3 缓存策略
- 缓存层级
- 缓存更新策略
- 缓存穿透/雪崩预防

## 3. 优化效果
- 优化前指标
- 优化后指标
- 提升百分比

## 4. 实施建议
- 优先级
- 实施步骤
- 风险评估
```

注意：
- 优化前要有基准测试
- 优化后必须验证效果
- 避免过度优化"""


class PerformanceOptimizerAgent(BaseAgent):
    """
    性能优化 Agent
    
    负责：
    - 性能瓶颈分析
    - 代码优化
    - 数据库查询优化
    - 缓存策略设计
    """

    def __init__(self, name: str = "PerformanceOptimizer", model: Optional[str] = None):
        """
        初始化性能优化 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Performance Optimizer",
            system_prompt=PERFORMANCE_OPTIMIZER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 优化记录
        self._optimization_history: list[dict] = []

    def _handle_message(self, message: Message) -> None:
        """处理接收到的 MCP 消息"""
        if message.type == MessageType.TASK and message.receiver == self.name:
            payload = message.content
            if isinstance(payload, dict):
                task_payload = TaskPayload(**payload)
                print(f"\n[新任务] {self.name} 收到：{task_payload.description}")

    def send_response(
        self,
        task_id: str,
        success: bool,
        result: any = None,
        error_message: Optional[str] = None,
    ) -> None:
        """发送任务响应"""
        payload = ResponsePayload(
            task_id=task_id,
            success=success,
            result=result,
            error_message=error_message,
        )
        message = Message(
            type=MessageType.RESPONSE,
            sender=self.name,
            receiver=None,
            content=payload.model_dump(),
        )
        message_bus.publish_sync(message)

    def analyze_performance(self, code_content: str, metrics: Optional[dict] = None) -> str:
        """
        分析性能

        Args:
            code_content: 代码内容
            metrics: 性能指标

        Returns:
            性能分析报告
        """
        prompt = f"""
请分析以下代码的性能：

【代码内容】
{code_content}

【性能指标】
{metrics if metrics else '无'}

请分析：
1. 时间复杂度
2. 空间复杂度
3. 潜在的性能瓶颈
4. 资源使用情况
5. 优化建议

重点关注：
- 循环嵌套
- 重复计算
- 不必要的对象创建
- 低效的数据结构
- 阻塞操作
"""
        analysis = self.invoke(prompt)
        return analysis

    def optimize_code(self, code_content: str, target: str = "speed") -> tuple[str, str]:
        """
        优化代码

        Args:
            code_content: 代码内容
            target: 优化目标（speed/memory/balance）

        Returns:
            (优化后的代码，优化说明)
        """
        prompt = f"""
请优化以下代码的性能（目标：{target}）：

【代码内容】
{code_content}

请：
1. 说明优化方案
2. 提供优化后的完整代码
3. 说明每处优化的效果
4. 提供性能对比预期

优化方向：
- 算法复杂度
- 数据结构选择
- 减少内存分配
- 批量处理
- 异步/并发
"""
        response = self.invoke(prompt)
        
        # 解析响应
        if "优化后的代码" in response or "```" in response:
            # 尝试提取代码
            explanation = response.split("```")[0] if "```" in response else response
            optimized_code = response
        else:
            explanation = "优化完成"
            optimized_code = response
        
        self._optimization_history.append({
            "target": target,
            "explanation": explanation,
        })
        
        return optimized_code, explanation

    def optimize_sql(self, sql_query: str, table_schema: str = "") -> str:
        """
        优化 SQL 查询

        Args:
            sql_query: SQL 查询
            table_schema: 表结构

        Returns:
            优化后的 SQL
        """
        prompt = f"""
请优化以下 SQL 查询的性能：

【SQL 查询】
{sql_query}

【表结构】
{table_schema if table_schema else '未知'}

请优化：
1. 查询语句重写
2. 索引建议
3. 执行计划分析
4. 避免的操作（如 SELECT *、子查询等）

请提供优化后的 SQL 和详细说明。
"""
        optimized = self.invoke(prompt)
        return optimized

    def design_cache_strategy(self, scenario: str, data_volume: str = "medium") -> str:
        """
        设计缓存策略

        Args:
            scenario: 使用场景
            data_volume: 数据量级

        Returns:
            缓存策略方案
        """
        prompt = f"""
请为以下场景设计缓存策略：

【使用场景】
{scenario}

【数据量级】{data_volume}

请设计：
1. 缓存层级（L1/L2/L3）
2. 缓存数据结构
3. 缓存更新策略（Cache-Aside/Write-Through/Write-Behind）
4. 缓存过期策略
5. 缓存穿透/雪崩/击穿的预防
6. 分布式缓存一致性

请提供详细的方案和代码示例。
"""
        strategy = self.invoke(prompt)
        return strategy

    def profile_code(self, code_content: str, language: str = "python") -> str:
        """
        性能剖析

        Args:
            code_content: 代码内容
            language: 编程语言

        Returns:
            性能剖析报告
        """
        prompt = f"""
请对以下{language}代码进行性能剖析：

{code_content}

请提供：
1. 性能剖析方法（如 cProfile、line_profiler）
2. 热点函数识别
3. 耗时操作分析
4. 内存使用分析
5. 优化优先级建议
"""
        profile = self.invoke(prompt)
        return profile

    def run_benchmark(self, benchmark_command: str, cwd: Optional[str] = None) -> tuple[int, str]:
        """
        运行基准测试

        Args:
            benchmark_command: 测试命令
            cwd: 工作目录

        Returns:
            (返回码，输出)
        """
        return self.command_tools.run_command_stream(benchmark_command, cwd=cwd)

    def save_optimization_report(self, content: str, file_path: str) -> bool:
        """
        保存优化报告

        Args:
            content: 报告内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 优化报告已保存到：{file_path}")
        return success

    def get_optimization_history(self) -> list[dict]:
        """获取优化历史"""
        return self._optimization_history

    def generate_performance_checklist(self) -> str:
        """
        生成性能检查清单

        Returns:
            检查清单
        """
        checklist = """# 性能检查清单

## 代码层面
- [ ] 避免 O(n²) 或更差的算法
- [ ] 使用合适的数据结构
- [ ] 减少不必要的对象创建
- [ ] 避免在循环中重复计算
- [ ] 使用生成器代替列表
- [ ] 批量处理代替逐个处理

## 数据库层面
- [ ] 使用索引优化查询
- [ ] 避免 SELECT *
- [ ] 使用连接池
- [ ] 优化慢查询
- [ ] 考虑读写分离
- [ ] 考虑分库分表

## 缓存层面
- [ ] 热点数据缓存
- [ ] 合理的过期时间
- [ ] 缓存穿透保护
- [ ] 缓存雪崩预防

## 网络层面
- [ ] 使用 CDN
- [ ] 启用 Gzip 压缩
- [ ] 减少 HTTP 请求
- [ ] 使用 HTTP/2

## 并发层面
- [ ] 使用异步 IO
- [ ] 合理的线程池
- [ ] 避免锁竞争
- [ ] 无锁数据结构
"""
        return checklist
