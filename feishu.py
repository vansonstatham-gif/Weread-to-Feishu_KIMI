import requests
import sys
from datetime import datetime

class FeishuClient:
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self._get_access_token()
    
    def _get_access_token(self):
        """获取飞书 access token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {'Content-Type': 'application/json'}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                print("✅ 成功获取飞书 access token")
            else:
                print(f"❌ 获取 access token 失败: {result}")
                print("请检查 App ID 和 App Secret 是否正确")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 获取 access token 异常: {e}")
            sys.exit(1)
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def list_records(self, base_id, table_id, filter_str=None):
        """查询多维表格记录"""
        url = f"{self.base_url}/bitable/v1/apps/{base_id}/tables/{table_id}/records"
        headers = self._get_headers()
        params = {}
        if filter_str:
            params['filter'] = filter_str
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                records = result.get('data', {}).get('items', [])
                print(f"✅ 查询到 {len(records)} 条现有记录")
                return records
            else:
                print(f"❌ 查询记录失败: {result}")
                self._check_permission_error(result)
                return []
        except Exception as e:
            print(f"❌ 查询记录异常: {e}")
            return []
    
    def add_record(self, base_id, table_id, fields):
        """添加单条记录"""
        url = f"{self.base_url}/bitable/v1/apps/{base_id}/tables/{table_id}/records"
        headers = self._get_headers()
        data = {"fields": fields}
        
        if not fields.get('书籍ID'):
            print(f"⚠️  跳过添加: 缺少书籍ID")
            return False
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                print(f"✅ 成功添加: {fields.get('标题', '未知')}")
                return True
            else:
                print(f"❌ 添加记录失败: {result}")
                self._check_permission_error(result)
                return False
        except Exception as e:
            print(f"❌ 添加记录异常: {e}")
            return False
    
    def update_record(self, base_id, table_id, record_id, fields):
        """更新记录"""
        url = f"{self.base_url}/bitable/v1/apps/{base_id}/tables/{table_id}/records/{record_id}"
        headers = self._get_headers()
        data = {"fields": fields}
        
        try:
            response = requests.patch(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                print(f"✅ 成功更新: {fields.get('标题', '未知')}")
                return True
            else:
                print(f"❌ 更新记录失败: {result}")
                self._check_permission_error(result)
                return False
        except Exception as e:
            print(f"❌ 更新记录异常: {e}")
            return False
    
    def _check_permission_error(self, result):
        """检查并提示权限问题"""
        code = result.get('code')
        msg = result.get('msg', '')
        
        if code == 99991401 or 'No permission' in msg:
            print("\n" + "="*60)
            print("🔐 权限错误排查指南:")
            print("1. 确保飞书应用已开通'查看、评论和编辑'多维表格权限")
            print("2. 确保已将应用添加到多维表格的协作者中")
            print("3. 确保应用版本已发布（应用管理后台 -> 版本管理与发布）")
            print("4. 重启多维表格，让权限生效")
            print("="*60 + "\n")
