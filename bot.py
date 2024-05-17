from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import asyncio

from config import *
from db_manage import *
from kb import *
from api import *


bot = Bot(
    token=BOT_TOKEN,
    disable_web_page_preview=True,
    parse_mode='HTML'
)

dp = Dispatcher(bot, storage=MemoryStorage())

class SearchFilmForm(StatesGroup):
    query = State()

class AddChannelSponsorForm(StatesGroup):
    channel = State()

class SendMessagesForm(StatesGroup):
    message = State()

async def check_subs(user_id: int) -> bool:

    channels = get_all_channels_sponsors()

    if not channels:
        return True

    check_results = []

    for channel in channels:

        try:

            m = await bot.get_chat_member(chat_id=channel, user_id=user_id)

            if m.status != 'left':
                check_results.append(True)
            else:
                check_results.append(False)
        
        except Exception as e:

            print(e)
            check_results.append(False)
    
    print(check_results)
    
    return all(check_results)

async def get_subs_kb() -> types.InlineKeyboardMarkup:

    channels = get_all_channels_sponsors()

    kb = types.InlineKeyboardMarkup(row_width=5)

    for index, channel in enumerate(channels, 1):

        try:

            link = await bot.create_chat_invite_link(channel)

            kb.add(
                types.InlineKeyboardButton(
                    text=f'Ссылка {index}',
                    url=link.invite_link
                )
            )
        
        except Exception as e:
            print(e)
    
    me = await bot.get_me()

    kb.add(
        types.InlineKeyboardButton(
            text='✅ Проверить подписку',
            url=f'https://t.me/{me.username}?start'
        )
    )
    
    return kb

async def get_films_kb(data: dict) -> types.InlineKeyboardMarkup:

    kb = types.InlineKeyboardMarkup(row_width=5)

    for film in data['results']:

        kb.add(
            types.InlineKeyboardButton(
                text=f'{film["name"]} - {film["year"]}',
                callback_data=f'watch_film|{film["id"]}'
            )
        )
    
    return kb

async def get_remove_channel_sponsor_kb(channels: list) -> types.InlineKeyboardMarkup:

    kb = types.InlineKeyboardMarkup(row_width=5)

    for channel in channels:

        channel_data = await bot.get_chat(channel)
        kb.add(
            types.InlineKeyboardButton(
                text=channel_data.full_name,
                callback_data=f'remove_channel|{channel}'
            )
        )
    
    kb.add(cancel_btn)
    
    return kb

async def send_message(message: types.Message, users: list):

    good = []
    bad = []

    for user in users:

        try:

            await message.copy_to(user, reply_markup=message.reply_markup)
            good.append(user)

            await asyncio.sleep(0.1)
        
        except:

            bad.append(user)
    
    await message.answer(f'Рассылка завершена!\n\nУспешно: {len(good)}\nНеуспешно: {len(bad)}')     

@dp.message_handler(lambda message: message.from_user.id in ADMINS, commands=['admin'])
async def admin(message: types.Message):
    await message.answer('Админ панель', reply_markup=admin_kb)

@dp.callback_query_handler(lambda call: call.message.chat.id in ADMINS and 'admin_send_message' == call.data, state="*")
async def admin_send_message(call: types.CallbackQuery):

    await SendMessagesForm.message.set()
    await call.message.edit_text('Отправьте сообщение для рассылки', reply_markup=cancel_kb)

@dp.message_handler(state=SendMessagesForm.message, content_types=['any'])
async def admin_send_message_msg(message: types.Message, state: FSMContext):

    await state.finish()

    users = get_all_users()

    asyncio.ensure_future(send_message(message, users), loop=asyncio.get_event_loop())

    await message.answer('Рассылка началась!\n\nПо ее окончанию вы получите отчет')

@dp.callback_query_handler(lambda call: call.message.chat.id in ADMINS and 'admin_get_stats' == call.data, state="*")
async def admin_get_stats(call: types.CallbackQuery):

    users = get_all_users()
    await call.message.edit_text(f'<b>Количество пользователей в боте:</b> {len(users)}', reply_markup=admin_kb)

@dp.callback_query_handler(lambda call: 'cancel' == call.data, state="*")
async def cancel(call: types.CallbackQuery, state: FSMContext):

    await state.finish()
    await call.message.edit_text('Отменено')

@dp.callback_query_handler(lambda call: call.message.chat.id in ADMINS and 'admin_delete_channel' == call.data, state="*")
async def admin_delete_channel(call: types.CallbackQuery):

    channels = get_all_channels_sponsors()
    kb = await get_remove_channel_sponsor_kb(channels)

    await call.message.edit_text('Выберите канал для удаления', reply_markup=kb)

@dp.callback_query_handler(lambda call: call.message.chat.id in ADMINS and 'remove_channel' in call.data, state="*")
async def remove_channel(call: types.CallbackQuery):

    channel_id = int(call.data.split('|')[-1])
    remove_channel_sponsor(channel_id)

    await call.message.edit_text('Канал был удален!', reply_markup=admin_kb)

@dp.callback_query_handler(lambda call: call.message.chat.id in ADMINS and 'admin_add_channel' == call.data, state="*")
async def admin_add_channel(call: types.CallbackQuery):

    await AddChannelSponsorForm.channel.set()
    await call.message.edit_text('Отправьте id канала\n\nУбедитесь в том, что бот является администратором в канале', reply_markup=cancel_kb)

@dp.message_handler(state=AddChannelSponsorForm.channel)
async def admin_add_channel_msg(message: types.Message, state: FSMContext):

    channel_id = int(message.text)

    try:

        await bot.get_chat(channel_id)
        create_channel_sponsor(channel_id)

        await state.finish()

        await message.answer('Канал успешно добавлен!')
    
    except Exception as e:

        print(e)
        await message.answer('Ошибка при добавлении канала!\n\nСкорее всего, дело в том, что бот не является администратором в канале', reply_markup=cancel_kb)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):

    create_user_if_not_exist(message.from_user.id)

    sub_status = await check_subs(message.from_user.id)

    if not sub_status:

        kb = await get_subs_kb()
        await message.answer('<b>Чтобы воспользоваться ботом, необходимо подписаться на каналы</b>', reply_markup=kb)
        return
    
    await SearchFilmForm.query.set()
    await message.answer('<b>Отправьте название фильма / сериала / аниме</b>\n\nНе указывайте года, озвучки и т.д.\n\nПравильный пример: Ведьмак\nНеправильный пример: Ведьмак 2022')
    # await message.answer('<b>Нажми кнопку ниже, чтобы начать поиск фильмов / сериалов / аниме</b>', reply_markup=search_kb)
    # await message.answer('⤵️', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).add('🔍 Поиск'))

@dp.callback_query_handler(lambda call: 'start_search' == call.data, state="*")
async def start_search(call: types.CallbackQuery, state: FSMContext):

    await SearchFilmForm.query.set()
    await call.message.answer('<b>Отправьте название фильма / сериала / аниме</b>\n\nНе указывайте года, озвучки и т.д.\n\nПравильный пример: Ведьмак\nНеправильный пример: Ведьмак 2022')

@dp.callback_query_handler(lambda call: 'watch_film' in call.data, state="*")
async def watch_film(call: types.CallbackQuery, state: FSMContext):

    film_id = int(call.data.split('|')[-1])

    film_data = await get_film_for_view(film_id)

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text='Смотреть', url=film_data['view_link'])
    )
    # kb.add(
    #     types.InlineKeyboardButton(text='🔍 Искать еще', callback_data='start_search')
    # )
    kb.add(
        types.InlineKeyboardButton(text='🔥 Лучшие фильмы 🔥', url='https://t.me/KinoPlay_HD')
    )
    kb.add(
        types.InlineKeyboardButton(text='🔍 Поиск фильмов 🔍', url=f'https://t.me/{BOT_UNAME}')
    )

    try:
        await call.message.answer_photo(photo=film_data['poster'], caption=f'<b>{film_data["name"]} {film_data["year"]}</b>\n\n{film_data["description"]}\n\n{film_data["country"]}\n{film_data["genres"]}', reply_markup=kb)

    except:
        await call.message.answer(f'<b>{film_data["name"]} {film_data["year"]}</b>\n\n{film_data["description"]}\n\n{film_data["country"]}\n{film_data["genres"]}', reply_markup=kb)

@dp.message_handler(lambda message: '🔍 Поиск' == message.text, state='*')
async def reply_start_search(message: types.Message):

    sub_status = await check_subs(message.from_user.id)

    if not sub_status:

        kb = await get_subs_kb()
        await message.answer('<b>Чтобы воспользоваться ботом, необходимо подписаться на каналы</b>', reply_markup=kb)
        return

    await SearchFilmForm.query.set()
    await message.answer('<b>Отправьте название фильма / сериала / аниме</b>\n\nНе указывайте года, озвучки и т.д.\n\nПравильный пример: Ведьмак\nНеправильный пример: Ведьмак 2022')

@dp.message_handler(state=SearchFilmForm.query)
async def get_results(message: types.Message, state: FSMContext):

    await state.finish()

    sub_status = await check_subs(message.from_user.id)

    if not sub_status:

        kb = await get_subs_kb()
        await message.answer('<b>Чтобы воспользоваться ботом, необходимо подписаться на каналы</b>', reply_markup=kb)
        return

    results = await film_search(message.text)

    if results['results_count'] == 0:
        await message.answer('<b>По вашему запросу не найдено результатов!</b>\n\nПроверьте корректность введенных данных')
        return
    
    kb = await get_films_kb(results)

    await message.answer(f'<b>Результаты поиска по ключевому слову</b>: {message.text}', reply_markup=kb)

@dp.message_handler()
async def simple_text_film_handler(message: types.Message):

    sub_status = await check_subs(message.from_user.id)

    if not sub_status:

        kb = await get_subs_kb()
        await message.answer('<b>Чтобы воспользоваться ботом, необходимо подписаться на каналы</b>', reply_markup=kb)
        return

    results = await film_search(message.text)

    if results['results_count'] == 0:
        await message.answer('<b>По вашему запросу не найдено результатов!</b>\n\nПроверьте корректность введенных данных')
        return
    
    kb = await get_films_kb(results)

    await message.answer(f'<b>Результаты поиска по ключевому слову</b>: {message.text}', reply_markup=kb)
  

@dp.inline_handler(lambda query: True)
async def inline_film_requests(query: types.InlineQuery):

    results = await film_search(query.query)

    inline_answer = []

    for film in results['results']:

        film_data = await get_film_for_view(film['id'])

        text = f'<a href="{film_data["poster"]}">🔥🎥</a> <b>{film_data["name"]} ({film_data["year"]})</b>\n\n{film_data["description"]}\n\n{film_data["country"]}\n{film_data["genres"]}'

        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(text='Смотреть', url=film_data['view_link'])
        )

        kb.add(
            types.InlineKeyboardButton(text='🔥 Лучшие фильмы 🔥', url='https://t.me/KinoPlay_HD')
        )

        kb.add(
            types.InlineKeyboardButton(text='🔍 Поиск фильмов 🔍', url=f'https://t.me/{BOT_UNAME}')
        )

        answer = types.InlineQueryResultArticle(
            id=f'{film["id"]}',
            title=f'{film_data["name"]} {film_data["year"]}',
            input_message_content=types.InputMessageContent(message_text=text, parse_mode='html'),
            reply_markup=kb,
            thumb_url=film_data["poster"]
        )

        inline_answer.append(answer)

    await bot.answer_inline_query(query.id, inline_answer, cache_time=240, is_personal=True)
    

if __name__ == "__main__":
    executor.start_polling(dp)