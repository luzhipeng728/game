 #!/usr/bin/env python3
"""简单LLM测试"""

import sys
sys.path.append('.')

from sultans_game.config import get_model_config
from langchain_openai import ChatOpenAI

def test_llm():
    """测试LLM调用"""
    print("🔧 正在创建LLM...")
    
    try:
        config = get_model_config()
        print(f"📋 使用配置: {config['model']}")
        
        llm = ChatOpenAI(
            model=config["model"],
            temperature=0.7,
            base_url=config["base_url"],
            api_key=config["api_key"],
        )
        
        print("✅ LLM创建成功")
        
        # 测试调用
        test_prompt = "你是一个智能助手。请简单回答：今天天气怎么样？（回答要简洁，不超过50字）"
        
        print("🔄 正在测试LLM调用...")
        
        # 尝试不同的调用方式
        if hasattr(llm, 'invoke'):
            print("📞 使用invoke方法...")
            result = llm.invoke(test_prompt)
            response = result.content if hasattr(result, 'content') else str(result)
            print(f"✅ invoke方法成功: {response}")
        elif hasattr(llm, '__call__'):
            print("📞 使用__call__方法...")
            result = llm(test_prompt)
            response = result.content if hasattr(result, 'content') else str(result)
            print(f"✅ __call__方法成功: {response}")
        elif hasattr(llm, 'predict'):
            print("📞 使用predict方法...")
            response = llm.predict(test_prompt)
            print(f"✅ predict方法成功: {response}")
        else:
            print("❌ 没有找到可用的调用方法")
            print(f"LLM对象的方法: {[m for m in dir(llm) if not m.startswith('_')]}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm()