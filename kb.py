from aiogram import types


search_kb = types.InlineKeyboardMarkup()
search_kb.add(
    types.InlineKeyboardButton(
        text='🔍 Поиск',
        callback_data='start_search'
    )
)

cancel_btn = types.InlineKeyboardButton(text='Отменить', callback_data='cancel')
cancel_kb = types.InlineKeyboardMarkup()
cancel_kb.add(cancel_btn)

admin_kb = types.InlineKeyboardMarkup(row_width=5)
admin_kb.add(
    types.InlineKeyboardButton(
        text='Статистика',
        callback_data='admin_get_stats'
    )
)
admin_kb.add(
    types.InlineKeyboardButton(
        text='Добавить канал',
        callback_data='admin_add_channel'
    )
)
admin_kb.add(
    types.InlineKeyboardButton(
        text='Удалить канал',
        callback_data='admin_delete_channel'
    )
)
admin_kb.add(
    types.InlineKeyboardButton(
        text='Рассылка',
        callback_data='admin_send_message'
    )
)