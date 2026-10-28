import tkinter as tk
from tkinter import ttk, messagebox, Listbox, Scrollbar, END, filedialog
import pygame
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import threading
from urllib.parse import quote, urljoin
from datetime import datetime

class ModernMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Music Player")
        self.root.geometry("1200x700")
        self.root.configure(bg='#121212')
        
        # Инициализация pygame mixer
        pygame.mixer.init()
        
        # Базовая ссылка
        self.base_url = "https://rus.hitmotop.com"
        
        # Сессия для запросов
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Переменные
        self.current_track = None
        self.is_playing = False
        self.paused = False
        self.search_results = {'albums': [], 'tracks': []}
        self.playlist = []
        
        # Цветовая схема (в стиле Яндекс.Музыки)
        self.colors = {
            'bg': '#121212',
            'bg_secondary': '#181818',
            'bg_tertiary': '#242424',
            'text': '#FFFFFF',
            'text_secondary': '#B3B3B3',
            'text_tertiary': '#7C7C7C',
            'accent': '#1DB954',
            'accent_hover': '#1ED760',
            'progress_bg': '#535353',
            'progress_fill': '#B3B3B3',
            'card_bg': '#181818',
            'hover_bg': '#282828',
            'sidebar_bg': '#000000',
        }
        
        # Иконки (эмодзи)
        self.icons = {
            'search': '🔍',
            'home': '🏠',
            'play': '▶',
            'pause': '⏸',
            'stop': '⏹',
            'next': '⏭',
            'prev': '⏮',
            'download': '⬇',
            'heart': '❤',
            'heart_outline': '🤍',
            'volume': '🔊',
            'repeat': '🔁',
            'shuffle': '🔀',
            'library': '📚',
            'playlist': '🎵',
            'artist': '👨‍🎤',
            'album': '💿',
            'time': '⏱',
            'user': '👤',
            'back': '⏪',
            'forward': '⏩',
            'queue': '📋',
            'device': '📱',
            'music_note': '🎵',
        }
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Папка для кеша
        self.cache_dir = "music_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def create_widgets(self):
        """Создание современного интерфейса"""
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель (сайдбар)
        self.create_sidebar(main_container)
        
        # Правая панель (основной контент)
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Верхняя панель (поиск и навигация)
        self.create_topbar(content_frame)
        
        # Основной контент
        self.create_main_content(content_frame)
        
        # Нижняя панель (плеер)
        self.create_player_bar(content_frame)
    
    def create_sidebar(self, parent):
        """Создание боковой панели"""
        sidebar = tk.Frame(parent, bg=self.colors['sidebar_bg'], width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Логотип
        logo_frame = tk.Frame(sidebar, bg=self.colors['sidebar_bg'], height=80)
        logo_frame.pack(fill=tk.X, pady=(20, 30))
        
        logo_label = tk.Label(logo_frame, 
                            text="🎵 Music Player",
                            font=("Segoe UI", 20, "bold"),
                            bg=self.colors['sidebar_bg'],
                            fg=self.colors['text'])
        logo_label.pack(pady=10)
        
        # Навигационные кнопки
        nav_items = [
            (self.icons['home'], 'Главная', lambda: self.notebook.select(0)),
            (self.icons['search'], 'Поиск', lambda: self.notebook.select(0)),
            (self.icons['library'], 'Медиатека', lambda: self.notebook.select(1)),
            (self.icons['playlist'], 'Плейлисты', lambda: self.show_message("Плейлисты")),
            (self.icons['artist'], 'Исполнители', lambda: self.show_message("Исполнители")),
            (self.icons['album'], 'Альбомы', lambda: self.notebook.select(2)),
        ]
        
        for icon, text, command in nav_items:
            btn = tk.Button(sidebar,
                          text=f"  {icon}  {text}",
                          font=("Segoe UI", 12),
                          bg=self.colors['sidebar_bg'],
                          fg=self.colors['text_secondary'],
                          activebackground=self.colors['hover_bg'],
                          activeforeground=self.colors['text'],
                          bd=0,
                          padx=20,
                          pady=12,
                          anchor='w',
                          command=command)
            btn.pack(fill=tk.X)
            self.bind_hover_effect(btn, self.colors['sidebar_bg'], self.colors['hover_bg'])
        
        # Разделитель
        separator = tk.Frame(sidebar, height=1, bg=self.colors['bg_secondary'])
        separator.pack(fill=tk.X, pady=20)
        
        # Ваши плейлисты
        playlists_label = tk.Label(sidebar,
                                 text="ВАШИ ПЛЕЙЛИСТЫ",
                                 font=("Segoe UI", 10, "bold"),
                                 bg=self.colors['sidebar_bg'],
                                 fg=self.colors['text_tertiary'],
                                 padx=20,
                                 pady=5,
                                 anchor='w')
        playlists_label.pack(fill=tk.X)
        
        # Пример плейлистов
        example_playlists = [
            "Топ недели",
            "Новые хиты",
            "Ретро волна",
            "Для работы",
            "Релакс"
        ]
        
        for playlist in example_playlists:
            pl_btn = tk.Button(sidebar,
                             text=f"  •  {playlist}",
                             font=("Segoe UI", 11),
                             bg=self.colors['sidebar_bg'],
                             fg=self.colors['text_secondary'],
                             activebackground=self.colors['hover_bg'],
                             activeforeground=self.colors['text'],
                             bd=0,
                             padx=20,
                             pady=8,
                             anchor='w')
            pl_btn.pack(fill=tk.X)
            self.bind_hover_effect(pl_btn, self.colors['sidebar_bg'], self.colors['hover_bg'])
        
        # Кнопка создания плейлиста
        create_btn = tk.Button(sidebar,
                             text="  +  Создать плейлист",
                             font=("Segoe UI", 11),
                             bg=self.colors['sidebar_bg'],
                             fg=self.colors['text_secondary'],
                             activebackground=self.colors['hover_bg'],
                             activeforeground=self.colors['text'],
                             bd=0,
                             padx=20,
                             pady=12,
                             anchor='w',
                             command=lambda: self.show_message("Создать плейлист"))
        create_btn.pack(fill=tk.X)
        self.bind_hover_effect(create_btn, self.colors['sidebar_bg'], self.colors['hover_bg'])
    
    def create_topbar(self, parent):
        """Создание верхней панели"""
        topbar = tk.Frame(parent, bg=self.colors['bg'], height=60)
        topbar.pack(fill=tk.X, padx=20, pady=(10, 0))
        topbar.pack_propagate(False)
        
        # Кнопки навигации
        nav_frame = tk.Frame(topbar, bg=self.colors['bg'])
        nav_frame.pack(side=tk.LEFT)
        
        nav_buttons = [
            (self.icons['back'], lambda: self.show_message("Назад")),
            (self.icons['forward'], lambda: self.show_message("Вперед"))
        ]
        
        for btn_text, command in nav_buttons:
            btn = tk.Button(nav_frame,
                          text=btn_text,
                          font=("Segoe UI", 16),
                          bg=self.colors['bg_secondary'],
                          fg=self.colors['text'],
                          activebackground=self.colors['hover_bg'],
                          activeforeground=self.colors['text'],
                          bd=0,
                          width=3,
                          height=1,
                          command=command)
            btn.pack(side=tk.LEFT, padx=2)
            self.bind_hover_effect(btn, self.colors['bg_secondary'], self.colors['hover_bg'])
        
        # Поле поиска
        search_frame = tk.Frame(topbar, bg=self.colors['bg_secondary'], bd=0, relief='flat')
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(20, 0))
        
        search_icon = tk.Label(search_frame,
                             text=self.icons['search'],
                             font=("Segoe UI", 14),
                             bg=self.colors['bg_secondary'],
                             fg=self.colors['text_tertiary'])
        search_icon.pack(side=tk.LEFT, padx=(15, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame,
                              textvariable=self.search_var,
                              font=("Segoe UI", 12),
                              bg=self.colors['bg_secondary'],
                              fg=self.colors['text'],
                              insertbackground=self.colors['text'],
                              bd=0,
                              relief='flat')
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=15)
        self.search_entry.insert(0, "Поиск исполнителей, альбомов или треков")
        self.search_entry.config(fg=self.colors['text_tertiary'])
        
        self.search_entry.bind('<FocusIn>', self.on_search_focus_in)
        self.search_entry.bind('<FocusOut>', self.on_search_focus_out)
        self.search_entry.bind('<Return>', lambda e: self.search_music())
        
        # Кнопка поиска
        search_btn = tk.Button(search_frame,
                             text="Найти",
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colors['accent'],
                             fg=self.colors['text'],
                             activebackground=self.colors['accent_hover'],
                             activeforeground=self.colors['text'],
                             bd=0,
                             padx=20,
                             command=self.search_music)
        search_btn.pack(side=tk.RIGHT, padx=10)
        
        # Привязка событий для изменения цвета при наведении
        for widget in [search_frame, search_icon, self.search_entry]:
            widget.bind('<Enter>', lambda e, f=search_frame: f.config(bg=self.colors['hover_bg']))
            widget.bind('<Leave>', lambda e, f=search_frame: f.config(bg=self.colors['bg_secondary']))
        
        # Кнопка пользователя
        user_btn = tk.Button(topbar,
                           text=self.icons['user'],
                           font=("Segoe UI", 14),
                           bg=self.colors['bg_secondary'],
                           fg=self.colors['text'],
                           activebackground=self.colors['hover_bg'],
                           activeforeground=self.colors['text'],
                           bd=0,
                           width=3,
                           height=1,
                           command=lambda: self.show_message("Профиль"))
        user_btn.pack(side=tk.RIGHT, padx=(10, 0))
        self.bind_hover_effect(user_btn, self.colors['bg_secondary'], self.colors['hover_bg'])
    
    def on_search_focus_in(self, event):
        """Обработчик фокуса на поле поиска"""
        if self.search_entry.get() == "Поиск исполнителей, альбомов или треков":
            self.search_entry.delete(0, END)
            self.search_entry.config(fg=self.colors['text'])
    
    def on_search_focus_out(self, event):
        """Обработчик потери фокуса полем поиска"""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Поиск исполнителей, альбомов или треков")
            self.search_entry.config(fg=self.colors['text_tertiary'])
    
    def create_main_content(self, parent):
        """Создание основного контента"""
        content_frame = tk.Frame(parent, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Создаем Notebook
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Настройка стиля вкладок
        style = ttk.Style()
        style.configure('TNotebook', background=self.colors['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_secondary'],
                       padding=[15, 5])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['bg_tertiary'])],
                 foreground=[('selected', self.colors['text'])])
        
        # Вкладка "Главная"
        self.create_home_tab()
        
        # Вкладка "Медиатека"
        self.create_library_tab()
        
        # Вкладка "Альбомы"
        self.create_albums_tab()
        
        # Вкладка "Треки"
        self.create_tracks_tab()
    
    def create_home_tab(self):
        """Создание вкладки главной страницы"""
        home_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(home_tab, text="Главная")
        
        # Контейнер с прокруткой
        home_canvas = tk.Canvas(home_tab, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(home_tab, orient="vertical", command=home_canvas.yview)
        scrollable_frame = tk.Frame(home_canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: home_canvas.configure(scrollregion=home_canvas.bbox("all"))
        )
        
        home_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        home_canvas.configure(yscrollcommand=scrollbar.set)
        
        home_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Связываем прокрутку колесиком мыши
        home_canvas.bind_all("<MouseWheel>", 
                           lambda e: home_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Содержимое главной страницы
        content_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Приветствие
        welcome_label = tk.Label(content_frame,
                               text="Добро пожаловать в Music Player",
                               font=("Segoe UI", 24, "bold"),
                               bg=self.colors['bg'],
                               fg=self.colors['text'])
        welcome_label.pack(anchor='w', pady=(0, 10))
        
        desc_label = tk.Label(content_frame,
                            text="Ищите музыку, создавайте плейлисты и наслаждайтесь любимыми треками",
                            font=("Segoe UI", 14),
                            bg=self.colors['bg'],
                            fg=self.colors['text_secondary'])
        desc_label.pack(anchor='w', pady=(0, 40))
        
        # Быстрый поиск
        quick_search_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        quick_search_frame.pack(fill=tk.X, pady=(0, 40))
        
        tk.Label(quick_search_frame,
               text="Быстрый поиск:",
               font=("Segoe UI", 16, "bold"),
               bg=self.colors['bg'],
               fg=self.colors['text']).pack(anchor='w', pady=(0, 15))
        
        # Кнопки популярных запросов
        popular_queries = ["The Weeknd", "Taylor Swift", "Drake", "Billie Eilish", "Dua Lipa"]
        queries_frame = tk.Frame(quick_search_frame, bg=self.colors['bg'])
        queries_frame.pack(fill=tk.X)
        
        for query in popular_queries:
            btn = tk.Button(queries_frame,
                          text=query,
                          font=("Segoe UI", 11),
                          bg=self.colors['card_bg'],
                          fg=self.colors['text'],
                          activebackground=self.colors['hover_bg'],
                          activeforeground=self.colors['text'],
                          bd=0,
                          padx=20,
                          pady=10,
                          command=lambda q=query: self.quick_search(q))
            btn.pack(side=tk.LEFT, padx=5)
            self.bind_hover_effect(btn, self.colors['card_bg'], self.colors['hover_bg'])
        
        # Рекомендации
        tk.Label(content_frame,
               text="Рекомендации:",
               font=("Segoe UI", 16, "bold"),
               bg=self.colors['bg'],
               fg=self.colors['text']).pack(anchor='w', pady=(0, 15))
        
        # Карточки рекомендаций
        recommendations = [
            (self.icons['music_note'], "Популярные хиты", "Самые прослушиваемые треки"),
            (self.icons['album'], "Новые альбомы", "Свежие релизы недели"),
            (self.icons['artist'], "Открытия года", "Новые таланты 2024"),
        ]
        
        rec_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        rec_frame.pack(fill=tk.X)
        
        for icon, title, desc in recommendations:
            card = self.create_recommendation_card(rec_frame, icon, title, desc)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    
    def create_recommendation_card(self, parent, icon, title, description):
        """Создание карточки рекомендации"""
        card = tk.Frame(parent,
                       bg=self.colors['card_bg'],
                       width=200,
                       height=150)
        
        icon_label = tk.Label(card,
                            text=icon,
                            font=("Segoe UI", 32),
                            bg=self.colors['card_bg'],
                            fg=self.colors['text'])
        icon_label.pack(pady=(20, 10))
        
        title_label = tk.Label(card,
                             text=title,
                             font=("Segoe UI", 14, "bold"),
                             bg=self.colors['card_bg'],
                             fg=self.colors['text'])
        title_label.pack()
        
        desc_label = tk.Label(card,
                            text=description,
                            font=("Segoe UI", 11),
                            bg=self.colors['card_bg'],
                            fg=self.colors['text_secondary'],
                            wraplength=180)
        desc_label.pack(pady=(5, 20))
        
        # Эффект при наведении
        self.bind_card_hover_effect(card)
        
        return card
    
    def create_library_tab(self):
        """Создание вкладки медиатеки"""
        library_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(library_tab, text="Медиатека")
        
        library_label = tk.Label(library_tab,
                               text="Ваша медиатека",
                               font=("Segoe UI", 24, "bold"),
                               bg=self.colors['bg'],
                               fg=self.colors['text'])
        library_label.pack(pady=50)
        
        # Показываем сообщение, так как функционал в разработке
        message_label = tk.Label(library_tab,
                               text="Раздел в разработке\n\nЗдесь будут отображаться\nваши сохраненные треки\nи плейлисты",
                               font=("Segoe UI", 14),
                               bg=self.colors['bg'],
                               fg=self.colors['text_secondary'],
                               justify='center')
        message_label.pack(pady=20)
    
    def create_albums_tab(self):
        """Создание вкладки альбомов"""
        albums_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(albums_tab, text="Альбомы")
        
        # Фрейм для содержимого
        self.albums_content = tk.Frame(albums_tab, bg=self.colors['bg'])
        self.albums_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок (будет обновляться при поиске)
        self.albums_title = tk.Label(self.albums_content,
                                   text="Найденные альбомы",
                                   font=("Segoe UI", 18, "bold"),
                                   bg=self.colors['bg'],
                                   fg=self.colors['text'])
        self.albums_title.pack(anchor='w', pady=(0, 20))
        
        # Контейнер для альбомов (сетка)
        self.albums_container = tk.Frame(self.albums_content, bg=self.colors['bg'])
        self.albums_container.pack(fill=tk.BOTH, expand=True)
        
        # Изначальное сообщение
        self.show_initial_message(self.albums_container, 
                                "🔍", 
                                "Начните поиск, чтобы увидеть альбомы здесь")
    
    def create_tracks_tab(self):
        """Создание вкладки треков"""
        tracks_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tracks_tab, text="Треки")
        
        # Фрейм для содержимого
        self.tracks_content = tk.Frame(tracks_tab, bg=self.colors['bg'])
        self.tracks_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Заголовок и кнопки
        header_frame = tk.Frame(self.tracks_content, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.tracks_title = tk.Label(header_frame,
                                   text="Найденные треки",
                                   font=("Segoe UI", 18, "bold"),
                                   bg=self.colors['bg'],
                                   fg=self.colors['text'])
        self.tracks_title.pack(side=tk.LEFT)
        
        # Кнопка воспроизвести все
        self.play_all_btn = tk.Button(header_frame,
                                    text=f"{self.icons['play']}  Воспроизвести все",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=self.colors['accent'],
                                    fg=self.colors['text'],
                                    activebackground=self.colors['accent_hover'],
                                    activeforeground=self.colors['text'],
                                    bd=0,
                                    padx=20,
                                    pady=8,
                                    state='disabled',
                                    command=self.play_all_tracks)
        self.play_all_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Контейнер для списка треков
        self.tracks_container = tk.Frame(self.tracks_content, bg=self.colors['bg'])
        self.tracks_container.pack(fill=tk.BOTH, expand=True)
        
        # Изначальное сообщение
        self.show_initial_message(self.tracks_container,
                                "🎵",
                                "Начните поиск, чтобы увидеть треки здесь")
    
    def create_player_bar(self, parent):
        """Создание нижней панели плеера"""
        player_bar = tk.Frame(parent, bg=self.colors['bg_secondary'], height=80)
        player_bar.pack(fill=tk.X, side=tk.BOTTOM)
        player_bar.pack_propagate(False)
        
        # Левая часть (информация о треке)
        track_info_frame = tk.Frame(player_bar, bg=self.colors['bg_secondary'], width=300)
        track_info_frame.pack(side=tk.LEFT, fill=tk.Y)
        track_info_frame.pack_propagate(False)
        
        # Обложка трека
        self.cover_label = tk.Label(track_info_frame,
                                  text="💿",
                                  font=("Segoe UI", 24),
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_secondary'])
        self.cover_label.pack(side=tk.LEFT, padx=15)
        
        # Информация
        info_frame = tk.Frame(track_info_frame, bg=self.colors['bg_secondary'])
        info_frame.pack(side=tk.LEFT, fill=tk.Y, pady=15)
        
        self.track_title_label = tk.Label(info_frame,
                                        text="Трек не выбран",
                                        font=("Segoe UI", 12, "bold"),
                                        bg=self.colors['bg_secondary'],
                                        fg=self.colors['text'])
        self.track_title_label.pack(anchor='w')
        
        self.artist_label = tk.Label(info_frame,
                                   text="Выберите трек для воспроизведения",
                                   font=("Segoe UI", 10),
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_secondary'])
        self.artist_label.pack(anchor='w')
        
        # Кнопка лайка
        self.like_btn = tk.Button(track_info_frame,
                                text=self.icons['heart_outline'],
                                font=("Segoe UI", 14),
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['text_secondary'],
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['accent'],
                                bd=0,
                                command=self.toggle_like)
        self.like_btn.pack(side=tk.RIGHT, padx=15)
        
        # Центральная часть (управление плеером)
        player_controls = tk.Frame(player_bar, bg=self.colors['bg_secondary'])
        player_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        
        # Кнопки управления
        controls_frame = tk.Frame(player_controls, bg=self.colors['bg_secondary'])
        controls_frame.pack(expand=True)
        
        # Кнопка перемешивания
        self.shuffle_btn = tk.Button(controls_frame,
                                   text=self.icons['shuffle'],
                                   font=("Segoe UI", 16),
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_secondary'],
                                   activebackground=self.colors['bg_secondary'],
                                   activeforeground=self.colors['text'],
                                   bd=0,
                                   command=self.toggle_shuffle)
        self.shuffle_btn.pack(side=tk.LEFT, padx=10)
        
        # Предыдущий трек
        self.prev_btn = tk.Button(controls_frame,
                                text=self.icons['prev'],
                                font=("Segoe UI", 20),
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['text'],
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['text'],
                                bd=0,
                                command=self.play_previous)
        self.prev_btn.pack(side=tk.LEFT, padx=10)
        
        # Play/Pause
        self.play_pause_btn = tk.Button(controls_frame,
                                      text=self.icons['play'],
                                      font=("Segoe UI", 24),
                                      bg=self.colors['text'],
                                      fg=self.colors['bg_secondary'],
                                      activebackground=self.colors['text_secondary'],
                                      activeforeground=self.colors['bg_secondary'],
                                      bd=0,
                                      width=3,
                                      height=1,
                                      command=self.toggle_play_pause,
                                      state='disabled')
        self.play_pause_btn.pack(side=tk.LEFT, padx=10)
        
        # Следующий трек
        self.next_btn = tk.Button(controls_frame,
                                text=self.icons['next'],
                                font=("Segoe UI", 20),
                                bg=self.colors['bg_secondary'],
                                fg=self.colors['text'],
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['text'],
                                bd=0,
                                command=self.play_next)
        self.next_btn.pack(side=tk.LEFT, padx=10)
        
        # Повтор
        self.repeat_btn = tk.Button(controls_frame,
                                  text=self.icons['repeat'],
                                  font=("Segoe UI", 16),
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_secondary'],
                                  activebackground=self.colors['bg_secondary'],
                                  activeforeground=self.colors['text'],
                                  bd=0,
                                  command=self.toggle_repeat)
        self.repeat_btn.pack(side=tk.LEFT, padx=10)
        
        # Прогресс-бар и время
        progress_frame = tk.Frame(player_controls, bg=self.colors['bg_secondary'])
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.time_current = tk.Label(progress_frame,
                                   text="0:00",
                                   font=("Segoe UI", 10),
                                   bg=self.colors['bg_secondary'],
                                   fg=self.colors['text_secondary'])
        self.time_current.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Scale(progress_frame,
                                    from_=0,
                                    to=100,
                                    value=0,
                                    orient='horizontal',
                                    length=400)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        self.time_total = tk.Label(progress_frame,
                                 text="0:00",
                                 font=("Segoe UI", 10),
                                 bg=self.colors['bg_secondary'],
                                 fg=self.colors['text_secondary'])
        self.time_total.pack(side=tk.RIGHT)
        
        # Правая часть (громкость и доп. функции)
        right_controls = tk.Frame(player_bar, bg=self.colors['bg_secondary'], width=200)
        right_controls.pack(side=tk.RIGHT, fill=tk.Y)
        right_controls.pack_propagate(False)
        
        # Кнопка очереди
        self.queue_btn = tk.Button(right_controls,
                                 text=self.icons['queue'],
                                 font=("Segoe UI", 16),
                                 bg=self.colors['bg_secondary'],
                                 fg=self.colors['text_secondary'],
                                 activebackground=self.colors['bg_secondary'],
                                 activeforeground=self.colors['text'],
                                 bd=0,
                                 command=lambda: self.show_message("Очередь"))
        self.queue_btn.pack(side=tk.LEFT, padx=5)
        
        # Кнопка устройства
        self.device_btn = tk.Button(right_controls,
                                  text=self.icons['device'],
                                  font=("Segoe UI", 16),
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_secondary'],
                                  activebackground=self.colors['bg_secondary'],
                                  activeforeground=self.colors['text'],
                                  bd=0,
                                  command=lambda: self.show_message("Устройства"))
        self.device_btn.pack(side=tk.LEFT, padx=5)
        
        # Громкость
        volume_frame = tk.Frame(right_controls, bg=self.colors['bg_secondary'])
        volume_frame.pack(side=tk.LEFT, padx=10)
        
        self.volume_icon = tk.Label(volume_frame,
                                  text=self.icons['volume'],
                                  font=("Segoe UI", 16),
                                  bg=self.colors['bg_secondary'],
                                  fg=self.colors['text_secondary'])
        self.volume_icon.pack(side=tk.LEFT)
        
        self.volume_scale = ttk.Scale(volume_frame,
                                    from_=0,
                                    to=100,
                                    value=70,
                                    command=self.set_volume,
                                    orient='horizontal',
                                    length=80)
        self.volume_scale.pack(side=tk.LEFT, padx=10)
    
    def bind_hover_effect(self, widget, normal_color, hover_color):
        """Привязка эффекта наведения для виджета"""
        widget.bind('<Enter>', lambda e, w=widget, c=hover_color: w.config(bg=c))
        widget.bind('<Leave>', lambda e, w=widget, c=normal_color: w.config(bg=c))
    
    def bind_card_hover_effect(self, card):
        """Привязка эффекта наведения для карточки"""
        bg_color = card.cget('bg')
        
        def on_enter(e):
            card.config(bg=self.colors['hover_bg'])
            for child in card.winfo_children():
                child.config(bg=self.colors['hover_bg'])
        
        def on_leave(e):
            card.config(bg=bg_color)
            for child in card.winfo_children():
                child.config(bg=bg_color)
        
        card.bind('<Enter>', on_enter)
        card.bind('<Leave>', on_leave)
        
        for child in card.winfo_children():
            child.bind('<Enter>', on_enter)
            child.bind('<Leave>', on_leave)
    
    def show_initial_message(self, parent, icon, message):
        """Показать начальное сообщение в контейнере"""
        for widget in parent.winfo_children():
            widget.destroy()
        
        message_frame = tk.Frame(parent, bg=self.colors['bg'])
        message_frame.pack(expand=True, fill=tk.BOTH)
        
        icon_label = tk.Label(message_frame,
                            text=icon,
                            font=("Segoe UI", 48),
                            bg=self.colors['bg'],
                            fg=self.colors['text_secondary'])
        icon_label.pack(pady=(50, 20))
        
        text_label = tk.Label(message_frame,
                            text=message,
                            font=("Segoe UI", 14),
                            bg=self.colors['bg'],
                            fg=self.colors['text_secondary'])
        text_label.pack()
    
    def quick_search(self, query):
        """Быстрый поиск по популярному запросу"""
        self.search_var.set(query)
        self.search_entry.delete(0, END)
        self.search_entry.insert(0, query)
        self.search_entry.config(fg=self.colors['text'])
        self.search_music()
    
    def search_music(self):
        """Поиск музыки"""
        query = self.search_var.get().strip()
        if not query or query == "Поиск исполнителей, альбомов или треков":
            messagebox.showwarning("Внимание", "Введите запрос для поиска")
            return
        
        # Показываем индикатор загрузки
        self.show_loading()
        
        # Запускаем поиск в отдельном потоке
        threading.Thread(target=self._perform_search, 
                        args=(query,), daemon=True).start()
    
    def _perform_search(self, query):
        """Выполнение поиска в отдельном потоке"""
        try:
            # Формируем URL для поиска
            search_url = f"{self.base_url}/search?q={quote(query)}"
            
            # Получаем страницу
            response = self.session.get(search_url)
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем альбомы
            albums = self._parse_albums(soup)
            
            # Извлекаем треки
            tracks = self._parse_tracks(soup)
            
            # Обновляем GUI в основном потоке
            self.root.after(0, self._update_search_results, albums, tracks, query)
            
        except Exception as e:
            self.root.after(0, self._show_error, f"Ошибка поиска: {str(e)}")
        finally:
            self.root.after(0, self.hide_loading)
    
    def _parse_albums(self, soup):
        """Парсинг списка альбомов"""
        albums = []
        album_items = soup.find_all('li', class_='album-item')
        
        for item in album_items:
            # Название альбома
            title_elem = item.find('span', class_='album-title')
            if title_elem:
                title = title_elem.get_text(strip=True)
                
                # Ссылка на альбом
                link_elem = item.find('a', href=True)
                if link_elem:
                    album_url = urljoin(self.base_url, link_elem['href'])
                    
                    # Обложка альбома
                    img_elem = item.find('span', class_='album-image')
                    cover_url = None
                    if img_elem and 'background-image' in img_elem.get('style', ''):
                        style = img_elem['style']
                        match = re.search(r"url\('(.+?)'\)", style)
                        if match:
                            cover_url = match.group(1)
                    
                    albums.append({
                        'title': title,
                        'url': album_url,
                        'cover': cover_url,
                        'type': 'album'
                    })
        
        return albums
    
    def _parse_tracks(self, soup):
        """Парсинг списка треков"""
        tracks = []
        track_items = soup.find_all('li', class_='tracks__item')
        
        for item in track_items:
            # Извлекаем данные из data-musmeta атрибута
            musmeta = item.get('data-musmeta')
            if musmeta:
                try:
                    data = json.loads(musmeta)
                    
                    # Название трека и исполнитель из текста
                    title_elem = item.find('div', class_='track__title')
                    desc_elem = item.find('div', class_='track__desc')
                    
                    title = title_elem.get_text(strip=True) if title_elem else data.get('title', '')
                    artist = desc_elem.get_text(strip=True) if desc_elem else data.get('artist', '')
                    
                    # Длительность
                    time_elem = item.find('div', class_='track__fulltime')
                    duration = time_elem.get_text(strip=True) if time_elem else ""
                    
                    tracks.append({
                        'title': title,
                        'artist': artist,
                        'url': data.get('url'),
                        'duration': duration,
                        'type': 'track'
                    })
                    
                except json.JSONDecodeError:
                    continue
        
        return tracks
    
    def _update_search_results(self, albums, tracks, query):
        """Обновление результатов поиска"""
        # Сохраняем результаты
        self.search_results = {
            'albums': albums,
            'tracks': tracks
        }
        
        # Обновляем альбомы
        self.update_albums_display(albums)
        
        # Обновляем треки
        self.update_tracks_display(tracks)
        
        # Активируем кнопку "Воспроизвести все"
        if tracks:
            self.play_all_btn.config(state='normal')
        
        # Переключаемся на вкладку альбомов
        self.notebook.select(2)
    
    def update_albums_display(self, albums):
        """Обновление отображения альбомов"""
        # Очищаем контейнер
        for widget in self.albums_container.winfo_children():
            widget.destroy()
        
        # Обновляем заголовок
        if albums:
            self.albums_title.config(text=f"Найдено альбомов: {len(albums)}")
        else:
            self.albums_title.config(text="Альбомы не найдены")
            self.show_initial_message(self.albums_container, 
                                    "💿", 
                                    "По данному запросу альбомы не найдены")
            return
        
        # Отображаем альбомы в сетке 4xN
        row, col = 0, 0
        max_cols = 4
        
        for album in albums[:20]:  # Ограничиваем 20 альбомами
            album_frame = self.create_album_card(album)
            album_frame.grid(row=row, column=col, padx=15, pady=15, sticky='nsew')
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Настраиваем расширение колонок
        for i in range(max_cols):
            self.albums_container.grid_columnconfigure(i, weight=1, uniform="albums")
    
    def create_album_card(self, album):
        """Создание карточки альбома"""
        card = tk.Frame(self.albums_container,
                       bg=self.colors['card_bg'],
                       width=200,
                       height=250)
        
        # Обложка альбома (эмодзи вместо реального изображения)
        cover_label = tk.Label(card,
                             text="💿",
                             font=("Segoe UI", 48),
                             bg=self.colors['card_bg'],
                             fg=self.colors['text_secondary'])
        cover_label.pack(pady=(20, 10))
        
        # Название альбома (обрезаем если слишком длинное)
        title = album['title']
        if len(title) > 30:
            title = title[:27] + "..."
        
        title_label = tk.Label(card,
                             text=title,
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colors['card_bg'],
                             fg=self.colors['text'],
                             wraplength=180,
                             justify='center')
        title_label.pack(padx=10)
        
        # Эффекты при наведении
        self.bind_card_hover_effect(card)
        
        return card
    
    def update_tracks_display(self, tracks):
        """Обновление отображения треков"""
        # Очищаем контейнер
        for widget in self.tracks_container.winfo_children():
            widget.destroy()
        
        # Обновляем заголовок
        if tracks:
            self.tracks_title.config(text=f"Найдено треков: {len(tracks)}")
        else:
            self.tracks_title.config(text="Треки не найдены")
            self.show_initial_message(self.tracks_container,
                                    "🎵",
                                    "По данному запросу треки не найдены")
            return
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(self.tracks_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tracks_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Связываем прокрутку колесиком мыши
        canvas.bind_all("<MouseWheel>", 
                       lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
        # Заголовки столбцов
        header_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_secondary'])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        headers = ["#", "НАЗВАНИЕ", "ИСПОЛНИТЕЛЬ", "🕒"]
        widths = [40, 300, 200, 60]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            label = tk.Label(header_frame,
                           text=header,
                           font=("Segoe UI", 10, "bold"),
                           bg=self.colors['bg_secondary'],
                           fg=self.colors['text_secondary'],
                           width=width // 10,
                           anchor='w' if i > 0 else 'center')
            label.pack(side=tk.LEFT, padx=(20 if i == 0 else 10, 0))
        
        # Добавляем треки
        for i, track in enumerate(tracks[:100], 1):  # Ограничиваем 100 треками
            self.create_track_row(scrollable_frame, i, track)
    
    def create_track_row(self, parent, index, track):
        """Создание строки с информацией о треке"""
        bg_color = self.colors['bg'] if index % 2 == 0 else self.colors['bg_secondary']
        
        row = tk.Frame(parent,
                      bg=bg_color,
                      height=50)
        row.pack(fill=tk.X, pady=1)
        
        # Номер
        num_label = tk.Label(row,
                           text=str(index),
                           font=("Segoe UI", 11),
                           bg=bg_color,
                           fg=self.colors['text_secondary'],
                           width=4)
        num_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Название
        title_label = tk.Label(row,
                             text=track['title'][:50] + ("..." if len(track['title']) > 50 else ""),
                             font=("Segoe UI", 12),
                             bg=bg_color,
                             fg=self.colors['text'],
                             anchor='w',
                             width=30)
        title_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Исполнитель
        artist_label = tk.Label(row,
                              text=track['artist'][:30] + ("..." if len(track['artist']) > 30 else ""),
                              font=("Segoe UI", 11),
                              bg=bg_color,
                              fg=self.colors['text_secondary'],
                              anchor='w',
                              width=20)
        artist_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Длительность
        duration_label = tk.Label(row,
                                text=track.get('duration', '0:00'),
                                font=("Segoe UI", 11),
                                bg=bg_color,
                                fg=self.colors['text_secondary'],
                                width=6)
        duration_label.pack(side=tk.RIGHT, padx=20)
        
        # Кнопка воспроизведения (скрыта по умолчанию)
        play_btn = tk.Button(row,
                           text="▶",
                           font=("Segoe UI", 12),
                           bg=self.colors['accent'],
                           fg=self.colors['text'],
                           bd=0,
                           width=2,
                           height=1,
                           command=lambda t=track: self.play_track(t))
        
        # Позиционируем кнопку
        play_btn.place(relx=0.02, rely=0.5, anchor='w')
        play_btn.lower()  # Отправляем на задний план
        
        # Эффекты при наведении
        def on_enter(e):
            for child in row.winfo_children():
                child.config(bg=self.colors['hover_bg'])
            play_btn.lift()
        
        def on_leave(e):
            for child in row.winfo_children():
                child.config(bg=bg_color)
            play_btn.lower()
        
        row.bind('<Enter>', on_enter)
        row.bind('<Leave>', on_leave)
        
        for child in row.winfo_children():
            child.bind('<Enter>', on_enter)
            child.bind('<Leave>', on_leave)
    
    def play_track(self, track):
        """Воспроизведение выбранного трека"""
        self.current_track = track
        
        # Обновляем информацию в плеере
        self.track_title_label.config(text=track['title'])
        self.artist_label.config(text=track['artist'])
        
        # Активируем кнопки управления
        self.play_pause_btn.config(state='normal', text=self.icons['pause'])
        
        # Обновляем время (если есть длительность)
        if 'duration' in track:
            self.time_total.config(text=track['duration'])
        
        # Запускаем воспроизведение в отдельном потоке
        threading.Thread(target=self._stream_track,
                       args=(track['url'],), daemon=True).start()
        
        self.is_playing = True
        self.paused = False
    
    def _stream_track(self, url):
        """Потоковое воспроизведение"""
        try:
            # Скачиваем трек
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Сохраняем во временный файл
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp.write(chunk)
                tmp_path = tmp.name
            
            # Воспроизводим
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            
            # Удаляем временный файл после завершения
            import atexit
            def cleanup():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            atexit.register(cleanup)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Ошибка воспроизведения: {str(e)}"))
    
    def play_all_tracks(self):
        """Воспроизведение всех треков"""
        if self.search_results['tracks']:
            # Начинаем с первого трека
            self.play_track(self.search_results['tracks'][0])
    
    def toggle_play_pause(self):
        """Переключение воспроизведение/пауза"""
        if self.is_playing:
            if self.paused:
                pygame.mixer.music.unpause()
                self.play_pause_btn.config(text=self.icons['pause'])
                self.paused = False
            else:
                pygame.mixer.music.pause()
                self.play_pause_btn.config(text=self.icons['play'])
                self.paused = True
        elif self.current_track:
            self.play_track(self.current_track)
    
    def play_previous(self):
        """Воспроизведение предыдущего трека"""
        self.show_message("Предыдущий трек")
    
    def play_next(self):
        """Воспроизведение следующего трека"""
        self.show_message("Следующий трек")
    
    def toggle_shuffle(self):
        """Переключение перемешивания"""
        self.show_message("Перемешивание")
    
    def toggle_repeat(self):
        """Переключение повтора"""
        self.show_message("Повтор")
    
    def toggle_like(self):
        """Переключение лайка"""
        if self.like_btn.cget('text') == self.icons['heart_outline']:
            self.like_btn.config(text=self.icons['heart'], fg=self.colors['accent'])
        else:
            self.like_btn.config(text=self.icons['heart_outline'], fg=self.colors['text_secondary'])
    
    def set_volume(self, value):
        """Установка громкости"""
        volume = float(value) / 100
        pygame.mixer.music.set_volume(volume)
    
    def show_loading(self):
        """Показать индикатор загрузки"""
        # Можно добавить индикатор загрузки
        pass
    
    def hide_loading(self):
        """Скрыть индикатор загрузки"""
        pass
    
    def show_message(self, message):
        """Показать информационное сообщение"""
        messagebox.showinfo("Информация", f"{message} - функция в разработке")
    
    def _show_error(self, message):
        """Показать ошибку"""
        messagebox.showerror("Ошибка", message)

def main():
    root = tk.Tk()
    
    # Центрирование окна
    window_width = 1200
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = ModernMusicPlayer(root)
    root.mainloop()

if __name__ == "__main__":
    # Установите необходимые библиотеки:
    # pip install requests beautifulsoup4 pygame
    
    main()