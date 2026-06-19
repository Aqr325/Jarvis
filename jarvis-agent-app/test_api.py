import httpx
import asyncio


async def test_coingecko():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd,cny"}
            )
            print(f"CoinGecko Status: {r.status_code}")
            print(f"CoinGecko Response: {r.text}")
        except httpx.HTTPError as e:
            print(f"CoinGecko Error: {e}")


async def test_frankfurter():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(
                "https://api.frankfurter.app/latest",
                params={"from": "USD", "to": "CNY"}
            )
            print(f"Frankfurter Status: {r.status_code}")
            print(f"Frankfurter Response: {r.text}")
        except httpx.HTTPError as e:
            print(f"Frankfurter Error: {e}")


async def test_nlp():
    """测试 NLP 模块"""
    from modules.nlp import NLPProcessor
    
    nlp = NLPProcessor()
    
    test_cases = [
        "查询比特币价格",
        "今天北京天气怎么样",
        "搜索一个关于编程的笑话",
        "解释一下 photoelectric effect",
        "2025年中国有哪些法定节假日",
        "12345.67 乘以 3.14 等于多少",
        "翻译 hello world 到中文",
        "帮我写一段 Python 快速排序代码",
    ]
    
    for text in test_cases:
        result = nlp.process(text)
        print(f"\n输入: {text}")
        print(f"  意图: {result.get('intent', 'unknown')} ({result.get('confidence', 0):.2f})")
        print(f"  实体: {result.get('entities', {})}")
        print(f"  情感: {result.get('sentiment', {})}")


async def test_server_chat():
    """测试后端 /api/chat 端点"""
    async with httpx.AsyncClient(timeout=30) as client:
        payload = {
            "category": "agent_chat",
            "input": "查询比特币价格",
            "client_id": "test_client"
        }
        try:
            r = await client.post(
                "http://localhost:8000/api/chat",
                json=payload
            )
            print(f"\nServer Chat Status: {r.status_code}")
            print(f"Server Chat Response: {r.json()}")
        except httpx.HTTPError as e:
            print(f"Server Chat Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Public APIs")
    print("=" * 60)
    asyncio.run(test_coingecko())
    asyncio.run(test_frankfurter())
    
    print("\n" + "=" * 60)
    print("Testing NLP Module")
    print("=" * 60)
    asyncio.run(test_nlp())
    
    print("\n" + "=" * 60)
    print("Testing Server Chat Endpoint")
    print("=" * 60)
    asyncio.run(test_server_chat())
