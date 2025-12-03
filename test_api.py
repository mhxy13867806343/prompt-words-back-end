"""
简单的 API 测试脚本
运行前确保服务已启动：uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    print("\n=== 测试注册 ===")
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": "testuser",
        "password": "123456"
    })
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()

def test_login():
    print("\n=== 测试登录 ===")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "testuser",
        "password": "123456"
    })
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    return data.get("data", {}).get("accessToken")

def test_create_prompt(token):
    print("\n=== 测试创建提示词 ===")
    response = requests.post(
        f"{BASE_URL}/prompts",
        json={
            "title": "测试提示词",
            "content": "这是一个测试内容" * 100
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()

def test_list_prompts():
    print("\n=== 测试获取提示词列表 ===")
    response = requests.get(f"{BASE_URL}/prompts?page=1&page_size=10")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_stats():
    print("\n=== 测试全局统计 ===")
    response = requests.get(f"{BASE_URL}/prompts/stats/global")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    try:
        # 测试注册
        test_register()
        
        # 测试登录
        token = test_login()
        
        if token:
            # 测试创建提示词
            test_create_prompt(token)
            
            # 测试列表
            test_list_prompts()
            
            # 测试统计
            test_stats()
        
        print("\n✅ 测试完成")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
