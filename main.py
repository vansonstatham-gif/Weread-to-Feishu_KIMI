import os
import sys
from datetime import datetime
from weread import WeReadClient
from feishu import FeishuClient

def sync_books_to_feishu(weread_client, feishu_client, base_id, table_id):
    """同步书籍信息到飞书多维表格"""
    print("\n📚 开始同步书籍信息...")
    
    books = weread_client.get_shelf()
    if not books:
        print("⚠️ 没有找到有效书籍，跳过同步")
        return
    
    print("\n🔍 查询飞书现有书籍记录...")
    existing_records = feishu_client.list_records(base_id, table_id)
    existing_books = {record.get('fields', {}).get('书籍ID'): record 
                     for record in existing_records}
    
    print(f"✅ 找到 {len(existing_books)} 本已存在的书籍")
    
    success_count, update_count, error_count = 0, 0, 0
    
    for idx, book in enumerate(books, 1):
        book_id = book['book_id']
        title = book['title']
        
        print(f"[{idx}/{len(books)}] 处理: {title}")
        
        stats = weread_client.get_reading_stats(book_id)
        
        progress_pct = float(book['progress']) * 100
        read_minutes = int(book['reading_time'] / 60) if book['reading_time'] else 0
        
        # 🔥 封面URL改为Link对象格式（修复飞书超链接字段）
        fields = {
            '书籍ID': book_id,
            '标题': title,
            '作者': book['author'],
            '封面': {'link': book['cover']},  # 超链接字段必须是对象
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
        
        # 智能处理：存在则更新，更新失败则新增
        if book_id in existing_books:
            record_id = existing_books[book_id]['record_id']
            
            if feishu_client.update_record(base_id, table_id, record_id, fields):
                update_count += 1
            else:
                # 更新失败也不删除，直接新增一条
                print(f"  ⚠️  更新失败，改为新增记录...")
                if feishu_client.add_record(base_id, table_id, fields):
                    success_count += 1
                else:
                    error_count += 1
        else:
            if feishu_client.add_record(base_id, table_id, fields):
                success_count += 1
            else:
                error_count += 1
    
    print(f"\n📊 书籍同步完成: 新增 {success_count} 本, 更新 {update_count} 本, 失败 {error_count} 本")

def sync_notes_to_feishu(weread_client, feishu_client, base_id, notes_table_id):
    """同步读书笔记到飞书多维表格"""
    print("\n📝 开始同步读书笔记...")
    
    books = weread_client.get_shelf()
    if not books:
        print("⚠️ 没有找到书籍，跳过笔记同步")
        return
    
    print("\n🔍 查询飞书现有笔记...")
    existing_notes = feishu_client.list_records(base_id, notes_table_id)
    existing_review_ids = {record.get('fields', {}).get('笔记ID') for record in existing_notes}
    
    print(f"✅ 找到 {len(existing_review_ids)} 条已存在的笔记")
    
    success_count, skip_count, error_count = 0, 0, 0
    
    # 为每本书获取笔记
    for book_idx, book in enumerate(books, 1):
        book_id = book['book_id']
        title = book['title']
        
        notes = weread_client.get_book_notes(book_id)
        if not notes:
            continue
        
        print(f"\n[{book_idx}/{len(books)}] 同步《{title}》的 {len(notes)} 条笔记...")
        
        new_notes_count = 0
        
        for note in notes:
            review_id = note['review_id']
            
            if review_id in existing_review_ids:
                skip_count += 1
                continue
            
            fields = {
                '笔记ID': review_id,
                '书籍ID': book_id,
                '书名': title,
                '章节': note['chapter_name'],
                '高亮内容': note['abstract'],
                '笔记': note['content'],
                '创建时间': note['create_time'],
                '更新时间': note['update_time'],
            }
            
            if feishu_client.add_record(base_id, notes_table_id, fields):
                success_count += 1
                new_notes_count += 1
            else:
                error_count += 1
        
        if new_notes_count > 0:
            print(f"  ✅ 新增 {new_notes_count} 条笔记")
    
    print(f"\n📝 笔记同步完成: 新增 {success_count} 条, 跳过 {skip_count} 条, 失败 {error_count} 条")

def main():
    """主函数"""
    # 🔥 FEISHU_NOTES_TABLE_ID 是可选的
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
    
    # 笔记表格ID是可选的
    notes_table_id = os.environ.get('FEISHU_NOTES_TABLE_ID')
    
    print("="*60)
    print("📚 微信读书 → 飞书多维表格 同步工具")
    print("="*60)
    print(f"✅ 环境变量检查通过")
    print(f"📌 飞书 Base ID: {required_vars['FEISHU_BASE_ID']}")
    print(f"📌 书籍表格 ID: {required_vars['FEISHU_TABLE_ID']}")
    if notes_table_id:
        print(f"📌 笔记表格 ID: {notes_table_id}")
    else:
        print(f"ℹ️  未配置 FEISHU_NOTES_TABLE_ID，将跳过笔记同步")
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
    
    # 执行同步
    try:
        # 同步书籍信息（必须）
        sync_books_to_feishu(
            weread_client, 
            feishu_client, 
            required_vars['FEISHU_BASE_ID'], 
            required_vars['FEISHU_TABLE_ID']
        )
        
        # 🔥 可选：同步读书笔记
        if notes_table_id:
            sync_notes_to_feishu(
                weread_client, 
                feishu_client, 
                required_vars['FEISHU_BASE_ID'], 
                notes_table_id
            )
        else:
            print("\nℹ️  未配置 FEISHU_NOTES_TABLE_ID，跳过笔记同步")
        
        print("\n" + "="*60)
        print("🎉 所有数据同步完成!")
        print("📊 请检查飞书多维表格")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 同步过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
