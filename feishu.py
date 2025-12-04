import requests
import json
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
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                self.access_token = result['tenant_access_token']
                print("成功获取飞书 access token")
            else:
                print(f"获取 access token 失败: {result}")
        except Exception as e:
            print(f"获取 access token 异常: {e}")
    
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
                return result.get('data', {}).get('items', [])
            else:
                print(f"查询记录失败: {result}")
                return []
        except Exception as e:
            print(f"查询记录异常: {e}")
            return []
    
    def add_record(self, base_id, table_id, fields):
        """添加单条记录"""
        url = f"{self.base_url}/bitable/v1/apps/{base_id}/tables/{table_id}/records"
        headers = self._get_headers()
        data = {"fields": fields}
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                print(f"成功添加记录: {fields.get('标题', '')}")
                return True
            else:
                print(f"添加记录失败: {result}")
                return False
        except Exception as e:
            print(f"添加记录异常: {e}")
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
                print(f"成功更新记录: {fields.get('标题', '')}")
                return True
            else:
                print(f"更新记录失败: {result}")
                return False
        except Exception as e:
            print(f"更新记录异常: {e}")
            return False
    
    def delete_record(self, base_id, table_id, record_id):
        """删除记录"""
        url = f"{self.base_url}/bitable/v1/apps/{base_id}/tables/{table_id}/records/{record_id}"
        headers = self._get_headers()
        
        try:
            response = requests.delete(url, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('code') == 0:
                print(f"成功删除记录: {record_id}")
                return True
            else:
                print(f"删除记录失败: {result}")
                return False
        except Exception as e:
            print(f"删除记录异常: {e}")
            return False
