from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math


OUT = Path(__file__).parent
W, H = 1080, 2400

GREEN = "#007A3D"
GREEN_DARK = "#005C2F"
GREEN_LIGHT = "#E7F5ED"
GREEN_PALE = "#F1F9F5"
RED = "#D9363E"
RED_LIGHT = "#FDECEE"
TEXT = "#19221E"
MUTED = "#6F7C75"
LINE = "#E2E8E5"
BG = "#F5F7F6"
WHITE = "#FFFFFF"
AMBER = "#C37A00"

FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEMI = r"C:\Windows\Fonts\seguisb.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def font(size, weight="regular"):
    path = {"regular": FONT_REG, "semi": FONT_SEMI, "bold": FONT_BOLD}[weight]
    return ImageFont.truetype(path, size)


F = {
    "xs": font(28),
    "sm": font(32),
    "body": font(38),
    "body_semi": font(38, "semi"),
    "h3": font(44, "semi"),
    "h2": font(54, "bold"),
    "h1": font(72, "bold"),
    "amount": font(86, "bold"),
}


def canvas():
    return Image.new("RGB", (W, H), BG)


def rr(draw, box, radius=30, fill=WHITE, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, style="body", fill=TEXT, anchor=None):
    draw.text(xy, value, font=F[style], fill=fill, anchor=anchor)


def status_bar(draw):
    text(draw, (54, 40), "12:30", "sm", TEXT)
    text(draw, (1025, 40), "4G   87%", "xs", TEXT, "ra")


def app_bar(draw, title, subtitle=None, back=False, action=None):
    y = 98
    if back:
        text(draw, (52, y + 46), "‹", "h2", TEXT, "lm")
    text(draw, (120 if back else 52, y + 20), title, "h3")
    if subtitle:
        text(draw, (120 if back else 52, y + 82), subtitle, "xs", MUTED)
    if action:
        text(draw, (1028, y + 48), action, "sm", GREEN, "rm")
    draw.line((40, 215, 1040, 215), fill=LINE, width=2)


def logo(draw, x=52, y=110):
    rr(draw, (x, y, x + 70, y + 70), 18, GREEN)
    text(draw, (x + 35, y + 33), "Б", "h3", WHITE, "mm")


def bottom_nav(draw, active):
    top = 2220
    draw.rectangle((0, top, W, H), fill=WHITE)
    draw.line((0, top, W, top), fill=LINE, width=2)
    items = ["Портфель", "Рынок", "Заявки", "Сервисы", "Профиль"]
    xs = [105, 320, 540, 755, 970]
    for label, x in zip(items, xs):
        color = GREEN if label == active else MUTED
        cy = top + 48
        if label == "Портфель":
            draw.rounded_rectangle((x - 24, cy - 18, x + 24, cy + 22), 6, outline=color, width=5)
            draw.line((x - 10, cy - 18, x - 10, cy - 28, x + 10, cy - 28, x + 10, cy - 18), fill=color, width=5)
        elif label == "Рынок":
            for j, height in enumerate((20, 38, 56)):
                xx = x - 30 + j * 28
                draw.rounded_rectangle((xx, cy + 25 - height, xx + 14, cy + 25), 4, fill=color)
        elif label == "Заявки":
            for offset in (-18, 0, 18):
                draw.line((x - 28, cy + offset, x + 28, cy + offset), fill=color, width=5)
        elif label == "Сервисы":
            draw.polygon([(x, cy - 30), (x + 30, cy), (x, cy + 30), (x - 30, cy)], outline=color)
            draw.ellipse((x - 5, cy - 5, x + 5, cy + 5), fill=color)
        else:
            draw.ellipse((x - 18, cy - 28, x + 18, cy + 8), outline=color, width=5)
            draw.arc((x - 34, cy + 5, x + 34, cy + 55), 190, 350, fill=color, width=5)
        text(draw, (x, top + 115), label, "xs", color, "ma")


def section(draw, y, title, action=None):
    text(draw, (52, y), title, "h3")
    if action:
        text(draw, (1028, y + 4), action, "sm", GREEN, "ra")


def pill(draw, x, y, label, active=False, width=None):
    width = width or max(130, 45 + len(label) * 20)
    fill = GREEN if active else WHITE
    outline = GREEN if active else LINE
    rr(draw, (x, y, x + width, y + 72), 36, fill, outline)
    text(draw, (x + width / 2, y + 35), label, "xs", WHITE if active else TEXT, "mm")
    return x + width + 18


def button(draw, x, y, w, label, primary=True, danger=False):
    fill = RED if danger else (GREEN if primary else WHITE)
    outline = fill if primary or danger else GREEN
    rr(draw, (x, y, x + w, y + 108), 28, fill, outline, 3)
    text(draw, (x + w / 2, y + 52), label, "body_semi", WHITE if primary or danger else GREEN, "mm")


def balance_card(draw, y=270):
    rr(draw, (40, y, 1040, y + 390), 42, GREEN)
    text(draw, (78, y + 55), "Стоимость портфеля", "sm", "#D9F1E4")
    text(draw, (78, y + 125), "28 347,39 BYN", "amount", WHITE)
    text(draw, (78, y + 235), "+1 256,72 BYN  •  +4,64%", "body_semi", "#CBF4DB")
    pts = [(660, y + 285), (715, y + 245), (760, y + 262), (815, y + 188),
           (865, y + 220), (915, y + 145), (990, y + 105)]
    draw.line(pts, fill="#8EE0B2", width=9, joint="curve")


def quick_actions(draw, y):
    labels = ["Пополнить", "Вывести", "История", "Аналитика"]
    for i, label in enumerate(labels):
        x = 40 + i * 252
        rr(draw, (x, y, x + 230, y + 180), 28, GREEN_PALE)
        cx, cy = x + 115, y + 60
        if label == "Пополнить":
            draw.line((cx - 22, cy, cx + 22, cy), fill=GREEN, width=6)
            draw.line((cx, cy - 22, cx, cy + 22), fill=GREEN, width=6)
        elif label == "Вывести":
            draw.line((cx - 24, cy + 20, cx + 24, cy - 28), fill=GREEN, width=6)
            draw.line((cx + 5, cy - 28, cx + 24, cy - 28, cx + 24, cy - 9), fill=GREEN, width=6)
        elif label == "История":
            for offset in (-16, 0, 16):
                draw.line((cx - 24, cy + offset, cx + 24, cy + offset), fill=GREEN, width=5)
        else:
            draw.arc((cx - 28, cy - 28, cx + 28, cy + 28), 15, 315, fill=GREEN, width=6)
            draw.line((cx, cy, cx + 18, cy - 16), fill=GREEN, width=5)
        text(draw, (x + 115, y + 130), label, "xs", TEXT, "ma")


def asset_row(draw, y, name, ticker, amount, change, positive=True, color=GREEN):
    rr(draw, (40, y, 1040, y + 165), 26, WHITE, LINE)
    rr(draw, (65, y + 35, 155, y + 125), 24, color)
    text(draw, (110, y + 77), name[0], "h3", WHITE, "mm")
    text(draw, (185, y + 34), name, "body_semi")
    text(draw, (185, y + 92), ticker, "xs", MUTED)
    text(draw, (1005, y + 35), amount, "body_semi", TEXT, "ra")
    text(draw, (1005, y + 94), change, "sm", GREEN if positive else RED, "ra")


def save(img, name):
    img.save(OUT / name, quality=95)


def screen_login():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    logo(d, 505, 190)
    text(d, (540, 315), "Беларусбанк", "h2", GREEN_DARK, "ma")
    text(d, (540, 390), "Инвестиции", "h1", TEXT, "ma")
    text(d, (540, 500), "Управляйте портфелем и совершайте сделки", "sm", MUTED, "ma")
    text(d, (70, 690), "Логин", "sm", MUTED)
    rr(d, (55, 745, 1025, 865), 28, WHITE, LINE, 3)
    text(d, (95, 785), "Введите логин", "body", MUTED)
    text(d, (70, 925), "Пароль", "sm", MUTED)
    rr(d, (55, 980, 1025, 1100), 28, WHITE, LINE, 3)
    text(d, (95, 1020), "••••••••", "body", TEXT)
    button(d, 55, 1190, 970, "Войти")
    text(d, (540, 1350), "Восстановить пароль", "body_semi", GREEN, "ma")
    draw_y = 1515
    d.line((55, draw_y, 420, draw_y), fill=LINE, width=2)
    text(d, (540, draw_y), "или", "sm", MUTED, "mm")
    d.line((660, draw_y, 1025, draw_y), fill=LINE, width=2)
    button(d, 55, 1595, 970, "Стать клиентом", primary=False)
    rr(d, (55, 1810, 1025, 2010), 28, GREEN_PALE)
    text(d, (90, 1850), "Демо-режим", "body_semi", GREEN_DARK)
    text(d, (90, 1912), "Для просмотра макета используйте любые данные", "sm", MUTED)
    save(img, "01-вход.png")


def screen_home():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    logo(d)
    text(d, (145, 120), "Беларусбанк Инвестиции", "h3", GREEN_DARK)
    text(d, (1028, 145), "◯", "h3", TEXT, "rm")
    balance_card(d, 250)
    quick_actions(d, 680)
    section(d, 920, "Позиции", "Все")
    asset_row(d, 995, "Беларусбанк", "BRBB • БВФБ", "8 884,20 BYN", "+6,12%")
    asset_row(d, 1180, "Беларусь ОФЗ", "BYGOV-27", "6 240,00 BYN", "+2,08%", True, "#2B62A3")
    asset_row(d, 1365, "Apple Inc.", "AAPL • NASDAQ", "5 732,00 BYN", "+3,56%", True, "#232A27")
    section(d, 1585, "Ближайшие события", "Календарь")
    rr(d, (40, 1660, 1040, 1885), 28, WHITE, LINE)
    text(d, (75, 1700), "18 июля", "sm", GREEN)
    text(d, (75, 1762), "Купон по облигациям BYGOV-27", "body_semi")
    text(d, (75, 1825), "Ожидаемая выплата: 124,80 BYN", "sm", MUTED)
    bottom_nav(d, "Портфель")
    save(img, "02-главная.png")


def screen_portfolio():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Портфель", "Брокерский счёт BY12 •••• 4582", action="Отчёт")
    text(d, (52, 285), "28 347,39 BYN", "amount")
    text(d, (52, 390), "+1 256,72 BYN  •  +4,64% за всё время", "body_semi", GREEN)
    x = 52
    for label in ["Активы", "Отрасли", "Валюты"]:
        x = pill(d, x, 490, label, label == "Активы")
    cx, cy, r = 300, 840, 210
    d.arc((cx-r, cy-r, cx+r, cy+r), 0, 215, fill=GREEN, width=65)
    d.arc((cx-r, cy-r, cx+r, cy+r), 220, 305, fill="#2B62A3", width=65)
    d.arc((cx-r, cy-r, cx+r, cy+r), 310, 355, fill="#E0A22E", width=65)
    text(d, (cx, cy - 22), "28 347", "h2", TEXT, "mm")
    text(d, (cx, cy + 45), "BYN", "sm", MUTED, "mm")
    legends = [("Акции", "56%", GREEN), ("Облигации", "31%", "#2B62A3"), ("Деньги", "13%", "#E0A22E")]
    for i, (name, pct, color) in enumerate(legends):
        y = 680 + i * 125
        rr(d, (590, y, 630, y + 40), 12, color)
        text(d, (660, y - 5), name, "body")
        text(d, (1005, y - 5), pct, "body_semi", anchor="ra")
    section(d, 1145, "Состав портфеля", "Сортировка")
    asset_row(d, 1220, "Беларусбанк", "12 шт. • 740,35 BYN", "8 884,20 BYN", "+512,30 BYN")
    asset_row(d, 1405, "Беларусь ОФЗ", "6 шт. • 1 040 BYN", "6 240,00 BYN", "+127,40 BYN", True, "#2B62A3")
    asset_row(d, 1590, "Apple Inc.", "8 шт. • 716,50 BYN", "5 732,00 BYN", "+231,67 BYN", True, "#232A27")
    bottom_nav(d, "Портфель")
    save(img, "03-портфель.png")


def screen_market():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Рынок", "Ценные бумаги и валюты")
    rr(d, (40, 260, 1040, 375), 28, WHITE, LINE)
    text(d, (85, 298), "⌕  Название или тикер", "body", MUTED)
    x = 40
    for label in ["Все", "Акции", "Облигации", "Фонды"]:
        x = pill(d, x, 415, label, label == "Все")
    section(d, 545, "Индексы")
    cards = [("БВФБ", "1 284,6", "+1,24%"), ("USD/BYN", "3,176", "-0,18%"), ("EUR/BYN", "3,452", "+0,36%")]
    for i, (name, value, ch) in enumerate(cards):
        x0 = 40 + i * 338
        rr(d, (x0, 620, x0 + 316, 820), 28, WHITE, LINE)
        text(d, (x0 + 28, 652), name, "sm", MUTED)
        text(d, (x0 + 28, 710), value, "h3")
        text(d, (x0 + 28, 765), ch, "sm", GREEN if "+" in ch else RED)
    section(d, 890, "Популярные инструменты", "Фильтры")
    asset_row(d, 965, "Беларусбанк", "BRBB • Акция", "740,35 BYN", "+2,90%")
    asset_row(d, 1150, "Беларусь ОФЗ", "BYGOV-27 • Облигация", "1 040,00 BYN", "+0,42%", True, "#2B62A3")
    asset_row(d, 1335, "Газпром", "GAZP • MOEX", "5,21 BYN", "-1,18%", False, "#2E73A8")
    asset_row(d, 1520, "Apple Inc.", "AAPL • NASDAQ", "716,50 BYN", "+3,56%", True, "#232A27")
    section(d, 1745, "Подборки")
    rr(d, (40, 1820, 510, 2100), 30, GREEN)
    text(d, (75, 1860), "Надёжные", "h3", WHITE)
    text(d, (75, 1920), "облигации", "h3", WHITE)
    text(d, (75, 2015), "Доходность до 12%", "sm", "#C9EFDA")
    rr(d, (530, 1820, 1040, 2100), 30, "#2B62A3")
    text(d, (565, 1860), "Дивидендные", "h3", WHITE)
    text(d, (565, 1920), "акции", "h3", WHITE)
    text(d, (565, 2015), "Регулярные выплаты", "sm", "#D8E7F8")
    bottom_nav(d, "Рынок")
    save(img, "04-рынок.png")


def chart(draw, box, color=GREEN, candles=False):
    x1, y1, x2, y2 = box
    draw.line((x1, y2, x2, y2), fill=LINE, width=2)
    draw.line((x1, y1, x1, y2), fill=LINE, width=2)
    if candles:
        values = [0.65, 0.5, 0.58, 0.42, 0.46, 0.3, 0.36, 0.25, 0.2, 0.33, 0.17, 0.12]
        step = (x2 - x1 - 50) / len(values)
        for i, v in enumerate(values):
            x = x1 + 35 + i * step
            cy = y1 + v * (y2 - y1)
            up = i % 3 != 1
            c = GREEN if up else RED
            draw.line((x, cy - 55, x, cy + 55), fill=c, width=5)
            draw.rectangle((x - 15, cy - 25, x + 15, cy + 25), fill=c)
    else:
        pts = []
        for i in range(32):
            x = x1 + i * (x2 - x1) / 31
            v = 0.72 - i * 0.014 + math.sin(i * 1.15) * 0.08
            y = y1 + v * (y2 - y1)
            pts.append((x, y))
        draw.line(pts, fill=color, width=8, joint="curve")


def screen_security():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Беларусбанк", "BRBB • БВФБ", back=True, action="☆")
    text(d, (52, 275), "740,35 BYN", "amount")
    text(d, (52, 378), "+20,85 BYN  •  +2,90%", "body_semi", GREEN)
    x = 52
    for label in ["День", "Неделя", "Месяц", "Год"]:
        x = pill(d, x, 470, label, label == "День")
    chart(d, (70, 610, 1010, 1110))
    stats = [("Открытие", "721,10"), ("Максимум", "745,60"), ("Минимум", "718,40"), ("Объём", "1,23 млн")]
    for i, (name, value) in enumerate(stats):
        col = i % 2
        row = i // 2
        x0 = 55 + col * 510
        y0 = 1185 + row * 115
        text(d, (x0, y0), name, "sm", MUTED)
        text(d, (x0 + 440, y0), value, "body_semi", TEXT, "ra")
    section(d, 1450, "О компании")
    rr(d, (40, 1525, 1040, 1790), 28, WHITE, LINE)
    text(d, (75, 1570), "ОАО «АСБ Беларусбанк»", "body_semi")
    text(d, (75, 1635), "Финансовый сектор • Беларусь", "sm", MUTED)
    text(d, (75, 1705), "Дивидендная доходность", "sm", MUTED)
    text(d, (1005, 1705), "8,4%", "body_semi", TEXT, "ra")
    button(d, 40, 1930, 480, "Купить")
    button(d, 560, 1930, 480, "Продать", danger=True)
    bottom_nav(d, "Рынок")
    save(img, "05-карточка-бумаги.png")


def screen_chart():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "График BRBB", "Беларусбанк • БВФБ", back=True, action="Настройки")
    text(d, (52, 270), "740,35 BYN", "h1")
    text(d, (52, 360), "+2,90% сегодня", "body_semi", GREEN)
    x = 52
    for label in ["1Д", "1Н", "1М", "6М", "1Г", "Все"]:
        x = pill(d, x, 455, label, label == "1Д", 130)
    rr(d, (40, 570, 1040, 1420), 34, WHITE, LINE)
    chart(d, (85, 640, 995, 1325), candles=True)
    text(d, (85, 1350), "10:00", "xs", MUTED)
    text(d, (540, 1350), "13:00", "xs", MUTED, "ma")
    text(d, (995, 1350), "16:00", "xs", MUTED, "ra")
    section(d, 1505, "Индикаторы")
    x = 52
    for label in ["Объём", "SMA", "EMA", "RSI"]:
        x = pill(d, x, 1580, label, label == "Объём")
    rr(d, (40, 1710, 1040, 1960), 28, WHITE, LINE)
    text(d, (75, 1750), "Диапазон дня", "sm", MUTED)
    text(d, (75, 1812), "718,40 — 745,60 BYN", "body_semi")
    d.line((75, 1900, 1005, 1900), fill=LINE, width=18)
    d.line((310, 1900, 855, 1900), fill=GREEN, width=18)
    button(d, 40, 2045, 1000, "Создать заявку")
    save(img, "06-график.png")


def screen_orderbook():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Биржевой стакан", "BRBB • 740,35 BYN", back=True, action="Вид")
    text(d, (55, 275), "Покупка", "body_semi", GREEN)
    text(d, (540, 275), "Цена, BYN", "body_semi", TEXT, "ma")
    text(d, (1025, 275), "Продажа", "body_semi", RED, "ra")
    rows = [
        (1250, "740,30", 0, ""), (2160, "740,25", 0, ""), (1780, "740,20", 0, ""),
        (3450, "740,15", 0, ""), (2310, "740,10", 0, ""), (0, "740,40", 1120, ""),
        (0, "740,45", 2340, ""), (0, "740,50", 1980, ""), (0, "740,55", 2770, ""),
        (0, "740,60", 1560, ""),
    ]
    y = 365
    for buy, price, sell, _ in rows:
        h = 135
        if buy:
            width = min(440, 120 + buy / 10)
            rr(d, (40, y, 40 + width, y + h - 10), 12, GREEN_LIGHT)
            text(d, (70, y + 45), f"{buy:,}".replace(",", " "), "body_semi", GREEN)
        if sell:
            width = min(440, 120 + sell / 10)
            rr(d, (1040 - width, y, 1040, y + h - 10), 12, RED_LIGHT)
            text(d, (1010, y + 45), f"{sell:,}".replace(",", " "), "body_semi", RED, "ra")
        text(d, (540, y + 45), price, "body_semi", TEXT, "ma")
        d.line((40, y + h, 1040, y + h), fill=LINE, width=2)
        y += h
    rr(d, (40, 1785, 1040, 1975), 28, WHITE, LINE)
    text(d, (75, 1825), "Последняя цена", "sm", MUTED)
    text(d, (75, 1885), "740,35 BYN", "h3")
    text(d, (1005, 1825), "Объём за день", "sm", MUTED, "ra")
    text(d, (1005, 1885), "1,23 млн BYN", "h3", TEXT, "ra")
    button(d, 40, 2035, 1000, "Создать заявку")
    save(img, "07-биржевой-стакан.png")


def field(draw, y, label, value, suffix=None):
    text(draw, (55, y), label, "sm", MUTED)
    rr(draw, (40, y + 55, 1040, y + 175), 26, WHITE, LINE)
    text(draw, (75, y + 91), value, "body_semi")
    if suffix:
        text(draw, (1005, y + 91), suffix, "body", MUTED, "ra")


def screen_order():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Покупка", "Беларусбанк • BRBB", back=True)
    rr(d, (40, 260, 1040, 430), 28, WHITE, LINE)
    text(d, (75, 300), "Текущая цена", "sm", MUTED)
    text(d, (75, 360), "740,35 BYN", "h3")
    text(d, (1005, 315), "+2,90%", "body_semi", GREEN, "ra")
    text(d, (55, 505), "Тип заявки", "sm", MUTED)
    x = 40
    for label in ["Рыночная", "Лимитная", "Стоп"]:
        x = pill(d, x, 560, label, label == "Рыночная", 260)
    field(d, 700, "Количество", "10", "шт.")
    field(d, 930, "Цена за одну бумагу", "740,35", "BYN")
    rr(d, (40, 1190, 1040, 1545), 30, WHITE, LINE)
    rows = [("Стоимость бумаг", "7 403,50 BYN"), ("Комиссия", "18,51 BYN"), ("Итого", "7 422,01 BYN")]
    for i, (name, value) in enumerate(rows):
        y = 1235 + i * 100
        text(d, (75, y), name, "body" if i < 2 else "body_semi", MUTED if i < 2 else TEXT)
        text(d, (1005, y), value, "body_semi", TEXT, "ra")
    rr(d, (40, 1625, 1040, 1785), 28, GREEN_PALE)
    text(d, (75, 1660), "Доступно на счёте", "sm", MUTED)
    text(d, (75, 1715), "12 480,00 BYN", "h3", GREEN_DARK)
    button(d, 40, 1880, 1000, "Продолжить")
    save(img, "08-заявка-на-покупку.png")


def screen_history():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Заявки и операции", "По всем счетам", action="Фильтр")
    x = 40
    for label in ["Активные", "Исполненные", "Операции"]:
        x = pill(d, x, 270, label, label == "Операции", 285)
    entries = [
        ("Сегодня, 14:32", "Покупка 10 акций Беларусбанка", "-7 422,01 BYN", "Исполнена", RED),
        ("Сегодня, 14:31", "Комиссия брокера", "-18,51 BYN", "Списана", RED),
        ("14 июля, 10:05", "Пополнение брокерского счёта", "+5 000,00 BYN", "Выполнено", GREEN),
        ("12 июля, 16:48", "Купон по облигациям BYGOV-27", "+124,80 BYN", "Зачислено", GREEN),
        ("10 июля, 11:20", "Продажа 5 акций Apple Inc.", "+3 582,50 BYN", "Исполнена", GREEN),
    ]
    y = 420
    for date, name, amount, state, color in entries:
        rr(d, (40, y, 1040, y + 290), 28, WHITE, LINE)
        text(d, (75, y + 38), date, "sm", MUTED)
        text(d, (75, y + 98), name, "body_semi")
        text(d, (75, y + 175), state, "sm", color)
        text(d, (1005, y + 103), amount, "body_semi", color, "ra")
        text(d, (1005, y + 195), "›", "h3", MUTED, "ra")
        y += 315
    bottom_nav(d, "Заявки")
    save(img, "09-история-операций.png")


def screen_calendar():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Календарь инвестора", "Июль 2026", back=True, action="Фильтр")
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i, day in enumerate(days):
        text(d, (90 + i * 145, 280), day, "sm", MUTED, "ma")
    start_y = 365
    n = 1
    marked = {5: GREEN, 12: "#2B62A3", 18: GREEN, 24: AMBER, 30: GREEN}
    for row in range(5):
        for col in range(7):
            x = 90 + col * 145
            y = start_y + row * 150
            if n in marked:
                rr(d, (x - 47, y - 38, x + 47, y + 56), 30, GREEN_LIGHT)
                d.ellipse((x - 9, y + 70, x + 9, y + 88), fill=marked[n])
            text(d, (x, y), str(n), "body_semi", TEXT, "ma")
            n += 1
    x = 40
    for label in ["Все", "Дивиденды", "Купоны", "Погашения"]:
        x = pill(d, x, 1160, label, label == "Все")
    section(d, 1285, "18 июля")
    events = [
        ("Купон", "Беларусь ОФЗ BYGOV-27", "124,80 BYN", GREEN),
        ("Дивиденды", "Беларусбанк BRBB", "86,40 BYN", "#2B62A3"),
    ]
    y = 1360
    for kind, name, amount, color in events:
        rr(d, (40, y, 1040, y + 240), 28, WHITE, LINE)
        rr(d, (70, y + 45, 210, y + 105), 30, color)
        text(d, (140, y + 74), kind, "xs", WHITE, "mm")
        text(d, (70, y + 135), name, "body_semi")
        text(d, (1005, y + 135), amount, "body_semi", TEXT, "ra")
        y += 270
    rr(d, (40, 1940, 1040, 2105), 28, GREEN_PALE)
    text(d, (75, 1980), "Ожидаемые выплаты в июле", "sm", MUTED)
    text(d, (75, 2035), "438,20 BYN", "h3", GREEN_DARK)
    bottom_nav(d, "Сервисы")
    save(img, "10-календарь-инвестора.png")


def screen_deposit():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Пополнение счёта", "Брокерский счёт BY12 •••• 4582", back=True)
    text(d, (55, 280), "Карта списания", "sm", MUTED)
    rr(d, (40, 335, 1040, 570), 32, GREEN)
    text(d, (80, 375), "БЕЛКАРТ", "sm", "#D4F0E0")
    text(d, (80, 455), "••••  2486", "h3", WHITE)
    text(d, (1000, 455), "8 240,15 BYN", "body_semi", WHITE, "ra")
    field(d, 650, "Сумма пополнения", "5 000,00", "BYN")
    text(d, (55, 920), "Валюта брокерского счёта", "sm", MUTED)
    x = 40
    for label in ["BYN", "USD", "EUR", "RUB"]:
        x = pill(d, x, 980, label, label == "BYN", 205)
    rr(d, (40, 1135, 1040, 1445), 30, WHITE, LINE)
    rows = [("Сумма списания", "5 000,00 BYN"), ("Комиссия", "0,00 BYN"), ("Будет зачислено", "5 000,00 BYN")]
    for i, (name, value) in enumerate(rows):
        y = 1178 + i * 90
        text(d, (75, y), name, "body" if i < 2 else "body_semi", MUTED if i < 2 else TEXT)
        text(d, (1005, y), value, "body_semi", GREEN if i == 2 else TEXT, "ra")
    rr(d, (40, 1535, 1040, 1715), 28, GREEN_PALE)
    text(d, (75, 1575), "Средства появятся на счёте сразу", "body_semi", GREEN_DARK)
    text(d, (75, 1640), "Это демонстрационный сценарий без реального платежа", "sm", MUTED)
    button(d, 40, 1840, 1000, "Пополнить")
    save(img, "11-пополнение-счёта.png")


def screen_profile():
    img = canvas()
    d = ImageDraw.Draw(img)
    status_bar(d)
    app_bar(d, "Профиль", "Клиент Беларусбанка", action="Настройки")
    d.ellipse((55, 275, 235, 455), fill=GREEN)
    text(d, (145, 360), "АП", "h2", WHITE, "mm")
    text(d, (275, 292), "Алексей Петров", "h2")
    text(d, (275, 370), "Клиент № 104582", "sm", MUTED)
    text(d, (55, 520), "Счета и договоры", "h3")
    items = [
        ("Брокерский счёт", "BY12 •••• 4582"),
        ("Счёт депо", "DEPO •••• 9184"),
        ("Договор комиссии", "Действует до 15.07.2029"),
    ]
    y = 595
    for name, sub in items:
        rr(d, (40, y, 1040, y + 175), 26, WHITE, LINE)
        text(d, (75, y + 36), name, "body_semi")
        text(d, (75, y + 96), sub, "sm", MUTED)
        text(d, (1005, y + 76), "›", "h3", MUTED, "ra")
        y += 195
    text(d, (55, 1215), "Настройки и помощь", "h3")
    menu = [
        ("Документы", "Оферты, отчёты и свидетельства"),
        ("Уведомления", "Сделки, выплаты и новости"),
        ("Настройки входа", "SMS и биометрия"),
        ("Чат поддержки", "Ответим на вопросы"),
    ]
    y = 1290
    for name, sub in menu:
        rr(d, (40, y, 1040, y + 165), 24, WHITE, LINE)
        text(d, (75, y + 32), name, "body_semi")
        text(d, (75, y + 92), sub, "sm", MUTED)
        text(d, (1005, y + 72), "›", "h3", MUTED, "ra")
        y += 180
    button(d, 40, 2050, 1000, "Выйти", primary=False)
    bottom_nav(d, "Профиль")
    save(img, "12-профиль.png")


if __name__ == "__main__":
    screen_login()
    screen_home()
    screen_portfolio()
    screen_market()
    screen_security()
    screen_chart()
    screen_orderbook()
    screen_order()
    screen_history()
    screen_calendar()
    screen_deposit()
    screen_profile()
    print("Создано 12 макетов в", OUT)
