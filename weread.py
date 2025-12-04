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
            if 'books' in data:
                for idx, book in enumerate(data['books']):
                    book_info = book.get('book', {})
                    
                    # 调试：打印原始数据结构（首次运行时可取消注释）
                    # if idx == 0:
                    #     print(f"原始数据结构: {json.dumps(book_info, ensure_ascii=False, indent=2)}")
                    
                    # 跳过无效书籍（没有bookId或title）
                    book_id = book_info.get('bookId') or book.get('bookId')
                    title = book_info.get('title')
                    
                    if not book_id or not title:
                        print(f"跳过无效书籍: ID={book_id}, 标题={title}")
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
            
            print(f"有效书籍数量: {len(books)}/{len(data.get('books', []))}")
            return books
        except Exception as e:
            print(f"获取书架数据失败: {e}")
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
                    # 跳过无效笔记
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
            print(f"获取书籍 {book_id} 笔记失败: {e}")
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
        except Exception as e:
            # 对于非书籍内容（如公众号），这个接口可能返回404，这是正常的
            if '404' in str(e):
                return {
                    'read_time': 0, 'read_pages': 0, 'finish_pages': 0,
                    'total_pages': 0, 'read_days': 0, 'max_continuous_days': 0
                }
            print(f"获取书籍 {book_id} 统计失败: {e}")
            return {}
