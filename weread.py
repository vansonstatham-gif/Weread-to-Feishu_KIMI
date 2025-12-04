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
        """获取书架数据"""
        url = "https://weread.qq.com/web/shelf/sync"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            books = []
            all_books = data.get('books', [])
            print(f"📦 API返回的书籍总数: {len(all_books)}")
            
            for book in all_books:
                # 获取书籍基本信息
                book_id = book.get('bookId')
                title = book.get('title')
                
                if not book_id or not title:
                    print(f"⚠️  跳过无效书籍: ID={book_id}, 标题={title}")
                    continue
                
                # 跳过非数字ID的内容（如公众号）
                if isinstance(book_id, str) and not book_id.isdigit():
                    print(f"📄 跳过非书籍内容: ID={book_id}, 标题={title}")
                    continue
                
                # 🔥 关键修复：正确提取所有字段
                # 最后阅读时间（从readingBook对象获取）
                last_read_time = 0
                if book.get('readingBook'):
                    # readingBook对象里的readingTime是最后阅读时间戳
                    last_read_time = int(book['readingBook'].get('readingTime', 0))
                
                # 如果readingBook没有，使用book自身的updateTime
                if last_read_time == 0:
                    last_read_time = int(book.get('updateTime', 0))
                
                books.append({
                    'book_id': str(book_id),
                    'title': title,
                    'author': book.get('author', '未知作者'),
                    'cover': book.get('cover', ''),
                    'category': book.get('category', ''),
                    'finished': bool(book.get('finishReading', False)),
                    'reading_time': int(book.get('readingTime', 0)),  # 总阅读时长（秒）
                    'progress': float(book.get('progress', 0)),  # 阅读进度0-1
                    'format': book.get('format', 'book'),
                    'intro': book.get('intro', ''),
                    'last_read_time': last_read_time,  # Unix时间戳
                })
            
            print(f"✅ 有效书籍数量: {len(books)}/{len(all_books)}")
            return books
        except Exception as e:
            print(f"❌ 获取书架数据失败: {e}")
            import traceback
            traceback.print_exc()
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
                        'create_time': int(review.get('createTime', 0)),
                        'update_time': int(review.get('updateTime', 0)),
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
                return {
                    'read_time': 0, 'read_pages': 0, 'finish_pages': 0,
                    'total_pages': 0, 'read_days': 0, 'max_continuous_days': 0
                }
            print(f"⚠️  获取书籍 {book_id} 统计失败: {e}")
            return {}
        except Exception as e:
            print(f"⚠️  获取书籍 {book_id} 统计异常: {e}")
            return {}
