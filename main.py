import os
import sys
from datetime import datetime
from weread import WeReadClient
from feishu import FeishuClient

def sync_books_to_feishu(weread_client, feishu_client, base_id, table_id):
    """同步书籍信息到飞书多维表格"""
    print("开始同步书籍信息...")
    
    # 获取书架数据
    books = weread_client.get_shelf()
    print(f"获取到 {len(books)} 本书")
    
    if not books:
        print("书架为空，跳过同步")
        return
    
    # 查询已存在的记录，用于判断是新增还是更新
    existing_records = feishu_client.list_records(base_id, table_id)
    
    # 创建一个以 book_id 为 key 的映射
    existing_books = {}
    for record in existing_records:
        fields = record.get('fields', {})
        book_id = fields.get('书籍ID')
        if book_id:
            existing_books[book_id] = record
    
    # 同步每本书
    for book in books:
        book_id = book['book_id']
        title = book['title']
        author = book['author']
        
        # 获取阅读统计
        stats = weread_client.get_reading_stats(book_id)
        
        # 构建字段数据
        fields = {
            '书籍ID': book_id,
            '标题': title,
            '作者': author,
            '封面': book['cover'],
            '分类': book['category'],
            '阅读进度': float(book['progress']),
            '阅读时长(分钟)': int(book['reading_time'] / 60) if book['reading_time'] else 0,
            '是否读完': book['finished'],
            '阅读页数': stats.get('read_pages', 0),
            '总页数': stats.get('total_pages', 0),
            '阅读天数': stats.get('read_days', 0),
            '最后阅读时间': book['last_read_date'],
            '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 判断是新增还是更新
        if book_id in existing_books:
            record_id = existing_books[book_id]['record_id']
            print(f"更新书籍: {title}")
            feishu_client.update_record(base_id, table_id, record_id, fields)
        else:
            print(f"新增书籍: {title}")
            feishu_client.add_record(base_id, table_id, fields)

def sync_notes_to_feishu(weread_client, feishu_client, base_id, notes_table_id):
    """同步笔记到飞书多维表格"""
    print("\n开始同步笔记...")
    
    # 获取书架数据
    books = weread_client.get_shelf()
    
    # 查询已存在的笔记，用于去重
    existing_notes = feishu_client.list_records(base_id, notes_table_id)
    existing_review_ids = set()
    for record in existing_notes:
        fields = record.get('fields', {})
        review_id = fields.get('笔记ID')
        if review_id:
            existing_review_ids.add(review_id)
    
    # 为每本书获取笔记
    total_notes = 0
    for book in books:
        book_id = book['book_id']
        title = book['title']
        
        notes = weread_client.get_book_notes(book_id)
        if not notes:
            continue
        
        print(f"正在同步《{title}》的 {len(notes)} 条笔记...")
        
        for note in notes:
            review_id = note['review_id']
            
            # 跳过已存在的笔记
            if review_id in existing_review_ids:
                continue
            
            fields = {
                '笔记ID': review_id,
                '书籍ID': book_id,
                '书名': title,
                '章节': note['chapter_name'],
                '高亮内容': note['abstract'],
                '笔记': note['content'],
                '创建时间': note['create_time'],
                '更新时间': note['update_time']
            }
            
            feishu_client.add_record(base_id, notes_table_id, fields)
            total_notes += 1
    
    print(f"同步完成，新增 {total_notes} 条笔记")

def main():
    """主函数"""
    # 从环境变量获取配置
    feishu_app_id = os.environ.get('FEISHU_APP_ID')
    feishu_app_secret = os.environ.get('FEISHU_APP_SECRET')
    feishu_base_id = os.environ.get('FEISHU_BASE_ID')
    weread_cookie = os.environ.get('WEREAD_COOKIE')
    
    # 检查必要的环境变量
    if not all([feishu_app_id, feishu_app_secret, feishu_base_id, weread_cookie]):
        print("错误: 缺少必要的环境变量!")
        print("请确保设置了 FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BASE_ID, WEREAD_COOKIE")
        sys.exit(1)
    
    # 初始化客户端
    print("初始化客户端...")
    weread_client = WeReadClient(weread_cookie)
    feishu_client = FeishuClient(feishu_app_id, feishu_app_secret)
    
    # 书籍表格ID（用于存储书籍信息）
    books_table_id = os.environ.get('FEISHU_TABLE_ID')
    # 笔记表格ID（可选，如果不设置则不同步笔记）
    notes_table_id = os.environ.get('FEISHU_NOTES_TABLE_ID', '')
    
    try:
        # 同步书籍信息
        sync_books_to_feishu(weread_client, feishu_client, feishu_base_id, books_table_id)
        
        # 如果配置了笔记表格，则同步笔记
        if notes_table_id:
            sync_notes_to_feishu(weread_client, feishu_client, feishu_base_id, notes_table_id)
        else:
            print("\n未配置笔记表格ID，跳过笔记同步")
        
        print("\n✅ 所有数据同步完成!")
        
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
