from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✱ Створити завдання",
                    callback_data="menu:create"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✱ Мої завдання",
                    callback_data="menu:tasks"
                ),
                InlineKeyboardButton(
                    text="✱ На сьогодні",
                    callback_data="menu:today"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✱ Статистика",
                    callback_data="menu:stats"
                ),
                InlineKeyboardButton(
                    text="⚒︎ Налаштування",
                    callback_data="menu:settings"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✱ Допомога",
                    callback_data="menu:help"
                )
            ]
        ]
    )


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="← Головне меню",
                    callback_data="menu:home"
                )
            ]
        ]
    )
