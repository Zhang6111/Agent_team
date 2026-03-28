"""产品 Agent - 智能产品助手（增强版）"""
from typing import Optional, List, Dict
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


PRODUCT_MANAGER_PROMPT = """你是资深产品经理，负责需求分析、产品规划和决策支持。

你的职责：
1. 需求调研与分析
   - 理解用户需求，挖掘隐性需求
   - 生成用户故事和用户画像
   - 竞品分析和市场调研

2. 产品文档输出
   - 输出标准化 PRD 文档
   - 生成流程图（Mermaid 格式）
   - 生成页面原型描述

3. 决策支持
   - 功能优先级排序
   - 工作量估算
   - 风险评估

4. 变更管理
   - 版本对比
   - 变更影响分析
   - 变更日志生成

工作流程：
1. 理解需求背景和目标
2. 分析功能需求和非功能需求
3. 生成用户故事和验收标准
4. 输出 PRD 文档和流程图
5. 进行优先级排序和工作量估算
6. 跟进需求实现和变更管理

可用工具：
- read_file: 读取现有文档
- write_file: 创建/保存文档
- file_exists: 检查文件是否存在
- list_directory: 查看项目结构

输出规范：
- 需求要清晰、可执行
- 优先级要有依据
- 验收标准要可量化
- 流程图使用 Mermaid 格式
- 不预设技术栈，技术选型由架构师决定"""


class ProductManagerAgent(BaseAgent):
    """产品 Agent - 智能产品助手"""

    def __init__(self, name: str = "ProductManager", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Product Manager",
            system_prompt=PRODUCT_MANAGER_PROMPT,
            model=model,
            memory=memory,
        )

        self.file_tools = FileTools()
        message_bus.subscribe(self.name, self._handle_message)
        self._prd_cache: Dict[str, str] = {}

    def _handle_message(self, message: Message) -> None:
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

    # ==================== 基础功能 ====================

    def analyze_requirement(self, requirement: str) -> str:
        """分析需求并生成 PRD 文档"""
        prompt = f"""请分析以下需求并生成完整的 PRD 文档：

【需求描述】
{requirement}

请按照以下结构输出：
1. 项目概述（背景、目标用户、核心价值）
2. 功能需求（功能列表、功能详情、用户故事、验收标准）
3. 非功能需求（性能、安全、兼容性）
4. 其他说明"""
        return self.invoke(prompt)

    def save_prd(self, prd_content: str, file_path: str) -> bool:
        """保存 PRD 文档"""
        success = self.file_tools.write_file(file_path, prd_content)
        if success:
            print(f"✓ PRD 已保存到：{file_path}")
        return success

    def extract_features(self, prd_content: str) -> List[Dict]:
        """从 PRD 中提取功能列表"""
        features = []
        lines = prd_content.split('\n')
        for line in lines:
            if '[P0]' in line or '[P1]' in line or '[P2]' in line:
                features.append({
                    'priority': 'P0' if '[P0]' in line else ('P1' if '[P1]' in line else 'P2'),
                    'description': line.split(']')[-1].strip()
                })
        return features

    # ==================== P0: 需求调研 ====================

    def generate_user_stories(self, requirement: str) -> str:
        """生成用户故事"""
        prompt = f"""根据以下需求，生成用户故事列表：

【需求描述】
{requirement}

请按照以下格式输出用户故事：

## 用户故事列表

### 角色1：[用户角色名称]

**故事1**
- 作为【用户角色】
- 我希望【功能描述】
- 以便【价值说明】
- 验收标准：
  - Given: 前置条件
  - When: 触发动作
  - Then: 预期结果

请生成 5-10 个用户故事，覆盖主要功能场景。"""
        return self.invoke(prompt)

    def generate_user_personas(self, product_description: str) -> str:
        """生成用户画像"""
        prompt = f"""根据以下产品描述，生成用户画像：

【产品描述】
{product_description}

请按照以下格式输出用户画像：

## 用户画像

### 画像1：[用户名称]
- 基本信息：年龄、职业、收入
- 行为特征：使用习惯、偏好
- 痛点需求：主要问题和期望
- 使用场景：典型使用情况
- 目标：使用产品想达成的目的

请生成 3-5 个典型用户画像。"""
        return self.invoke(prompt)

    # ==================== P0: 文档增强 ====================

    def generate_flowchart(self, process: str, flow_type: str = "flowchart") -> str:
        """生成 Mermaid 流程图"""
        prompt = f"""将以下流程描述转换为 Mermaid 流程图代码：

【流程描述】
{process}

【图表类型】
{flow_type} (flowchart/sequence/swimlane)

请输出可直接使用的 Mermaid 代码，格式如下：

```mermaid
flowchart TD
    A[开始] --> B[步骤1]
    B --> C{判断}
    C -->|是| D[步骤2]
    C -->|否| E[步骤3]
    D --> F[结束]
    E --> F
```

注意：
- 使用清晰的节点命名
- 包含必要的判断分支
- 确保流程完整"""
        return self.invoke(prompt)

    def generate_sequence_diagram(self, interaction: str) -> str:
        """生成时序图"""
        prompt = f"""将以下交互描述转换为 Mermaid 时序图代码：

【交互描述】
{interaction}

请输出 Mermaid 时序图代码：

```mermaid
sequenceDiagram
    participant A as 参与者A
    participant B as 参与者B
    A->>B: 消息1
    B-->>A: 响应1
```
"""
        return self.invoke(prompt)

    def generate_wireframe_description(self, page_name: str, features: List[str]) -> str:
        """生成页面原型描述"""
        features_text = "\n".join([f"- {f}" for f in features])
        prompt = f"""为以下页面生成线框图描述：

【页面名称】
{page_name}

【功能点】
{features_text}

请按照以下格式输出：

## 页面布局描述

### 整体布局
- 布局类型：顶部导航/侧边栏/全屏等
- 主要区域划分

### 组件详情
1. **组件名称**
   - 位置：页面位置
   - 尺寸：大致比例
   - 内容：显示内容
   - 交互：点击/滑动等

### ASCII 线框图
```
+------------------+
|     Header       |
+------------------+
| 侧边栏 |  主内容  |
|        |         |
+------------------+
|     Footer       |
+------------------+
```

### 交互说明
- 交互1：触发条件 -> 响应动作
"""
        return self.invoke(prompt)

    # ==================== P1: 决策支持 ====================

    def prioritize_features(self, features: List[Dict]) -> str:
        """功能优先级矩阵"""
        features_text = "\n".join([f"- {f.get('name', f.get('description', str(f)))}" for f in features])
        prompt = f"""对以下功能进行优先级排序：

【功能列表】
{features_text}

请按照以下维度评估并排序：

## 功能优先级矩阵

| 功能名称 | 业务价值(1-5) | 技术成本(1-5) | 用户需求(1-5) | 紧迫性(1-5) | 总分 | 优先级 |
|---------|-------------|-------------|-------------|------------|-----|-------|

评分说明：
- 业务价值：对公司业务目标的贡献程度
- 技术成本：开发难度和资源消耗（分数越低成本越高）
- 用户需求：用户需求强度
- 紧迫性：市场竞争和时间敏感性

总分 = 业务价值 × 0.3 + 用户需求 × 0.3 + 紧迫性 × 0.2 + (6-技术成本) × 0.2

优先级划分：
- P0：总分 >= 4，必须实现
- P1：总分 3-4，应该实现
- P2：总分 2-3，可以实现
- P3：总分 < 2，暂缓实现

请给出评估依据和建议。"""
        return self.invoke(prompt)

    def estimate_effort(self, feature: str) -> str:
        """工作量估算"""
        prompt = f"""估算以下功能的工作量：

【功能描述】
{feature}

请按照以下格式输出工作量估算：

## 工作量估算

### 功能拆解
| 子任务 | 前端(人天) | 后端(人天) | 测试(人天) |
|--------|-----------|-----------|-----------|

### 工作量汇总
- 前端开发：X 人天
- 后端开发：X 人天
- 测试工作：X 人天
- 设计工作：X 人天
- 总工作量：X 人天

### 风险点
1. 风险描述
   - 可能性：高/中/低
   - 影响：高/中/低
   - 应对措施

### 依赖项
- 外部依赖
- 技术依赖
- 资源依赖

### 建议
- 开发顺序建议
- 资源配置建议"""
        return self.invoke(prompt)

    def assess_risks(self, requirements: str) -> str:
        """风险评估"""
        prompt = f"""评估以下需求的风险：

【需求描述】
{requirements}

请按照以下格式输出风险评估：

## 风险评估

### 风险列表
| 编号 | 风险类型 | 风险描述 | 可能性 | 影响 | 风险等级 | 应对措施 |
|------|---------|---------|-------|------|---------|---------|

风险类型：
- 技术风险：技术难点、新技术应用
- 业务风险：需求变更、市场变化
- 资源风险：人员、时间、预算
- 外部风险：第三方依赖、政策法规

风险等级：
- 高：可能性×影响 >= 9
- 中：可能性×影响 4-8
- 低：可能性×影响 < 4

### 风险应对计划
1. 高风险项应对方案
2. 中风险项监控措施
3. 低风险项记录跟踪

### 风险监控建议
- 监控指标
- 预警机制
- 应急预案"""
        return self.invoke(prompt)

    # ==================== P2: 竞品分析 ====================

    def analyze_competitors(self, product_type: str) -> str:
        """竞品分析"""
        prompt = f"""分析 {product_type} 类型的产品竞品：

## 竞品分析报告

### 1. 市场概况
- 市场规模
- 发展趋势
- 用户群体

### 2. 主要竞品
| 竞品名称 | 公司 | 市场份额 | 核心优势 | 主要劣势 |
|---------|------|---------|---------|---------|

### 3. 功能对比
| 功能点 | 我方产品 | 竞品A | 竞品B | 竞品C |
|--------|---------|-------|-------|-------|

### 4. 差异化分析
- 竞品共性问题
- 市场空白点
- 差异化机会

### 5. 建议策略
- 产品定位建议
- 功能优先级建议
- 差异化方向"""
        return self.invoke(prompt)

    # ==================== P2: 变更管理 ====================

    def compare_prd_versions(self, old_prd: str, new_prd: str) -> str:
        """PRD 版本对比"""
        prompt = f"""对比两个 PRD 版本的变化：

【旧版本】
{old_prd}

【新版本】
{new_prd}

请按照以下格式输出对比结果：

## 版本对比报告

### 变更概览
- 新增功能：X 项
- 修改功能：X 项
- 删除功能：X 项

### 详细变更

#### 新增功能
1. 功能名称
   - 描述
   - 影响范围

#### 修改功能
1. 功能名称
   - 变更前
   - 变更后
   - 变更原因

#### 删除功能
1. 功能名称
   - 删除原因
   - 替代方案

### 影响分析
- 对开发进度的影响
- 对已有功能的影响
- 对用户的影响

### 建议
- 需要同步修改的文档
- 需要通知的相关方"""
        return self.invoke(prompt)

    def analyze_change_impact(self, change: str, current_features: List[str]) -> str:
        """变更影响分析"""
        features_text = "\n".join([f"- {f}" for f in current_features])
        prompt = f"""分析以下变更对现有功能的影响：

【变更内容】
{change}

【现有功能】
{features_text}

请按照以下格式输出影响分析：

## 变更影响分析

### 直接影响
| 功能 | 影响程度 | 影响说明 |
|------|---------|---------|

### 间接影响
| 功能 | 影响程度 | 影响说明 |
|------|---------|---------|

### 技术影响
- 需要修改的代码模块
- 需要修改的数据库表
- 需要修改的接口

### 测试影响
- 需要新增的测试用例
- 需要回归测试的范围

### 风险评估
- 变更风险等级
- 风险缓解措施

### 实施建议
- 实施步骤
- 注意事项"""
        return self.invoke(prompt)

    def generate_changelog(self, version: str, changes: List[Dict]) -> str:
        """生成变更日志"""
        changes_text = "\n".join([f"- {c.get('type', '修改')}: {c.get('description', str(c))}" for c in changes])
        prompt = f"""根据以下变更生成变更日志：

【版本号】
{version}

【变更列表】
{changes_text}

请按照以下格式输出变更日志：

## [{version}] - YYYY-MM-DD

### 新增 (Added)
- 新增功能1
- 新增功能2

### 修改 (Changed)
- 修改功能1
- 修改功能2

### 修复 (Fixed)
- 修复问题1
- 修复问题2

### 删除 (Removed)
- 删除功能1

### 弃用 (Deprecated)
- 弃用功能1（将在 X 版本移除）

### 安全 (Security)
- 安全更新1"""
        return self.invoke(prompt)

    # ==================== P3: 用户访谈 ====================

    def generate_interview_questions(self, product_goal: str) -> str:
        """生成用户访谈问题"""
        prompt = f"""为了验证以下产品目标，生成用户访谈问题：

【产品目标】
{product_goal}

请按照以下格式输出访谈问题：

## 用户访谈提纲

### 开场问题（破冰）
1. 请简单介绍一下您自己
2. 您平时如何处理 [相关场景]？

### 痛点探索
1. 您在 [场景] 中遇到的最大困难是什么？
2. 您目前是如何解决这个问题的？
3. 这个解决方案有什么不满意的地方？

### 需求验证
1. 如果有一个产品能 [功能描述]，您会使用吗？
2. 您希望这个产品具备哪些功能？
3. 您愿意为这个产品付费吗？付费意愿是多少？

### 使用场景
1. 您通常在什么情况下会使用这个产品？
2. 您希望产品如何与您现有的工作流程结合？

### 竞品了解
1. 您使用过类似的产品吗？
2. 您对这些产品有什么评价？
3. 您觉得它们缺少什么功能？

### 结束语
1. 您还有什么想说的吗？
2. 如果后续有产品更新，您愿意参与测试吗？"""
        return self.invoke(prompt)

    # ==================== 便捷方法 ====================

    def full_analysis(self, requirement: str) -> Dict[str, str]:
        """完整需求分析（一站式）"""
        result = {}
        
        result['prd'] = self.analyze_requirement(requirement)
        result['user_stories'] = self.generate_user_stories(requirement)
        result['personas'] = self.generate_user_personas(requirement)
        
        features = self.extract_features(result['prd'])
        if features:
            result['priorities'] = self.prioritize_features(features)
        
        return result

    def save_full_analysis(self, requirement: str, output_dir: str) -> Dict[str, bool]:
        """保存完整分析结果"""
        results = {}
        
        analysis = self.full_analysis(requirement)
        
        results['prd'] = self.save_prd(analysis['prd'], f"{output_dir}/PRD.md")
        results['user_stories'] = self.file_tools.write_file(f"{output_dir}/user_stories.md", analysis['user_stories'])
        results['personas'] = self.file_tools.write_file(f"{output_dir}/personas.md", analysis['personas'])
        
        if 'priorities' in analysis:
            results['priorities'] = self.file_tools.write_file(f"{output_dir}/priorities.md", analysis['priorities'])
        
        return results
