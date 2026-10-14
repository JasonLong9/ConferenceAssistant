#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API接口全面测试脚本
测试系统的所有API接口，检查功能和性能
"""

import requests
import json
import time
import os
from datetime import datetime

# 服务器配置
BASE_URL = "http://localhost:8080"
TEST_AUDIO_FILE = "test_file/admin.mp3"

class APITester:
    def __init__(self):
        self.results = []
        self.task_id = None
        
    def log_test(self, test_name, status, details="", response_time=0):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'response_time': response_time,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        self.results.append(result)
        
        # 实时输出
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   详情: {details}")
        if response_time > 0:
            print(f"   响应时间: {response_time:.3f}s")
        print()

    def test_health_check(self):
        """测试健康检查接口"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['message', 'status', 'endpoints']
                missing_fields = [f for f in expected_fields if f not in data]
                
                if not missing_fields:
                    self.log_test("健康检查接口", "PASS", 
                                f"状态: {data.get('status')}", response_time)
                else:
                    self.log_test("健康检查接口", "FAIL", 
                                f"缺少字段: {missing_fields}", response_time)
            else:
                self.log_test("健康检查接口", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            self.log_test("健康检查接口", "ERROR", str(e))

    def test_audio_upload(self):
        """测试音频上传接口"""
        if not os.path.exists(TEST_AUDIO_FILE):
            self.log_test("音频上传接口", "SKIP", f"测试文件不存在: {TEST_AUDIO_FILE}")
            return
            
        try:
            start_time = time.time()
            with open(TEST_AUDIO_FILE, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{BASE_URL}/audio2summary_async", 
                                       files=files, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'task_id' in data and 'status' in data:
                    self.task_id = data['task_id']
                    self.log_test("音频上传接口", "PASS", 
                                f"任务ID: {self.task_id[:8]}...", response_time)
                else:
                    self.log_test("音频上传接口", "FAIL", 
                                "响应格式错误", response_time)
            else:
                self.log_test("音频上传接口", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}", response_time)
        except Exception as e:
            self.log_test("音频上传接口", "ERROR", str(e))

    def test_task_status(self):
        """测试任务状态查询接口"""
        if not self.task_id:
            self.log_test("任务状态查询", "SKIP", "需要先成功上传音频")
            return
            
        try:
            # 测试有效任务ID
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/task_status", 
                                  params={'task_id': self.task_id}, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['status', 'progress']
                if all(f in data for f in required_fields):
                    self.log_test("任务状态查询", "PASS", 
                                f"状态: {data['status']}, 进度: {data['progress']}%", 
                                response_time)
                else:
                    self.log_test("任务状态查询", "FAIL", 
                                "响应字段不完整", response_time)
            else:
                self.log_test("任务状态查询", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
                
            # 测试无效任务ID
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/task_status", 
                                  params={'task_id': 'invalid-id'}, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                self.log_test("任务状态查询(无效ID)", "PASS", 
                            "正确返回404错误", response_time)
            else:
                self.log_test("任务状态查询(无效ID)", "FAIL", 
                            f"应返回404，实际返回 {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("任务状态查询", "ERROR", str(e))

    def test_task_result(self):
        """测试任务结果获取接口"""
        if not self.task_id:
            self.log_test("任务结果获取", "SKIP", "需要先成功上传音频")
            return
            
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/task_result", 
                                  params={'task_id': self.task_id}, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    if data['status'] == 'done':
                        # 检查完成任务的结果字段
                        result_fields = ['full_transcript', 'meeting_minutes']
                        available_fields = [f for f in result_fields if f in data and data[f]]
                        self.log_test("任务结果获取", "PASS", 
                                    f"任务已完成，包含字段: {available_fields}", response_time)
                    else:
                        self.log_test("任务结果获取", "PASS", 
                                    f"任务状态: {data['status']}", response_time)
                else:
                    self.log_test("任务结果获取", "FAIL", 
                                "响应格式错误", response_time)
            else:
                self.log_test("任务结果获取", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            self.log_test("任务结果获取", "ERROR", str(e))

    def test_meeting_ask(self):
        """测试智能问答接口"""
        if not self.task_id:
            self.log_test("智能问答接口", "SKIP", "需要先成功上传音频")
            return
            
        try:
            question_data = {
                "task_id": self.task_id,
                "question": "这是一个测试问题，请简单回答即可"
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/meeting/ask", 
                                   json=question_data, timeout=30)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    answer_data = data['data']
                    if 'answer' in answer_data:
                        self.log_test("智能问答接口", "PASS", 
                                    f"回答长度: {len(answer_data['answer'])}字符", 
                                    response_time)
                    else:
                        self.log_test("智能问答接口", "FAIL", 
                                    "响应中缺少answer字段", response_time)
                else:
                    self.log_test("智能问答接口", "FAIL", 
                                f"业务错误: {data.get('message', '未知错误')}", response_time)
            else:
                self.log_test("智能问答接口", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                            
        except Exception as e:
            self.log_test("智能问答接口", "ERROR", str(e))

    def test_chat_status(self):
        """测试问答状态检查接口"""
        if not self.task_id:
            self.log_test("问答状态检查", "SKIP", "需要先成功上传音频")
            return
            
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/meeting/chat/status", 
                                  params={'task_id': self.task_id}, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'available' in data:
                    self.log_test("问答状态检查", "PASS", 
                                f"可用性: {data['available']}", response_time)
                else:
                    self.log_test("问答状态检查", "FAIL", 
                                "响应格式错误", response_time)
            else:
                self.log_test("问答状态检查", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            self.log_test("问答状态检查", "ERROR", str(e))

    def test_chat_history(self):
        """测试对话历史接口"""
        if not self.task_id:
            self.log_test("对话历史接口", "SKIP", "需要先成功上传音频")
            return
            
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/meeting/chat/history", 
                                  params={'task_id': self.task_id}, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("对话历史接口", "PASS", 
                                f"历史记录数量: {len(data)}", response_time)
                else:
                    self.log_test("对话历史接口", "FAIL", 
                                "响应应为数组格式", response_time)
            else:
                self.log_test("对话历史接口", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            self.log_test("对话历史接口", "ERROR", str(e))

    def test_docs_endpoint(self):
        """测试API文档接口"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/docs", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                if 'swagger' in response.text.lower() or 'openapi' in response.text.lower():
                    self.log_test("API文档接口", "PASS", 
                                "Swagger文档可访问", response_time)
                else:
                    self.log_test("API文档接口", "PARTIAL", 
                                "响应正常但不是标准Swagger格式", response_time)
            else:
                self.log_test("API文档接口", "FAIL", 
                            f"HTTP {response.status_code}", response_time)
        except Exception as e:
            self.log_test("API文档接口", "ERROR", str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("开始API接口全面测试")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标服务: {BASE_URL}")
        print("=" * 60)
        
        # 按顺序执行测试
        self.test_health_check()
        self.test_audio_upload()
        self.test_task_status()
        self.test_task_result()
        self.test_meeting_ask()
        self.test_chat_status()
        self.test_chat_history()
        self.test_docs_endpoint()
        
        # 生成测试报告
        self.generate_report()
        
    def generate_report(self):
        """生成测试报告"""
        print("=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.results if r['status'] == 'ERROR'])
        skipped_tests = len([r for r in self.results if r['status'] == 'SKIP'])
        
        print(f"总测试数: {total_tests}")
        print(f"[PASS] 通过: {passed_tests}")
        print(f"[FAIL] 失败: {failed_tests}")
        print(f"[ERROR] 错误: {error_tests}")
        print(f"[SKIP] 跳过: {skipped_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细问题列表:")
        issues = [r for r in self.results if r['status'] in ['FAIL', 'ERROR']]
        if issues:
            for issue in issues:
                print(f"[ISSUE] {issue['test_name']}: {issue['details']}")
        else:
            print("没有发现问题")
            
        # 保存详细报告到文件
        report_file = f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_time': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'errors': error_tests,
                    'skipped': skipped_tests,
                    'success_rate': passed_tests/total_tests*100
                },
                'details': self.results
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\n详细报告已保存到: {report_file}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()