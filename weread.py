import requests
import json
from datetime import datetime

class WeReadClient:
    def __init__(self, cookie):
        self.cookie = cookie
        self.headers = {
            'Cookie': cookie,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://weread.qq.com/',
            'Accept': 'application/json, text/plain, */*'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_shelf(self):
        """获取书架数据，跳过无效书籍"""
        url = "https://weread.qq.com/web/shelf/sync"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            books = []
            print(f"📦 API返回的书籍总数: {len(data.get('books', []))}")
            
            if 'books' in data and len(data['books']) > 0:
                # 🔍 打印第一本书的完整结构用于调试
                print("\n=== 调试：第一本书的原始数据结构 ===")
                first_book = data['books'][0]
                print(json.dumps(first_book, ensure_ascii=False, indent=2))
                print("="*50 + "\n")
            
            for idx, book in enumerate(data.get('books', [])):
                book_info = book.get('book', {})
                
                # 🔍 尝试多种可能的书名字段
                title = (
                    book_info.get('title') or 
                    book.get('title') or 
                    book_info.get('bookName') or
                    book.get('bookName') or
                    '未知标题'
                )
                
                book_id = book_info.get('bookId') or book.get('bookId')
                
                # 跳过无效书籍
                if not book_id or not title or title == '未知标题':
                    print(f"跳过无效书籍: ID={book_id}, 标题={title}")
                    continue
                
                # 跳过公众号等特殊内容（ID包含字母）
                if isinstance(book_id, str) and not book_id.isdigit():
                    print(f"跳过非书籍内容: ID={book_id}, 标题={title}")
                    continue
                
                books.append({
                    'book_id': str(book_id),
                    'title': title,
                    'author': book_info.get('author', '未知作者'),
                    'cover': book_info.get('cover', ''),
                    'category': book_info.get('category', ''),
                    'finished': bool(book.get('finishReading', False)),
                    'reading_time': int(book.get('readingTime', 0)),
                    'progress': float(book.get('progress', 0)),
                    'format': book_info.get('format', 'book'),
                    'intro': book_info.get('intro', ''),
                    'last_read_date': datetime.fromtimestamp(
                        book.get('readingBook', {}).get('readingTime', 0)
                    ).strftime('%Y-%m-%d %H:%M:%S') if book.get('readingBook') else None
                })
            
            print(f"✅ 有效书籍数量: {len(books)}/{len(data.get('books', []))}")
            return books
        except Exception as e:
            print(f"❌ 获取书架数据失败: {e}")
            return []
    
    def get_book_notes(self, book_id):
        """获取单本书的笔记和高亮"""
        if not book_id:
            return []
            
        url = f"https://weread.qq.com/web/review/list?bookId={book_id}&listType=1"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            notes = []
            if 'reviews' in data:
                for review in data['reviews']:
                    if not review.get('reviewId'):
                        continue
                    
                    notes.append({
                        'review_id': str(review['reviewId']),
                        'book_id': str(book_id),
                        'chapter_name': review.get('chapterName', ''),
                        'abstract': review.get('abstract', ''),
                        'content': review.get('content', ''),
                        'create_time': datetime.fromtimestamp(
                            review.get('createTime', 0)
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'update_time': datetime.fromtimestamp(
                            review.get('updateTime', 0)
                        ).strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return notes
        except Exception as e:
            print(f"⚠️  获取书籍 {book_id} 笔记失败: {e}")
            return []
    
    def get_reading_stats(self, book_id):
        """获取单本书的阅读统计"""
        if not book_id:
            return {}
            
        url = f"https://weread.qq.com/web/read/format?bookId={book_id}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'read_time': int(data.get('readTime', 0)),
                'read_pages': int(data.get('readPages', 0)),
                'finish_pages': int(data.get('finishPages', 0)),
                'total_pages': int(data.get('totalPages', 0)),
                'read_days': int(data.get('readDays', 0)),
                'max_continuous_days': int(data.get('maxContinuousReadDays', 0))
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # 对于非书籍内容，返回空统计
                return {
                    'read_time': 0, 'read_pages': 0, 'finish_pages': 0,
                    'total_pages': 0, 'read_days': 0, 'max_continuous_days': 0
                }
            print(f"⚠️  获取书籍 {book_id} 统计失败: {e}")
            return {}
        except Exception as e:
            print(f"⚠️  获取书籍 {book_id} 统计异常: {e}")
            return {}
