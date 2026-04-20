import sqlite3
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='library_bot.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection_with_retry(self, max_retries=5, delay=0.1):
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=10.0)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.row_factory = sqlite3.Row
                return conn
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(delay * (2 ** attempt))
                    continue
                raise e
        raise sqlite3.OperationalError("Не удается получить доступ к базе данных")

    def init_db(self):
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notifications_enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    year INTEGER,
                    isbn TEXT UNIQUE,
                    cover_file_id TEXT,
                    description TEXT,
                    page_count INTEGER,
                    added_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by_user_id) REFERENCES users(user_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'want_to_read',
                    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                    note TEXT,
                    started_at DATE,
                    finished_at DATE,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (book_id) REFERENCES books(book_id),
                    UNIQUE(user_id, book_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotes (
                    quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    page INTEGER,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (book_id) REFERENCES books(book_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shelves (
                    shelf_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    color TEXT DEFAULT '#808080',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, name)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shelf_books (
                    shelf_id INTEGER NOT NULL,
                    user_book_id INTEGER NOT NULL,
                    FOREIGN KEY (shelf_id) REFERENCES shelves(shelf_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_book_id) REFERENCES user_books(id) ON DELETE CASCADE,
                    PRIMARY KEY (shelf_id, user_book_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL,
                    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, achievement_type)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("База данных инициализирована")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {e}")
            raise

    async def get_or_create_user(self, user_id: int, username: str = None, first_name: str = None) -> Dict[str, Any]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = dict(cursor.fetchone())
            
            conn.commit()
            conn.close()
            return user
            
        except Exception as e:
            logger.error(f"Ошибка получения/создания пользователя {user_id}: {e}")
            return None

    async def update_user_settings(self, user_id: int, **kwargs) -> bool:
        try:
            if not kwargs:
                return True
                
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            set_clause = ", ".join(f"{k} = ?" for k in kwargs.keys())
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления настроек пользователя {user_id}: {e}")
            return False

    async def add_book(self, title: str, author: str, added_by: int, 
                       year: int = None, isbn: str = None, 
                       cover_file_id: str = None, description: str = None,
                       page_count: int = None) -> Optional[int]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            if isbn:
                cursor.execute('SELECT book_id FROM books WHERE isbn = ?', (isbn,))
                existing = cursor.fetchone()
                if existing:
                    conn.close()
                    return existing['book_id']
            
            cursor.execute('''
                INSERT INTO books 
                (title, author, year, isbn, cover_file_id, description, page_count, added_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, year, isbn, cover_file_id, description, page_count, added_by))
           
            book_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Книга '{title}' добавлена в каталог (ID: {book_id})")
            return book_id
            
        except Exception as e:
            logger.error(f"Ошибка добавления книги: {e}")
            return None

    async def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
            book = cursor.fetchone()
            conn.close()
            
            return dict(book) if book else None
            
        except Exception as e:
            logger.error(f"Ошибка получения книги {book_id}: {e}")
            return None

    async def search_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            search_pattern = f"%{query}%"
            cursor.execute('''
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ?
                ORDER BY title
                LIMIT ?
            ''', (search_pattern, search_pattern, limit))
            
            books = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return books
            
        except Exception as e:
            logger.error(f"Ошибка поиска книг: {e}")
            return []

    async def add_to_library(self, user_id: int, book_id: int, status: str = 'want_to_read') -> bool:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO user_books (user_id, book_id, status)
                VALUES (?, ?, ?)
            ''', (user_id, book_id, status))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            if success:
                logger.info(f"Книга {book_id} добавлена в библиотеку пользователя {user_id}")
                await self._check_achievements(user_id)
                
            return success
            
        except Exception as e:
            logger.error(f"Ошибка добавления книги в библиотеку: {e}")
            return False

    async def update_reading_status(self, user_id: int, book_id: int, 
                                    status: str, rating: int = None, 
                                    note: str = None) -> bool:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            updates = ["status = ?"]
            params = [status]
            
            if status == 'reading':
                updates.append("started_at = ?")
                params.append(datetime.now().date().isoformat())
            elif status == 'read':
                updates.append("finished_at = ?")
                params.append(datetime.now().date().isoformat())
                
            if rating is not None:
                updates.append("rating = ?")
                params.append(rating)
            if note is not None:
                updates.append("note = ?")
                params.append(note)
                
            params.extend([user_id, book_id])
            
            cursor.execute(f'''
                UPDATE user_books 
                SET {', '.join(updates)}
                WHERE user_id = ? AND book_id = ?
            ''', params)
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()

            if success and status == 'read':
                await self._check_achievements(user_id)
                    
            return success
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса чтения: {e}")
            return False

    async def get_user_library(self, user_id: int, status: str = None, 
                               limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    b.*, 
                    ub.status, ub.rating, ub.note, 
                    ub.started_at, ub.finished_at, ub.added_at,
                    ub.id as user_book_id
                FROM user_books ub
                JOIN books b ON ub.book_id = b.book_id
                WHERE ub.user_id = ?
            '''
            params = [user_id]
            
            if status:
                query += " AND ub.status = ?"
                params.append(status)
                
            query += " ORDER BY ub.added_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            books = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return books
            
        except Exception as e:
            logger.error(f"Ошибка получения библиотеки пользователя {user_id}: {e}")
            return []

    async def remove_from_library(self, user_id: int, book_id: int) -> bool:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM user_books WHERE user_id = ? AND book_id = ?', (user_id, book_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка удаления книги из библиотеки: {e}")
            return False

    async def get_reading_stats(self, user_id: int) -> Dict[str, Any]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM user_books
                WHERE user_id = ?
                GROUP BY status
            ''', (user_id,))
            by_status = {row['status']: row['count'] for row in cursor.fetchall()}
            
            year_start = datetime.now().replace(month=1, day=1).date().isoformat()
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM user_books
                WHERE user_id = ? AND status = 'read' AND finished_at >= ?
            ''', (user_id, year_start))
            read_this_year = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT 
                    b.author, 
                    COUNT(*) as count, 
                    AVG(ub.rating) as avg_rating
                FROM user_books ub
                JOIN books b ON ub.book_id = b.book_id
                WHERE ub.user_id = ? AND ub.status = 'read' AND ub.rating IS NOT NULL
                GROUP BY b.author
                ORDER BY count DESC, avg_rating DESC
                LIMIT 1
            ''', (user_id,))
            fav = cursor.fetchone()
            favorite_author = dict(fav) if fav else None
            
            cursor.execute('''
                SELECT COALESCE(SUM(b.page_count), 0) as total_pages
                FROM user_books ub
                JOIN books b ON ub.book_id = b.book_id
                WHERE ub.user_id = ? AND ub.status = 'read'
            ''', (user_id,))
            total_pages = cursor.fetchone()['total_pages']
            
            cursor.execute('''
                SELECT AVG(rating) as avg_rating, COUNT(rating) as rated_count
                FROM user_books
                WHERE user_id = ? AND rating IS NOT NULL
            ''', (user_id,))
            rating_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT finished_at FROM user_books
                WHERE user_id = ? AND status = 'read' AND finished_at IS NOT NULL
                ORDER BY finished_at DESC
            ''', (user_id,))
            read_dates = [row['finished_at'] for row in cursor.fetchall()]
            streak = self._calculate_streak(read_dates)
            
            conn.close()
            
            return {
                'by_status': by_status,
                'read_this_year': read_this_year,
                'favorite_author': favorite_author,
                'total_pages': total_pages,
                'avg_rating': round(rating_stats['avg_rating'], 1) if rating_stats['avg_rating'] else 0,
                'rated_count': rating_stats['rated_count'],
                'current_streak': streak
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
            return {}

    def _calculate_streak(self, dates: List[str]) -> int:
        if not dates:
            return 0
            
        from datetime import datetime, timedelta
        
        date_objects = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in dates], reverse=True)
        
        streak = 0
        current = datetime.now().date()
        
        if date_objects[0] < current - timedelta(days=1):
            return 0
            
        for d in date_objects:
            expected = current - timedelta(days=streak)
            if d == expected:
                streak += 1
            else:
                break
                
        return streak

    async def add_quote(self, user_id: int, book_id: int, text: str, page: int = None) -> Optional[int]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quotes (user_id, book_id, text, page)
                VALUES (?, ?, ?, ?)
            ''', (user_id, book_id, text, page))
            
            quote_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return quote_id
            
        except Exception as e:
            logger.error(f"Ошибка добавления цитаты: {e}")
            return None

    async def get_user_quotes(self, user_id: int, book_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            query = '''
                SELECT q.*, b.title, b.author
                FROM quotes q
                JOIN books b ON q.book_id = b.book_id
                WHERE q.user_id = ?
            '''
            params = [user_id]
            
            if book_id:
                query += " AND q.book_id = ?"
                params.append(book_id)
                
            query += " ORDER BY q.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            quotes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return quotes
            
        except Exception as e:
            logger.error(f"Ошибка получения цитат пользователя {user_id}: {e}")
            return []

    async def delete_quote(self, user_id: int, quote_id: int) -> bool:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM quotes WHERE quote_id = ? AND user_id = ?', (quote_id, user_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка удаления цитаты: {e}")
            return False

    async def create_shelf(self, user_id: int, name: str, color: str = '#808080') -> Optional[int]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO shelves (user_id, name, color)
                VALUES (?, ?, ?)
            ''', (user_id, name, color))
            
            shelf_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return shelf_id
            
        except sqlite3.IntegrityError:
            return None
        except Exception as e:
            logger.error(f"Ошибка создания полки: {e}")
            return None

    async def get_user_shelves(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    s.*,
                    COUNT(sb.user_book_id) as book_count
                FROM shelves s
                LEFT JOIN shelf_books sb ON s.shelf_id = sb.shelf_id
                WHERE s.user_id = ?
                GROUP BY s.shelf_id
                ORDER BY s.name
            ''', (user_id,))
            
            shelves = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return shelves
            
        except Exception as e:
            logger.error(f"Ошибка получения полок пользователя {user_id}: {e}")
            return []

    async def add_book_to_shelf(self, user_id: int, shelf_id: int, user_book_id: int) -> bool:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('SELECT shelf_id FROM shelves WHERE shelf_id = ? AND user_id = ?', (shelf_id, user_id))
            
            if not cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute('''
                INSERT OR IGNORE INTO shelf_books (shelf_id, user_book_id)
                VALUES (?, ?)
            ''', (shelf_id, user_book_id))
            
            conn.commit()
            success = cursor.rowcount > 0
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Ошибка добавления книги на полку: {e}")
            return False

    async def _check_achievements(self, user_id: int, conn: sqlite3.Connection = None) -> None:
        should_close = False
        if conn is None:
            conn = self.get_connection_with_retry()
            should_close = True
            
        try:
            cursor = conn.cursor()
            stats = await self.get_reading_stats(user_id)
            
            achievements = {
                'first_book': stats['by_status'].get('read', 0) >= 1,
                'five_books': stats['by_status'].get('read', 0) >= 5,
                'ten_books': stats['by_status'].get('read', 0) >= 10,
                'twenty_books': stats['by_status'].get('read', 0) >= 20,
                'hundred_pages': stats['total_pages'] >= 100,
                'thousand_pages': stats['total_pages'] >= 1000,
                'five_thousand_pages': stats['total_pages'] >= 5000,
                'perfect_rater': stats['rated_count'] >= 10 and stats['avg_rating'] >= 4.5,
                'week_streak': stats['current_streak'] >= 7,
                'month_streak': stats['current_streak'] >= 30
            }
            
            for ach_type, achieved in achievements.items():
                if achieved:
                    cursor.execute('''
                        INSERT OR IGNORE INTO achievements (user_id, achievement_type)
                        VALUES (?, ?)
                    ''', (user_id, ach_type))
                    
            conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка проверки достижений пользователя {user_id}: {e}")
        finally:
            if should_close:
                conn.close()

    async def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT achievement_type, unlocked_at
                FROM achievements
                WHERE user_id = ?
                ORDER BY unlocked_at DESC
            ''', (user_id,))
            
            achievements = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return achievements
            
        except Exception as e:
            logger.error(f"Ошибка получения достижений пользователя {user_id}: {e}")
            return []

    async def cleanup_old_data(self, user_id: int = None) -> Dict[str, int]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            cleaned = {'quotes': 0, 'shelves': 0}
            
            cursor.execute('''
                DELETE FROM quotes 
                WHERE book_id NOT IN (SELECT book_id FROM books)
            ''')
            cleaned['quotes'] = cursor.rowcount
            
            if user_id:
                cursor.execute('''
                    DELETE FROM shelves 
                    WHERE user_id = ? 
                    AND shelf_id NOT IN (
                        SELECT DISTINCT shelf_id FROM shelf_books
                    )
                ''', (user_id,))
                cleaned['shelves'] = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Ошибка очистки данных: {e}")
            return {'quotes': 0, 'shelves': 0}

    async def export_user_library(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    b.title,
                    b.author,
                    b.year,
                    b.isbn,
                    b.page_count,
                    ub.status,
                    ub.rating,
                    ub.note,
                    ub.started_at,
                    ub.finished_at,
                    ub.added_at
                FROM user_books ub
                JOIN books b ON ub.book_id = b.book_id
                WHERE ub.user_id = ?
                ORDER BY ub.added_at DESC
            ''', (user_id,))
            
            library = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return library
            
        except Exception as e:
            logger.error(f"Ошибка экспорта библиотеки пользователя {user_id}: {e}")
            return []


db = Database()