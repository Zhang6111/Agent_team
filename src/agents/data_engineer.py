"""数据工程师 Agent - 数据库设计、数据校验、存储规则"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 数据工程师 Agent 的系统提示词
DATA_ENGINEER_PROMPT = """你是数据工程师，负责数据库设计、数据校验和存储规则。

你的职责：
1. 根据需求设计数据库表结构
2. 定义数据模型和关系
3. 编写数据校验规则
4. 设计数据存储和索引策略
5. 优化数据库查询性能

输出格式：
```
# 数据库设计文档

## 1. 数据库选型
- 数据库类型（MySQL/PostgreSQL/MongoDB）
- 版本要求
- 配置建议

## 2. ER 图设计
- 实体列表
- 关系说明
- 基数说明

## 3. 表结构设计
### 3.1 表名
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id   | INT  | PK   | 主键 |

### 3.2 索引设计
- 主键索引
- 唯一索引
- 普通索引

## 4. 数据校验规则
- 字段级校验
- 业务规则校验

## 5. SQL 示例
- 创建表语句
- 常用查询语句

## 6. 数据迁移方案
- 初始数据
- 迁移脚本
```

注意：
- 设计要符合范式
- 考虑查询性能
- 预留扩展空间"""


class DataEngineerAgent(BaseAgent):
    """
    数据工程师 Agent
    
    负责：
    - 数据库表设计
    - 数据模型定义
    - 数据校验规则
    """

    def __init__(self, name: str = "DataEngineer", model: Optional[str] = None):
        """
        初始化数据工程师 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Data Engineer",
            system_prompt=DATA_ENGINEER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)

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

    def design_database(self, prd_content: str, db_type: str = "mysql") -> str:
        """
        设计数据库

        Args:
            prd_content: PRD 文档内容
            db_type: 数据库类型

        Returns:
            数据库设计文档
        """
        prompt = f"""
请根据以下 PRD 设计数据库：

【PRD 内容】
{prd_content}

【数据库类型】{db_type}

请输出完整的数据库设计文档，包括：
1. 表结构设计（字段、类型、约束）
2. 索引设计
3. 外键关系
4. 创建表 SQL 语句
"""
        design = self.invoke(prompt)
        return design

    def generate_create_table_sql(
        self, table_name: str, columns: list[dict], indexes: Optional[list] = None
    ) -> str:
        """
        生成创建表 SQL

        Args:
            table_name: 表名
            columns: 列定义列表
            indexes: 索引列表

        Returns:
            CREATE TABLE SQL
        """
        sql = f"CREATE TABLE `{table_name}` (\n"
        col_defs = []
        for col in columns:
            col_def = f"  `{col['name']}` {col['type']}"
            if col.get('primary_key'):
                col_def += " PRIMARY KEY"
            if col.get('auto_increment'):
                col_def += " AUTO_INCREMENT"
            if col.get('not_null'):
                col_def += " NOT NULL"
            if col.get('default') is not None:
                col_def += f" DEFAULT {col['default']}"
            if col.get('comment'):
                col_def += f" COMMENT '{col['comment']}'"
            col_defs.append(col_def)
        
        sql += ",\n".join(col_defs)
        
        if indexes:
            for idx in indexes:
                sql += f",\n  KEY `{idx['name']}` (`{idx['column']}`)"
        
        sql += "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='';"
        return sql

    def generate_model_code(
        self, table_schema: str, framework: str = "sqlalchemy"
    ) -> str:
        """
        生成 ORM 模型代码

        Args:
            table_schema: 表结构定义
            framework: ORM 框架（sqlalchemy/django/peewee）

        Returns:
            ORM 模型代码
        """
        prompt = f"""
请根据以下表结构生成{framework}ORM 模型代码：

【表结构】
{table_schema}

要求：
1. 包含所有字段和类型
2. 包含关系定义
3. 包含常用方法
4. 添加必要的注释
"""
        code = self.invoke(prompt)
        return code

    def generate_validation_rules(self, fields: list[dict]) -> str:
        """
        生成数据校验规则

        Args:
            fields: 字段定义列表

        Returns:
            校验规则代码
        """
        rules = []
        for field in fields:
            rule = f"# {field['name']} 校验规则\n"
            if field.get('required'):
                rule += f"- 必填字段\n"
            if field.get('max_length'):
                rule += f"- 最大长度：{field['max_length']}\n"
            if field.get('pattern'):
                rule += f"- 正则匹配：{field['pattern']}\n"
            if field.get('min_value') is not None:
                rule += f"- 最小值：{field['min_value']}\n"
            if field.get('max_value') is not None:
                rule += f"- 最大值：{field['max_value']}\n"
            rules.append(rule)
        return "\n".join(rules)

    def save_sql(self, content: str, file_path: str) -> bool:
        """
        保存 SQL 文件

        Args:
            content: SQL 内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ SQL 文件已保存到：{file_path}")
        return success

    def generate_migration_script(
        self, from_schema: str, to_schema: str
    ) -> str:
        """
        生成数据库迁移脚本

        Args:
            from_schema: 原 schema
            to_schema: 新 schema

        Returns:
            迁移脚本
        """
        prompt = f"""
请生成数据库迁移脚本。

【原 schema】
{from_schema}

【新 schema】
{to_schema}

请生成：
1. 升级脚本 (upgrade)
2. 降级脚本 (downgrade)
3. 数据迁移逻辑（如需要）
"""
        migration = self.invoke(prompt)
        return migration
