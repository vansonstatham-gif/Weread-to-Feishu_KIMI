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
            if 'books' in data:
                for book in data['books']:
                    book_info = book.get('book', {})
                    books.append({
                        'book_id': book_info.get('bookId'),
                        'title': book_info.get('title'),
                        'author': book_info.get('author'),
                        'cover': book_info.get('cover'),
                        'category': book_info.get('category'),
                        'finished': book.get('finishReading', False),
                        'reading_time': book.get('readingTime', 0),  # 阅读时长(秒)
                        'progress': book.get('progress', 0),  # 阅读进度 0-100
                        'format': book_info.get('format'),  # 书籍类型
                        'intro': book_info.get('intro'),
                        'last_read_date': datetime.fromtimestamp(book.get('readingBook', {}).get('readingTime', 0)).strftime('%Y-%m-%d %H:%M:%S') if book.get('readingBook') else None
                    })
            return books
        except Exception as e:
            print(f"获取书架数据失败: {e}")
            return []
    
    def get_book_notes(self, book_id):
        """获取单本书的笔记和高亮"""
        url = f"https://weread.qq.com/web/review/list?bookId={book_id}&listType=1"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            notes = []
            if 'reviews' in data:
                for review in data['reviews']:
                    notes.append({
                        'review_id': review.get('reviewId'),
                        'book_id': book_id,
                        'chapter_name': review.get('chapterName'),
                        'abstract': review.get('abstract'),  # 高亮内容
                        'content': review.get('content'),  # 笔记内容
                        'create_time': datetime.fromtimestamp(review.get('createTime', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                        'update_time': datetime.fromtimestamp(review.get('updateTime', 0)).strftime('%Y-%m-%d %H:%M:%S')
                    })
            return notes
        except Exception as e:
            print(f"获取书籍 {book_id} 笔记失败: {e}")
            return []
    
    def get_reading_stats(self, book_id):
        """获取单本书的阅读统计"""
        url = f"https://weread.qq.com/web/read/format?bookId={book_id}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'read_time': data.get('readTime', 0),  # 阅读时长(秒)
                'read_pages': data.get('readPages', 0),  # 阅读页数
                'finish_pages': data.get('finishPages', 0),  # 完成页数
                'total_pages': data.get('totalPages', 0),  # 总页数
                'read_days': data.get('readDays', 0),  # 阅读天数
                'max_continuous_days': data.get('maxContinuousReadDays', 0)  # 最大连续阅读天数
            }
        except Exception as e:
            print(f"获取书籍 {book_id} 统计失败: {e}")
            return {}
