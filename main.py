import os
import sys
from dotenv import load_dotenv
from maze_game import MazeGame
from llm_client import LLMClient

# 加载 .env 文件
load_dotenv()


def main():
    """主函数"""
    # 检查是否启用自动模式
    auto_mode = "--auto" in sys.argv or os.getenv("AUTO_MODE", "").lower() == "true"
    
    llm_client = None
    if auto_mode:
        try:
            # 从 .env 文件读取配置
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("错误: 自动模式需要设置 OPENAI_API_KEY")
                print("请在 .env 文件中设置 OPENAI_API_KEY，或设置环境变量")
                print("可以参考 .env.example 文件创建 .env 文件")
                sys.exit(1)
            
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1/")
            model = os.getenv("LLM_MODEL", "gpt-4o")
            
            llm_client = LLMClient(api_key=api_key, base_url=base_url, model=model)
            print(f"LLM客户端初始化成功，使用模型: {model}")
            if base_url:
                print(f"使用自定义API地址: {base_url}")
            print("游戏将以自动模式启动，AI将自动控制移动")
        except Exception as e:
            print(f"初始化LLM客户端失败: {e}")
            print("将使用手动模式启动")
            auto_mode = False
    
    # 创建游戏实例
    # 可以调整迷宫大小（必须是奇数）
    game = MazeGame(
        maze_width=21,
        maze_height=21,
        auto_mode=auto_mode,
        llm_client=llm_client
    )
    
    # 运行游戏
    game.run()


if __name__ == "__main__":
    main()
