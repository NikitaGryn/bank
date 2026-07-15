from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Callable

import flet as ft

from api import ApiClient
from helpers import money, percent, to_decimal, trade_calculation


GREEN = "#007A3D"
GREEN_DARK = "#005C2F"
GREEN_LIGHT = "#E7F5ED"
BG = "#F5F7F6"
TEXT = "#19221E"
MUTED = "#6F7C75"
LINE = "#E2E8E5"
RED = "#D9363E"
RED_LIGHT = "#FDECEE"
BLUE = "#2B62A3"


def field_value(data: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if data.get(name) is not None:
            return data[name]
    return default


def card(content: ft.Control, padding: int = 18, bgcolor: str = "#FFFFFF") -> ft.Container:
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=bgcolor,
        border=ft.Border.all(1, LINE),
        border_radius=20,
    )


def heading(title: str, subtitle: str | None = None) -> ft.Column:
    controls: list[ft.Control] = [
        ft.Text(title, size=26, weight=ft.FontWeight.BOLD, color=TEXT)
    ]
    if subtitle:
        controls.append(ft.Text(subtitle, size=13, color=MUTED))
    return ft.Column(controls, spacing=2)


def status_color(value: object) -> str:
    return GREEN if to_decimal(value) >= 0 else RED


def security_type_label(value: object) -> str:
    labels = {
        "STOCK": "Акции",
        "BOND": "Облигации",
        "FUND": "Фонды",
    }
    raw = str(value or "Акции")
    return labels.get(raw.upper(), raw)


def enum_label(value: object) -> str:
    labels = {
        "EXECUTED": "Исполнена",
        "REJECTED": "Отклонена",
        "DIVIDEND": "Дивиденды",
        "REPORT": "Отчётность",
        "MEETING": "Собрание акционеров",
        "OTHER": "Другое",
    }
    raw = str(value or "")
    return labels.get(raw.upper(), raw)


class InvestmentsApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.api = ApiClient()
        self.logged_in = False
        self.index = 0
        self.portfolio: dict[str, Any] = {}
        self.securities: list[dict[str, Any]] = []
        self.orders: list[dict[str, Any]] = []
        self.transactions: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.search_query = ""
        self.market_filter = "Все"
        self.current_ticker: str | None = None
        self.live_quotes: dict[str, dict[str, Any]] = {}
        self.content = ft.Container(expand=True)

        page.title = "Belarusbank Investments"
        page.bgcolor = BG
        page.padding = 0
        page.theme = ft.Theme(
            color_scheme_seed=GREEN,
            font_family="Segoe UI",
            scaffold_bgcolor=BG,
            navigation_bar_theme=ft.NavigationBarTheme(
                bgcolor="#FFFFFF",
                indicator_color="#BCE8CE",
                label_text_style={
                    ft.ControlState.DEFAULT: ft.TextStyle(
                        color=TEXT, size=12, weight=ft.FontWeight.W_600
                    ),
                    ft.ControlState.SELECTED: ft.TextStyle(
                        color=GREEN_DARK, size=12, weight=ft.FontWeight.BOLD
                    ),
                },
            ),
            navigation_rail_theme=ft.NavigationRailTheme(
                bgcolor="#FFFFFF",
                indicator_color="#BCE8CE",
                selected_label_text_style=ft.TextStyle(
                    color=GREEN_DARK, size=14, weight=ft.FontWeight.BOLD
                ),
                unselected_label_text_style=ft.TextStyle(
                    color=TEXT, size=14, weight=ft.FontWeight.W_600
                ),
                use_indicator=True,
            ),
        )
        page.on_resize = self.on_resize
        self.show_login()

    @property
    def is_desktop(self) -> bool:
        return bool(self.page.width and self.page.width >= 900)

    def on_resize(self, _event: ft.Event) -> None:
        if self.logged_in:
            self.render_shell()

    def demo_badge(self) -> ft.Container:
        return ft.Container(visible=False)

    def show_login(self) -> None:
        self.logged_in = False
        login = ft.TextField(
            label="Логин",
            hint_text="Введите логин",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            autofocus=True,
            text_style=ft.TextStyle(color=TEXT, size=16),
            label_style=ft.TextStyle(color=GREEN_DARK),
            bgcolor="#FFFFFF",
            border_color="#738078",
            focused_border_color=GREEN,
        )
        password = ft.TextField(
            label="Пароль",
            hint_text="Введите пароль",
            password=False,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            text_style=ft.TextStyle(color=TEXT, size=16),
            label_style=ft.TextStyle(color=GREEN_DARK),
            bgcolor="#FFFFFF",
            border_color="#738078",
            focused_border_color=GREEN,
        )
        error = ft.Text("", color=RED, size=13)

        def submit(_event: ft.Event) -> None:
            if not (login.value or "").strip() or not (password.value or "").strip():
                error.value = "Введите логин и пароль"
                self.page.update()
                return
            self.logged_in = True
            self.load_data()
            self.render_shell()

        panel = ft.Container(
            width=460,
            padding=32,
            bgcolor="#FFFFFF",
            border_radius=28,
            border=ft.Border.all(1, LINE),
            content=ft.Column(
                [
                    ft.Container(
                        width=64,
                        height=64,
                        bgcolor=GREEN,
                        border_radius=18,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(ft.Icons.ACCOUNT_BALANCE, color="#FFFFFF", size=34),
                    ),
                    ft.Text("Беларусбанк", color=GREEN_DARK, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("Инвестиции", color=TEXT, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Управляйте портфелем и совершайте сделки",
                        color=MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    login,
                    password,
                    error,
                    ft.Button(
                        "Войти",
                        icon=ft.Icons.LOGIN,
                        bgcolor=GREEN,
                        color="#FFFFFF",
                        height=50,
                        on_click=submit,
                    ),
                    ft.TextButton("Восстановить пароль", on_click=lambda _: self.notice("Запрос на восстановление отправлен")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
        )
        self.page.clean()
        self.page.add(
            ft.Container(
                expand=True,
                padding=20,
                alignment=ft.Alignment.CENTER,
                content=panel,
            )
        )

    def load_data(self) -> None:
        self.portfolio = self.api.portfolio()
        self.securities = self.api.securities()
        self.orders = self.api.orders()
        self.transactions = self.api.transactions()
        self.events = self.api.events()

    def refresh_data(self, message: str | None = None) -> None:
        self.load_data()
        self.render_shell()
        if message:
            self.notice(message)

    def navigation_items(self) -> list[tuple[str, str]]:
        return [
            ("Портфель", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
            ("Рынок", ft.Icons.CANDLESTICK_CHART),
            ("Заявки", ft.Icons.RECEIPT_LONG_OUTLINED),
            ("Сервисы", ft.Icons.GRID_VIEW_OUTLINED),
            ("Профиль", ft.Icons.PERSON_OUTLINE),
        ]

    def select_nav(self, event: ft.Event) -> None:
        self.index = int(event.control.selected_index)
        self.current_ticker = None
        self.render_shell()

    def select_rail(self, event: ft.Event) -> None:
        self.select_nav(event)

    def render_shell(self) -> None:
        if not self.logged_in:
            return
        self.page.clean()
        self.content = ft.Container(
            expand=True,
            content=self.screen(),
            padding=ft.Padding.only(left=16, right=16, top=18, bottom=12),
        )
        if self.is_desktop:
            self.page.navigation_bar = None
            extended = bool(self.page.width and self.page.width >= 1150)
            rail = ft.NavigationRail(
                selected_index=self.index,
                on_change=self.select_rail,
                label_type=(
                    ft.NavigationRailLabelType.NONE
                    if extended
                    else ft.NavigationRailLabelType.ALL
                ),
                bgcolor="#FFFFFF",
                min_width=92,
                min_extended_width=190,
                extended=extended,
                indicator_color="#BCE8CE",
                selected_label_text_style=ft.TextStyle(
                    color=GREEN_DARK, size=14, weight=ft.FontWeight.BOLD
                ),
                unselected_label_text_style=ft.TextStyle(
                    color=TEXT, size=14, weight=ft.FontWeight.W_600
                ),
                destinations=[
                    ft.NavigationRailDestination(
                        icon=ft.Icon(icon, color=TEXT),
                        selected_icon=ft.Icon(icon, color=GREEN_DARK),
                        label=ft.Text(label, color=TEXT, weight=ft.FontWeight.W_600),
                    )
                    for label, icon in self.navigation_items()
                ],
            )
            body = ft.Row(
                [
                    rail,
                    ft.VerticalDivider(width=1, color=LINE),
                    ft.Container(
                        expand=True,
                        alignment=ft.Alignment.TOP_CENTER,
                        content=ft.Container(width=1120, expand=True, content=self.content),
                    ),
                ],
                spacing=0,
                expand=True,
            )
            self.page.add(body)
        else:
            nav = ft.NavigationBar(
                selected_index=self.index,
                on_change=self.select_nav,
                bgcolor="#FFFFFF",
                indicator_color="#BCE8CE",
                height=82,
                label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
                destinations=[
                    ft.NavigationBarDestination(
                        icon=ft.Icon(icon, color=TEXT),
                        selected_icon=ft.Icon(icon, color=GREEN_DARK),
                        label=label,
                    )
                    for label, icon in self.navigation_items()
                ],
            )
            self.page.add(self.content)
            self.page.navigation_bar = nav
            self.page.update()

    def screen(self) -> ft.Control:
        if self.current_ticker:
            return self.security_detail(self.current_ticker)
        return [
            self.portfolio_screen,
            self.market_screen,
            self.orders_screen,
            self.services_screen,
            self.profile_screen,
        ][self.index]()

    def top(self, title: str, subtitle: str) -> ft.Row:
        return ft.Row(
            [
                heading(title, subtitle),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Обновить",
                    on_click=lambda _: self.refresh_data("Данные обновлены"),
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def scroll_page(self, controls: list[ft.Control]) -> ft.Column:
        return ft.Column(controls, expand=True, scroll=ft.ScrollMode.AUTO, spacing=16)

    def portfolio_screen(self) -> ft.Control:
        total = field_value(self.portfolio, "total_value", "total", "balance", default=0)
        cash = field_value(self.portfolio, "cash", "cash_balance", "available_cash", default=0)
        profit = field_value(self.portfolio, "profit", "pnl", "total_profit", default=0)
        profit_pct = field_value(self.portfolio, "profit_percent", "pnl_percent", "return_percent", default=0)
        currency = str(field_value(self.portfolio, "currency", default="BYN"))
        if not profit_pct and to_decimal(total) != to_decimal(profit):
            profit_pct = (
                to_decimal(profit)
                / (to_decimal(total) - to_decimal(profit))
                * Decimal("100")
            )
        holdings = field_value(self.portfolio, "holdings", "positions", "assets", default=[])
        if not isinstance(holdings, list):
            holdings = []

        balance = ft.Container(
            padding=24,
            border_radius=24,
            bgcolor=GREEN,
            col={"xs": 12, "md": 8},
            content=ft.Column(
                [
                    ft.Text("Стоимость портфеля", color="#FFFFFF", size=13, weight=ft.FontWeight.BOLD),
                    ft.Text(money(total, currency), color="#FFFFFF", size=25, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"{money(profit, currency)}  •  {percent(profit_pct)}",
                        color="#CBF4DB" if to_decimal(profit) >= 0 else "#FFDADD",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Divider(color="#4A9C70"),
                    ft.Row(
                        [
                            ft.Column([ft.Text("Свободные деньги", color="#D9F1E4", size=12), ft.Text(money(cash, currency), color="#FFFFFF", weight=ft.FontWeight.BOLD)]),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.TRENDING_UP, color="#8EE0B2", size=42),
                        ]
                    ),
                ],
                spacing=8,
            ),
        )
        allocation = card(
            ft.Column(
                [
                    ft.Text("Структура", size=18, weight=ft.FontWeight.BOLD, color=TEXT),
                    self.allocation_row("Акции", "56%", GREEN),
                    self.allocation_row("Облигации", "31%", BLUE),
                    self.allocation_row("Деньги", "13%", "#E0A22E"),
                ],
                spacing=13,
            )
        )
        allocation.col = {"xs": 12, "md": 4}
        actions = ft.ResponsiveRow(
            [
                self.action_card("Пополнить", ft.Icons.ADD_CARD, self.money_dialog("deposit")),
                self.action_card("Вывести", ft.Icons.ACCOUNT_BALANCE, self.money_dialog("withdraw")),
                self.action_card("Операции", ft.Icons.HISTORY, lambda _: self.go_to(2)),
                self.action_card("Календарь", ft.Icons.EVENT_OUTLINED, lambda _: self.go_to(3)),
            ],
            spacing=10,
            run_spacing=10,
        )
        position_cards = [self.holding_card(item) for item in holdings]
        return self.scroll_page(
            [
                self.top("Главная", "Брокерский счёт BY12 •••• 4582"),
                ft.ResponsiveRow([balance, allocation], spacing=14, run_spacing=14),
                actions,
                ft.Text("Позиции", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(position_cards, spacing=12, run_spacing=12)
                if position_cards
                else card(ft.Text("В портфеле пока нет ценных бумаг", color=MUTED)),
            ]
        )

    def allocation_row(self, label: str, value: str, color: str) -> ft.Row:
        return ft.Row(
            [
                ft.Container(width=11, height=11, bgcolor=color, border_radius=4),
                ft.Text(label, color=MUTED),
                ft.Container(expand=True),
                ft.Text(value, color=TEXT, weight=ft.FontWeight.BOLD),
            ]
        )

    def action_card(self, label: str, icon: str, handler: Callable) -> ft.Container:
        control = ft.Container(
            col={"xs": 6, "sm": 3},
            padding=14,
            bgcolor=GREEN_LIGHT,
            border_radius=17,
            ink=True,
            on_click=handler,
            content=ft.Column(
                [ft.Icon(icon, color=GREEN), ft.Text(label, size=13, color=TEXT, weight=ft.FontWeight.BOLD)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=7,
            ),
        )
        return control

    def holding_card(self, item: dict[str, Any]) -> ft.Container:
        ticker = str(field_value(item, "ticker", "symbol", default="—"))
        name = str(field_value(item, "name", "security_name", default=ticker))
        qty = field_value(item, "quantity", "qty", default=0)
        return ft.Container(
            col={"xs": 12, "md": 6},
            padding=16,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, LINE),
            border_radius=18,
            ink=True,
            on_click=lambda _, t=ticker: self.open_security(t),
            content=ft.Row(
                [
                    ft.Container(
                        width=46,
                        height=46,
                        bgcolor=GREEN,
                        border_radius=14,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text(ticker[:2], color="#FFFFFF", weight=ft.FontWeight.BOLD),
                    ),
                    ft.Column([ft.Text(name, weight=ft.FontWeight.BOLD, color=TEXT), ft.Text(f"{ticker} • {qty} шт.", color=MUTED, size=12)], spacing=3, expand=True),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=GREEN),
                ]
            ),
        )

    def market_screen(self) -> ft.Control:
        search = ft.TextField(
            value=self.search_query,
            hint_text="Название или тикер",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.market_search,
            dense=True,
            col={"xs": 12, "md": 7},
        )
        filters = ft.Row(
            [
                ft.Button(
                    label,
                    bgcolor=GREEN if self.market_filter == label else "#FFFFFF",
                    color="#FFFFFF" if self.market_filter == label else TEXT,
                    on_click=lambda _, value=label: self.set_market_filter(value),
                )
                for label in ["Все", "Акции", "Облигации", "Фонды"]
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        rows = []
        for item in self.securities:
            ticker = str(field_value(item, "ticker", "symbol", default=""))
            name = str(field_value(item, "name", "title", default=ticker))
            kind = security_type_label(field_value(item, "type", "security_type", "category", default="Акции"))
            query = self.search_query.casefold()
            if query and query not in f"{ticker} {name}".casefold():
                continue
            if self.market_filter != "Все" and self.market_filter.casefold() not in kind.casefold():
                continue
            rows.append(self.security_card(item))
        return self.scroll_page(
            [
                self.top("Рынок", "Ценные бумаги и котировки"),
                ft.ResponsiveRow([search], spacing=10),
                filters,
                ft.Text("Популярные инструменты", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(rows, spacing=12, run_spacing=12)
                if rows
                else card(ft.Text("По вашему запросу ничего не найдено", color=MUTED)),
            ]
        )

    def market_search(self, event: ft.Event) -> None:
        self.search_query = event.control.value or ""
        self.render_shell()

    def set_market_filter(self, value: str) -> None:
        self.market_filter = value
        self.render_shell()

    def security_card(self, item: dict[str, Any]) -> ft.Container:
        ticker = str(field_value(item, "ticker", "symbol", default="—"))
        name = str(field_value(item, "name", "title", default=ticker))
        kind = security_type_label(field_value(item, "type", "security_type", default="Инструмент"))
        return ft.Container(
            col={"xs": 12, "sm": 6, "lg": 4},
            padding=17,
            bgcolor="#FFFFFF",
            border_radius=18,
            border=ft.Border.all(1, LINE),
            ink=True,
            on_click=lambda _, t=ticker: self.open_security(t),
            content=ft.Column(
                [
                    ft.Row([ft.Text(ticker, size=17, weight=ft.FontWeight.BOLD, color=TEXT), ft.Container(expand=True), ft.Text(kind, size=11, color=MUTED)]),
                    ft.Text(name, color=MUTED, size=13),
                    ft.Row(
                        [
                            ft.Text("Открыть инструмент", color=GREEN_DARK, weight=ft.FontWeight.BOLD),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=GREEN),
                        ]
                    ),
                ],
                spacing=8,
            ),
        )

    def open_security(self, ticker: str) -> None:
        self.current_ticker = ticker
        self.render_shell()

    def fetch_live_quote(self, ticker: str) -> None:
        quote = self.api.market(ticker)
        if quote.get("error") or not str(quote.get("source", "")).startswith("moex"):
            self.notice("Не удалось получить цену акции. Попробуйте ещё раз.")
            return
        quote["fetched_at"] = datetime.now().strftime("%H:%M:%S")
        self.live_quotes[ticker] = quote
        self.render_shell()
        self.notice("Цена акции обновлена", success=True)

    def security_detail(self, ticker: str) -> ft.Control:
        security = self.api.security(ticker)
        quote = self.live_quotes.get(ticker, {})
        data = {**security, **quote}
        name = str(field_value(data, "name", "title", default=ticker))
        price = field_value(quote, "price", default=None)
        currency = "BYN"
        source = str(field_value(quote, "source", default=""))
        has_quote = source.startswith("moex") and price is not None
        price_controls: list[ft.Control] = [
            ft.Text("Цена акции", size=18, weight=ft.FontWeight.BOLD, color=TEXT)
        ]
        if has_quote:
            price_controls.extend(
                [
                    ft.Text(
                        money(price, currency),
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT,
                    ),
                    ft.Text(
                        f"Обновлено в {field_value(quote, 'fetched_at', default='только что')}",
                        size=12,
                        color=MUTED,
                    ),
                ]
            )
        price_controls.append(
            ft.Button(
                "Обновить цену" if has_quote else "Запросить цену акции",
                icon=ft.Icons.CLOUD_DOWNLOAD_OUTLINED,
                bgcolor=GREEN,
                color="#FFFFFF",
                on_click=lambda _: self.fetch_live_quote(ticker),
            )
        )
        return self.scroll_page(
            [
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: self.close_security()),
                        heading(name, f"{ticker} • Биржевой инструмент"),
                        ft.Container(expand=True),
                    ]
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            col={"xs": 12, "md": 7},
                            content=card(
                                ft.Column(price_controls, spacing=12)
                            ),
                        ),
                        ft.Container(
                            col={"xs": 12, "md": 5},
                            content=card(
                                ft.Column(
                                    [
                                        ft.Text("Об инструменте", size=18, weight=ft.FontWeight.BOLD),
                                        self.info_row("Тикер", ticker),
                                        self.info_row("Валюта", currency),
                                        self.info_row("Тип", security_type_label(field_value(data, "type", "security_type", default="Ценная бумага"))),
                                        self.info_row("Биржа", "MOEX"),
                                    ],
                                    spacing=12,
                                )
                            ),
                        ),
                    ],
                    spacing=14,
                    run_spacing=14,
                ),
                ft.Row(
                    [
                        ft.Button("Купить", icon=ft.Icons.ADD_SHOPPING_CART, bgcolor=GREEN, color="#FFFFFF", expand=True, height=50, disabled=not has_quote, on_click=lambda _: self.trade_dialog(data, "buy")),
                        ft.Button("Продать", icon=ft.Icons.SELL_OUTLINED, bgcolor=RED, color="#FFFFFF", expand=True, height=50, disabled=not has_quote, on_click=lambda _: self.trade_dialog(data, "sell")),
                    ]
                ),
            ]
        )

    def price_chart(self, change: object) -> ft.Container:
        heights = [34, 42, 38, 58, 49, 65, 60, 78, 72, 94, 86, 105]
        if to_decimal(change) < 0:
            heights.reverse()
        color = status_color(change)
        return ft.Container(
            height=130,
            padding=ft.Padding.only(top=10),
            content=ft.Row(
                [
                    ft.Container(width=10, height=h, bgcolor=color, border_radius=5)
                    for h in heights
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
        )

    def info_row(self, label: str, value: str) -> ft.Row:
        return ft.Row([ft.Text(label, color=MUTED), ft.Container(expand=True), ft.Text(value, color=TEXT, weight=ft.FontWeight.BOLD)])

    def orderbook_card(self, bids: list, asks: list) -> ft.Container:
        controls: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text("Покупка", color=GREEN, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text("Цена", color=MUTED),
                    ft.Text("Продажа", color=RED, weight=ft.FontWeight.BOLD, expand=True, text_align=ft.TextAlign.RIGHT),
                ]
            )
        ]
        for i in range(max(len(bids), len(asks), 1)):
            bid = bids[i] if i < len(bids) and isinstance(bids[i], dict) else {}
            ask = asks[i] if i < len(asks) and isinstance(asks[i], dict) else {}
            bid_qty = field_value(bid, "quantity", "qty", "volume", default="—")
            bid_price = field_value(bid, "price", default="")
            ask_price = field_value(ask, "price", default="")
            ask_qty = field_value(ask, "quantity", "qty", "volume", default="—")
            controls.append(
                ft.Row(
                    [
                        ft.Container(expand=True, bgcolor=GREEN_LIGHT, border_radius=8, padding=7, content=ft.Text(str(bid_qty), color=GREEN)),
                        ft.Text(f"{bid_price or ask_price}", width=88, text_align=ft.TextAlign.CENTER, color=TEXT),
                        ft.Container(expand=True, bgcolor=RED_LIGHT, border_radius=8, padding=7, content=ft.Text(str(ask_qty), color=RED, text_align=ft.TextAlign.RIGHT)),
                    ]
                )
            )
        return card(ft.Column(controls, spacing=6))

    def close_security(self) -> None:
        self.current_ticker = None
        self.render_shell()

    def trade_dialog(self, security: dict[str, Any], side: str) -> None:
        ticker = str(field_value(security, "ticker", "symbol", default=self.current_ticker or ""))
        price_value = field_value(security, "price", "last_price", "current_price", default=0)
        currency = str(field_value(security, "currency", default=field_value(self.portfolio, "currency", default="BYN")))
        quantity = ft.TextField(label="Количество, шт.", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        price = ft.TextField(label=f"Цена, {currency}", value=str(price_value), keyboard_type=ft.KeyboardType.NUMBER)
        preview = ft.Column(spacing=5)
        feedback = ft.Text("", size=13)

        def update_preview(_event: ft.Event | None = None) -> None:
            try:
                calc = trade_calculation(quantity.value, price.value)
                preview.controls = [
                    self.info_row("Стоимость бумаг", money(calc["subtotal"], currency)),
                    self.info_row("Комиссия 0,25%", money(calc["commission"], currency)),
                    self.info_row("Итого", money(calc["total"], currency)),
                ]
                feedback.value = ""
            except ValueError as exc:
                preview.controls = []
                feedback.value = str(exc)
                feedback.color = RED
            self.page.update()

        quantity.on_change = update_preview
        price.on_change = update_preview

        def submit(_event: ft.Event) -> None:
            try:
                qty = float(to_decimal(quantity.value))
                value = float(to_decimal(price.value))
                trade_calculation(qty, value)
            except ValueError as exc:
                feedback.value = str(exc)
                feedback.color = RED
                self.page.update()
                return
            ok, message = self.api.trade(ticker, side, qty, value)
            feedback.value = message
            feedback.color = GREEN if ok else RED
            self.page.update()
            if ok:
                dialog.open = False
                self.load_data()
                self.render_shell()
                self.notice(message, success=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Покупка" if side == "buy" else "Продажа"),
            content=ft.Container(
                width=430,
                content=ft.Column(
                    [
                        ft.Text(f"{field_value(security, 'name', default=ticker)} • {ticker}", color=MUTED),
                        quantity,
                        price,
                        card(preview, padding=14, bgcolor=BG),
                        feedback,
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
            actions=[
                ft.TextButton("Отмена", on_click=lambda _: self.close_dialog(dialog)),
                ft.Button("Отправить заявку", bgcolor=GREEN if side == "buy" else RED, color="#FFFFFF", on_click=submit),
            ],
        )
        self.page.show_dialog(dialog)
        update_preview()

    def money_dialog(self, action: str) -> Callable:
        def open_dialog(_event: ft.Event) -> None:
            currency = str(field_value(self.portfolio, "currency", default="BYN"))
            amount = ft.TextField(label=f"Сумма, {currency}", value="1000", keyboard_type=ft.KeyboardType.NUMBER, autofocus=True)
            feedback = ft.Text("", size=13)

            def submit(_event: ft.Event) -> None:
                value = to_decimal(amount.value)
                if value <= 0:
                    feedback.value = "Введите сумму больше нуля"
                    feedback.color = RED
                    self.page.update()
                    return
                ok, message = (self.api.deposit(float(value)) if action == "deposit" else self.api.withdraw(float(value)))
                feedback.value = message
                feedback.color = GREEN if ok else RED
                self.page.update()
                if ok:
                    dialog.open = False
                    self.refresh_data(message)

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Пополнение счёта" if action == "deposit" else "Вывод средств"),
                content=ft.Container(
                    width=400,
                    content=ft.Column(
                        [
                            ft.Text("Брокерский счёт BY12 •••• 4582", color=MUTED),
                            amount,
                            ft.Container(
                                padding=12,
                                bgcolor=GREEN_LIGHT,
                                border_radius=12,
                                content=ft.Text("Операция выполняется через API.", color=GREEN_DARK, size=12),
                            ),
                            feedback,
                        ],
                        tight=True,
                    ),
                ),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda _: self.close_dialog(dialog)),
                    ft.Button("Подтвердить", bgcolor=GREEN, color="#FFFFFF", on_click=submit),
                ],
            )
            self.page.show_dialog(dialog)

        return open_dialog

    def close_dialog(self, dialog: ft.AlertDialog) -> None:
        dialog.open = False
        self.page.update()

    def orders_screen(self) -> ft.Control:
        order_cards = [self.order_card(item) for item in self.orders]
        tx_cards = [self.transaction_card(item) for item in self.transactions]
        return self.scroll_page(
            [
                self.top("Заявки", "Активные и недавние операции"),
                ft.Text("Заявки", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(order_cards, spacing=12, run_spacing=12)
                if order_cards
                else card(ft.Text("Заявок пока нет", color=MUTED)),
                ft.Text("История операций", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(tx_cards, spacing=12, run_spacing=12)
                if tx_cards
                else card(ft.Text("Операций пока нет", color=MUTED)),
            ]
        )

    def order_card(self, item: dict[str, Any]) -> ft.Container:
        side = str(field_value(item, "side", default="buy")).lower()
        status = enum_label(field_value(item, "status", "state", default="Создана"))
        ticker = str(field_value(item, "ticker", "symbol", default="—"))
        qty = field_value(item, "quantity", "qty", default=0)
        price = field_value(item, "price", default=0)
        currency = str(field_value(self.portfolio, "currency", default="BYN"))
        return ft.Container(
            col={"xs": 12, "md": 6},
            content=card(
                ft.Column(
                    [
                        ft.Row([ft.Text("Покупка" if side == "buy" else "Продажа", color=GREEN if side == "buy" else RED, weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.Text(status, color=MUTED, size=12)]),
                        ft.Text(f"{ticker} • {qty} шт.", size=17, weight=ft.FontWeight.BOLD, color=TEXT),
                        ft.Text(f"По цене {money(price, currency)}", color=MUTED, size=13),
                        ft.Text(str(field_value(item, "created_at", "date", default="Недавно")), color=MUTED, size=11),
                    ],
                    spacing=6,
                )
            ),
        )

    def transaction_card(self, item: dict[str, Any]) -> ft.Container:
        amount = field_value(item, "amount", "value", default=0)
        currency = str(field_value(self.portfolio, "currency", default="BYN"))
        return ft.Container(
            col={"xs": 12, "md": 6},
            content=card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.SWAP_HORIZ, color=status_color(amount)),
                        ft.Column([ft.Text(str(field_value(item, "description", "title", "type", default="Операция")), color=TEXT, weight=ft.FontWeight.BOLD), ft.Text(str(field_value(item, "created_at", "date", default="")), color=MUTED, size=11)], expand=True, spacing=4),
                        ft.Text(money(amount, currency), color=status_color(amount), weight=ft.FontWeight.BOLD),
                    ]
                )
            ),
        )

    def services_screen(self) -> ft.Control:
        event_cards = []
        for event in self.events:
            event_cards.append(
                ft.Container(
                    col={"xs": 12, "md": 6},
                    content=card(
                        ft.Column(
                            [
                                ft.Text(str(field_value(event, "date", "event_date", default="Скоро")), color=GREEN, weight=ft.FontWeight.BOLD),
                                ft.Text(str(field_value(event, "title", "name", default="Событие")), color=TEXT, weight=ft.FontWeight.BOLD),
                                ft.Text(enum_label(field_value(event, "type", default="Выплата")), color=MUTED),
                            ]
                        )
                    ),
                )
            )
        service_cards = [
            self.service_card("Калькулятор доходности", "Оцените потенциальный результат вложений", ft.Icons.CALCULATE_OUTLINED, self.yield_dialog),
            self.service_card("Новости и идеи", "Обзор рынка: облигации и дивидендные акции", ft.Icons.NEWSPAPER_OUTLINED, lambda _: self.notice("Подборка новостей открыта")),
            self.service_card("Поддержка", "Задайте вопрос специалисту", ft.Icons.SUPPORT_AGENT, lambda _: self.notice("Сообщение отправлено в чат", success=True)),
        ]
        return self.scroll_page(
            [
                self.top("Сервисы", "Инструменты для инвестора"),
                ft.Text("Календарь инвестора", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(event_cards, spacing=12, run_spacing=12),
                ft.Text("Полезное", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(service_cards, spacing=12, run_spacing=12),
            ]
        )

    def service_card(self, title: str, subtitle: str, icon: str, handler: Callable) -> ft.Container:
        return ft.Container(
            col={"xs": 12, "md": 6, "lg": 4},
            padding=18,
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, LINE),
            border_radius=18,
            ink=True,
            on_click=handler,
            content=ft.Column([ft.Icon(icon, color=GREEN, size=30), ft.Text(title, color=TEXT, weight=ft.FontWeight.BOLD, size=16), ft.Text(subtitle, color=MUTED, size=13)], spacing=8),
        )

    def yield_dialog(self, _event: ft.Event) -> None:
        currency = str(field_value(self.portfolio, "currency", default="BYN"))
        amount = ft.TextField(label=f"Сумма, {currency}", value="10000", keyboard_type=ft.KeyboardType.NUMBER)
        rate = ft.TextField(label="Доходность в год, %", value="12", keyboard_type=ft.KeyboardType.NUMBER)
        years = ft.TextField(label="Срок, лет", value="3", keyboard_type=ft.KeyboardType.NUMBER)
        result = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=GREEN)

        def calculate(_event: ft.Event) -> None:
            principal = to_decimal(amount.value)
            annual = to_decimal(rate.value) / Decimal("100")
            term = to_decimal(years.value)
            final = principal * ((Decimal("1") + annual) ** int(max(term, 0)))
            result.value = f"Прогноз: {money(final, currency)}"
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Калькулятор доходности"),
            content=ft.Container(width=400, content=ft.Column([amount, rate, years, result], tight=True)),
            actions=[ft.TextButton("Закрыть", on_click=lambda _: self.close_dialog(dialog)), ft.Button("Рассчитать", bgcolor=GREEN, color="#FFFFFF", on_click=calculate)],
        )
        self.page.show_dialog(dialog)

    def profile_screen(self) -> ft.Control:
        account_cards = [
            self.profile_item("Брокерский счёт", "BY12 •••• 4582", ft.Icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
            self.profile_item("Счёт депо", "DEPO •••• 9184", ft.Icons.INVENTORY_2_OUTLINED),
        ]
        menu_cards = [
            self.profile_item("Документы", "Оферты, отчёты и свидетельства", ft.Icons.DESCRIPTION_OUTLINED),
            self.profile_item("Уведомления", "Сделки, выплаты и новости", ft.Icons.NOTIFICATIONS_OUTLINED),
            self.profile_item("Настройки входа", "SMS и биометрия", ft.Icons.SECURITY_OUTLINED),
        ]
        return self.scroll_page(
            [
                self.top("Профиль", "Клиент Беларусбанка"),
                card(
                    ft.Row(
                        [
                            ft.Container(width=74, height=74, bgcolor=GREEN, border_radius=37, alignment=ft.Alignment.CENTER, content=ft.Text("АП", size=23, weight=ft.FontWeight.BOLD, color="#FFFFFF")),
                            ft.Column([ft.Text("Алексей Петров", size=21, weight=ft.FontWeight.BOLD, color=TEXT), ft.Text("Клиент № 104582", color=MUTED)], spacing=4),
                        ]
                    )
                ),
                ft.Text("Счета и договоры", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(account_cards, spacing=12, run_spacing=12),
                ft.Text("Настройки и документы", size=21, weight=ft.FontWeight.BOLD, color=TEXT),
                ft.ResponsiveRow(menu_cards, spacing=12, run_spacing=12),
                ft.Button("Выйти", icon=ft.Icons.LOGOUT, color=GREEN, height=48, on_click=lambda _: self.logout()),
            ]
        )

    def profile_item(self, title: str, subtitle: str, icon: str) -> ft.Container:
        return ft.Container(
            col={"xs": 12, "md": 6},
            content=card(
                ft.Row(
                    [
                        ft.Icon(icon, color=GREEN),
                        ft.Column([ft.Text(title, color=TEXT, weight=ft.FontWeight.BOLD), ft.Text(subtitle, color=MUTED, size=12)], expand=True, spacing=3),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED),
                    ]
                )
            ),
        )

    def go_to(self, index: int) -> None:
        self.index = index
        self.current_ticker = None
        self.render_shell()

    def logout(self) -> None:
        self.page.navigation_bar = None
        self.show_login()

    def notice(self, message: str, success: bool = False) -> None:
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(message, color="#FFFFFF"),
                bgcolor=GREEN if success else TEXT,
            )
        )


def main(page: ft.Page) -> None:
    InvestmentsApp(page)


if __name__ == "__main__":
    ft.run(main)
