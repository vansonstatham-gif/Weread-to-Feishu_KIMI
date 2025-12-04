import os
import sys
from datetime import datetime
from weread import WeReadClient
from feishu import FeishuClient

def sync_books_to_feishu(weread_client, feishu_client, base_id, table_id):
    """同步书籍信息到飞书多维表格（智能覆盖模式）"""
    print("\n📚 开始同步书籍信息...")
    
    # 获取书架数据
    books = weread_client.get_shelf()
    if not books:
        print("⚠️ 没有找到有效书籍，跳过同步")
        return
    
    # 查询已存在的记录
    print("\n🔍 查询飞书现有记录...")
    existing_records = feishu_client.list_records(base_id, table_id)
    
    # 构建书籍ID到记录的映射
    existing_books = {}
    for record in existing_records:
        fields = record.get('fields', {})
        book_id = fields.get('书籍ID')
        if book_id:
            existing_books[book_id] = {
                'record_id': record.get('record_id'),
                'fields': fields
            }
    
    print(f"✅ 找到 {len(existing_books)} 本已存在的书籍")
    
    # 统计
    success_count, update_count, delete_add_count, error_count = 0, 0, 0, 0
    
    # 同步每本书
    for idx, book in enumerate(books, 1):
        book_id = book['book_id']
        title = book['title']
        
        print(f"[{idx}/{len(books)}] 处理: {title}")
        
        # 获取阅读统计
        stats = weread_client.get_reading_stats(book_id)
        
        # 构建字段数据
        progress_pct = float(book['progress']) * 100
        read_minutes = int(book['reading_time'] / 60) if book['reading_time'] else 0
        
        fields = {
            '书籍ID': book_id,
            '标题': title,
            '作者': book['author'],
            '封面': book['cover'],
            '分类': book['category'],
            '阅读进度': progress_pct,
            '阅读时长(分钟)': read_minutes,
            '是否读完': book['finished'],
            '阅读页数': stats.get('read_pages', 0),
            '总页数': stats.get('total_pages', 0),
            '阅读天数': stats.get('read_days', 0),
            '最后阅读时间': book['last_read_time'],
            '更新时间': int(datetime.now().timestamp()),
        }
        
        # 智能处理：存在则更新，更新失败则删除后新增
        if book_id in existing_books:
            record_id = existing_books[book_id]['record_id']
            
            # 🔥 尝试更新
            if feishu_client.update_record(base_id, table_id, record_id, fields):
                update_count += 1
            else:
                # 更新失败（可能是记录ID无效），删除后新增
                print(f"  ⚠️  更新失败，尝试删除后新增...")
                if feishu_client.delete_record(base_id, table_id, record_id):
                    if feishu_client.add_record(base_id, table_id, fields):
                        delete_add_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
        else:
            # 新增
            if feishu_client.add_record(base_id, table_id, fields):
                success_count += 1
            else:
                error_count += 1
    
    print(f"\n" + "="*60)
    print("📊 同步完成统计:")
    print(f"  ✅ 新增: {success_count} 本")
    print(f"  🔄 更新: {update_count} 本")
    print(f"  🔄 删除后新增: {delete_add_count} 本")
    print(f"  ❌ 失败: {error_count} 本")
    print("="*60)

def full_sync_books(weread_client, feishu_client, base_id, table_id):
    """全量同步：先清空表格再同步所有书籍"""
    print("\n" + "!"*60)
    print("⚠️  全量同步模式：将清空所有现有数据！")
    print("!"*60)
    
    # 确认清空
    confirm = os.environ.get('FULL_SYNC_CONFIRM', 'false').lower()
    if confirm != 'true':
        print("❌ 全量同步需设置 FULL_SYNC_CONFIRM=true")
        return
    
    # 清空表格
    records = feishu_client.list_records(base_id, table_id)
    print(f"\n🗑️  正在清空 {len(records)} 条记录...")
    for record in records:
        record_id = record.get('record_id')
        if record_id:
            feishu_client.delete_record(base_id, table_id, record_id)
    
    print("✅ 表格已清空，开始全量同步...")
    
    # 同步所有书籍
    books = weread_client.get_shelf()
    success_count = 0
    
    for idx, book in enumerate(books, 1):
        stats = weread_client.get_reading_stats(book['book_id'])
        
        fields = {
            '书籍ID': book['book_id'],
            '标题': book['title'],
            '作者': book['author'],
            '封面': book['cover'],
            '分类': book['category'],
            '阅读进度': float(book['progress']) * 100,
            '阅读时长(分钟)': int(book['reading_time'] / 60) if book['reading_time'] else 0,
            '是否读完': book['finished'],
            '阅读页数': stats.get('read_pages', 0),
            '总页数': stats.get('total_pages', 0),
            '阅读天数': stats.get('read_days', 0),
            '最后阅读时间': book['last_read_time'],
            '更新时间': int(datetime.now().timestamp()),
        }
        
        if feishu_client.add_record(base_id, table_id, fields):
            success_count += 1
    
    print(f"\n✅ 全量同步完成: 新增 {success_count} 本")

def main():
    """主函数"""
    required_vars = {
        'FEISHU_APP_ID': os.environ.get('FEISHU_APP_ID'),
        'FEISHU_APP_SECRET': os.environ.get('FEISHU_APP_SECRET'),
        'FEISHU_BASE_ID': os.environ.get('FEISHU_BASE_ID'),
        'FEISHU_TABLE_ID': os.environ.get('FEISHU_TABLE_ID'),
        'WEREAD_COOKIE': os.environ.get('WEREAD_COOKIE')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("="*60)
    print("📚 微信读书 → 飞书多维表格 同步工具")
    print("="*60)
    print(f"✅ 环境变量检查通过")
    print(f"📌 飞书 Base ID: {required_vars['FEISHU_BASE_ID']}")
    print(f"👤 微信读书用户: {dict(item.split('=') for item in required_vars['WEREAD_COOKIE'].split('; ')).get('wr_name', '未知')}")
    
    # 初始化客户端
    try:
        weread_client = WeReadClient(required_vars['WEREAD_COOKIE'])
        feishu_client = FeishuClient(required_vars['FEISHU_APP_ID'], required_vars['FEISHU_APP_SECRET'])
    except Exception as e:
        print(f"❌ 初始化客户端失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # 判断同步模式
    sync_mode = os.environ.get('SYNC_MODE', 'incremental')  # incremental 或 full
    
    try:
        if sync_mode == 'full':
            # 全量同步（会清空表格）
            full_sync_books(
                weread_client, 
                feishu_client, 
                required_vars['FEISHU_BASE_ID'], 
                required_vars['FEISHU_TABLE_ID']
            )
        else:
            # 增量同步（智能覆盖）
            sync_books_to_feishu(
                weread_client, 
                feishu_client, 
                required_vars['FEISHU_BASE_ID'], 
                required_vars['FEISHU_TABLE_ID']
            )
        
        print("\n" + "="*60)
        print("🎉 所有数据同步完成!")
        print("📊 请检查飞书多维表格中的数据")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 同步过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
