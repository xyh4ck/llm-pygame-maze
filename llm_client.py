"""LLM客户端，用于获取下一步移动决策"""

import os
import json
from typing import Optional, Tuple, List
from openai import OpenAI


class LLMClient:
    """LLM客户端类，用于与AI模型交互获取移动决策"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o"):
        """
        初始化LLM客户端

        Args:
            api_key: OpenAI API密钥，如果为None则从环境变量OPENAI_API_KEY读取
            base_url: API基础URL，如果为None则从环境变量OPENAI_BASE_URL读取，如果都未设置则使用OpenAI默认URL
            model: 使用的模型名称，默认为gpt-4o-mini
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("需要提供OpenAI API密钥，可以通过参数传入或设置环境变量OPENAI_API_KEY")

        base_url = base_url or os.getenv("OPENAI_BASE_URL")

        # 构建客户端参数
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)
        self.model = model

    def get_next_move(self, maze_state: str, current_pos: Tuple[int, int], target_pos: Tuple[int, int], move_history: List[Tuple[int, int]], available_directions: List[str], is_looping: bool = False, recent_pattern: str = "") -> Tuple[int, int]:
        """
        获取下一步移动坐标

        Args:
            maze_state: 迷宫状态的文本描述
            current_pos: 当前位置 (x, y)
            target_pos: 目标位置 (x, y)
            move_history: 移动历史，包含之前访问过的所有位置
            available_directions: 可用的移动方向列表，如 ['UP', 'DOWN', 'LEFT', 'RIGHT']
            is_looping: 是否检测到循环模式
            recent_pattern: 最近移动模式的描述

        Returns:
            下一步的坐标 (x, y)
        """
        print("\n" + "="*80)
        print("🤖 LLM 推理开始")
        print("="*80)
        
        # 构建提示词
        prompt = self._build_prompt(maze_state, current_pos, target_pos, move_history, available_directions, is_looping, recent_pattern)
        
        # 打印输入信息
        print(f"\n📍 当前位置: {current_pos}")
        print(f"🎯 目标位置: {target_pos}")
        print(f"📊 已访问位置数量: {len(move_history)}")
        print(f"🔄 可用移动方向: {', '.join(available_directions)}")
        # print(f"📏 到目标的曼哈顿距离: {abs(target_pos[0] - current_pos[0]) + abs(target_pos[1] - current_pos[1])}")
        
        # 计算相邻位置信息
        visited_set = set(move_history)
        x, y = current_pos
        adjacent_info = []
        for dx, dy, direction in [(0, -1, "UP"), (0, 1, "DOWN"), (-1, 0, "LEFT"), (1, 0, "RIGHT")]:
            adj_x, adj_y = x + dx, y + dy
            is_visited = (adj_x, adj_y) in visited_set
            adjacent_info.append((adj_x, adj_y, direction, is_visited))
        
        print(f"\n🔍 相邻位置分析:")
        for adj_x, adj_y, direction, is_visited in adjacent_info:
            status = "✅ 未访问" if not is_visited else "⚠️  已访问"
            print(f"   {direction}: ({adj_x}, {adj_y}) - {status}")
        
        # 打印系统提示词摘要
        system_prompt = """
        你是一个迷宫求解助手。根据给定的迷宫状态和当前位置，推理出下一步应该移动到哪个坐标点。
        重要规则（按优先级排序）：
        1. 坐标必须是可通行的（不是墙）
        2. 坐标必须是当前位置的相邻位置（上下左右，距离为1）
        3. 优先选择未访问过的位置（避免走回头路）
        4. 尽量朝着目标位置前进（计算曼哈顿距离）
        5. 只有在所有未访问的相邻位置都不可行时，才允许回溯到已访问的位置（这是最后的选择）
        6. ⚠️ 绝对禁止重复移动！如果检测到你在来回移动（如左右左右、上下上下），必须立即改变方向，选择不同的路径
        7. 如果提示词中显示"检测到循环"或"重复模式"，你必须选择与最近移动方向不同的方向，优先选择未访问的位置
        请只返回坐标，格式为JSON: {"x": 数字, "y": 数字}
        """
        
        if is_looping:
            print(f"\n⚠️  循环检测警告: 检测到重复移动模式")
            print(f"   {recent_pattern}")
        
        print(f"\n⏳ 正在调用 LLM API...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # 降低随机性，使决策更稳定
                max_tokens=200,
            )

            # 打印API响应信息
            print(f"✅ LLM API 调用成功")
            print(f"📊 响应统计:")
            print(f"   - 使用的模型: {response.model}")
            print(f"   - 完成原因: {response.choices[0].finish_reason}")
            if hasattr(response, 'usage') and response.usage:
                print(f"   - 输入token数: {response.usage.prompt_tokens}")
                print(f"   - 输出token数: {response.usage.completion_tokens}")
                print(f"   - 总token数: {response.usage.total_tokens}")

            # 解析响应
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM返回的响应内容为空")
            content = content.strip()
            print(f"\n📨 原始响应内容:")
            print(f"   {content}")

            # 尝试提取JSON
            print(f"\n🔍 开始解析响应...")
            try:
                # 如果响应包含JSON代码块，提取它
                if "```json" in content:
                    print(f"   检测到 JSON 代码块 (```json)")
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    print(f"   检测到代码块 (```)")
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    print(f"   直接使用响应内容作为JSON")
                    json_str = content

                print(f"   提取的JSON字符串: {json_str}")
                result = json.loads(json_str)
                print(f"   ✅ JSON解析成功: {result}")
                
                next_x = int(result["x"])
                next_y = int(result["y"])
                next_pos = (next_x, next_y)
                
                print(f"\n🎯 解析结果:")
                print(f"   下一步坐标: ({next_x}, {next_y})")
                
                # 验证返回的位置是否是已访问的位置
                if next_pos in move_history:
                    print(f"   ⚠️  注意: LLM选择回溯到已访问位置 ({next_x}, {next_y})")
                    print(f"   已访问位置索引: {move_history.index(next_pos) + 1}/{len(move_history)}")
                else:
                    print(f"   ✅ 下一步移动到未访问位置: ({next_x}, {next_y})")
                
                # 验证是否是相邻位置
                dx = next_x - current_pos[0]
                dy = next_y - current_pos[1]
                distance = abs(dx) + abs(dy)
                if distance == 1:
                    print(f"   ✅ 验证通过: 是相邻位置 (距离=1)")
                else:
                    print(f"   ⚠️  警告: 不是相邻位置 (距离={distance})")
                
                # 计算到目标的新距离
                new_distance = abs(target_pos[0] - next_x) + abs(target_pos[1] - next_y)
                old_distance = abs(target_pos[0] - current_pos[0]) + abs(target_pos[1] - current_pos[1])
                distance_change = new_distance - old_distance
                if distance_change < 0:
                    print(f"   ✅ 距离目标更近了 (减少 {abs(distance_change)} 步)")
                elif distance_change > 0:
                    print(f"   ⚠️  距离目标更远了 (增加 {distance_change} 步)")
                else:
                    print(f"   ➡️  距离目标不变")

                print("="*80)
                print("🤖 LLM 推理完成\n")
                
                return next_pos
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"   ❌ JSON解析失败: {e}")
                print(f"   尝试使用正则表达式提取数字...")
                # 如果JSON解析失败，尝试从文本中提取数字
                import re

                numbers = re.findall(r"\d+", content)
                if len(numbers) >= 2:
                    extracted_pos = (int(numbers[0]), int(numbers[1]))
                    print(f"   ✅ 从文本中提取到坐标: {extracted_pos}")
                    print("="*80)
                    print("🤖 LLM 推理完成\n")
                    return extracted_pos
                else:
                    print(f"   ❌ 无法从响应中提取有效坐标")
                    print("="*80)
                    raise ValueError(f"无法解析LLM响应: {content}")

        except Exception as e:
            print(f"\n❌ LLM API 调用失败:")
            print(f"   错误类型: {type(e).__name__}")
            print(f"   错误信息: {str(e)}")
            print("="*80)
            raise RuntimeError(f"调用LLM时出错: {str(e)}")

    def _build_prompt(self, maze_state: str, current_pos: Tuple[int, int], target_pos: Tuple[int, int], move_history: List[Tuple[int, int]], available_directions: List[str], is_looping: bool = False, recent_pattern: str = "") -> str:
        """构建发送给LLM的提示词"""
        # 将移动历史转换为集合以便快速查找
        visited_set = set(move_history)
        
        # 计算当前位置的相邻位置，并标记哪些已访问
        adjacent_positions = []
        x, y = current_pos
        for dx, dy, direction in [(0, -1, "UP"), (0, 1, "DOWN"), (-1, 0, "LEFT"), (1, 0, "RIGHT")]:
            adj_x, adj_y = x + dx, y + dy
            is_visited = (adj_x, adj_y) in visited_set
            adjacent_positions.append((adj_x, adj_y, direction, is_visited))
        
        # 计算到目标的曼哈顿距离
        manhattan_distance = abs(target_pos[0] - current_pos[0]) + abs(target_pos[1] - current_pos[1])
        
        # 统计未访问的相邻位置数量
        unvisited_count = sum(1 for _, _, _, is_visited in adjacent_positions if not is_visited)
        can_backtrack = unvisited_count == 0
        
        prompt = f"""当前迷宫状态：
                    {maze_state}

                    当前位置: ({current_pos[0]}, {current_pos[1]})
                    目标位置: ({target_pos[0]}, {target_pos[1]})
                    到目标的曼哈顿距离: {manhattan_distance}

                    当前位置的相邻位置（必须从这些位置中选择一个）：
                    """
        for adj_x, adj_y, direction, is_visited in adjacent_positions:
            if is_visited:
                status = "⚠️ 已访问过（不推荐，仅在必要时回溯）"
            else:
                status = "✅ 未访问（优先选择）"
            prompt += f"  - {direction}: ({adj_x}, {adj_y}) {status}\n"

        prompt += f"""
                可用移动方向（可通行的方向）: {', '.join(available_directions)}

                未访问的相邻位置数量: {unvisited_count}
                """
        if can_backtrack:
            prompt += "⚠️ 注意：所有相邻位置都已访问，此时允许回溯到已访问的位置。\n"
        else:
            prompt += "✅ 存在未访问的相邻位置，请优先选择未访问的位置。\n"
        
        # 添加循环检测警告
        if is_looping:
            prompt += f"""
⚠️⚠️⚠️ 重要警告：检测到重复移动模式！⚠️⚠️⚠️
{recent_pattern}
你必须立即改变移动方向，避免继续重复！优先选择未访问的位置，且必须选择与最近移动方向不同的方向！
如果继续重复移动，将无法找到正确路径！
"""
        
        prompt += f"""
已访问过的所有位置（共{len(move_history)}个，尽量避免移动到这些位置）：
"""
        if move_history:
            # 显示所有已访问位置，但分组显示以提高可读性
            if len(move_history) <= 20:
                # 如果位置不多，全部显示
                for i, pos in enumerate(move_history, 1):
                    prompt += f"  {i}. ({pos[0]}, {pos[1]})\n"
            else:
                # 如果位置很多，显示前5个和最后15个
                for i, pos in enumerate(move_history[:5], 1):
                    prompt += f"  {i}. ({pos[0]}, {pos[1]})\n"
                prompt += f"  ... (省略中间 {len(move_history) - 20} 个位置) ...\n"
                for i, pos in enumerate(move_history[-15:], len(move_history) - 14):
                    prompt += f"  {i}. ({pos[0]}, {pos[1]})\n"
        else:
            prompt += "  无\n"

        prompt += f"""
        重要提示：
        1. 你必须从当前位置的相邻位置中选择一个（上下左右，距离为1）
        2. 优先选择未访问的位置（标记为✅的位置），避免走回头路
        3. 在未访问的位置中，优先选择更接近目标的位置（计算曼哈顿距离）
        4. 只有在所有未访问的相邻位置都不可行时，才允许回溯到已访问的位置（标记为⚠️的位置）
        5. 回溯是最后的选择，应该尽量避免
        6. ⚠️ 绝对禁止重复移动！如果最近几步在来回移动（如左右左右），必须立即选择不同的方向
        7. 如果看到"检测到循环"警告，你必须选择与最近移动方向不同的方向，优先选择未访问的位置

        请返回JSON格式: {{"x": 数字, "y": 数字}}
        """
        return prompt
