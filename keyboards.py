from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Моя библиотека"), KeyboardButton(text="🔍 Поиск в каталоге")],
            [KeyboardButton(text="🔎 Поиск в моей библиотеке"), KeyboardButton(text="➕ Добавить книгу")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="💬 Мои цитаты")],
            [KeyboardButton(text="📁 Мои полки")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_add_book_method_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Ввести вручную")],
            [KeyboardButton(text="📷 Сканировать ISBN (штрихкод)")],
            [KeyboardButton(text="🔍 Найти в каталоге")],
            [KeyboardButton(text="↩️ Назад к меню")]
        ],
        resize_keyboard=True
    )

def get_confirmation_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, всё верно"), KeyboardButton(text="❌ Нет, исправить")],
            [KeyboardButton(text="↩️ Назад к меню")]
        ],
        resize_keyboard=True
    )

def get_library_filter_keyboard(current_filter: str = 'all') -> InlineKeyboardMarkup:
    filters = [
        ("📚 Все", "all"),
        ("📌 Хочу прочитать", "want_to_read"),
        ("📖 Читаю сейчас", "reading"),
        ("✅ Прочитано", "read")
    ]
    
    buttons = []
    for text, value in filters:
        prefix = "✓ " if value == current_filter else ""
        buttons.append(InlineKeyboardButton(
            text=f"{prefix}{text}",
            callback_data=f"filter_lib:{value}"
        ))
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def get_book_actions_keyboard(book_id: int, in_library: bool = False, 
                              status: str = None, user_book_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    
    if not in_library:
        buttons.append([InlineKeyboardButton(
            text="📥 Добавить в библиотеку",
            callback_data=f"add_to_lib:{book_id}"
        )])
    else:
        if status == 'want_to_read':
            buttons.append([InlineKeyboardButton(
                text="📖 Начать читать",
                callback_data=f"start_read:{book_id}"
            )])
        elif status == 'reading':
            buttons.append([
                InlineKeyboardButton(
                    text="✅ Завершить",
                    callback_data=f"finish_read:{book_id}"
                ),
                InlineKeyboardButton(
                    text="📝 Заметка",
                    callback_data=f"add_note:{book_id}"
                )
            ])
        elif status == 'read':
            buttons.append([
                InlineKeyboardButton(
                    text="🔄 Перечитать",
                    callback_data=f"reread:{book_id}"
                ),
                InlineKeyboardButton(
                    text="⭐ Оценить",
                    callback_data=f"rate_book:{book_id}"
                )
            ])
        
        # Кнопка удаления доступна для ВСЕХ статусов
        buttons.append([InlineKeyboardButton(
            text="🗑️ Удалить из библиотеки",
            callback_data=f"remove_from_lib:{book_id}"
        )])
    
    buttons.append([
        InlineKeyboardButton(
            text="💬 Цитата",
            callback_data=f"add_quote:{book_id}"
        ),
        InlineKeyboardButton(
            text="📁 На полку",
            callback_data=f"add_to_shelf_select:{book_id}"
        )
    ])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 К списку",
        callback_data="back_to_library"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_library_books_keyboard(books: List[Dict[str, Any]], page: int = 0, 
                               total_pages: int = 1) -> InlineKeyboardMarkup:
    buttons = []
    
    for book in books:
        status_icons = {
            'want_to_read': '📌',
            'reading': '📖',
            'read': '✅'
        }
        icon = status_icons.get(book.get('status'), '📕')
        
        title = book['title'][:25] + "..." if len(book['title']) > 25 else book['title']
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {title} — {book['author']}",
            callback_data=f"view_lib_book:{book['book_id']}"
        )])
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"lib_page:{page-1}"
        ))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️ Далее",
            callback_data=f"lib_page:{page+1}"
        ))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_search_results_keyboard(books: List[Dict[str, Any]], query: str = "", 
                                page: int = 0) -> InlineKeyboardMarkup:
    buttons = []
    
    for book in books:
        title = book['title'][:30] + "..." if len(book['title']) > 30 else book['title']
        buttons.append([InlineKeyboardButton(
            text=f"📕 {title} — {book['author']}",
            callback_data=f"view_book:{book['book_id']}"
        )])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"search_page:{page-1}:{query}"
        ))
    if len(books) == 10:
        nav_row.append(InlineKeyboardButton(
            text="➡️ Далее",
            callback_data=f"search_page:{page+1}:{query}"
        ))
    if nav_row:
        buttons.append(nav_row)
    
    buttons.append([
        InlineKeyboardButton(
            text="🔍 Новый поиск",
            callback_data="new_search"
        ),
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rating_keyboard(book_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for i in range(1, 6):
        buttons.append([InlineKeyboardButton(
            text="⭐" * i,
            callback_data=f"submit_rating:{book_id}:{i}"
        )])
    buttons.append([InlineKeyboardButton(
        text="⏭️ Пропустить",
        callback_data=f"skip_rating:{book_id}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_stats")],
            [InlineKeyboardButton(text="🏆 Мои достижения", callback_data="show_achievements")],
            [InlineKeyboardButton(text="📅 По месяцам", callback_data="stats_by_month")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
    )

def get_achievements_keyboard(achievements: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    achievement_names = {
        'first_book': '📖 Первая книга',
        'five_books': '📚 5 прочитанных книг',
        'ten_books': '🎓 10 прочитанных книг',
        'twenty_books': '🏛️ 20 прочитанных книг',
        'hundred_pages': '📄 100 страниц',
        'thousand_pages': '📚 1000 страниц',
        'five_thousand_pages': '📚📚 5000 страниц',
        'perfect_rater': '⭐ Идеальный критик',
        'week_streak': '🔥 Неделя чтения',
        'month_streak': '🔥🔥 Месяц чтения'
    }
    
    buttons = []
    for ach in achievements:
        name = achievement_names.get(ach['achievement_type'], ach['achievement_type'])
        unlocked = ach['unlocked_at'][:10] if ach['unlocked_at'] else ''
        buttons.append([InlineKeyboardButton(
            text=f"{name} ({unlocked})",
            callback_data=f"ach_info:{ach['achievement_type']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 К статистике", callback_data="back_to_stats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Очистить старые данные", callback_data="cleanup_data")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
    )

def get_quote_actions_keyboard(quote_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🗑️ Удалить цитату",
                callback_data=f"delete_quote:{quote_id}"
            )]
        ]
    )

def get_quotes_menu_keyboard(book_id: int = None) -> InlineKeyboardMarkup:
    buttons = []
    if book_id:
        buttons.append([InlineKeyboardButton(
            text="💬 Добавить цитату к этой книге",
            callback_data=f"add_quote:{book_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text="📖 Все цитаты",
        callback_data="all_quotes"
    )])
    buttons.append([InlineKeyboardButton(
        text="🎲 Случайная цитата",
        callback_data="random_quote"
    )])
    buttons.append([InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_shelves_menu_keyboard(shelves: List[Dict[str, Any]] = None) -> InlineKeyboardMarkup:
    buttons = []
    
    if shelves:
        for shelf in shelves:
            buttons.append([InlineKeyboardButton(
                text=f"📁 {shelf['name']} ({shelf['book_count']} книг)",
                callback_data=f"view_shelf:{shelf['shelf_id']}"
            )])
    
    buttons.append([InlineKeyboardButton(
        text="➕ Создать полку",
        callback_data="create_shelf"
    )])
    buttons.append([InlineKeyboardButton(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_add_to_shelf_keyboard(shelves: List[Dict[str, Any]], book_id: int) -> InlineKeyboardMarkup:
    buttons = []
    
    for shelf in shelves:
        buttons.append([InlineKeyboardButton(
            text=f"📁 {shelf['name']}",
            callback_data=f"add_to_shelf:{shelf['shelf_id']}:{book_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="➕ Создать новую полку",
        callback_data=f"create_shelf_for_book:{book_id}"
    )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"view_book:{book_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard(action: str, item_id: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да",
                    callback_data=f"confirm:{action}:{item_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"cancel:{action}"
                )
            ]
        ]
    )