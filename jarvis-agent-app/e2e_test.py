"""
J.A.R.V.I.S. End-to-End Test Suite
====================================
Tests the complete pipeline: NLP processing -> Public API -> Agent -> Server
"""

import asyncio
import httpx
import sys
import os

# Import NLP module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.nlp import NLPProcessor
from modules.public_apis import (
    crypto_price, crypto_list, exchange_rate,
    dictionary_lookup, tell_joke, search_books,
)

SERVER_BASE = "http://localhost:8000"

# ===========================================================================
# 1. NLP Module Tests
# ===========================================================================
async def test_nlp_module():
    """测试 NLP 模块 - Intent recognition, entity extraction, sentiment analysis"""
    print("=" * 70)
    print(" 1. NLP MODULE TESTS")
    print("=" * 70)
    
    nlp = NLPProcessor()
    
    test_cases = [
        ("查询比特币最新价格", "crypto"),
        ("今天北京天气怎么样", "weather"),
        ("解释一下 photoelectric effect", "dictionary"),
        ("2025年中国有哪些法定节假日", "holiday"),
        ("给我讲个笑话", "joke"),
        ("搜索关于人工智能的书籍", "book_search"),
        ("1美元等于多少人民币", "exchange"),
        ("帮我写一段 Python 快速排序代码", "code_help"),
        ("搜索一个关于程序员的笑话", "joke"),
        ("查看我的待办事项", "list_tasks"),
    ]
    
    passed = 0
    for text, expected_intent in test_cases:
        result = nlp.process(text)
        intent = result.get("intent", "unknown")
        confidence = result.get("confidence", 0)
        entities = result.get("entities", {})
        sentiment = result.get("sentiment", {})
        
        status = "PASS" if intent == expected_intent else "PARTIAL"
        if status == "PASS":
            passed += 1
        
        print(f"\n  [{status}] Input: {text}")
        print(f"       Intent: {intent} (confidence: {confidence:.2f}, expected: {expected_intent})")
        if entities:
            print(f"       Entities: {entities}")
        print(f"       Sentiment: {sentiment.get('label', 'unknown')} ({sentiment.get('score', 0):.2f})")
    
    print(f"\n  NLP Results: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ===========================================================================
# 2. Public API Tests
# ===========================================================================
async def test_coingecko():
    """测试 CoinGecko Crypto API"""
    print("\n" + "=" * 70)
    print(" 2. PUBLIC API TESTS")
    print("=" * 70)
    
    try:
        result = await crypto_price("bitcoin", "usd")
        if result and result.get("success"):
            print(f"\n  [PASS] CoinGecko BTC Price: ${result['data'].get('price', 'N/A')}")
            return True
        else:
            print(f"\n  [FAIL] CoinGecko: {result}")
            return False
    except Exception as e:
        print(f"\n  [ERROR] CoinGecko: {e}")
        return False


async def test_frankfurter():
    """测试 Frankfurter Exchange Rate API"""
    try:
        result = await exchange_rate("USD", "CNY", 1.0)
        if result and result.get("success"):
            data = result["data"]
            print(f"  [PASS] Frankfurter 1 USD = {data.get('rate', 'N/A')} CNY")
            return True
        else:
            print(f"  [FAIL] Frankfurter: {result}")
            return False
    except Exception as e:
        print(f"  [ERROR] Frankfurter: {e}")
        return False


async def test_dictionary():
    """测试 Free Dictionary API"""
    try:
        result = await dictionary_lookup("hello")
        if result and result.get("success"):
            print(f"  [PASS] Dictionary 'hello': {result['data'].get('meanings', [])[:1]}")
            return True
        else:
            print(f"  [FAIL] Dictionary: {result}")
            return False
    except Exception as e:
        print(f"  [ERROR] Dictionary: {e}")
        return False


async def test_joke_api():
    """测试 JokeAPI"""
    try:
        result = await tell_joke("Any", "en")
        if result and result.get("success"):
            joke_text = result["data"].get("joke", "")[:80]
            print(f"  [PASS] Joke API: '{joke_text}...'")
            return True
        else:
            print(f"  [FAIL] Joke API: {result}")
            return False
    except Exception as e:
        print(f"  [ERROR] Joke API: {e}")
        return False


async def test_book_search():
    """测试 Open Library"""
    try:
        result = await search_books("artificial intelligence", limit=3)
        if result and result.get("success"):
            books = result["data"].get("books", [])
            if books:
                print(f"  [PASS] Book Search: found {len(books)} results")
                print(f"        Top: {books[0].get('title', 'N/A')}")
                return True
        print(f"  [FAIL] Book Search: {result}")
        return False
    except Exception as e:
        print(f"  [ERROR] Book Search: {e}")
        return False


# ===========================================================================
# 3. Server Endpoint Tests
# ===========================================================================
async def test_server_health():
    """测试服务器健康检查"""
    print("\n" + "=" * 70)
    print(" 3. SERVER ENDPOINT TESTS")
    print("=" * 70)
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{SERVER_BASE}/health")
            if r.status_code == 200:
                data = r.json()
                print(f"\n  [PASS] Server Health: {data.get('service', 'N/A')} v{data.get('version', 'N/A')}")
                return True
            else:
                print(f"\n  [FAIL] Server Health: HTTP {r.status_code}")
                return False
    except Exception as e:
        print(f"\n  [ERROR] Server Health: {e}")
        return False


async def test_server_chat():
    """测试 /api/chat 端点"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {"message": "查询比特币最新价格"}
            r = await client.post(f"{SERVER_BASE}/api/chat", json=payload)
            
            if r.status_code == 200:
                data = r.json()
                output = data.get("output", "")[:100]
                print(f"\n  [PASS] /api/chat: {output}...")
                if data.get("nlp"):
                    print(f"        NLP Intent: {data['nlp'].get('intent', 'N/A')}")
                return True
            else:
                print(f"\n  [FAIL] /api/chat: HTTP {r.status_code} - {r.text[:200]}")
                return False
    except Exception as e:
        print(f"\n  [ERROR] /api/chat: {e}")
        return False


async def test_server_tool_call():
    """测试 /api/tool 端点"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            payload = {"tool": "crypto_price", "args": {"coin_id": "bitcoin", "vs_currency": "usd"}}
            r = await client.post(f"{SERVER_BASE}/api/tool", json=payload)
            
            if r.status_code == 200:
                data = r.json()
                print(f"\n  [PASS] /api/tool (crypto_price): {str(data)[:100]}")
                return True
            else:
                print(f"\n  [FAIL] /api/tool: HTTP {r.status_code} - {r.text[:200]}")
                return False
    except Exception as e:
        print(f"\n  [ERROR] /api/tool: {e}")
        return False


async def test_server_public_endpoints():
    """测试公共 API 端点"""
    results = []
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test public crypto
            r = await client.post(f"{SERVER_BASE}/api/public/crypto", json={"coin_id": "ethereum", "vs_currency": "usd"})
            if r.status_code == 200:
                data = r.json()
                print(f"\n  [PASS] /api/public/crypto: ETH = ${data.get('data', {}).get('price', 'N/A')}")
                results.append(True)
            else:
                print(f"\n  [FAIL] /api/public/crypto: HTTP {r.status_code}")
                results.append(False)
            
            # Test public exchange
            r = await client.post(f"{SERVER_BASE}/api/public/exchange", json={"from_currency": "USD", "to_currency": "JPY", "amount": 100})
            if r.status_code == 200:
                data = r.json()
                print(f"  [PASS] /api/public/exchange: 100 USD = {data.get('data', {}).get('converted', 'N/A')} JPY")
                results.append(True)
            else:
                print(f"  [FAIL] /api/public/exchange: HTTP {r.status_code}")
                results.append(False)
            
            # Test public joke
            r = await client.post(f"{SERVER_BASE}/api/public/joke", json={"category": "Any", "lang": "en"})
            if r.status_code == 200:
                print(f"  [PASS] /api/public/joke: retrieved successfully")
                results.append(True)
            else:
                print(f"  [FAIL] /api/public/joke: HTTP {r.status_code}")
                results.append(False)
            
            # Test capabilities
            r = await client.get(f"{SERVER_BASE}/api/public/capabilities")
            if r.status_code == 200:
                data = r.json()
                print(f"  [PASS] /api/public/capabilities: {data.get('count', 0)} APIs available")
                results.append(True)
            else:
                print(f"  [FAIL] /api/public/capabilities: HTTP {r.status_code}")
                results.append(False)
                
    except Exception as e:
        print(f"\n  [ERROR] Public endpoints: {e}")
        results.extend([False, False, False, False])
    
    return all(results)


async def test_server_tools_list():
    """测试 /api/tools 端点"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{SERVER_BASE}/api/tools")
            if r.status_code == 200:
                data = r.json()
                tools = data.get("available_tools", [])
                print(f"\n  [PASS] /api/tools: {len(tools)} tools available")
                print(f"        Tools: {', '.join(tools[:8])}{'...' if len(tools) > 8 else ''}")
                return True
            else:
                print(f"\n  [FAIL] /api/tools: HTTP {r.status_code}")
                return False
    except Exception as e:
        print(f"\n  [ERROR] /api/tools: {e}")
        return False


# ===========================================================================
# 4. Integrated Pipeline Test
# ===========================================================================
async def test_integrated_pipeline():
    """测试完整集成链路: User Input -> NLP -> API -> Response"""
    print("\n" + "=" * 70)
    print(" 4. INTEGRATED PIPELINE TEST")
    print("=" * 70)
    
    test_scenarios = [
        {
            "name": "Crypto Query",
            "input": "帮我查一下以太坊的价格",
            "expected_intent": "crypto",
        },
        {
            "name": "Weather Query", 
            "input": "上海今天的天气如何",
            "expected_intent": "weather",
        },
        {
            "name": "Dictionary Query",
            "input": "解释一下 quantum computing",
            "expected_intent": "dictionary",
        },
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n  Scenario: {scenario['name']}")
        print(f"  Input: {scenario['input']}")
        
        # Step 1: NLP Processing
        nlp = NLPProcessor()
        nlp_result = nlp.process(scenario["input"])
        intent = nlp_result.get("intent", "unknown")
        
        print(f"    NLP Intent: {intent} (expected: {scenario['expected_intent']})")
        
        # Step 2: Server Chat
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{SERVER_BASE}/api/chat",
                    json={"message": scenario["input"]}
                )
                if r.status_code == 200:
                    data = r.json()
                    output = data.get("output", "")
                    print(f"    Server Output: {output[:80]}...")
                    
                    # Verify NLP data in response
                    if data.get("nlp"):
                        print(f"    NLP in Response: intent={data['nlp'].get('intent', 'N/A')}")
                    results.append(True)
                else:
                    print(f"    Server Error: HTTP {r.status_code}")
                    results.append(False)
        except Exception as e:
            print(f"    Server Error: {e}")
            results.append(False)
    
    print(f"\n  Pipeline Results: {sum(results)}/{len(results)} scenarios passed")
    return all(results)


# ===========================================================================
# Main
# ===========================================================================
async def main():
    print("\n" + "#" * 70)
    print("#  J.A.R.V.I.S. END-TO-END TEST SUITE")
    print("#" * 70)
    
    all_results = {}
    
    # 1. NLP Module
    all_results["NLP Module"] = await test_nlp_module()
    
    # 2. Public APIs (direct)
    api_results = []
    api_results.append(await test_coingecko())
    api_results.append(await test_frankfurter())
    api_results.append(await test_dictionary())
    api_results.append(await test_joke_api())
    api_results.append(await test_book_search())
    all_results["Public APIs (Direct)"] = all(api_results)
    
    # 3. Server Endpoints
    server_results = []
    server_results.append(await test_server_health())
    server_results.append(await test_server_chat())
    server_results.append(await test_server_tool_call())
    server_results.append(await test_server_public_endpoints())
    server_results.append(await test_server_tools_list())
    all_results["Server Endpoints"] = all(server_results)
    
    # 4. Integrated Pipeline
    all_results["Integrated Pipeline"] = await test_integrated_pipeline()
    
    # Summary
    print("\n" + "#" * 70)
    print("#  TEST SUMMARY")
    print("#" * 70)
    
    for category, passed in all_results.items():
        status = "ALL PASSED ✓" if passed else "SOME FAILED ✗"
        print(f"  [{status}] {category}")
    
    total_passed = sum(1 for v in all_results.values() if v)
    total_tests = len(all_results)
    print(f"\n  Overall: {total_passed}/{total_tests} categories passed")
    print("#" * 70 + "\n")
    
    return all(all_results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
