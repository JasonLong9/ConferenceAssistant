#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速API接口测试脚本
测试ConferenceAssistant的所有meeting接口
"""

import requests
import json
import time

class QuickAPITest:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_endpoint(self, method, endpoint, **kwargs):
        """测试单个接口"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, **kwargs)
            elif method.upper() == "POST":
                response = self.session.post(url, **kwargs)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, **kwargs)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            return True, {
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200],
                'headers': dict(response.headers)
            }
        
        except requests.exceptions.ConnectionError:
            return False, "连接失败 - 请确保服务已启动"
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except json.JSONDecodeError:
            return False, f"JSON解析失败: {response.text[:100]}"
        except Exception as e:
            return False, f"异常: {str(e)}"
    
    def run_tests(self):
        """运行所有接口测试"""
        print("=" * 70)
        print("ConferenceAssistant API 接口测试")
        print("=" * 70)
        
        # 测试用的假task_id
        fake_task_id = "test-task-id-12345"
        
        tests = [
            {
                'name': '1. 服务器健康检查',
                'method': 'GET',
                'endpoint': '/',
                'expected': '检查服务是否启动'
            },
            {
                'name': '2. 任务状态查询 (无效ID)',
                'method': 'GET',
                'endpoint': '/task_status',
                'params': {'task_id': fake_task_id},
                'expected': '应返回404或错误信息'
            },
            {
                'name': '3. 任务结果获取 (无效ID)',
                'method': 'GET',
                'endpoint': '/task_result',
                'params': {'task_id': fake_task_id},
                'expected': '应返回404或错误信息'
            },
            {
                'name': '4. 会议问答 (无效ID)',
                'method': 'POST',
                'endpoint': '/meeting/ask',
                'json': {
                    'task_id': fake_task_id,
                    'question': '这是一个测试问题'
                },
                'expected': '应返回会话不存在错误'
            },
            {
                'name': '5. 获取对话历史 (无效ID)',
                'method': 'GET',
                'endpoint': '/meeting/chat/history',
                'params': {'task_id': fake_task_id},
                'expected': '应返回会话不存在错误'
            },
            {
                'name': '6. 检查会话状态 (无效ID)',
                'method': 'GET',
                'endpoint': '/meeting/chat/status',
                'params': {'task_id': fake_task_id},
                'expected': '应返回会话不存在'
            },
            {
                'name': '7. 清空对话历史 (无效ID)',
                'method': 'DELETE',
                'endpoint': '/meeting/chat/clear',
                'params': {'task_id': fake_task_id},
                'expected': '应返回会话不存在错误'
            },
        ]
        
        results = []
        
        for test in tests:
            print(f"\n测试: {test['name']}")
            print(f"期望: {test['expected']}")
            
            # 准备请求参数
            kwargs = {}
            if 'params' in test:
                kwargs['params'] = test['params']
            if 'json' in test:
                kwargs['json'] = test['json']
            if 'data' in test:
                kwargs['data'] = test['data']
            if 'files' in test:
                kwargs['files'] = test['files']
            
            success, result = self.test_endpoint(test['method'], test['endpoint'], **kwargs)
            
            if success:
                status_code = result['status_code']
                response = result['response']
                
                print(f"接口可访问")
                print(f"   状态码: {status_code}")
                
                if isinstance(response, dict):
                    if 'code' in response:
                        print(f"   业务码: {response.get('code')}")
                    if 'msg' in response:
                        print(f"   消息: {response.get('msg')}")
                    if 'data' in response:
                        data = response.get('data')
                        if isinstance(data, dict) and len(str(data)) < 100:
                            print(f"   数据: {data}")
                        else:
                            print(f"   数据: {type(data).__name__}类型数据")
                else:
                    print(f"   响应: {str(response)[:100]}...")
                
                results.append({'test': test['name'], 'success': True, 'details': f"状态码: {status_code}"})
            else:
                print(f"测试失败: {result}")
                results.append({'test': test['name'], 'success': False, 'details': result})
        
        # 生成汇总报告
        print("\n" + "=" * 70)
        print("测试汇总")
        print("=" * 70)
        
        total = len(results)
        passed = sum(1 for r in results if r['success'])
        failed = total - passed
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"成功率: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n失败的测试:")
            for result in results:
                if not result['success']:
                    print(f"  失败 {result['test']}: {result['details']}")
        
        print(f"\n注意事项:")
        print(f"1. 此测试使用无效的task_id，主要验证接口可访问性和错误处理")
        print(f"2. 要测试完整功能，需要先上传音频文件获得有效的task_id")
        print(f"3. 如果所有接口都能正确返回错误信息，说明服务运行正常")
        
        return passed == total

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='快速API接口测试')
    parser.add_argument('--url', '-u', default='http://localhost:8080',
                       help='API服务地址 (默认: http://localhost:8080)')
    
    args = parser.parse_args()
    
    tester = QuickAPITest(args.url)
    success = tester.run_tests()
    
    if success:
        print("\n所有接口测试通过！")
    else:
        print("\n部分接口测试失败，请检查服务状态")

if __name__ == "__main__":
    main()