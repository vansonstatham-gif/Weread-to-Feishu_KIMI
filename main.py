import os
import sys
from datetime import datetime
from weread import WeReadClient
from feishu import FeishuClient

def sync_books_to_feishu(weread_client, feishu_client, base_id, table_id):
    """同步书籍信息到飞书多维表格"""
    print("\n📚 开始同步书籍信息...")
    
    # 获取书架数据
    books = weread_client.get_shelf()
    if not books:
        print("⚠️ 没有找到有效书籍，跳过同步")
        return
    
    # 查询已存在的记录
    existing_records = feishu_client.list_records(base_id, table_id)
    existing_books = {record.get('fields', {}).get('书籍ID'): record 
                     for record in existing_records}
    
    # 统计
    success_count, update_count = 0, 0
    
    # 同步每本书
    for idx, book in enumerate(books, 1):
        book_id = book['book_id']
        title = book['title']
        
        print(f"[{idx}/{len(books)}] 处理: {title}")
        
        # 获取阅读统计
        stats = weread_client.get_reading_stats(book_id)
        
        # 🔥 关键修复：所有日期字段改为Unix时间戳
        fields = {
            '书籍ID': book_id,
            '标题': title,
            '作者': book['author'],
            '封面': book['cover'],
            '分类': book['category'],
            '阅读进度': float(book['progress']),
            '阅读时长(分钟)': int(book['reading_time'] / 60) if book['reading_time'] else 0,
            '是否读完': book['finished'],
            '阅读页数': stats.get('read_pages', 0),
            '总页数': stats.get('total_pages', 0),
            '阅读天数': stats.get('read_days', 0),
            '最后阅读时间': book['last_read_time'],  # Unix时间戳
            '更新时间': int(datetime.now().timestamp()),  # Unix时间戳
        }
        
        # 判断是新增还是更新
        if book_id in existing_books:
            record_id = existing_books[book_id]['record_id']
            if feishu_client.update_record(base_id, table_id, record_id, fields):
                update_count += 1
        else:
            if feishu_client.add_record(base_id, table_id, fields):
                success_count += 1
    
    print(f"\n📊 书籍同步完成: 新增 {success_count} 本, 更新 {update_count} 本")

def main():
    """主函数"""
    # 从环境变量获取配置
    required_vars = {
        'FEISHU_APP_ID': os.environ.get('FEISHU_APP_ID'),
        'FEISHU_APP_SECRET': os.environ.get('FEISHU_APP_SECRET'),
        'FEISHU_BASE_ID': os.environ.get('FEISHU_BASE_ID'),
        'FEISHU_TABLE_ID': os.environ.get('FEISHU_TABLE_ID'),
        'WEREAD_COOKIE': os.environ.get('WEREAD_COOKIE')
    }
    
    # 检查必要的环境变量
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("✅ 环境变量检查通过")
    print(f"飞书 Base ID: {required_vars['FEISHU_BASE_ID']}")
    print(f"微信读书用户: {dict(item.split('=') for item in required_vars['WEREAD_COOKIE'].split('; ')).get('wr_name', '未知')}")
    
    # 初始化客户端
    try:
        weread_client = WeReadClient(required_vars['WEREAD_COOKIE'])
        feishu_client = FeishuClient(required_vars['FEISHU_APP_ID'], required_vars['FEISHU_APP_SECRET'])
    except Exception as e:
        print(f"❌ 初始化客户端失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 执行同步
    try:
        sync_books_to_feishu(
            weread_client, 
            feishu_client, 
            required_vars['FEISHU_BASE_ID'], 
            required_vars['FEISHU_TABLE_ID']
        )
        
        print("\n🎉 所有数据同步完成!")
        
    except Exception as e:
        print(f"\n❌ 同步过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
