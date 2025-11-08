import pygame
import random
import time
from typing import List, Tuple, Set, Optional
from enum import Enum
from llm_client import LLMClient

# 初始化pygame
pygame.init()

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 游戏配置
CELL_SIZE = 30
WALL_THICKNESS = 2


class Direction(Enum):
    """方向枚举"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


class MazeGenerator:
    """迷宫生成器，使用递归回溯算法"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        # 迷宫网格：True表示墙，False表示通道
        self.maze = [[True for _ in range(width)] for _ in range(height)]
        # 访问标记
        self.visited = [[False for _ in range(width)] for _ in range(height)]
    
    def is_valid(self, x: int, y: int) -> bool:
        """检查坐标是否有效"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        """获取未访问的邻居"""
        neighbors = []
        for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny) and not self.visited[ny][nx]:
                neighbors.append((nx, ny))
        return neighbors
    
    def remove_wall(self, x1: int, y1: int, x2: int, y2: int):
        """移除两个单元格之间的墙"""
        # 计算中间位置
        mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        self.maze[my][mx] = False
    
    def generate(self, start_x: int = 1, start_y: int = 1):
        """生成迷宫"""
        # 确保起始位置是奇数（保证边界是墙）
        if start_x % 2 == 0:
            start_x += 1
        if start_y % 2 == 0:
            start_y += 1
        
        # 递归回溯算法
        stack = [(start_x, start_y)]
        self.visited[start_y][start_x] = True
        self.maze[start_y][start_x] = False
        
        while stack:
            x, y = stack[-1]
            neighbors = self.get_neighbors(x, y)
            
            if neighbors:
                # 随机选择一个未访问的邻居
                nx, ny = random.choice(neighbors)
                # 移除墙
                self.remove_wall(x, y, nx, ny)
                # 标记为已访问
                self.visited[ny][nx] = True
                self.maze[ny][nx] = False
                # 添加到栈中
                stack.append((nx, ny))
            else:
                # 回溯
                stack.pop()
        
        # 确保起点和终点是通道
        self.maze[1][1] = False
        self.maze[self.height - 2][self.width - 2] = False
    
    def is_wall(self, x: int, y: int) -> bool:
        """检查指定位置是否是墙"""
        if not self.is_valid(x, y):
            return True
        return self.maze[y][x]


class Player:
    """玩家类"""
    
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
    
    def move(self, dx: int, dy: int, maze: MazeGenerator):
        """移动玩家"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 检查是否可以移动（不是墙）
        if not maze.is_wall(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True
        return False
    
    def reset(self):
        """重置玩家位置"""
        self.x = self.start_x
        self.y = self.start_y


class MazeGame:
    """迷宫游戏主类"""
    
    def __init__(
        self,
        maze_width: int = 21,
        maze_height: int = 21,
        auto_mode: bool = False,
        llm_client: Optional[LLMClient] = None
    ):
        self.maze_width = maze_width
        self.maze_height = maze_height
        
        # 计算窗口大小
        self.screen_width = maze_width * CELL_SIZE
        self.screen_height = maze_height * CELL_SIZE
        
        # 创建窗口
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        caption = "迷宫游戏 - 使用方向键移动，到达绿色终点！"
        if auto_mode:
            caption = "迷宫游戏 - AI自动模式 (按T切换手动模式，按R重新开始)"
        pygame.display.set_caption(caption)
        
        # 生成迷宫
        self.maze_generator = MazeGenerator(maze_width, maze_height)
        self.maze_generator.generate()
        
        # 创建玩家（起点）
        self.player = Player(1, 1)
        
        # 终点位置
        self.end_x = maze_width - 2
        self.end_y = maze_height - 2
        
        # 游戏状态
        self.running = True
        self.won = False
        self.clock = pygame.time.Clock()
        
        # 自动模式相关
        self.auto_mode = auto_mode
        self.llm_client = llm_client
        self.move_history: List[Tuple[int, int]] = [(1, 1)]  # 记录移动历史
        self.last_llm_call_time = 0
        self.llm_call_interval = 1.0  # LLM调用间隔（秒）
        self.step_count = 0  # 步数统计
        
        # 初始化字体（支持中文显示）
        self._init_fonts()
    
    def _init_fonts(self):
        """初始化字体，优先使用支持中文的系统字体"""
        # 优先尝试支持中文的字体（macOS/Linux/Windows）
        # macOS 常用中文字体（按优先级排序）
        chinese_fonts = [
            # 'PingFang SC', 
            # 'PingFang TC', 
            # 'STHeiti', 
            # 'STSong',
            # 'SimHei', 
            '仿宋gb2312',
            # 'Microsoft YaHei', 
            # 'WenQuanYi Micro Hei', 
            # 'Noto Sans CJK SC',
            # 'Arial Unicode MS'
        ]
        font_small: Optional[pygame.font.Font] = None
        font_large: Optional[pygame.font.Font] = None
        
        # 测试文本（包含我们要显示的实际字符）
        test_text = "模式: 手动模式 | 步数: 0"
        test_char = "中"  # 单个中文字符测试
        
        # 标记是否找到支持中文的字体
        chinese_font_found = False
        
        for font_name in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 14)
                # 先测试单个中文字符
                char_surface = test_font.render(test_char, True, WHITE)
                # 再测试完整文本
                text_surface = test_font.render(test_text, True, WHITE)
                
                # 检查渲染结果是否有效
                if (char_surface.get_width() > 0 and 
                    text_surface.get_width() > 0 and
                    text_surface.get_width() > len(test_text) * 3):  # 确保不是占位符
                    font_small = test_font
                    font_large = pygame.font.SysFont(font_name, 40)
                    chinese_font_found = True
                    print(f"✓ 成功加载支持中文的字体: {font_name}")
                    break
            except Exception as e:
                print(f"✗ 尝试字体 {font_name} 失败: {e}")
                continue
        
        # 如果所有中文字体都不可用，使用默认字体
        if not chinese_font_found:
            print("⚠ 警告: 未找到支持中文的字体，将使用默认字体（可能无法正确显示中文）")
            try:
                font_small = pygame.font.Font(None, 28)
                font_large = pygame.font.Font(None, 40)
            except:
                try:
                    font_small = pygame.font.SysFont('Arial', 28)
                    font_large = pygame.font.SysFont('Arial', 40)
                except Exception as e:
                    print(f"✗ 创建默认字体失败: {e}")
        
        # 确保字体已初始化
        if font_small is None or font_large is None:
            raise RuntimeError("字体初始化失败！无法创建字体对象。")
        
        # 最终验证：测试字体是否能正确渲染中文
        try:
            test_surface = font_small.render(test_text, True, WHITE)
            if test_surface.get_width() == 0:
                print("⚠ 警告: 字体可能不支持中文显示，将使用英文文本")
                self.use_chinese = False
            else:
                self.use_chinese = True
        except Exception as e:
            print(f"⚠ 字体测试失败: {e}，将使用英文文本")
            self.use_chinese = False
        
        # 赋值给实例变量
        self.font_small = font_small
        self.font_large = font_large
    
    def get_available_directions(self) -> List[str]:
        """获取当前位置可用的移动方向"""
        directions = []
        x, y = self.player.x, self.player.y
        
        # 检查四个方向
        if not self.maze_generator.is_wall(x, y - 1):
            directions.append("UP")
        if not self.maze_generator.is_wall(x, y + 1):
            directions.append("DOWN")
        if not self.maze_generator.is_wall(x - 1, y):
            directions.append("LEFT")
        if not self.maze_generator.is_wall(x + 1, y):
            directions.append("RIGHT")
        
        return directions
    
    def serialize_maze_state(self) -> str:
        """将迷宫状态序列化为文本描述"""
        lines = []
        lines.append(f"迷宫大小: {self.maze_width} x {self.maze_height}")
        lines.append("\n迷宫地图 (W=墙, .=通道, P=玩家位置, G=目标位置):")
        lines.append("")
        
        for y in range(self.maze_height):
            line = ""
            for x in range(self.maze_width):
                if x == self.player.x and y == self.player.y:
                    line += "P"
                elif x == self.end_x and y == self.end_y:
                    line += "G"
                elif self.maze_generator.is_wall(x, y):
                    line += "W"
                else:
                    line += "."
            lines.append(line)
        
        return "\n".join(lines)
    
    def move_to_position(self, target_x: int, target_y: int) -> bool:
        """移动到指定坐标位置"""
        # 检查目标位置是否有效且可通行
        if self.maze_generator.is_wall(target_x, target_y):
            return False
        
        # 检查是否是相邻位置
        dx = target_x - self.player.x
        dy = target_y - self.player.y
        if abs(dx) + abs(dy) != 1:
            # 如果不是相邻位置，尝试直接设置（可能是LLM返回的坐标）
            # 但需要验证路径是否可通行
            if not self.maze_generator.is_wall(target_x, target_y):
                self.player.x = target_x
                self.player.y = target_y
                self.move_history.append((target_x, target_y))
                self.step_count += 1
                return True
            return False
        
        # 使用现有的move方法
        moved = self.player.move(dx, dy, self.maze_generator)
        if moved:
            self.move_history.append((self.player.x, self.player.y))
            self.step_count += 1
        return moved
    
    def get_unvisited_adjacent_positions(self) -> List[Tuple[int, int]]:
        """获取未访问的相邻位置"""
        unvisited = []
        x, y = self.player.x, self.player.y
        visited_set = set(self.move_history)
        
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            adj_x, adj_y = x + dx, y + dy
            if (not self.maze_generator.is_wall(adj_x, adj_y) and 
                (adj_x, adj_y) not in visited_set):
                unvisited.append((adj_x, adj_y))
        
        return unvisited
    
    def detect_loop(self, lookback_steps: int = 8) -> bool:
        """
        检测最近N步是否形成了循环模式（来回重复移动）
        
        Args:
            lookback_steps: 检查最近多少步
            
        Returns:
            如果检测到循环返回True，否则返回False
        """
        if len(self.move_history) < lookback_steps:
            return False
        
        # 获取最近N步的位置
        recent_positions = self.move_history[-lookback_steps:]
        
        # 检测模式1: 检查是否有位置重复出现（来回移动）
        # 如果最近N步中有超过一半的位置是重复的，可能是在循环
        position_counts = {}
        for pos in recent_positions:
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # 如果某个位置出现3次或以上，且总步数>=6，可能是循环
        max_repeats = max(position_counts.values()) if position_counts else 0
        if max_repeats >= 3 and len(recent_positions) >= 6:
            # 检查是否是简单的来回模式（A->B->A->B）
            if len(recent_positions) >= 4:
                # 检查最近4步是否形成ABAB模式
                last_4 = recent_positions[-4:]
                if last_4[0] == last_4[2] and last_4[1] == last_4[3] and last_4[0] != last_4[1]:
                    return True
                # 检查最近6步是否形成ABCABC模式
                if len(recent_positions) >= 6:
                    last_6 = recent_positions[-6:]
                    if (last_6[0] == last_6[3] and last_6[1] == last_6[4] and 
                        last_6[2] == last_6[5] and len(set(last_6[:3])) == 3):
                        return True
        
        # 检测模式2: 检查是否在同一个区域反复移动（位置变化很小）
        if len(recent_positions) >= 6:
            # 计算最近N步的坐标范围
            x_coords = [p[0] for p in recent_positions]
            y_coords = [p[1] for p in recent_positions]
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            # 如果坐标范围很小（<=2），且步数很多，可能是在小范围内循环
            if x_range <= 2 and y_range <= 2 and len(recent_positions) >= 6:
                return True
        
        return False
    
    def get_recent_movement_pattern(self, lookback_steps: int = 6) -> str:
        """
        获取最近N步的移动模式描述，用于提示LLM
        
        Args:
            lookback_steps: 检查最近多少步
            
        Returns:
            移动模式的文本描述
        """
        if len(self.move_history) < 2:
            return "无移动历史"
        
        recent_steps = min(lookback_steps, len(self.move_history))
        recent_positions = self.move_history[-recent_steps:]
        
        # 计算移动方向序列
        directions = []
        for i in range(1, len(recent_positions)):
            prev = recent_positions[i-1]
            curr = recent_positions[i]
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            
            if dx == 0 and dy == -1:
                directions.append("UP")
            elif dx == 0 and dy == 1:
                directions.append("DOWN")
            elif dx == -1 and dy == 0:
                directions.append("LEFT")
            elif dx == 1 and dy == 0:
                directions.append("RIGHT")
            else:
                directions.append("UNKNOWN")
        
        # 检测重复模式
        if len(directions) >= 4:
            # 检查ABAB模式
            if (directions[-4] == directions[-2] and 
                directions[-3] == directions[-1] and 
                directions[-4] != directions[-3]):
                return f"⚠️ 警告：检测到重复模式！最近4步: {' -> '.join(directions[-4:])}，形成了来回移动的循环。请立即改变方向，避免继续重复！"
            
            # 检查ABCABC模式
            if len(directions) >= 6:
                if (directions[-6] == directions[-3] and 
                    directions[-5] == directions[-2] and 
                    directions[-4] == directions[-1]):
                    return f"⚠️ 警告：检测到重复模式！最近6步: {' -> '.join(directions[-6:])}，形成了循环移动。请立即改变方向！"
        
        return f"最近{recent_steps}步移动方向: {' -> '.join(directions)}"
    
    def handle_auto_move(self):
        """处理自动移动逻辑"""
        if not self.auto_mode or self.won or not self.llm_client:
            return
        
        current_time = time.time()
        # 检查是否到了调用LLM的时间
        if current_time - self.last_llm_call_time < self.llm_call_interval:
            return
        
        try:
            print(f"\n🎮 自动模式 - 准备调用LLM (步数: {self.step_count})")
            
            # 获取迷宫状态
            maze_state = self.serialize_maze_state()
            current_pos = (self.player.x, self.player.y)
            target_pos = (self.end_x, self.end_y)
            available_directions = self.get_available_directions()
            
            # 获取未访问的相邻位置
            unvisited_adjacent = self.get_unvisited_adjacent_positions()
            
            # 检测循环
            is_looping = self.detect_loop()
            recent_pattern = self.get_recent_movement_pattern()
            
            print(f"📋 准备发送给LLM的信息:")
            print(f"   - 迷宫状态长度: {len(maze_state)} 字符")
            print(f"   - 未访问相邻位置: {unvisited_adjacent}")
            print(f"   - 循环检测: {'⚠️ 检测到循环！' if is_looping else '✅ 无循环'}")
            print(f"   - {recent_pattern}")
            
            # 如果检测到循环，且存在未访问的相邻位置，强制选择未访问位置
            if is_looping and unvisited_adjacent:
                print(f"\n🛑 检测到循环模式，强制选择未访问位置以避免重复移动")
                # 选择最接近目标的未访问位置
                best_pos = min(unvisited_adjacent, 
                             key=lambda p: abs(p[0] - target_pos[0]) + abs(p[1] - target_pos[1]))
                print(f"   ✅ 强制选择: {best_pos} (最接近目标)")
                next_pos = best_pos
            else:
                # 调用LLM获取下一步移动
                next_pos = self.llm_client.get_next_move(
                    maze_state,
                    current_pos,
                    target_pos,
                    self.move_history,
                    available_directions,
                    is_looping,
                    recent_pattern
                )
            
            # 更新最后调用时间
            self.last_llm_call_time = current_time
            
            print(f"\n🎯 执行移动决策:")
            print(f"   LLM返回的坐标: {next_pos}")
            
            # 验证：如果LLM返回的位置是已访问的，且存在未访问的相邻位置，则建议改为未访问位置
            # 但允许回溯（不强制拒绝），因为有时需要回溯才能找到正确路径
            if next_pos in self.move_history and unvisited_adjacent:
                print(f"   ⚠️  注意: LLM选择回溯到已访问位置 ({next_pos[0]}, {next_pos[1]})，但存在未访问的相邻位置")
                print(f"   建议改为未访问位置，但如果确实需要回溯，将允许")
                # 可以选择改为未访问位置，但这里我们信任LLM的判断，允许回溯
                # 如果希望强制避免回溯，可以取消下面的注释：
                # best_pos = min(unvisited_adjacent, 
                #              key=lambda p: abs(p[0] - target_pos[0]) + abs(p[1] - target_pos[1]))
                # next_pos = best_pos
                # print(f"✅ 改为移动到: ({next_pos[0]}, {next_pos[1]})")
            
            # 执行移动
            moved = self.move_to_position(next_pos[0], next_pos[1])
            
            if moved:
                print(f"   ✅ 移动成功: ({self.player.x}, {self.player.y})")
            else:
                print(f"   ❌ 移动失败: 目标位置 {next_pos} 不可达")
            
            if not moved:
                # 如果移动失败，尝试从未访问的相邻位置中选择
                if unvisited_adjacent:
                    print(f"   🔄 尝试从未访问的相邻位置中选择...")
                    # 选择最接近目标的未访问位置
                    best_pos = min(unvisited_adjacent, 
                                 key=lambda p: abs(p[0] - target_pos[0]) + abs(p[1] - target_pos[1]))
                    print(f"   📍 选择最佳未访问位置: {best_pos}")
                    moved = self.move_to_position(best_pos[0], best_pos[1])
                elif available_directions:
                    # 如果所有相邻位置都已访问，才允许访问已访问的位置
                    import random
                    direction = random.choice(available_directions)
                    if direction == "UP":
                        _ = self.player.move(0, -1, self.maze_generator)
                    elif direction == "DOWN":
                        _ = self.player.move(0, 1, self.maze_generator)
                    elif direction == "LEFT":
                        _ = self.player.move(-1, 0, self.maze_generator)
                    elif direction == "RIGHT":
                        _ = self.player.move(1, 0, self.maze_generator)
                    if (self.player.x, self.player.y) not in self.move_history:
                        self.move_history.append((self.player.x, self.player.y))
                    self.step_count += 1
            
            # 检查是否到达终点
            if self.player.x == self.end_x and self.player.y == self.end_y:
                self.won = True
            
            self.last_llm_call_time = current_time
        
        except Exception as e:
            print(f"自动移动出错: {e}")
            # 出错时也更新时间，避免频繁重试
            self.last_llm_call_time = current_time
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_t:
                    # 切换自动/手动模式 (使用T键，避免与A键冲突)
                    if self.llm_client:
                        self.auto_mode = not self.auto_mode
                        caption = "迷宫游戏 - AI自动模式 (按T切换手动模式，按R重新开始)"
                        if not self.auto_mode:
                            caption = "迷宫游戏 - 手动模式 (使用方向键移动，按T切换自动模式，按R重新开始)"
                        pygame.display.set_caption(caption)
                elif event.key == pygame.K_r:
                    # 重新生成迷宫
                    self.maze_generator = MazeGenerator(self.maze_width, self.maze_height)
                    self.maze_generator.generate()
                    self.player.reset()
                    self.won = False
                    self.move_history = [(1, 1)]
                    self.step_count = 0
                elif not self.won and not self.auto_mode:
                    # 手动模式下的移动控制
                    moved = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        moved = self.player.move(0, -1, self.maze_generator)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        moved = self.player.move(0, 1, self.maze_generator)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        moved = self.player.move(-1, 0, self.maze_generator)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        moved = self.player.move(1, 0, self.maze_generator)
                    
                    if moved:
                        self.move_history.append((self.player.x, self.player.y))
                        self.step_count += 1
                    
                    # 检查是否到达终点
                    if self.player.x == self.end_x and self.player.y == self.end_y:
                        self.won = True
    
    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)
        
        # 绘制迷宫
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                if self.maze_generator.is_wall(x, y):
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, WHITE, rect)
        
        # 绘制终点
        end_rect = pygame.Rect(
            self.end_x * CELL_SIZE + 2,
            self.end_y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4
        )
        pygame.draw.rect(self.screen, GREEN, end_rect)
        
        # 绘制玩家
        player_rect = pygame.Rect(
            self.player.x * CELL_SIZE + 4,
            self.player.y * CELL_SIZE + 4,
            CELL_SIZE - 8,
            CELL_SIZE - 8
        )
        pygame.draw.ellipse(self.screen, RED, player_rect)
        
        # 显示模式信息（带半透明背景框，确保在任何背景下都可见）
        # 根据字体支持情况选择中文或英文
        if getattr(self, 'use_chinese', True):
            mode_text = "自动模式" if self.auto_mode else "手动模式"
            info_text = f"模式: {mode_text} | 步数: {self.step_count}"
        else:
            mode_text = "Auto" if self.auto_mode else "Manual"
            info_text = f"Mode: {mode_text} | Steps: {self.step_count}"
        
        # 渲染文本
        mode_surface = self.font_small.render(info_text, True, WHITE)
        text_width, text_height = mode_surface.get_size()
        
        # 创建半透明黑色背景框
        padding = 8
        bg_rect = pygame.Rect(5, 5, text_width + padding * 2, text_height + padding * 2)
        bg_surface = pygame.Surface((text_width + padding * 2, text_height + padding * 2))
        bg_surface.set_alpha(200)  # 半透明
        bg_surface.fill(BLACK)
        self.screen.blit(bg_surface, bg_rect)
        
        # 绘制文本
        self.screen.blit(mode_surface, (5 + padding, 5 + padding))
        
        # 如果获胜，显示提示（带半透明背景框）
        if self.won:
            if getattr(self, 'use_chinese', True):
                win_text = f"恭喜！你赢了！步数: {self.step_count} | 按R重新开始"
            else:
                win_text = f"Congratulations! Steps: {self.step_count} | Press R to restart"
            text_surface = self.font_small.render(win_text, True, WHITE)
            text_width, text_height = text_surface.get_size()
            
            # 创建半透明黑色背景框
            padding = 15
            bg_rect = pygame.Rect(
                (self.screen_width - text_width - padding * 2) // 2,
                (self.screen_height - text_height - padding * 2) // 2,
                text_width + padding * 2,
                text_height + padding * 2
            )
            bg_surface = pygame.Surface((text_width + padding * 2, text_height + padding * 2))
            bg_surface.set_alpha(220)  # 半透明
            bg_surface.fill(BLACK)
            self.screen.blit(bg_surface, bg_rect)
            
            # 绘制文本
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text_surface, text_rect)
        
        pygame.display.flip()
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()
            if self.auto_mode:
                self.handle_auto_move()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()


def main():
    """主函数"""
    # 可以调整迷宫大小（必须是奇数）
    game = MazeGame(maze_width=21, maze_height=21)
    game.run()


if __name__ == "__main__":
    main()
