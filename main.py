from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
from datetime import datetime, timedelta
from kivy.clock import Clock, mainthread
from kivy.config import Config
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty, BooleanProperty, ColorProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.utils import platform
from kivymd import fonts_path
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFillRoundFlatButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.list import OneLineListItem, TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget, MDList, ThreeLineAvatarIconListItem, IRightBodyTouch, ILeftBody
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivy.uix.camera import Camera
try:
    from pyzbar.pyzbar import decode
    from PIL import Image as PILImage
except ImportError:
    decode = None
    print("[WARNING] pyzbar library not found.")
from kivymd.uix.list import IconRightWidget, IconLeftWidget, TwoLineAvatarIconListItem
from kivy.uix.modalview import ModalView
from kivy.graphics.context_instructions import Rotate
from kivy.graphics.context_instructions import PushMatrix, PopMatrix
if platform == 'android':
    from jnius import autoclass
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
    UUID = autoclass('java.util.UUID')
    
    # --- إضافة: استيراد مولد النغمات ---
    AudioManager = autoclass('android.media.AudioManager')
    ToneGenerator = autoclass('android.media.ToneGenerator')
    # -----------------------------------
import arabic_reshaper
import json
import os
import random
import re
import socket
import sys
import textwrap
import threading
import time

if platform == 'android':
    from jnius import autoclass
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
    UUID = autoclass('java.util.UUID')
app_dir = os.path.dirname(os.path.abspath(__file__))

FONT_FILE = os.path.join(app_dir, 'font.ttf')
custom_font_loaded = False
try:
    if os.path.exists(FONT_FILE) and os.path.isfile(FONT_FILE):
        print(f'[INFO] Found custom font at: {FONT_FILE}')
        LabelBase.register(name='ArabicFont', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='Roboto', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='RobotoMedium', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        LabelBase.register(name='RobotoBold', fn_regular=FONT_FILE, fn_bold=FONT_FILE)
        custom_font_loaded = True
    else:
        print('[WARNING] Custom font file NOT found.')
except Exception as e:
    print(f'[ERROR] Critical error loading custom font: {e}')
if not custom_font_loaded:
    fallback_regular = os.path.join(fonts_path, 'Roboto-Regular.ttf')
    fallback_bold = os.path.join(fonts_path, 'Roboto-Bold.ttf')
    try:
        LabelBase.register(name='ArabicFont', fn_regular=fallback_regular, fn_bold=fallback_bold)
    except Exception:
        LabelBase.register(name='ArabicFont', fn_regular=None, fn_bold=None)

reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': True, 'use_unshaped_instead_of_isolated': True})

DEFAULT_PORT = '5000'

KV_BUILDER = '\n<LeftButtonsContainer>:\n    adaptive_width: True\n    spacing: "4dp"\n    padding: "4dp"\n    pos_hint: {"center_y": .5}\n\n<RightButtonsContainer>:\n    adaptive_width: True\n    spacing: "8dp"\n    pos_hint: {"center_y": .5}\n\n<CustomHistoryItem>:\n    orientation: "horizontal"\n    size_hint_y: None\n    height: dp(80)\n    padding: dp(10)\n    spacing: dp(5)\n    radius: [10]\n    elevation: 1\n    ripple_behavior: True\n    md_bg_color: root.bg_color\n    on_release: root.on_tap_action()\n    \n    MDIcon:\n        icon: root.icon\n        theme_text_color: "Custom"\n        text_color: root.icon_color\n        pos_hint: {"center_y": .5}\n        font_size: "32sp"\n        size_hint_x: None\n        width: dp(40)\n        \n    MDBoxLayout:\n        orientation: "vertical"\n        pos_hint: {"center_y": .5}\n        spacing: dp(4)\n        size_hint_x: 0.5\n        \n        MDLabel:\n            text: root.text\n            bold: True\n            font_style: "Subtitle1"\n            font_size: "16sp"\n            theme_text_color: "Primary"\n            shorten: True\n            shorten_from: \'right\'\n            font_name: \'ArabicFont\'\n            markup: True\n            \n        MDLabel:\n            text: root.secondary_text\n            font_style: "Caption"\n            theme_text_color: "Secondary"\n            font_name: \'ArabicFont\'\n            \n    MDLabel:\n        text: root.right_text\n        halign: "right"\n        pos_hint: {"center_y": .5}\n        font_style: "Subtitle2"\n        bold: True\n        theme_text_color: "Custom"\n        text_color: root.icon_color\n        size_hint_x: 0.3\n        font_name: \'ArabicFont\'\n\n    MDIconButton:\n        icon: "pencil"\n        theme_text_color: "Custom"\n        text_color: (0, 0.5, 0.8, 1)\n        pos_hint: {"center_y": .5}\n        on_release: root.on_edit_action()\n\n<ProductRecycleItem>:\n    orientation: \'vertical\'\n    size_hint_y: None\n    height: dp(90)\n    padding: 0\n    spacing: 0\n    \n    MDCard:\n        orientation: \'horizontal\'\n        padding: dp(10)\n        spacing: dp(10)\n        radius: [8]\n        elevation: 1\n        ripple_behavior: True\n        on_release: root.on_tap()\n        md_bg_color: (1, 1, 1, 1)\n        \n        MDIcon:\n            icon: root.icon_name\n            theme_text_color: "Custom"\n            text_color: root.icon_color\n            size_hint_x: None\n            width: dp(40)\n            pos_hint: {\'center_y\': .5}\n            font_size: \'32sp\'\n\n        MDBoxLayout:\n            orientation: \'vertical\'\n            pos_hint: {\'center_y\': .5}\n            spacing: dp(5)\n            \n            MDLabel:\n                text: root.text_name\n                font_style: "Subtitle1"\n                bold: True\n                shorten: True\n                shorten_from: \'right\'\n                font_size: \'17sp\'\n                theme_text_color: "Custom"\n                text_color: (0.1, 0.1, 0.1, 1)\n                font_name: \'ArabicFont\'\n            \n            MDBoxLayout:\n                orientation: \'horizontal\'\n                spacing: dp(10)\n                \n                MDLabel:\n                    text: root.text_price\n                    font_style: "H6"\n                    theme_text_color: "Custom"\n                    text_color: root.price_color\n                    bold: True\n                    size_hint_x: 0.6\n                    font_size: \'20sp\'\n                    font_name: \'ArabicFont\'\n                \n                MDLabel:\n                    text: root.text_stock\n                    theme_text_color: "Custom"\n                    text_color: (0.1, 0.1, 0.1, 1)\n                    halign: \'right\'\n                    size_hint_x: 0.4\n                    bold: True\n                    font_size: \'16sp\'\n                    font_name: \'ArabicFont\'\n\n<ProductRecycleView>:\n    viewclass: \'ProductRecycleItem\'\n    RecycleBoxLayout:\n        default_size: None, dp(95)\n        default_size_hint: 1, None\n        size_hint_y: None\n        height: self.minimum_height\n        orientation: \'vertical\'\n        spacing: dp(4)\n        padding: dp(5)\n\n<HistoryRecycleItem>:\n    orientation: "horizontal"\n    size_hint_y: None\n    height: dp(80)\n    padding: dp(10)\n    spacing: dp(5)\n    radius: [10]\n    elevation: 1\n    ripple_behavior: True\n    md_bg_color: root.bg_color\n    on_release: root.on_tap()\n\n    MDIcon:\n        icon: root.icon_name\n        theme_text_color: "Custom"\n        text_color: root.icon_color\n        pos_hint: {"center_y": .5}\n        font_size: "32sp"\n        size_hint_x: None\n        width: dp(40)\n\n    MDBoxLayout:\n        orientation: "vertical"\n        pos_hint: {"center_y": .5}\n        spacing: dp(4)\n        size_hint_x: 1\n\n        MDLabel:\n            text: root.text_primary\n            bold: True\n            font_style: "Subtitle1"\n            font_size: "16sp"\n            theme_text_color: "Primary"\n            text_size: self.width, None\n            halign: \'left\'\n            font_name: \'ArabicFont\'\n            markup: True\n\n        MDLabel:\n            text: root.text_secondary\n            font_style: "Caption"\n            theme_text_color: "Secondary"\n            font_name: \'ArabicFont\'\n\n    MDLabel:\n        text: root.text_amount\n        halign: "right"\n        pos_hint: {"center_y": .5}\n        font_style: "Subtitle2"\n        bold: True\n        theme_text_color: "Custom"\n        text_color: root.icon_color\n        size_hint_x: None\n        width: dp(110)\n        font_name: \'ArabicFont\'\n\n<HistoryRecycleView>:\n    viewclass: \'HistoryRecycleItem\'\n    RecycleBoxLayout:\n        default_size: None, dp(85)\n        default_size_hint: 1, None\n        size_hint_y: None\n        height: self.minimum_height\n        orientation: \'vertical\'\n        spacing: dp(5)\n        padding: dp(5)\n\n<EntityRecycleItem>:\n    orientation: "horizontal"\n    size_hint_y: None\n    height: dp(80)\n    padding: dp(10)\n    spacing: dp(15)\n    ripple_behavior: True\n    md_bg_color: (1, 1, 1, 1)\n    radius: [0]\n    on_release: root.on_tap()\n\n    MDIcon:\n        icon: root.icon_name\n        theme_text_color: "Custom"\n        text_color: root.icon_color\n        pos_hint: {"center_y": .5}\n        font_size: "32sp"\n        size_hint_x: None\n        width: dp(40)\n\n    MDBoxLayout:\n        orientation: "vertical"\n        pos_hint: {"center_y": .5}\n        size_hint_x: 1\n        spacing: dp(4)\n\n        MDLabel:\n            text: root.text_name\n            bold: True\n            font_style: "Subtitle1"\n            font_name: \'ArabicFont\'\n            theme_text_color: "Custom"\n            text_color: (0.1, 0.1, 0.1, 1)\n            shorten: True\n            shorten_from: \'right\'\n            valign: \'center\'\n\n        MDLabel:\n            text: root.text_balance\n            font_style: "Caption"\n            font_name: \'ArabicFont\'\n            markup: True\n            theme_text_color: "Secondary"\n            valign: \'top\'\n\n<EntityRecycleView>:\n    viewclass: \'EntityRecycleItem\'\n    RecycleBoxLayout:\n        default_size: None, dp(80)\n        default_size_hint: 1, None\n        size_hint_y: None\n        height: self.minimum_height\n        orientation: \'vertical\'\n        spacing: dp(2)\n        padding: dp(0)\n\n<MgmtEntityRecycleItem>:\n    orientation: "horizontal"\n    size_hint_y: None\n    height: dp(80)\n    padding: dp(10)\n    spacing: dp(5)\n    ripple_behavior: True\n    md_bg_color: (1, 1, 1, 1)\n    on_release: root.on_pay()\n\n    MDIcon:\n        icon: "account-circle"\n        theme_text_color: "Custom"\n        text_color: (0.5, 0.5, 0.5, 1)\n        pos_hint: {"center_y": .5}\n        font_size: "32sp"\n        size_hint_x: None\n        width: dp(40)\n\n    MDBoxLayout:\n        orientation: "vertical"\n        pos_hint: {"center_y": .5}\n        size_hint_x: 1\n        spacing: dp(2)\n        padding: [dp(10), 0, 0, 0]\n\n        MDLabel:\n            text: root.text_name\n            bold: True\n            font_style: "Subtitle1"\n            font_name: \'ArabicFont\'\n            theme_text_color: "Custom"\n            text_color: (0.1, 0.1, 0.1, 1)\n            shorten: True\n            shorten_from: \'right\'\n            halign: "left"\n\n        MDLabel:\n            text: root.text_balance\n            font_style: "Caption"\n            font_name: \'ArabicFont\'\n            markup: True\n            theme_text_color: "Secondary"\n            halign: "left"\n\n    MDIconButton:\n        icon: "clock-time-eight-outline"\n        theme_text_color: "Custom"\n        text_color: (0, 0.5, 0.5, 1)\n        pos_hint: {"center_y": .5}\n        on_release: root.on_history()\n\n<MgmtEntityRecycleView>:\n    viewclass: \'MgmtEntityRecycleItem\'\n    RecycleBoxLayout:\n        default_size: None, dp(80)\n        default_size_hint: 1, None\n        size_hint_y: None\n        height: self.minimum_height\n        orientation: \'vertical\'\n        spacing: dp(2)\n        padding: dp(0)\n'

class DataValidator:

    @staticmethod
    def validate_ip(ip_address):
        if not ip_address or not isinstance(ip_address, str):
            return False
        return len(ip_address) > 3

class SmartTextField(MDTextField):

    def __init__(self, **kwargs):
        self._raw_text = ''
        self.base_direction = 'ltr'
        self.halign = 'left'
        self._input_reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': False, 'use_unshaped_instead_of_isolated': True})
        super().__init__(**kwargs)
        self.font_name = 'ArabicFont'
        self.font_name_hint_text = 'ArabicFont'

    def insert_text(self, substring, from_undo=False):
        self._raw_text += substring
        reshaped = self._input_reshaper.reshape(self._raw_text)
        bidi_text = get_display(reshaped)
        self.text = bidi_text
        self._update_alignment(self._raw_text)

    def do_backspace(self, from_undo=False, mode='bkspc'):
        if not self._raw_text:
            return
        self._raw_text = self._raw_text[:-1]
        reshaped = self._input_reshaper.reshape(self._raw_text)
        bidi_text = get_display(reshaped)
        self.text = bidi_text
        self._update_alignment(self._raw_text)

    def _update_alignment(self, text):
        if not text:
            self.halign = 'left'
            self.base_direction = 'ltr'
            return
        has_arabic = any(('\u0600' <= c <= 'ۿ' for c in text))
        if has_arabic:
            self.halign = 'right'
            self.base_direction = 'rtl'
        else:
            self.halign = 'left'
            self.base_direction = 'ltr'

    def get_value(self):
        if not self._raw_text and self.text:
            return self.text
        return self._raw_text

class LeftButtonsContainer(ILeftBody, MDBoxLayout):
    adaptive_width = True

class RightButtonsContainer(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True

class ProductRecycleItem(RecycleDataViewBehavior, MDBoxLayout):
    index = None
    text_name = StringProperty('')
    text_price = StringProperty('')
    text_stock = StringProperty('')
    icon_name = StringProperty('package-variant')
    icon_color = ListProperty([0, 0, 0, 1])
    price_color = ListProperty([0, 0, 0, 1])
    product_data = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.text_name = data.get('name', '')
        self.text_price = data.get('price_text', '')
        self.text_stock = data.get('stock_text', '')
        self.icon_name = data.get('icon', 'package-variant')
        self.icon_color = data.get('icon_color', [0, 0, 0, 1])
        self.price_color = data.get('price_color', [0, 0, 0, 1])
        self.product_data = data.get('raw_data')
        return super().refresh_view_attrs(rv, index, data)

    def on_tap(self):
        app = MDApp.get_running_app()
        if self.product_data:
            app.open_add_to_cart_dialog(self.product_data, app.current_mode)

class HistoryRecycleItem(RecycleDataViewBehavior, MDCard):
    index = None
    text_primary = StringProperty('')
    text_secondary = StringProperty('')
    text_amount = StringProperty('')
    icon_name = StringProperty('file')
    icon_color = ColorProperty([0, 0, 0, 1])
    bg_color = ColorProperty([1, 1, 1, 1])
    item_data = ObjectProperty(None, allownone=True)
    is_local = BooleanProperty(False)
    key = StringProperty('')

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        app = MDApp.get_running_app()
        self.text_primary = app.fix_text(data.get('raw_text', ''))
        self.text_secondary = app.fix_text(data.get('raw_sec', ''))
        self.text_amount = data.get('amount_text', '')
        self.icon_name = data.get('icon', 'file')
        self.icon_color = data.get('icon_color', [0, 0, 0, 1])
        self.bg_color = data.get('bg_color', [1, 1, 1, 1])
        self.item_data = data.get('raw_data')
        self.is_local = data.get('is_local', False)
        self.key = data.get('key', '')
        return super().refresh_view_attrs(rv, index, data)

    def on_tap(self):
        app = MDApp.get_running_app()
        if self.is_local:
            app.handle_pending_item(self.key, False)
        elif self.item_data:
            app.handle_server_history_item(self.item_data)

class MgmtEntityRecycleItem(RecycleDataViewBehavior, MDCard):
    index = None
    text_name = StringProperty('')
    text_balance = StringProperty('')
    entity_data = ObjectProperty(None, allownone=True)
    _long_press_event = None
    _is_long_press = False

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        app = MDApp.get_running_app()
        raw_name = data.get('raw_name', '')
        self.text_name = app.fix_text(raw_name) if app else raw_name
        self.text_balance = data.get('balance_text', '')
        self.entity_data = data.get('raw_data')
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._is_long_press = False
            self._long_press_event = Clock.schedule_once(lambda dt: self._trigger_long_press(), 0.7)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        if self._is_long_press:
            return True
        return super().on_touch_up(touch)

    def _trigger_long_press(self):
        self._is_long_press = True
        self.on_menu()

    def on_pay(self):
        if self._is_long_press:
            return
        app = MDApp.get_running_app()
        if self.entity_data:
            app.start_direct_payment_from_manager(self.entity_data)

    def on_menu(self):
        app = MDApp.get_running_app()
        if self.entity_data:
            app.open_entity_edit_menu(self.entity_data)

    def on_history(self):
        app = MDApp.get_running_app()
        if self.entity_data:
            app.open_entity_history_dialog(self.entity_data)

    def on_edit(self):
        pass

class EntityRecycleItem(RecycleDataViewBehavior, MDCard):
    index = None
    text_name = StringProperty('')
    text_balance = StringProperty('')
    icon_name = StringProperty('account')
    icon_color = ListProperty([0, 0, 0, 1])
    entity_data = ObjectProperty(None, allownone=True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        app = MDApp.get_running_app()
        raw_name = data.get('raw_name', '')
        self.text_name = app.fix_text(raw_name) if app else raw_name
        self.text_balance = data.get('balance_text', '')
        self.icon_name = data.get('icon', 'account')
        self.icon_color = data.get('icon_color', [0, 0, 0, 1])
        self.entity_data = data.get('raw_data')
        return super().refresh_view_attrs(rv, index, data)

    def on_tap(self):
        app = MDApp.get_running_app()
        if self.entity_data:
            app.select_entity_from_rv(self.entity_data)

class HistoryRecycleView(RecycleView):

    def __init__(self, **kwargs):
        super(HistoryRecycleView, self).__init__(**kwargs)
        self.data = []

class MgmtEntityRecycleView(RecycleView):

    def __init__(self, **kwargs):
        super(MgmtEntityRecycleView, self).__init__(**kwargs)
        self.data = []

class EntityRecycleView(RecycleView):

    def __init__(self, **kwargs):
        super(EntityRecycleView, self).__init__(**kwargs)
        self.data = []

class ProductRecycleView(RecycleView):

    def __init__(self, **kwargs):
        super(ProductRecycleView, self).__init__(**kwargs)
        self.data = []

class StockApp(MDApp):
    cart = []
    all_products_raw = []
    all_clients = []
    all_suppliers = []
    last_ping = 0
    current_mode = 'sale'
    local_server_ip = '192.168.1.100'
    external_server_ip = ''
    active_server_ip = '192.168.1.100'
    current_user_name = 'ADMIN'
    is_server_reachable = False
    is_offline_mode = False
    sync_paused = False
    is_seller_mode = BooleanProperty(False)
    selected_location = 'store'
    selected_entity = None
    editing_transaction_key = None
    current_editing_server_id = None
    editing_payment_amount = None
    offline_store = None
    cache_store = None
    store = None
    stats_store = None
    dialog = None
    status_bar_label = None
    status_bar_bg = None
    rv_products = None
    _notify_event = None
    _heartbeat_event = None
    _ready_timer = None
    entity_list_layout = None
    history_list_layout = None
    pending_dialog = None
    action_dialog = None
    srv_dialog = None
    stat_sales_today = NumericProperty(0)
    stat_purchases_today = NumericProperty(0)
    stat_client_payments = NumericProperty(0)
    stat_supplier_payments = NumericProperty(0)
    stat_net_total = NumericProperty(0)
    buttons_container = None
    stats_container = None
    cart_list_layout = None
    lbl_cart_count = None
    lbl_cart_total = None
    lbl_total_title = None
    current_entity_type_mgmt = 'account'
    DOC_TRANSLATIONS = {'BV': 'Bon de Vente', 'BA': "Bon d'Achat", 'FC': 'Facture Vente', 'FF': 'Facture Achat', 'RC': 'Retour Client', 'RF': 'Retour Fournisseur', 'TR': 'Transfert de Stock', 'FP': 'Facture Proforma', 'DP': 'Bon de Commande', 'BI': 'Bon Initial'}

    def fix_text(self, text):
        if not text:
            return ''
        try:
            text = str(text)
            reshaped_text = reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            return str(text)

    def prepare_products_for_rv(self, products_list):
        initial_data = products_list[:50] if products_list else []
        threading.Thread(target=self._prepare_and_send_data, args=(initial_data,), daemon=True).start()

    def filter_products(self, instance, text):
        query = instance.get_value() if hasattr(instance, 'get_value') else text
        if self._search_event:
            self._search_event.cancel()
        self._search_event = Clock.schedule_once(lambda dt: self._start_background_search(query), 0.3)

    def _start_background_search(self, query):
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query):
        if not query:
            self._prepare_and_send_data(self.all_products_raw[:50])
            return
        txt = query.lower()
        filtered = [p for p in self.all_products_raw if txt in str(p.get('name', '')).lower() or txt in str(p.get('barcode', '')).lower() or txt in str(p.get('product_ref', '')).lower()]
        if len(filtered) > 50:
            filtered = filtered[:50]
        self._prepare_and_send_data(filtered)

    def _prepare_and_send_data(self, products_list):
        rv_data = []
        is_sale = self.current_mode in ['sale', 'return_sale', 'invoice_sale', 'proforma']
        is_transfer = self.current_mode == 'transfer'

        def fmt_qty(val):
            try:
                val = float(val)
                if val.is_integer():
                    return str(int(val))
                return str(val)
            except:
                return '0'
        try:
            for p in products_list:
                s_store = float(p.get('stock', 0) or 0)
                s_wh = float(p.get('stock_warehouse', 0) or 0)
                total_stock = s_store + s_wh
                price_fmt = ''
                price_color = [0, 0, 0, 1]
                stock_text = ''
                if is_transfer:
                    price_fmt = f'Qnt Tot: {fmt_qty(total_stock)}'
                    price_color = [0.2, 0.2, 0.8, 1]
                    stock_text = f'Mag: {fmt_qty(s_store)} | Dép: {fmt_qty(s_wh)}'
                else:
                    if is_sale:
                        price = float(p.get('price', 0) or 0)
                        price_fmt = f'{price:.2f} DA'
                        price_color = [0, 0.6, 0, 1]
                    else:
                        p_price = p.get('purchase_price', 0)
                        if p_price is None:
                            p_price = p.get('price', 0)
                        price = float(p_price or 0)
                        price_fmt = f'{price:.2f} DA'
                        price_color = [0.9, 0.5, 0, 1]
                    if total_stock < -900000:
                        stock_text = 'Illimité'
                    elif s_wh == 0:
                        stock_text = f'Qté: {fmt_qty(s_store)}'
                    else:
                        stock_text = f'Qté: {fmt_qty(s_store)} | Dép: {fmt_qty(s_wh)}'
                icon = 'package-variant' if total_stock > 0 or total_stock < -900000 else 'package-variant-closed'
                icon_col = [0, 0.6, 0, 1] if total_stock > 0 or total_stock < -900000 else [0.8, 0, 0, 1]
                raw_name = str(p.get('name', 'Inconnu'))
                display_name = self.fix_text(raw_name)
                rv_data.append({'name': display_name, 'price_text': price_fmt, 'stock_text': stock_text, 'icon': icon, 'icon_color': icon_col, 'price_color': price_color, 'raw_data': p})
        except Exception as e:
            print(f'Data Prep Error: {e}')
        self._apply_search_results(rv_data)

    def play_sound(self, type_):
        # دالة لتشغيل نغمات مختلفة حسب الحالة
        if platform == 'android' and hasattr(self, 'tone_gen') and self.tone_gen:
            try:
                if type_ == 'success':
                    # نغمة "بيب" قصيرة (نجاح)
                    # TONE_PROP_BEEP = 24
                    self.tone_gen.startTone(24, 150)
                
                elif type_ == 'error':
                    # نغمة منخفضة وقوية (خطأ/غير موجود)
                    # TONE_SUP_ERROR = 97
                    self.tone_gen.startTone(97, 300)
                
                elif type_ == 'duplicate':
                    # نغمة مزدوجة أو مميزة (مكرر)
                    # TONE_CDMA_PIP = 29
                    self.tone_gen.startTone(29, 150)
            except:
                pass

    def play_beep(self):
        # دالة لتشغيل صوت "بييب" قصير
        if platform == 'android' and hasattr(self, 'tone_gen') and self.tone_gen:
            try:
                # TONE_PROP_BEEP = 24, Duration = 150ms
                self.tone_gen.startTone(24, 150)
            except:
                pass

    @mainthread
    def _apply_search_results(self, rv_data):
        if self.rv_products:
            self.rv_products.data = rv_data
            self.rv_products.refresh_from_data()

    def open_bluetooth_selector(self, instance):
        if platform != 'android':
            self.notify('Fonction disponible uniquement sur Android', 'error')
            return
        try:
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter or not adapter.isEnabled():
                self.notify('Bluetooth désactivé !', 'error')
                return
            paired_devices = adapter.getBondedDevices().toArray()
            content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(400))
            scroll = MDScrollView()
            list_layout = MDList()
            if not paired_devices:
                list_layout.add_widget(OneLineListItem(text='Aucun appareil associé (Paired)'))
            else:
                for device in paired_devices:
                    d_name = device.getName()
                    d_mac = device.getAddress()
                    item = TwoLineAvatarIconListItem(text=d_name, secondary_text=d_mac, on_release=lambda x, name=d_name, mac=d_mac: self.select_printer(name, mac))
                    item.add_widget(IconLeftWidget(icon='printer-wireless'))
                    list_layout.add_widget(item)
            scroll.add_widget(list_layout)
            content.add_widget(scroll)
            self.bt_dialog = MDDialog(title='Choisir Imprimante', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.bt_dialog.dismiss())])
            self.bt_dialog.open()
        except Exception as e:
            self.notify(f'Erreur Bluetooth: {e}', 'error')

    def select_printer(self, name, mac):
        if hasattr(self, 'printer_name_field'):
            self.printer_name_field.text = name
            self.printer_name_field.helper_text = f'ID: {mac}'
        self.temp_selected_mac = mac
        if self.bt_dialog:
            self.bt_dialog.dismiss()
        self.notify(f'Sélectionné: {name}', 'success')

    def clear_printer_selection(self, instance):
        if hasattr(self, 'printer_name_field'):
            self.printer_name_field.text = ''
            self.printer_name_field.helper_text = 'Imprimante non définie'
        self.temp_selected_mac = ''
        self.notify('Imprimante effacée', 'info')

    def print_ticket_bluetooth(self, transaction_data):
        if platform != 'android':
            return
        if not self.store.exists('printer_config'):
            self.notify('Imprimante non configurée', 'error')
            return
        config = self.store.get('printer_config')
        target_mac = config.get('mac', '').strip()
        if not target_mac:
            return
        socket = None
        try:
            adapter = BluetoothAdapter.getDefaultAdapter()
            if not adapter or not adapter.isEnabled():
                self.notify('Bluetooth OFF', 'error')
                return
            device = adapter.getRemoteDevice(target_mac)
            uuid = UUID.fromString('00001101-0000-1000-8000-00805F9B34FB')
            img = self.create_receipt_image(transaction_data)
            raster_data = self.get_image_raster_data(img)
            socket = device.createRfcommSocketToServiceRecord(uuid)
            socket.connect()
            output_stream = socket.getOutputStream()
            ESC = b'\x1b'
            GS = b'\x1d'
            INIT = ESC + b'@'
            CUT = GS + b'V\x00'
            output_stream.write(INIT)
            time.sleep(0.1)
            chunk_size = 1024
            for i in range(0, len(raster_data), chunk_size):
                output_stream.write(raster_data[i:i + chunk_size])
                output_stream.flush()
                time.sleep(0.02)
            output_stream.write(b'\n\n\n')
            output_stream.write(CUT)
            output_stream.flush()
            time.sleep(0.1)
            socket.close()
        except Exception as e:
            try:
                if socket:
                    socket.close()
            except:
                pass
            print(f'Print Image Error: {e}')

    def get_wrapped_text(self, text, font, max_width):
        lines = []
        if not text:
            return lines
        words = text.split(' ')
        current_line = []
        for word in words:
            current_line.append(word)
            line_str = ' '.join(current_line)
            bbox = font.getbbox(line_str)
            w = bbox[2] - bbox[0]
            if w > max_width:
                if len(current_line) == 1:
                    lines.append(current_line[0])
                    current_line = []
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def create_receipt_image(self, transaction_data):
        PAPER_WIDTH = 576
        margin = 10
        img_height = 4000
        image = Image.new('RGB', (PAPER_WIDTH, img_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        try:
            font_size_reg = 24
            font_size_large = 40
            font_size_med = 28
            font_reg = ImageFont.truetype(FONT_FILE, font_size_reg)
            font_bold = ImageFont.truetype(FONT_FILE, font_size_reg)
            font_large = ImageFont.truetype(FONT_FILE, font_size_large)
            font_med = ImageFont.truetype(FONT_FILE, font_size_med)
        except:
            font_reg = ImageFont.load_default()
            font_bold = font_reg
            font_large = font_reg
            font_med = font_reg

        def proc_ar(text):
            if not text:
                return ''
            try:
                text = str(text)
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)
                return bidi_text
            except:
                return str(text)

        def draw_text_line(text, y_pos, font_obj, align='left', color=(0, 0, 0)):
            if not text:
                return y_pos
            bidi_text = proc_ar(text)
            bbox = font_obj.getbbox(bidi_text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_pos = margin
            if align == 'center':
                x_pos = (PAPER_WIDTH - text_width) // 2
            elif align == 'right':
                x_pos = PAPER_WIDTH - text_width - margin
            draw.text((x_pos, y_pos), bidi_text, font=font_obj, fill=color)
            return y_pos + text_height + 8

        def draw_separator(curr_y):
            draw.line([(margin, curr_y), (PAPER_WIDTH - margin, curr_y)], fill=(0, 0, 0), width=2)
            return curr_y + 10

        def draw_lr(left, right, font, y_pos, is_bold=False):
            l = proc_ar(left)
            r = proc_ar(right)
            bbox_r = font.getbbox(r)
            bbox_l = font.getbbox(l)
            w_r = bbox_r[2] - bbox_r[0]
            x_r = PAPER_WIDTH - w_r - margin
            draw.text((margin, y_pos), l, font=font, fill=(0, 0, 0))
            draw.text((x_r, y_pos), r, font=font, fill=(0, 0, 0))
            if is_bold:
                draw.text((margin + 1, y_pos), l, font=font, fill=(0, 0, 0))
                draw.text((x_r + 1, y_pos), r, font=font, fill=(0, 0, 0))
            return max(bbox_r[3] - bbox_r[1], bbox_l[3] - bbox_l[1], 30) + 8
        y = 10
        store_name = 'MagPro Store'
        store_address = ''
        store_phone = ''
        if self.store.exists('print_header'):
            header_conf = self.store.get('print_header')
            store_name = header_conf.get('name', store_name)
            store_address = header_conf.get('address', '')
            store_phone = header_conf.get('phone', '')
        y = draw_text_line(store_name, y, font_large, 'center')
        if store_address:
            y = draw_text_line(store_address, y, font_reg, 'center')
        if store_phone:
            y = draw_text_line(f'Tel: {store_phone}', y, font_reg, 'center')
        y += 5
        y = draw_separator(y)
        ts_str = transaction_data.get('timestamp', '')
        if not ts_str:
            ts_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        else:
            ts_str = ts_str[:16]
        user_str = transaction_data.get('user_name', self.current_user_name)
        entity_name_raw = 'Passager'
        ent_id = transaction_data.get('entity_id')
        if self.selected_entity:
            entity_name_raw = self.selected_entity.get('name', 'Passager')
        elif ent_id:
            found = next((c for c in self.all_clients if c['id'] == ent_id), None)
            if not found:
                found = next((s for s in self.all_suppliers if s['id'] == ent_id), None)
            if found:
                entity_name_raw = found.get('name', 'Client')
            else:
                entity_name_raw = transaction_data.get('entity', 'Inconnu')
        doc_type = transaction_data.get('doc_type', 'BV')
        is_simple = transaction_data.get('is_simple_payment', False)
        doc_title = ''
        if is_simple:
            pay_type = transaction_data.get('type', '')
            amt = float(transaction_data.get('amount', 0))
            custom_lbl = transaction_data.get('custom_label')
            if custom_lbl:
                doc_title = custom_lbl
            elif amt < 0:
                doc_title = 'BON DE CREDIT' if pay_type == 'client_pay' else 'DETTE'
            else:
                doc_title = 'VERSEMENT' if pay_type == 'client_pay' else 'REGLEMENT'
        else:
            labels = {'BV': 'BON DE VENTE', 'BA': "BON D'ACHAT", 'FC': 'FACTURE', 'FF': 'FACTURE ACHAT', 'RC': 'RETOUR', 'RF': 'RETOUR FOURN.', 'TR': 'TRANSFERT', 'FP': 'PROFORMA', 'DP': 'COMMANDE', 'BI': 'BON INITIAL'}
            doc_title = labels.get(doc_type, doc_type)
        y = draw_text_line(doc_title, y, font_large, 'center')
        y += 10
        y = draw_separator(y)
        ref_num = transaction_data.get('invoice_number') or transaction_data.get('server_id')
        if ref_num:
            y = draw_text_line(f'Ref: {ref_num}', y, font_reg, 'left')
        y = draw_text_line(f'Date: {ts_str}', y, font_reg, 'left')
        y = draw_text_line(f'User: {user_str}', y, font_reg, 'left')
        y = draw_text_line(f'Client: {entity_name_raw}', y, font_med, 'left')
        y += 5
        y = draw_separator(y)
        if is_simple:
            amount = abs(float(transaction_data.get('amount', 0)))
            y += 20
            y = draw_text_line(f'MONTANT: {amount:.2f} DA', y, font_large, 'center')
            y += 20
        else:
            items = transaction_data.get('items', [])
            total = 0
            for item in items:
                raw_prod = item.get('name', 'Article')
                qty = float(item.get('qty', 0))
                price = float(item.get('price', 0))
                row_total = qty * price
                total += row_total
                prod_lines = self.get_wrapped_text(raw_prod, font_bold, PAPER_WIDTH - 2 * margin)
                for line in prod_lines:
                    y = draw_text_line(line, y, font_bold, 'right')
                qty_str = str(int(qty)) if qty.is_integer() else str(qty)
                price_str = f'{price:.2f}'
                total_str = f'{row_total:.2f}'
                line_calc = f'{qty_str} x {price_str}'
                line_total = f'= {total_str} DA'
                y += draw_lr(line_calc, line_total, font_reg, y)
                draw.line([(margin + 50, y - 2), (PAPER_WIDTH - margin - 50, y - 2)], fill=(200, 200, 200), width=1)
                y += 5
            y += 10
            y = draw_separator(y)
            if doc_type != 'TR':
                y += 10
                y += draw_lr('TOTAL:', f'{total:.2f} DA', font_large, y, True)
                y += 10
                payment = transaction_data.get('payment_info', {})
                paid = float(payment.get('amount', 0))
                y += draw_lr('VERSEMENT:', f'{paid:.2f} DA', font_med, y)
                reste = total - paid
                label_reste = 'RESTE' if reste >= 0 else 'RENDU'
                y += draw_lr(f'{label_reste}:', f'{abs(reste):.2f} DA', font_med, y, True)
        y += 30
        y = draw_text_line('Merci de votre visite', y, font_reg, 'center')
        y += 50
        final_image = image.crop((0, 0, PAPER_WIDTH, y))
        return final_image

    def get_image_raster_data(self, image):
        max_width = 576
        if image.width != max_width:
            ratio = max_width / float(image.width)
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        image = image.convert('1')
        width, height = image.size
        xL = width // 8 % 256
        xH = width // 8 // 256
        yL = height % 256
        yH = height // 256
        cmd = b'\x1dv0\x00' + bytes([xL, xH, yL, yH])
        raw_bytes = image.tobytes()
        inverted_bytes = bytearray([b ^ 255 for b in raw_bytes])
        return cmd + inverted_bytes

    def build(self):
        Builder.load_string(KV_BUILDER)
        self.title = 'MagPro Gestion de Stock'
        self._search_event = None
        self._entity_search_event = None
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'Amber'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.font_styles['H4'] = ['ArabicFont', 34, False, 0.25]
        self.theme_cls.font_styles['H5'] = ['ArabicFont', 24, False, 0]
        self.theme_cls.font_styles['H6'] = ['ArabicFont', 20, False, 0.15]
        self.theme_cls.font_styles['Subtitle1'] = ['ArabicFont', 16, False, 0.15]
        self.theme_cls.font_styles['Subtitle2'] = ['ArabicFont', 14, False, 0.1]
        self.theme_cls.font_styles['Body1'] = ['ArabicFont', 16, False, 0.5]
        self.theme_cls.font_styles['Body2'] = ['ArabicFont', 14, False, 0.25]
        self.theme_cls.font_styles['Button'] = ['ArabicFont', 14, True, 1.25]
        self.theme_cls.font_styles['Caption'] = ['ArabicFont', 12, False, 0.4]
        try:
            self.data_dir = self.user_data_dir
            self.offline_store = JsonStore(os.path.join(self.data_dir, 'stock_pending_orders.json'))
            self.cache_store = JsonStore(os.path.join(self.data_dir, 'stock_cache.json'))
            self.stats_store = JsonStore(os.path.join(self.data_dir, 'local_stats.json'))
            self.store = JsonStore(os.path.join(self.data_dir, 'app_settings.json'))
            if self.store.exists('config'):
                conf = self.store.get('config')
                self.local_server_ip = conf.get('ip', '192.168.1.100')
                self.external_server_ip = conf.get('ext_ip', '')
                self.is_seller_mode = conf.get('seller_mode', False)
                self.active_server_ip = self.local_server_ip
        except Exception as e:
            print(f'Storage Init Error: {e}')
        self.root_box = MDBoxLayout(orientation='vertical')
        self.sm = MDScreenManager()
        self.sm.add_widget(self._build_login_screen())
        self.sm.add_widget(self._build_dashboard_screen())
        self.sm.add_widget(self._build_products_screen())
        self.sm.add_widget(self._build_cart_screen())
        self.root_box.add_widget(self.sm)
        self.status_bar_bg = MDCard(size_hint_y=None, height=dp(40), radius=[0], md_bg_color=(0.2, 0.2, 0.2, 1), elevation=0)
        self.status_bar_label = MDLabel(text='Initialisation...', halign='center', theme_text_color='Custom', text_color=(1, 1, 1, 1), font_style='Caption', bold=True)
        self.status_bar_bg.add_widget(self.status_bar_label)
        self.root_box.add_widget(self.status_bar_bg)
        self._heartbeat_event = Clock.schedule_interval(self.check_server_heartbeat, 5)
        return self.root_box

    def on_start(self):
        if platform == 'android':
            self.request_android_permissions()
            
            # --- إضافة: تهيئة مولد الصوت ---
            try:
                # STREAM_MUSIC = 3, Volume = 100 (Max)
                self.tone_gen = ToneGenerator(3, 100)
            except Exception as e:
                print(f"Error init sound: {e}")
                self.tone_gen = None
            # -----------------------------

        Clock.schedule_once(self._deferred_start, 0.5)

    def request_android_permissions(self):
        if platform != 'android':
            return
        try:
            from android.permissions import request_permissions, Permission
            from jnius import autoclass

            def callback(permissions, results):
                pass
            Build = autoclass('android.os.Build')
            VERSION = autoclass('android.os.Build$VERSION')
            permissions_list = [Permission.BLUETOOTH, Permission.BLUETOOTH_ADMIN, Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION]
            if VERSION.SDK_INT >= 31:
                permissions_list.extend(['android.permission.BLUETOOTH_CONNECT', 'android.permission.BLUETOOTH_SCAN'])
            request_permissions(permissions_list, callback)
        except Exception:
            pass

    def _deferred_start(self, dt):
        self.cleanup_old_synced_data()
        self._auto_login_check(0)
        self.check_and_load_stats()
        self.update_dashboard_layout()

    def cleanup_old_synced_data(self):
        try:
            keys = list(self.offline_store.keys())
            now = time.time()
            count = 0
            retention_period = 172800
            for key in keys:
                item = self.offline_store.get(key)
                if item.get('synced', False):
                    sync_time = item.get('sync_timestamp', 0)
                    if now - sync_time > retention_period:
                        self.offline_store.delete(key)
                        count += 1
            if count > 0:
                print(f'Cleaned {count} old synced items.')
        except Exception as e:
            print(f'Cleanup Error: {e}')

    def select_entity_from_rv(self, entity_data):
        server_default_names = ['Comptoir', 'Fournisseur', 'زبون افتراضي', 'مورد افتراضي']
        final_name = entity_data.get('name', '')
        if final_name in server_default_names:
            final_name = 'COMPTOIR'
        
        self.selected_entity = {
            'id': entity_data['id'], 
            'name': final_name, 
            'category': entity_data.get('price_category', 'تجزئة')
        }
        
        # تحديث اسم الزر في شاشة المنتجات فوراً
        if hasattr(self, 'btn_ent_screen'):
            self.btn_ent_screen.text = self.fix_text(final_name)[:15]
            # تحديث لون الزر حسب الوضع
            if self.current_mode in ['sale', 'return_sale', 'client_payment', 'invoice_sale', 'proforma']:
                self.btn_ent_screen.md_bg_color = (0, 0.6, 0.6, 1)
            else:
                self.btn_ent_screen.md_bg_color = (0.8, 0.4, 0, 1)

        self.recalculate_cart_prices()
        
        if hasattr(self, 'entity_dialog') and self.entity_dialog:
            self.entity_dialog.dismiss()
            
        # تنفيذ الإجراء التالي (وهو الدخول لشاشة المنتجات في حالتنا الجديدة)
        if hasattr(self, 'pending_entity_next_action') and self.pending_entity_next_action:
            self.pending_entity_next_action()
            self.pending_entity_next_action = None

    def check_and_load_stats(self):
        today_str = str(datetime.now().date())
        if self.stats_store.exists('daily_data'):
            data = self.stats_store.get('daily_data')
            if data.get('date') == today_str:
                self.stat_sales_today = data.get('sales', 0)
                self.stat_purchases_today = data.get('purchases', 0)
                self.stat_client_payments = data.get('c_pay', 0)
                self.stat_supplier_payments = data.get('s_pay', 0)
            else:
                self.reset_local_stats()
        else:
            self.reset_local_stats()
        self.calculate_net_total()

    def open_history_date_picker(self, instance):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_history_date_save)
        date_dialog.open()

    def on_history_date_save(self, instance, value, date_range):
        self.btn_hist_date.text = str(value)
        self.filter_history_list(specific_date=value)

    def reset_local_stats(self):
        self.stat_sales_today = 0
        self.stat_purchases_today = 0
        self.stat_client_payments = 0
        self.stat_supplier_payments = 0
        self.save_local_stats()

    def save_local_stats(self):
        today_str = str(datetime.now().date())
        self.stats_store.put('daily_data', date=today_str, sales=self.stat_sales_today, purchases=self.stat_purchases_today, c_pay=self.stat_client_payments, s_pay=self.stat_supplier_payments)

    def calculate_net_total(self):
        self.stat_net_total = self.stat_sales_today + self.stat_client_payments - (self.stat_purchases_today + self.stat_supplier_payments)
        self.update_dashboard_labels()

    def update_local_entity_balance(self, entity_id, change_amount):
        if not entity_id:
            return
        target_entity = None
        is_client = False
        for c in self.all_clients:
            if c['id'] == entity_id:
                target_entity = c
                is_client = True
                break
        if not target_entity:
            for s in self.all_suppliers:
                if s['id'] == entity_id:
                    target_entity = s
                    is_client = False
                    break
        if target_entity:
            try:
                current_bal = float(target_entity.get('balance', 0))
                new_bal = current_bal + float(change_amount)
                target_entity['balance'] = new_bal
                key = 'clients' if is_client else 'suppliers'
                data_list = self.all_clients if is_client else self.all_suppliers
                self.cache_store.put(key, data=data_list)
            except Exception as e:
                pass

    def filter_entity_history_list(self, day_offset=None, specific_date=None):
        if not hasattr(self, 'rv_entity_history'):
            return
        inactive_color = (0.5, 0.5, 0.5, 1)
        active_color = self.theme_cls.primary_color
        target_date = None
        if specific_date:
            target_date = specific_date
            self.btn_ent_hist_today.md_bg_color = inactive_color
            self.btn_ent_hist_yesterday.md_bg_color = inactive_color
            self.btn_ent_hist_date.md_bg_color = active_color
        else:
            if day_offset is None:
                day_offset = 0
            target_date = datetime.now().date() - timedelta(days=day_offset)
            self.btn_ent_hist_today.md_bg_color = active_color if day_offset == 0 else inactive_color
            self.btn_ent_hist_yesterday.md_bg_color = active_color if day_offset == 1 else inactive_color
            self.btn_ent_hist_date.md_bg_color = inactive_color
            self.btn_ent_hist_date.text = 'CALENDRIER'
        self.rv_entity_history.data = [{'raw_text': 'Chargement...', 'raw_sec': '', 'amount_text': '', 'icon': 'timer-sand', 'icon_color': [0.5, 0.5, 0.5, 1], 'bg_color': [1, 1, 1, 1], 'is_local': False, 'raw_data': None}]

        def on_history_fetched(req, result):
            rv_data = []
            if not result:
                rv_data.append({'raw_text': 'Aucune opération trouvée.', 'raw_sec': '', 'amount_text': '', 'icon': 'information-outline', 'icon_color': [0.5, 0.5, 0.5, 1], 'bg_color': [1, 1, 1, 1], 'is_local': False, 'raw_data': None})
                self.rv_entity_history.data = rv_data
                return
            target_name = self.history_target_entity['name'].lower()
            doc_markers = ['BV', 'BA', 'FC', 'FF', 'RC', 'RF', 'FP', 'BL', 'TR']
            for item in result:
                server_entity_name = str(item.get('entity', '')).lower()
                if target_name in server_entity_name:
                    desc = item.get('desc', '')
                    desc_lower = desc.lower()
                    prefix = desc[:2].upper()
                    is_credit = any((kw in desc_lower for kw in ['crédit', 'dette', 'solde', 'دين']))
                    is_payment = any((kw in desc_lower for kw in ['versement', 'règlement', 'encaissement', 'pay', 'دفعة', 'تسديد']))
                    is_financial = is_credit or is_payment
                    has_doc_ref = any((marker in desc for marker in doc_markers))
                    if is_financial and has_doc_ref and (not is_credit):
                        continue
                    amount = float(item.get('amount', 0))
                    time_str = item.get('time', '')
                    icon = 'file-document'
                    color = (0.2, 0.2, 0.2, 1)
                    amount_text = f'{abs(amount):.2f} DA'
                    if is_financial:
                        if is_credit:
                            icon = 'notebook-edit'
                            color = (0.8, 0, 0, 1)
                            amount_text = f'- {abs(amount):.2f} DA'
                        else:
                            icon = 'cash-plus'
                            color = (0, 0.7, 0, 1)
                            amount_text = f'+ {abs(amount):.2f} DA'
                    elif prefix == 'BV':
                        icon = 'cart'
                        color = (0, 0.5, 0.8, 1)
                    elif prefix == 'BA':
                        icon = 'truck'
                        color = (1, 0.6, 0, 1)
                    elif prefix == 'FC':
                        icon = 'file-document'
                        color = (0, 0, 0.8, 1)
                    elif prefix == 'RC':
                        icon = 'keyboard-return'
                        color = (0.8, 0, 0, 1)
                    final_desc = f'{desc}'
                    final_sec = f"{time_str} • {item.get('user', '')}"
                    rv_data.append({'raw_text': final_desc, 'raw_sec': final_sec, 'amount_text': amount_text, 'icon': icon, 'icon_color': color, 'bg_color': (0.98, 0.98, 0.98, 1), 'is_local': False, 'raw_data': item, 'key': ''})
            if not rv_data:
                rv_data.append({'raw_text': 'Aucune transaction (filtrée).', 'raw_sec': '', 'amount_text': '', 'icon': 'filter-outline', 'icon_color': [0.5, 0.5, 0.5, 1], 'bg_color': [1, 1, 1, 1], 'is_local': False, 'raw_data': None})
            self.rv_entity_history.data = rv_data
            self.rv_entity_history.refresh_from_data()

        def on_fail(req, err):
            self.rv_entity_history.data = [{'raw_text': 'Erreur de connexion serveur.', 'raw_sec': str(err), 'amount_text': '', 'icon': 'wifi-off', 'icon_color': [0.8, 0, 0, 1], 'bg_color': [1, 1, 1, 1], 'is_local': False, 'raw_data': None}]
        if self.is_server_reachable:
            url = f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/history?date={target_date}'
            UrlRequest(url, on_success=on_history_fetched, on_failure=on_fail, on_error=on_fail)
        else:
            self.rv_entity_history.data = [{'raw_text': 'Mode Hors Ligne', 'raw_sec': "Impossible de voir l'historique", 'amount_text': '', 'icon': 'wifi-off', 'icon_color': [0.5, 0.5, 0.5, 1], 'bg_color': [1, 1, 1, 1], 'is_local': False, 'raw_data': None}]

    def fetch_and_edit_transaction(self, item_data):
        if self.is_seller_mode:
            try:
                item_date_str = str(item_data.get('time', '')).split(' ')[0]
                today_str = str(datetime.now().date())
                if item_date_str != today_str:
                    self.notify('Modification interdite (Date passée)', 'error')
                    return
            except Exception as e:
                print(f'Date check error: {e}')
                self.notify('Modification interdite', 'error')
                return
        self.notify('Chargement pour modification...', 'info')
        if hasattr(self, 'entity_hist_dialog'):
            self.entity_hist_dialog.dismiss()
        is_tr_str = 'true' if item_data.get('is_transfer') else 'false'
        url = f"http://{self.active_server_ip}:{DEFAULT_PORT}/api/get_transaction_details?id={item_data['id']}&is_transfer={is_tr_str}"

        def on_details_success(req, res):
            items = res.get('items', [])
            header_data = item_data.copy()
            if res.get('purchase_location'):
                header_data['purchase_location'] = res.get('purchase_location')
            if res.get('location'):
                header_data['location'] = res.get('location')
            if res.get('source_location'):
                header_data['source_location'] = res.get('source_location')
            if hasattr(self, 'history_target_entity') and self.history_target_entity:
                header_data['entity_id'] = self.history_target_entity['id']
                header_data['entity'] = self.history_target_entity['name']
            if not items:
                self.current_mode = 'client_payment'
                if 'règlement' in header_data.get('desc', '').lower():
                    self.current_mode = 'supplier_payment'
                self.selected_entity = self.history_target_entity
                self.editing_transaction_key = 'SERVER_EDIT_MODE'
                self.current_editing_server_id = header_data['id']
                amount = abs(float(header_data.get('amount', 0)))
                self.show_simple_payment_dialog(amount=amount)
            else:
                self.load_server_transaction_for_edit(header_data, items)

        def on_details_fail(req, err):
            self.notify('Erreur chargement détails', 'error')
            if hasattr(self, 'entity_hist_dialog'):
                self.entity_hist_dialog.open()
        UrlRequest(url, on_success=on_details_success, on_failure=on_details_fail, on_error=on_details_fail)

    def open_entity_history_dialog(self, entity):
        self.history_target_entity = entity
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(550))
        tabs_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=5)
        self.btn_ent_hist_today = MDRaisedButton(text='AUJ.', size_hint_x=0.33, elevation=0, on_release=lambda x: self.filter_entity_history_list(day_offset=0))
        self.btn_ent_hist_yesterday = MDRaisedButton(text='HIER', size_hint_x=0.33, elevation=0, md_bg_color=(0.5, 0.5, 0.5, 1), on_release=lambda x: self.filter_entity_history_list(day_offset=1))
        self.btn_ent_hist_date = MDRaisedButton(text='CALENDRIER', size_hint_x=0.33, elevation=0, md_bg_color=(0.5, 0.5, 0.5, 1), on_release=self.open_entity_history_date_picker)
        tabs_box.add_widget(self.btn_ent_hist_today)
        tabs_box.add_widget(self.btn_ent_hist_yesterday)
        tabs_box.add_widget(self.btn_ent_hist_date)
        content.add_widget(tabs_box)
        self.rv_entity_history = HistoryRecycleView()
        content.add_widget(self.rv_entity_history)
        title_text = self.fix_text(f"Historique: {entity['name']}")
        self.entity_hist_dialog = MDDialog(title=title_text, type='custom', content_cls=content, size_hint=(0.95, 0.9))
        self.entity_hist_dialog.open()
        self.filter_entity_history_list(day_offset=0)

    def submit_simple_payment(self, x):
        current_time = time.time()
        if current_time - getattr(self, '_last_click_time', 0) < 1.0:
            return
        self._last_click_time = current_time
        if getattr(self, 'is_transaction_in_progress', False):
            return
        self.is_transaction_in_progress = True
        try:
            amount = float(self.txt_simple_amount.get_value())
        except:
            self.notify('Montant invalide', 'error')
            self.is_transaction_in_progress = False
            return
        if amount == 0:
            self.notify('Le montant ne peut pas être 0', 'error')
            self.is_transaction_in_progress = False
            return
        if self.simple_pay_dialog:
            self.simple_pay_dialog.dismiss()
        if self.current_mode in ['client_payment', 'client_pay']:
            self.stat_client_payments += amount
        elif self.current_mode in ['supplier_payment', 'supplier_pay']:
            self.stat_supplier_payments += amount
        self.calculate_net_total()
        self.save_local_stats()
        base_type = 'client_pay'
        if self.current_mode in ['client_payment', 'client_pay']:
            base_type = 'client_pay'
        elif self.current_mode in ['supplier_payment', 'supplier_pay']:
            base_type = 'supplier_pay'
        custom_note = 'Versement' if amount >= 0 else 'Crédit'
        server_id_to_update = None
        if self.editing_transaction_key:
            if self.editing_transaction_key == 'SERVER_EDIT_MODE':
                server_id_to_update = self.current_editing_server_id
            elif self.offline_store.exists(self.editing_transaction_key):
                old_item = self.offline_store.get(self.editing_transaction_key)
                if old_item.get('synced') and old_item.get('order_data', {}).get('server_id'):
                    server_id_to_update = old_item['order_data']['server_id']
        final_timestamp = str(datetime.now())
        if server_id_to_update and hasattr(self, 'current_editing_date') and self.current_editing_date:
            final_timestamp = self.current_editing_date
        try:
            if '.' in final_timestamp:
                final_timestamp = final_timestamp.split('.')[0]
        except:
            pass
        data = {'entity_id': self.selected_entity['id'], 'amount': amount, 'type': base_type, 'custom_label': custom_note, 'user_name': self.current_user_name, 'note': self.current_user_name, 'is_simple_payment': True, 'timestamp': final_timestamp, 'server_id': server_id_to_update}
        self.current_editing_server_id = None
        self.current_editing_date = None

        def release_lock_and_finish(req=None, res=None):
            self.is_transaction_in_progress = False
            try:
                if self.store.exists('printer_config'):
                    conf = self.store.get('printer_config')
                    if conf.get('auto', False) and conf.get('mac', ''):
                        threading.Thread(target=self.print_ticket_bluetooth, args=(data,), daemon=True).start()
            except Exception as e:
                print(f'Auto print payment error: {e}')
        if self.is_server_reachable:

            def on_success(req, res):
                if res.get('server_id'):
                    data['server_id'] = res.get('server_id')
                if res.get('invoice_number'):
                    data['invoice_number'] = res.get('invoice_number')
                self.save_to_history(data, synced=True)
                self.notify('Enregistré' if not server_id_to_update else 'Modifié avec succès', 'success')
                entity_type_to_refresh = 'account' if base_type == 'client_pay' else 'supplier'
                self.fetch_entities(entity_type_to_refresh)
                release_lock_and_finish()
            UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/submit_payment', req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=on_success, on_error=lambda r, e: [self.submit_simple_payment_offline(data), release_lock_and_finish()], on_failure=lambda r, e: [self.submit_simple_payment_offline(data), release_lock_and_finish()])
        else:
            self.submit_simple_payment_offline(data)
            release_lock_and_finish()

    def submit_simple_payment_offline(self, data):
        self.save_to_history(data, synced=False)
        change = -float(data['amount'])
        self.update_local_entity_balance(data['entity_id'], change)
        if hasattr(self, 'mgmt_dialog') and self.mgmt_dialog:
            target_list = self.all_clients if data['type'] == 'client_pay' else self.all_suppliers
            self.populate_entity_manager_list(target_list)
        self.notify('Enregistré (Offline & Cache Update)', 'warning')

    def update_dashboard_labels(self):
        try:
            if hasattr(self, 'lbl_stat_sales') and self.lbl_stat_sales:
                self.lbl_stat_sales.text = f'{self.stat_sales_today:.2f} DA'
            if hasattr(self, 'lbl_stat_purchases') and self.lbl_stat_purchases:
                self.lbl_stat_purchases.text = f'{self.stat_purchases_today:.2f} DA'
            if hasattr(self, 'lbl_stat_client_pay') and self.lbl_stat_client_pay:
                self.lbl_stat_client_pay.text = f'{self.stat_client_payments:.2f} DA'
            if hasattr(self, 'lbl_stat_supp_pay') and self.lbl_stat_supp_pay:
                self.lbl_stat_supp_pay.text = f'{self.stat_supplier_payments:.2f} DA'
            if hasattr(self, 'lbl_stat_net') and self.lbl_stat_net:
                self.lbl_stat_net.text = f'{self.stat_net_total:.2f} DA'
        except:
            pass

    def update_dashboard_layout(self):
        if not self.buttons_container or not self.stats_card_container:
            return
        self.buttons_container.clear_widgets()
        self.stats_card_container.clear_widgets()
        col_green = (0, 0.7, 0, 1)
        col_blue = (0, 0, 0.8, 1)
        col_purple = (0.5, 0, 0.5, 1)
        col_red = (0.8, 0, 0, 1)
        col_teal = (0, 0.5, 0.5, 1)
        col_orange = (1, 0.6, 0, 1)
        col_deep_orange = (1, 0.3, 0, 1)
        col_brown = (0.4, 0.2, 0.1, 1)
        col_cyan = (0, 0.6, 0.6, 1)
        bg_green = (0.9, 1, 0.9, 1)
        bg_blue = (0.9, 0.95, 1, 1)
        bg_purple = (0.95, 0.9, 1, 1)
        bg_red = (1, 0.9, 0.9, 1)
        bg_teal = (0.8, 1, 1, 1)
        bg_orange = (1, 0.95, 0.8, 1)
        bg_deep_orange = (1, 0.9, 0.8, 1)
        bg_brown = (1, 0.85, 0.85, 1)
        if self.is_seller_mode:
            self.buttons_container.add_widget(self._create_dash_btn('cart', 'VENTE (BV)', bg_green, col_green, lambda x: self.open_mode('sale')))
            grid = MDGridLayout(cols=2, spacing=dp(10), adaptive_height=True)
            grid.add_widget(self._create_dash_btn('keyboard-return', 'RETOUR CL.', bg_red, col_red, lambda x: self.open_mode('return_sale')))
            grid.add_widget(self._create_dash_btn('account-group', 'CLIENTS', bg_teal, col_teal, lambda x: self.open_entity_manager('account')))
            self.buttons_container.add_widget(grid)
        else:
            grid = MDGridLayout(cols=2, spacing=dp(10), adaptive_height=True)
            grid.add_widget(self._create_dash_btn('cart', 'VENTE (BV)', bg_green, col_green, lambda x: self.open_mode('sale')))
            grid.add_widget(self._create_dash_btn('truck', 'ACHAT (BA)', bg_orange, col_orange, lambda x: self.open_mode('purchase')))
            grid.add_widget(self._create_dash_btn('file-document', 'FACTURE (FC)', bg_blue, col_blue, lambda x: self.open_mode('invoice_sale')))
            grid.add_widget(self._create_dash_btn('file-document-edit', 'FACT. ACHAT (FF)', bg_deep_orange, col_deep_orange, lambda x: self.open_mode('invoice_purchase')))
            grid.add_widget(self._create_dash_btn('file-document-outline', 'PROFORMA (FP)', bg_purple, col_purple, lambda x: self.open_mode('proforma')))
            grid.add_widget(self._create_dash_btn('clipboard-list', 'COMMANDE (DP)', bg_teal, col_cyan, lambda x: self.open_mode('order_purchase')))
            grid.add_widget(self._create_dash_btn('keyboard-return', 'RETOUR CL.', bg_red, col_red, lambda x: self.open_mode('return_sale')))
            grid.add_widget(self._create_dash_btn('undo', 'RETOUR FR.', bg_blue, col_blue, lambda x: self.open_mode('return_purchase')))
            grid.add_widget(self._create_dash_btn('account-group', 'CLIENTS', bg_teal, col_teal, lambda x: self.open_entity_manager('account')))
            grid.add_widget(self._create_dash_btn('truck-delivery', 'FOURNISSEURS', bg_brown, col_brown, lambda x: self.open_entity_manager('supplier')))
            grid.add_widget(self._create_dash_btn('database-edit', 'PRODUITS', bg_blue, col_blue, lambda x: self.open_mode('manage_products')))
            grid.add_widget(self._create_dash_btn('transfer', 'TRANSFERT (TR)', bg_purple, col_purple, lambda x: self.open_mode('transfer')))
            self.buttons_container.add_widget(grid)
        self.stats_card_container.add_widget(MDLabel(text='Statistiques Journalières', font_style='Subtitle1', bold=True, halign='center', size_hint_y=None, height=dp(30)))
        stats_grid = MDGridLayout(cols=2, spacing=dp(10))
        stats_grid.add_widget(self._create_stat_item('Ventes (Espèce)', 'lbl_stat_sales', col_green))
        if not self.is_seller_mode:
            stats_grid.add_widget(self._create_stat_item('Achats', 'lbl_stat_purchases', col_orange))
        stats_grid.add_widget(self._create_stat_item('Encaissements', 'lbl_stat_client_pay', col_teal))
        if not self.is_seller_mode:
            stats_grid.add_widget(self._create_stat_item('Décaissements', 'lbl_stat_supp_pay', col_red))
        self.stats_card_container.add_widget(stats_grid)
        total_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), padding=[0, 10, 0, 0])
        total_box.add_widget(MDLabel(text='Total', font_style='Caption', halign='center'))
        self.lbl_stat_net = MDLabel(text='0.00 DA', font_style='H5', bold=True, halign='center', theme_text_color='Custom', text_color=(0.2, 0.2, 0.8, 1))
        total_box.add_widget(self.lbl_stat_net)
        self.stats_card_container.add_widget(total_box)
        self.update_dashboard_labels()

    def open_entity_history_date_picker(self, instance):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_entity_history_date_save)
        date_dialog.open()

    def on_entity_history_date_save(self, instance, value, date_range):
        self.btn_ent_hist_date.text = str(value)
        self.filter_entity_history_list(specific_date=value)

    def open_entity_manager(self, entity_type):
        self.current_entity_type_mgmt = entity_type
        title_text = 'Gestion Clients' if entity_type == 'account' else 'Gestion Fournisseurs'
        if self.is_server_reachable:
            self.fetch_entities(entity_type)
        else:
            key = 'clients' if entity_type == 'account' else 'suppliers'
            if self.cache_store.exists(key):
                data = self.cache_store.get(key)['data']
                if entity_type == 'account':
                    self.all_clients = data
                else:
                    self.all_suppliers = data
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(600))
        self.entity_search = SmartTextField(hint_text='Rechercher...', icon_right='magnify')
        self.entity_search.bind(text=lambda instance, text: self.filter_entities_for_manager(text))
        content.add_widget(self.entity_search)
        self.rv_mgmt_entity = MgmtEntityRecycleView()
        content.add_widget(self.rv_mgmt_entity)
        btn_add = MDFillRoundFlatButton(text='AJOUTER NOUVEAU', size_hint_x=1, md_bg_color=(0, 0.7, 0, 1), on_release=lambda x: self.show_add_edit_entity_dialog(None))
        content.add_widget(btn_add)
        self.mgmt_dialog = MDDialog(title=title_text, type='custom', content_cls=content, size_hint=(0.95, 0.9))
        self.mgmt_dialog.open()
        source = self.all_clients if entity_type == 'account' else self.all_suppliers
        self.populate_entity_manager_list(source)

    def filter_entities_for_manager(self, text_arg):
        query = ''
        if hasattr(self, 'entity_search'):
            query = self.entity_search.get_value()
        else:
            query = text_arg
        if self._entity_search_event:
            self._entity_search_event.cancel()
        self._entity_search_event = Clock.schedule_once(lambda dt: self._start_mgmt_background_search(query), 0.3)

    def _start_mgmt_background_search(self, text):
        threading.Thread(target=self._mgmt_search_worker, args=(text,), daemon=True).start()

    def _mgmt_search_worker(self, text):
        source = self.all_clients if self.current_entity_type_mgmt == 'account' else self.all_suppliers
        if not text:
            self.populate_entity_manager_list(source[:50])
            return
        txt = text.lower()
        filtered = [e for e in source if txt in str(e.get('name', '')).lower()]
        if not filtered:
            try:
                fixed_query = self.fix_text(txt)
                filtered = [e for e in source if fixed_query in self.fix_text(str(e.get('name', '')))]
            except Exception:
                pass
        if len(filtered) > 50:
            filtered = filtered[:50]
        self.populate_entity_manager_list(filtered)

    @mainthread
    def populate_entity_manager_list(self, entities):
        server_default_names = ['Comptoir', 'Fournisseur', 'زبون افتراضي', 'مورد افتراضي']
        sorted_entities = sorted(entities, key=lambda x: x.get('name', '').lower())
        rv_data = []
        for e in sorted_entities:
            name = e.get('name', '')
            if name in server_default_names:
                continue
            balance = float(e.get('balance', 0))
            bal_text = f'{balance:.2f} DA'
            col_hex = 'D50000' if balance > 0 else '00C853'
            balance_markup = f'Solde: [color={col_hex}][b]{bal_text}[/b][/color]'
            rv_data.append({'raw_name': name, 'balance_text': balance_markup, 'raw_data': e})
        if hasattr(self, 'rv_mgmt_entity'):
            self.rv_mgmt_entity.data = rv_data
            self.rv_mgmt_entity.refresh_from_data()

    def start_direct_payment_from_manager(self, entity):
        self.selected_entity = entity
        if self.current_entity_type_mgmt == 'account':
            self.current_mode = 'client_payment'
        else:
            self.current_mode = 'supplier_payment'
        self.show_simple_payment_dialog()

    def open_entity_edit_menu(self, entity):
        self.mgmt_selected_entity = entity
        title_text = self.fix_text(entity['name'])
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=dp(130))
        btn_edit = MDRaisedButton(text='Modifier Informations', size_hint_x=1, md_bg_color=(0.2, 0.2, 0.2, 1), on_release=lambda x: [self.options_dialog.dismiss(), self.show_add_edit_entity_dialog(entity)])
        content.add_widget(btn_edit)
        btn_del = MDFlatButton(text='Supprimer ce compte', theme_text_color='Error', size_hint_x=1, on_release=lambda x: self.confirm_delete_entity(entity))
        content.add_widget(btn_del)
        self.options_dialog = MDDialog(title=title_text, type='custom', content_cls=content)
        self.options_dialog.open()

    def show_add_edit_entity_dialog(self, entity=None):
        if not self.is_server_reachable:
            self.ae_dialog = MDDialog(title='Hors Ligne', text='Modification des tiers impossible en mode hors ligne.\nVeuillez vous connecter au serveur.', buttons=[MDFlatButton(text='OK', on_release=lambda x: self.ae_dialog.dismiss())])
            self.ae_dialog.open()
            return
        is_edit = entity is not None
        title = 'Modifier Fiche' if is_edit else 'Ajouter Nouveau'
        scroll_container = MDScrollView(size_hint_y=None, height=dp(450))
        content = MDBoxLayout(orientation='vertical', spacing=15, adaptive_height=True, padding=[0, 10, 0, 20])
        val_name = entity.get('name', '') if is_edit else ''
        val_phone = entity.get('phone', '') if is_edit else ''
        val_address = entity.get('address', '') if is_edit else ''
        val_activity = entity.get('activity', '') if is_edit else ''
        val_email = entity.get('email', '') if is_edit else ''
        val_rc = entity.get('rc', '') if is_edit else ''
        val_nif = entity.get('nif', '') if is_edit else ''
        val_nis = entity.get('nis', '') if is_edit else ''
        val_nai = entity.get('nai', '') if is_edit else ''
        raw_cat = str(entity.get('price_category', '')).strip() if is_edit else ''
        if raw_cat in ['Gros', 'جملة']:
            display_cat = 'Gros'
        elif raw_cat in ['Demi-Gros', 'نصف جملة']:
            display_cat = 'Demi-Gros'
        else:
            display_cat = 'Détail'
        f_name = SmartTextField(text=val_name, hint_text='Nom Complet *', required=True)
        f_phone = SmartTextField(text=val_phone, hint_text='Téléphone', input_filter='int')
        f_address = SmartTextField(text=val_address, hint_text='Adresse')
        f_activity = SmartTextField(text=val_activity, hint_text='Activité')
        f_email = SmartTextField(text=val_email, hint_text='Email')
        f_price_cat = MDTextField(text=display_cat, hint_text='Catégorie de Prix', readonly=True)

        def on_cat_focus(instance, value):
            if value:
                instance.focus = False
                self.show_price_cat_selector(instance)
        f_price_cat.bind(focus=on_cat_focus)
        f_rc = SmartTextField(text=val_rc, hint_text='N° Registre Commerce (RC)')
        f_nif = SmartTextField(text=val_nif, hint_text='N.I.F')
        f_nis = SmartTextField(text=val_nis, hint_text='N.I.S')
        f_nai = SmartTextField(text=val_nai, hint_text='N.A.I')
        content.add_widget(f_name)
        content.add_widget(f_phone)
        content.add_widget(f_address)
        content.add_widget(f_activity)
        if self.current_entity_type_mgmt == 'account':
            content.add_widget(f_price_cat)
        content.add_widget(f_email)
        content.add_widget(f_rc)
        content.add_widget(f_nif)
        content.add_widget(f_nis)
        content.add_widget(f_nai)
        scroll_container.add_widget(content)

        def save(x):
            name_val = f_name.get_value().strip()
            if not name_val:
                f_name.error = True
                return
            cat_ar = 'تجزئة'
            if self.current_entity_type_mgmt == 'account':
                selected_cat_fr = f_price_cat.text
                if selected_cat_fr == 'Gros':
                    cat_ar = 'جملة'
                elif selected_cat_fr == 'Demi-Gros':
                    cat_ar = 'نصف جملة'
                else:
                    cat_ar = 'تجزئة'
            payload = {'action': 'update' if is_edit else 'add', 'type': self.current_entity_type_mgmt, 'name': name_val, 'phone': f_phone.get_value().strip(), 'address': f_address.get_value().strip(), 'activity': f_activity.get_value().strip(), 'email': f_email.get_value().strip(), 'price_category': cat_ar, 'rc': f_rc.get_value().strip(), 'nif': f_nif.get_value().strip(), 'nis': f_nis.get_value().strip(), 'nai': f_nai.get_value().strip(), 'id': entity.get('id') if is_edit else None}
            if self.is_server_reachable:
                UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/manage_entity', req_body=json.dumps(payload), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, s: [self.ae_dialog.dismiss(), self.notify('Enregistré avec succès', 'success'), self.fetch_entities(self.current_entity_type_mgmt)], on_failure=lambda r, e: self.notify(f'Erreur: {e}', 'error'))
            else:
                self.notify('Impossible: Mode Hors Ligne', 'error')
        self.ae_dialog = MDDialog(title=title, type='custom', content_cls=scroll_container, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.ae_dialog.dismiss()), MDRaisedButton(text='ENREGISTRER', on_release=save)])
        self.ae_dialog.open()

    def show_price_cat_selector(self, text_field_instance):
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=dp(160), padding=dp(10))

        def select(value):
            text_field_instance.text = value
            self.cat_dialog.dismiss()
        content.add_widget(MDRaisedButton(text='Détail', size_hint_x=1, md_bg_color=(0, 0.6, 0.6, 1), on_release=lambda x: select('Détail')))
        content.add_widget(MDRaisedButton(text='Demi-Gros', size_hint_x=1, md_bg_color=(0.9, 0.6, 0, 1), on_release=lambda x: select('Demi-Gros')))
        content.add_widget(MDRaisedButton(text='Gros', size_hint_x=1, md_bg_color=(0.5, 0, 0.5, 1), on_release=lambda x: select('Gros')))
        self.cat_dialog = MDDialog(title='Choisir Catégorie', type='custom', content_cls=content, size_hint=(0.8, None))
        self.cat_dialog.open()

    def confirm_delete_entity(self, entity):
        if not self.is_server_reachable:
            if hasattr(self, 'options_dialog') and self.options_dialog:
                self.options_dialog.dismiss()
            self.ae_dialog = MDDialog(title='Hors Ligne', text='Gestion des tiers impossible en mode hors ligne.\nVeuillez vous connecter au serveur.', buttons=[MDFlatButton(text='OK', on_release=lambda x: self.ae_dialog.dismiss())])
            self.ae_dialog.open()
            return
        if self.options_dialog:
            self.options_dialog.dismiss()

        def do_delete(x):
            if self.del_conf_dialog:
                self.del_conf_dialog.dismiss()
            payload = {'action': 'delete', 'id': entity['id'], 'type': self.current_entity_type_mgmt}
            if self.is_server_reachable:
                UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/manage_entity', req_body=json.dumps(payload), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, s: [self.notify('Compte supprimé', 'success'), self.fetch_entities(self.current_entity_type_mgmt)], on_failure=lambda r, e: self.notify('Impossible (Contient des opérations)', 'error'))
            else:
                self.notify('Erreur connexion', 'error')
        name_display = self.fix_text(entity['name'])
        self.del_conf_dialog = MDDialog(title='Confirmation', text=f'Voulez-vous vraiment supprimer {name_display} ?\nCette action est irréversible.', buttons=[MDFlatButton(text='NON', on_release=lambda x: self.del_conf_dialog.dismiss()), MDRaisedButton(text='OUI, SUPPRIMER', md_bg_color=(1, 0, 0, 1), on_release=do_delete)])
        self.del_conf_dialog.open()

    def check_server_heartbeat(self, dt):
        if self.sync_paused:
            self.is_server_reachable = False
            if self.status_bar_label:
                self.status_bar_label.text = 'Synchronisation Arrêtée (PAUSE)'
                self.status_bar_bg.md_bg_color = (0.8, 0, 0, 1)
            return
        threading.Thread(target=self._run_socket_ping_logic, daemon=True).start()

    def _run_socket_ping_logic(self):
        ping_val = self._try_ping_host(self.local_server_ip)
        if ping_val is not None:
            self._finalize_ping_ui(True, ping_val, self.local_server_ip)
            return
        if self.external_server_ip:
            ping_val_ext = self._try_ping_host(self.external_server_ip)
            if ping_val_ext is not None:
                self._finalize_ping_ui(True, ping_val_ext, self.external_server_ip)
                return
        self._finalize_ping_ui(False, 0, None)

    def _try_ping_host(self, ip_address):
        if not ip_address:
            return None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            start_time = time.time()
            sock.connect((ip_address, int(DEFAULT_PORT)))
            sock.close()
            end_time = time.time()
            return int((end_time - start_time) * 1000)
        except:
            return None

    @mainthread
    def _finalize_ping_ui(self, success, ping_val, confirmed_ip):
        if success:
            self.last_ping = ping_val
            self.active_server_ip = confirmed_ip
            self._on_heartbeat_success()
        else:
            self._on_heartbeat_fail_final(None, 'Connection Failed')

    def _reset_notification_state(self, dt):
        if not self.status_bar_label:
            return
        self.status_bar_label.markup = True
        if self._ready_timer:
            self._ready_timer.cancel()
            self._ready_timer = None
        if self.sync_paused:
            self.status_bar_label.text = 'Synchronisation Arrêtée (PAUSE)'
            self.status_bar_bg.md_bg_color = (0.8, 0, 0, 1)
            return
        self._notify_event = None
        pending = len([k for k in self.offline_store.keys() if not self.offline_store.get(k).get('synced', False)])
        ping_display = ''
        bg_color = (0.4, 0.4, 0.4, 1)
        ping_val = getattr(self, 'last_ping', 0)
        if self.is_server_reachable:
            if ping_val < 100:
                bg_color = (0, 0.7, 0, 1)
            elif ping_val < 300:
                bg_color = (0.9, 0.5, 0, 1)
            else:
                bg_color = (0.8, 0, 0, 1)
            ping_display = f' • [color=FFFFFF][b][size=16sp]{ping_val}ms[/size][/b][/color]'
        if pending > 0:
            if self.is_server_reachable and ping_val >= 300:
                self.status_bar_bg.md_bg_color = (0.8, 0, 0, 1)
            else:
                self.status_bar_bg.md_bg_color = (0.9, 0.5, 0, 1)
            self.status_bar_label.text = f'En attente de sync: {pending}{ping_display}'
        elif self.is_server_reachable:
            net = 'Local' if self.active_server_ip == self.local_server_ip else 'Ext'
            self.status_bar_bg.md_bg_color = bg_color
            self.status_bar_label.text = f'Connecté ({net}){ping_display}'
        else:
            self.status_bar_label.text = 'Hors Ligne'
            self.status_bar_bg.md_bg_color = (0.4, 0.4, 0.4, 1)

    def fetch_store_info(self):
        if self.is_server_reachable:
            url = f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/store_info'
            UrlRequest(url, on_success=self.save_store_info_callback)

    def save_store_info_callback(self, req, res):
        if res:
            self.store.put('print_header', name=res.get('name', 'MagPro Store'), address=res.get('address', ''), phone=res.get('phone', ''))

    def _on_heartbeat_success(self):
        self.is_server_reachable = True
        unsynced = [k for k in self.offline_store.keys() if not self.offline_store.get(k).get('synced', False)]
        if unsynced:
            self.try_sync_offline_data()
        if self.is_offline_mode:
            self.is_offline_mode = False
            self.notify(f"Connexion OK ({('Local' if self.active_server_ip == self.local_server_ip else 'Ext')})", 'success')
            self.fetch_products()
            self.fetch_entities('account')
            self.fetch_entities('supplier')
            self.fetch_store_info()
        if hasattr(self, 'login_status_icon'):
            self.login_status_icon.text_color = (0, 0.8, 0, 1)
        if not self._notify_event:
            self._reset_notification_state(0)
        if not self.store.exists('print_header'):
            self.fetch_store_info()

    def _on_heartbeat_fail_final(self, req, err):
        if self.is_server_reachable:
            self.is_server_reachable = False
            self.is_offline_mode = True
            self.notify('Mode Hors Ligne (No Connection)', 'error')
        if hasattr(self, 'login_status_icon'):
            self.login_status_icon.text_color = (0.8, 0, 0, 1)
        if not self._notify_event:
            self._reset_notification_state(0)

    def try_sync_offline_data(self):
        if self.sync_paused:
            return
        if not self.is_server_reachable:
            return
        keys = list(self.offline_store.keys())
        unsynced = [k for k in keys if not self.offline_store.get(k).get('synced', False)]
        if not unsynced:
            self._reset_notification_state(0)
            return
        sorted_keys = sorted(unsynced, key=lambda x: int(x.split('_')[0]) if x.split('_')[0].isdigit() else 0)
        key = sorted_keys[0]
        try:
            item_data = self.offline_store.get(key)
            data = item_data['order_data']
            endpoint = '/api/submit_payment' if data.get('is_simple_payment') else '/api/submit_order'

            def next_step(*args):
                Clock.schedule_once(lambda d: self.try_sync_offline_data(), 0.5)

            def success(r, res):
                item_data['synced'] = True
                item_data['sync_timestamp'] = time.time()
                if res.get('server_id'):
                    item_data['order_data']['server_id'] = res.get('server_id')
                if res.get('invoice_number'):
                    item_data['order_data']['invoice_number'] = res.get('invoice_number')
                self.offline_store.put(key, **item_data)
                self.notify(f"Sync OK: {data.get('doc_type', 'Op')}", 'success')
                next_step()

            def failure(req, err):
                print(f'Sync Fail for {key}: {err}')
                next_step()
            UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}{endpoint}', req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=success, on_failure=failure, on_error=failure, timeout=10)
        except Exception as e:
            print(f'Sync Logic Error: {e}')
            Clock.schedule_once(lambda d: self.try_sync_offline_data(), 1)

    def toggle_sync(self):
        self.sync_paused = not self.sync_paused
        action_items = self.dash_toolbar.right_action_items
        if self.sync_paused:
            action_items[1] = ['sync-off', lambda x: self.toggle_sync()]
            self.is_server_reachable = False
            self.notify('SYNC ARRÊTÉE', 'error')
        else:
            action_items[1] = ['sync', lambda x: self.toggle_sync()]
            self.notify('SYNC ACTIVE... Connexion', 'success')
            self.check_server_heartbeat(0)
        self.dash_toolbar.right_action_items = action_items

    def notify(self, text, type='info'):
        if not self.status_bar_label:
            return
        color_map = {'success': (0, 0.6, 0, 1), 'error': (0.8, 0.1, 0.1, 1), 'warning': (0.9, 0.5, 0, 1), 'info': (0.2, 0.2, 0.2, 1)}
        self.status_bar_label.text = text
        self.status_bar_bg.md_bg_color = color_map.get(type, (0.2, 0.2, 0.2, 1))
        if self._notify_event:
            self._notify_event.cancel()
        self._notify_event = Clock.schedule_once(self._reset_notification_state, 3)

    def change_status_to_ready(self, dt):
        pending = len([k for k in self.offline_store.keys() if not self.offline_store.get(k).get('synced', False)])
        if self.is_server_reachable and (not self.sync_paused) and (pending == 0):
            self.status_bar_label.text = 'Prêt'
            self.status_bar_bg.md_bg_color = (0.15, 0.5, 0.15, 1)

    def _auto_login_check(self, dt):
        if self.store.exists('credentials'):
            creds = self.store.get('credentials')
            self.username_field.text = creds.get('username', '')
            self.password_field.text = creds.get('password', '')
            if self.username_field.text:
                self.do_login(None)

    def do_login(self, x):
        self.notify('Connexion...', 'info')
        url = f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/login'
        body = json.dumps({'username': self.username_field.get_value(), 'password': self.password_field.get_value()})
        UrlRequest(url, req_body=body, req_headers={'Content-type': 'application/json'}, method='POST', on_success=self.login_success, on_failure=self.login_fail, on_error=self.login_error, timeout=4)

    def login_success(self, req, res):
        if res.get('status') == 'success':
            self.current_user_name = self.username_field.get_value()
            self.store.put('credentials', username=self.current_user_name, password=self.password_field.get_value())
            self.is_offline_mode = False
            self.is_server_reachable = True
            self.sm.current = 'dashboard'
            self.fetch_products()
            self.fetch_entities('account')
            self.fetch_entities('supplier')
            self.fetch_store_info()
            self.check_and_load_stats()
        else:
            self.notify('Identifiants incorrects', 'error')

    def login_fail(self, req, res):
        self.check_offline_access()

    def login_error(self, req, error):
        self.check_offline_access()

    def check_offline_access(self):
        if self.store.exists('credentials'):
            creds = self.store.get('credentials')
            if self.username_field.get_value() == creds.get('username', '') and self.password_field.get_value() == creds.get('password', ''):
                if self.cache_store.exists('products'):
                    self.notify('Mode Hors Ligne', 'warning')
                    self.is_offline_mode = True
                    self.current_user_name = self.username_field.get_value()
                    self.sm.current = 'dashboard'
                    self.load_products_from_cache()
                    if self.cache_store.exists('clients'):
                        self.all_clients = self.cache_store.get('clients')['data']
                    if self.cache_store.exists('suppliers'):
                        self.all_suppliers = self.cache_store.get('suppliers')['data']
                    self.check_and_load_stats()
                else:
                    self.notify('Pas de données locales', 'error')
            else:
                self.notify('Erreur Login', 'error')
        else:
            self.notify('Serveur inaccessible', 'error')

    def logout(self):

        def perform_logout(x):
            if hasattr(self, 'logout_diag') and self.logout_diag:
                self.logout_diag.dismiss()
            if self.store.exists('credentials'):
                self.store.delete('credentials')
            self.password_field.text = ''
            self.sm.current = 'login'
        if not self.is_server_reachable:
            self.logout_diag = MDDialog(title='Attention : Hors Ligne', text="Le serveur est inaccessible !\nSi vous vous déconnectez maintenant, vous ne pourrez plus vous reconnecter tant que la liaison avec le serveur n'est pas rétablie.\n\nVoulez-vous vraiment continuer ?", buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.logout_diag.dismiss()), MDRaisedButton(text='OUI, SE DÉCONNECTER', md_bg_color=(1, 0, 0, 1), on_release=perform_logout)])
            self.logout_diag.open()
        else:
            perform_logout(None)

    def _create_stat_item(self, title, ref_name, color):
        box = MDBoxLayout(orientation='vertical', padding=dp(5), md_bg_color=(1, 1, 1, 1), radius=[5])
        box.add_widget(MDLabel(text=title, font_style='Caption', halign='center'))
        val_lbl = MDLabel(text='0.00 DA', font_style='Subtitle2', bold=True, halign='center', theme_text_color='Custom', text_color=color)
        setattr(self, ref_name, val_lbl)
        box.add_widget(val_lbl)
        return box

    def _create_dash_btn(self, icon, text, bg_color, icon_color, action):
        card = MDCard(orientation='vertical', padding=dp(15), radius=[12], ripple_behavior=True, on_release=action, md_bg_color=bg_color, elevation=2, size_hint_y=None, height=dp(110))
        card.add_widget(MDIcon(icon=icon, font_size='38sp', pos_hint={'center_x': 0.5}, theme_text_color='Custom', text_color=icon_color))
        card.add_widget(MDLabel(text=text, halign='center', bold=True, font_style='Caption'))
        return card

    def _build_login_screen(self):
        screen = MDScreen(name='login')
        layout = MDFloatLayout()
        self.login_status_icon = MDIcon(icon='circle', font_size='15sp', pos_hint={'top': 0.96, 'right': 0.85}, theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1))
        layout.add_widget(self.login_status_icon)
        layout.add_widget(MDIconButton(icon='cog', pos_hint={'top': 0.98, 'right': 0.98}, on_release=self.open_ip_settings))
        card = MDCard(orientation='vertical', size_hint=(0.85, None), height=dp(340), pos_hint={'center_x': 0.5, 'center_y': 0.5}, padding=dp(20), spacing=dp(15), radius=[20], elevation=4)
        icon_box = MDFloatLayout(size_hint_y=None, height=dp(70))
        icon_box.add_widget(MDIcon(icon='store', font_size='60sp', pos_hint={'center_x': 0.5, 'center_y': 0.5}, theme_text_color='Primary'))
        card.add_widget(icon_box)
        card.add_widget(MDLabel(text='MagPro Gestion de Stock', halign='center', font_style='H5', bold=True))
        self.username_field = SmartTextField(hint_text='Utilisateur', text=self.current_user_name, icon_right='account')
        self.password_field = SmartTextField(hint_text='Mot de passe', password=True, icon_right='key')
        card.add_widget(self.username_field)
        card.add_widget(self.password_field)
        card.add_widget(MDFillRoundFlatButton(text='CONNEXION', font_size='18sp', size_hint_x=1, on_release=self.do_login))
        layout.add_widget(card)
        footer_label = MDLabel(text='MagPro v7.1.0.0 © 2026', halign='center', pos_hint={'center_x': 0.5, 'y': 0.02}, size_hint_y=None, height=dp(20), font_style='Caption', theme_text_color='Hint')
        layout.add_widget(footer_label)
        screen.add_widget(layout)
        return screen

    def _build_dashboard_screen(self):
        screen = MDScreen(name='dashboard')
        layout = MDBoxLayout(orientation='vertical')
        self.dash_toolbar = MDTopAppBar(title='Accueil', right_action_items=[['clock-time-eight-outline', lambda x: self.show_pending_dialog()], ['sync', lambda x: self.toggle_sync()], ['logout', lambda x: self.logout()]])
        layout.add_widget(self.dash_toolbar)
        scroll = MDScrollView()
        self.main_dash_content = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(20), padding=dp(15))
        self.buttons_container = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(15))
        self.main_dash_content.add_widget(self.buttons_container)
        self.stats_card_container = MDCard(orientation='vertical', size_hint_y=None, height=dp(280), padding=dp(10), radius=[10], elevation=2, md_bg_color=(0.97, 0.97, 0.97, 1))
        self.main_dash_content.add_widget(self.stats_card_container)
        scroll.add_widget(self.main_dash_content)
        layout.add_widget(scroll)
        screen.add_widget(layout)
        return screen

    def _build_products_screen(self):
        screen = MDScreen(name='products')
        layout = MDBoxLayout(orientation='vertical')
        self.prod_toolbar = MDTopAppBar(title='Produits', left_action_items=[['arrow-left', lambda x: self.go_back()]])
        layout.add_widget(self.prod_toolbar)
        
        # --- التعديل: إضافة زر الباركود ---
        self.prod_search_layout = MDBoxLayout(padding=(10, 5), spacing=dp(5), size_hint_y=None, height=dp(60))
        
        # زر الباركود
        btn_scan = MDIconButton(
            icon='barcode-scan',
            theme_text_color="Custom",
            text_color=(0, 0, 0, 1),
            pos_hint={'center_y': 0.5},
            icon_size='32sp',
            on_release=self.open_barcode_scanner
        )
        self.prod_search_layout.add_widget(btn_scan)
        
        self.search_field = SmartTextField(hint_text='Rechercher (Nom/Codebar)...', mode='rectangle', icon_right='magnify')
        self.search_field.bind(text=self.filter_products)
        
        self.btn_add_prod = MDIconButton(icon='plus', theme_text_color='Custom', text_color=(0, 0.7, 0, 1), pos_hint={'center_y': 0.5}, icon_size='36sp', on_release=lambda x: self.show_manage_product_dialog(None))
        
        self.prod_search_layout.add_widget(self.search_field)
        layout.add_widget(self.prod_search_layout)
        # ----------------------------------

        self.rv_products = ProductRecycleView()
        layout.add_widget(self.rv_products)
        self.cart_bar = MDCard(size_hint_y=None, height=dp(60), padding=[dp(15), dp(5)], md_bg_color=self.theme_cls.primary_color, radius=[10, 10, 0, 0], ripple_behavior=True, on_release=self.open_cart_screen, elevation=2)
        cart_box = MDBoxLayout(orientation='horizontal')
        self.lbl_cart_count = MDLabel(text='PANIER (0)', theme_text_color='Custom', text_color=(1, 1, 1, 1), bold=True, halign='left', size_hint_x=0.5)
        self.lbl_cart_total = MDLabel(text='0.00 DA', theme_text_color='Custom', text_color=(1, 1, 1, 1), bold=True, halign='right', font_style='H6', size_hint_x=0.5)
        cart_box.add_widget(self.lbl_cart_count)
        cart_box.add_widget(self.lbl_cart_total)
        self.cart_bar.add_widget(cart_box)
        layout.add_widget(self.cart_bar)
        screen.add_widget(layout)
        return screen

    def _build_cart_screen(self):
        screen = MDScreen(name='cart')
        layout = MDBoxLayout(orientation='vertical')
        toolbar = MDTopAppBar(title='Panier', left_action_items=[['arrow-left', lambda x: self.back_to_products()]])
        layout.add_widget(toolbar)
        selectors_frame = MDCard(orientation='horizontal', size_hint_y=None, height=dp(70), padding=[dp(10), dp(10)], radius=[0], elevation=0, md_bg_color=(0.95, 0.95, 0.95, 1))
        self.btn_ent_screen = MDFillRoundFlatButton(text='Client', size_hint_x=0.4, md_bg_color=(0.3, 0.3, 0.3, 1), on_release=self.handle_entity_button_click)
        spacer = MDBoxLayout(size_hint_x=0.2)
        self.btn_loc_screen = MDFillRoundFlatButton(text='Magasin', size_hint_x=0.4, on_release=self.toggle_location)
        selectors_frame.add_widget(self.btn_ent_screen)
        selectors_frame.add_widget(spacer)
        selectors_frame.add_widget(self.btn_loc_screen)
        layout.add_widget(selectors_frame)
        self.cart_scroll_view = MDScrollView()
        self.cart_list_layout = MDList()
        self.cart_scroll_view.add_widget(self.cart_list_layout)
        layout.add_widget(self.cart_scroll_view)
        footer_card = MDCard(orientation='vertical', size_hint_y=None, height=dp(120), padding=dp(15), spacing=dp(10), elevation=4, radius=[15, 15, 0, 0])
        total_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.lbl_total_title = MDLabel(text='TOTAL À PAYER', font_style='Subtitle2', theme_text_color='Hint', valign='center')
        total_row.add_widget(self.lbl_total_title)
        self.lbl_cart_screen_total = MDLabel(text='0.00 DA', halign='right', font_style='H4', bold=True, theme_text_color='Custom', text_color=self.theme_cls.primary_color)
        total_row.add_widget(self.lbl_cart_screen_total)
        footer_card.add_widget(total_row)
        self.btn_validate_cart = MDFillRoundFlatButton(text='VALIDER LA COMMANDE', font_size='18sp', size_hint=(1, None), height=dp(50), md_bg_color=(0, 0.7, 0, 1), on_release=self.open_payment_dialog)
        footer_card.add_widget(self.btn_validate_cart)
        layout.add_widget(footer_card)
        screen.add_widget(layout)
        return screen

    def open_cart_screen(self, x=None):
        if self.current_mode != 'transfer' and self.selected_entity is None:
            self.show_entity_selection_dialog(None, next_action=lambda: self.open_cart_screen(None))
            return
        self.refresh_cart_screen_items()
        self.sm.transition.direction = 'left'
        self.sm.current = 'cart'

    def back_to_products(self):
        self.sm.transition.direction = 'right'
        self.sm.current = 'products'

    def handle_entity_button_click(self, instance):
        if self.current_mode == 'transfer':
            self.toggle_location(instance)
        else:
            self.show_entity_selection_dialog(instance)

    def refresh_cart_screen_items(self):
        try:
            total_val = sum((float(i.get('price', 0)) * float(i.get('qty', 0)) for i in self.cart))
        except:
            total_val = 0
        if self.current_mode == 'transfer':
            if hasattr(self, 'lbl_cart_screen_total'):
                self.lbl_cart_screen_total.text = ''
            if hasattr(self, 'btn_validate_cart'):
                self.btn_validate_cart.text = 'VALIDER TRANSFERT'
        else:
            if hasattr(self, 'lbl_cart_screen_total'):
                self.lbl_cart_screen_total.text = f'{total_val:.2f} DA'
            if hasattr(self, 'btn_validate_cart'):
                self.btn_validate_cart.text = 'VALIDER LA COMMANDE'
        if hasattr(self, 'btn_ent_screen'):
            if self.current_mode == 'transfer':
                src = 'Magasin' if self.selected_location == 'store' else 'Dépôt'
                dst = 'Dépôt' if self.selected_location == 'store' else 'Magasin'
                self.btn_ent_screen.text = f'{src}  >>>  {dst}'
                self.btn_ent_screen.disabled = False
                self.btn_ent_screen.md_bg_color = (0.5, 0, 0.5, 1)
                self.btn_loc_screen.opacity = 0
                self.btn_loc_screen.disabled = True
            else:
                self.btn_ent_screen.disabled = False
                self.btn_loc_screen.opacity = 1
                self.btn_loc_screen.disabled = False
                if self.selected_entity:
                    self.btn_ent_screen.text = self.fix_text(self.selected_entity.get('name', 'Tiers'))[:15]
                self.btn_ent_screen.md_bg_color = (0, 0.6, 0.6, 1) if self.current_mode in ['sale', 'client_payment', 'invoice_sale', 'proforma'] else (0.8, 0.4, 0, 1)
        self.update_location_display()
        self.cart_list_layout.clear_widgets()
        if not self.cart:
            return
        for item in self.cart:
            try:
                p = float(item.get('price', 0))
                q = float(item.get('qty', 0))
                t = p * q
                q_disp = str(int(q)) if q.is_integer() else str(q)
                if self.current_mode == 'transfer':
                    sec = f'[color=#1976D2][b][size=20sp]Qté: {q_disp}[/size][/b][/color]'
                else:
                    sec = f'[b][size=16sp]{p:.2f} DA x {q_disp} = {t:.2f} DA[/size][/b]'
                li = TwoLineAvatarIconListItem(text=self.fix_text(item.get('name', '')), secondary_text=sec, on_release=lambda x, it=item: self.edit_cart_item(it))
                del_btn = IconRightWidget(icon='delete', theme_text_color='Custom', text_color=(0.9, 0, 0, 1), on_release=lambda x, it=item: self.remove_from_cart(it))
                li.add_widget(del_btn)
                li.add_widget(IconLeftWidget(icon='package-variant'))
                self.cart_list_layout.add_widget(li)
            except Exception as e:
                print(e)

    def edit_cart_item(self, item):

        def fmt_num(value):
            try:
                val_float = float(value)
                if val_float.is_integer():
                    return str(int(val_float))
                return str(val_float)
            except:
                return '0'
        content = MDBoxLayout(orientation='vertical', spacing='10dp', size_hint_y=None, height=dp(520), padding=[0, '5dp', 0, 0])
        self.active_edit_target = 'qty'
        product_name = self.fix_text(item.get('name', 'Produit'))
        lbl_prod = MDLabel(text=product_name, halign='center', bold=True, font_style='Subtitle1', theme_text_color='Primary', adaptive_height=True)
        content.add_widget(lbl_prod)
        if self.current_mode != 'transfer':
            price_val = item.get('price', 0)
            self.edit_price_field = MDTextField(text=fmt_num(price_val), hint_text='Prix Unitaire (DA)', font_size='26sp', halign='center', mode='fill', readonly=True, line_color_normal=(0, 0, 0, 0))

            def on_price_focus(instance, value):
                if value:
                    self.active_edit_target = 'price'
                    self.edit_price_field.line_color_normal = (0, 0.7, 0, 1)
                    self.edit_qty_field.line_color_normal = (0, 0, 0, 0)
                    instance.focus = False
            self.edit_price_field.bind(focus=on_price_focus)
            price_box = MDBoxLayout(size_hint_y=None, height='80dp', padding=[60, 0, 60, 0])
            price_box.add_widget(self.edit_price_field)
            content.add_widget(price_box)
        qty_row = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp', padding=[40, 0])
        btn_minus = MDIconButton(icon='minus', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.9, 0.3, 0.3, 1), pos_hint={'center_y': 0.5}, icon_size='20sp')
        qty_val = item.get('qty', 1)
        self.edit_qty_field = MDTextField(text=fmt_num(qty_val), hint_text='Qté', font_size='28sp', halign='center', readonly=True, size_hint_x=1, pos_hint={'center_y': 0.5}, mode='line', line_color_normal=(0, 0.7, 0, 1))

        def on_qty_focus(instance, value):
            if value:
                self.active_edit_target = 'qty'
                self.edit_qty_field.line_color_normal = (0, 0.7, 0, 1)
                if hasattr(self, 'edit_price_field'):
                    self.edit_price_field.line_color_normal = (0, 0, 0, 0)
                instance.focus = False
        self.edit_qty_field.bind(focus=on_qty_focus)
        btn_plus = MDIconButton(icon='plus', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.2, 0.7, 0.2, 1), pos_hint={'center_y': 0.5}, icon_size='20sp')
        qty_row.add_widget(btn_minus)
        qty_row.add_widget(self.edit_qty_field)
        qty_row.add_widget(btn_plus)
        content.add_widget(qty_row)
        self.btn_save_edit = MDRaisedButton(text='MODIFIER', md_bg_color=(0, 0.6, 0, 1), text_color=(1, 1, 1, 1), size_hint_x=0.7, size_hint_y=1, font_size='18sp', elevation=3)

        def update_calculations():
            try:
                q = float(self.edit_qty_field.text)
            except:
                q = 0.0
            p = 0.0
            if hasattr(self, 'edit_price_field'):
                try:
                    p = float(self.edit_price_field.text)
                except:
                    p = 0.0
            else:
                p = float(item.get('price', 0))
            total = p * q
            if self.current_mode != 'transfer':
                self.btn_save_edit.text = f'MODIFIER\n{total:.2f} DA'
            else:
                self.btn_save_edit.text = 'MODIFIER'

        def change_qty(amount):
            try:
                current = float(self.edit_qty_field.text)
                new_val = current + amount
                if new_val < 1:
                    new_val = 1
                self.edit_qty_field.text = fmt_num(new_val)
                update_calculations()
            except:
                self.edit_qty_field.text = '1'
        btn_plus.bind(on_release=lambda x: change_qty(1))
        btn_minus.bind(on_release=lambda x: change_qty(-1))

        def get_active_field():
            if self.active_edit_target == 'price' and hasattr(self, 'edit_price_field'):
                return self.edit_price_field
            return self.edit_qty_field

        def add_digit(digit):
            field = get_active_field()
            current = field.text
            if digit == '.':
                if '.' in current:
                    return
                if not current:
                    field.text = '0.'
                else:
                    field.text = current + '.'
            elif current == '0' or (self.active_edit_target == 'qty' and current == '1' and (len(current) == 1)):
                field.text = str(digit)
            else:
                field.text = current + str(digit)
            update_calculations()

        def backspace(x=None):
            field = get_active_field()
            current = field.text
            if len(current) > 0:
                field.text = current[:-1]
            if not field.text:
                field.text = '1' if self.active_edit_target == 'qty' else '0'
            update_calculations()
        grid = MDGridLayout(cols=3, spacing='8dp', size_hint_y=1, padding=[20, 0])
        keys = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0', 'DEL']
        for key in keys:
            if key == 'DEL':
                btn = MDIconButton(icon='backspace-outline', theme_text_color='Custom', text_color=(0, 0, 0, 1), md_bg_color=(0.8, 0.8, 0.8, 1), size_hint=(1, 1), icon_size='22sp', on_release=backspace)
            else:
                btn = MDRaisedButton(text=key, md_bg_color=(0.95, 0.95, 0.95, 1), theme_text_color='Custom', text_color=(0, 0, 0, 1), font_size='22sp', size_hint=(1, 1), elevation=1, on_release=lambda x, k=key: add_digit(k))
            grid.add_widget(btn)
        content.add_widget(grid)
        content.add_widget(MDLabel(text='', size_hint_y=None, height='5dp'))
        buttons_box = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp')
        btn_cancel = MDFlatButton(text='ANNULER', theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1), size_hint_x=0.3, on_release=lambda x: self.edit_dialog.dismiss())

        def save_changes(x):
            try:
                new_q = float(self.edit_qty_field.text)
                if new_q <= 0:
                    raise ValueError
                item['qty'] = new_q
                if self.current_mode != 'transfer' and hasattr(self, 'edit_price_field'):
                    new_p = float(self.edit_price_field.text)
                    if new_p < 0:
                        raise ValueError
                    item['price'] = new_p
                self.refresh_cart_screen_items()
                self.update_cart_button()
                self.edit_dialog.dismiss()
            except:
                self.notify('Valeurs invalides', 'error')
        self.btn_save_edit.bind(on_release=save_changes)
        buttons_box.add_widget(btn_cancel)
        buttons_box.add_widget(self.btn_save_edit)
        content.add_widget(buttons_box)
        update_calculations()
        self.edit_dialog = MDDialog(title='', type='custom', content_cls=content, buttons=[], size_hint=(0.85, None))
        self.edit_dialog.open()

    def open_ip_settings(self, instance):
        content = MDBoxLayout(orientation='vertical', spacing='12dp', size_hint_y=None, height='450dp', padding='15dp')
        scroll = MDScrollView()
        box = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='20dp')
        box.add_widget(MDBoxLayout(size_hint_y=None, height='20dp'))
        server_card = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='10dp')
        server_card.add_widget(MDLabel(text='Configuration Serveur', font_style='Subtitle2', theme_text_color='Primary', bold=True))
        self.local_ip_field = MDTextField(text=self.local_server_ip, hint_text='IP Local', icon_right='lan-connect')
        self.external_ip_field = MDTextField(text=self.external_server_ip, hint_text='IP Externe', icon_right='web')
        server_card.add_widget(self.local_ip_field)
        server_card.add_widget(self.external_ip_field)
        box.add_widget(server_card)
        box.add_widget(MDBoxLayout(size_hint_y=None, height='1dp', md_bg_color=(0.9, 0.9, 0.9, 1)))
        printer_card = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='10dp')
        printer_card.add_widget(MDLabel(text='Imprimante Bluetooth (80mm)', font_style='Subtitle2', theme_text_color='Primary', bold=True))
        printer_conf = {'name': '', 'mac': '', 'auto': False}
        if self.store.exists('printer_config'):
            printer_conf = self.store.get('printer_config')
        self.temp_selected_mac = printer_conf.get('mac', '')
        printer_box = MDBoxLayout(orientation='horizontal', spacing='8dp', size_hint_y=None, height='50dp')
        self.printer_name_field = MDTextField(text=printer_conf.get('name', ''), hint_text='Imprimante non définie', readonly=True, size_hint_x=0.7, pos_hint={'center_y': 0.5})
        if self.temp_selected_mac:
            self.printer_name_field.helper_text = f'ID: {self.temp_selected_mac}'
        btn_search_bt = MDIconButton(icon='magnify', icon_size='20sp', md_bg_color=(0.2, 0.2, 0.2, 1), theme_text_color='Custom', text_color=(1, 1, 1, 1), pos_hint={'center_y': 0.6}, size_hint=(None, None), size=(dp(40), dp(40)), on_release=self.open_bluetooth_selector)
        btn_clear_bt = MDIconButton(icon='delete', icon_size='20sp', md_bg_color=(0.8, 0.2, 0.2, 1), theme_text_color='Custom', text_color=(1, 1, 1, 1), pos_hint={'center_y': 0.6}, size_hint=(None, None), size=(dp(40), dp(40)), on_release=self.clear_printer_selection)
        printer_box.add_widget(self.printer_name_field)
        printer_box.add_widget(btn_search_bt)
        printer_box.add_widget(btn_clear_bt)
        printer_card.add_widget(printer_box)
        row_opts = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='40dp')
        lbl_auto = MDLabel(text='Impression Auto après validation:', size_hint_x=0.85, valign='center', theme_text_color='Secondary')
        self.chk_auto_print = MDCheckbox(active=printer_conf.get('auto', False), size_hint=(None, None), size=(dp(40), dp(40)), pos_hint={'center_y': 0.5})
        row_opts.add_widget(lbl_auto)
        row_opts.add_widget(self.chk_auto_print)
        printer_card.add_widget(row_opts)
        box.add_widget(printer_card)
        box.add_widget(MDBoxLayout(size_hint_y=None, height='1dp', md_bg_color=(0.9, 0.9, 0.9, 1)))
        admin_card = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='10dp')
        admin_card.add_widget(MDLabel(text='Administration', font_style='Subtitle2', theme_text_color='Primary', bold=True))
        btn_seller = MDRaisedButton(text='GÉRER LE MODE VENDEUR', md_bg_color=(0.25, 0.25, 0.25, 1), text_color=(1, 1, 1, 1), size_hint_x=1, elevation=2, on_release=self.open_seller_auth_dialog)
        admin_card.add_widget(btn_seller)
        box.add_widget(admin_card)
        scroll.add_widget(box)
        content.add_widget(scroll)
        self.dialog = MDDialog(title='Paramètres', type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1), on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text='SAUVEGARDER', md_bg_color=self.theme_cls.primary_color, on_release=self.save_ip)], size_hint=(0.9, None))
        self.dialog.open()

    def save_ip(self, x):
        local_ip = self.local_ip_field.text
        ext_ip = self.external_ip_field.text
        p_name = self.printer_name_field.text
        p_mac = getattr(self, 'temp_selected_mac', '')
        p_auto = self.chk_auto_print.active
        if DataValidator.validate_ip(local_ip):
            self.local_server_ip = local_ip
            self.external_server_ip = ext_ip
            self.active_server_ip = local_ip
            self.store.put('config', ip=self.local_server_ip, ext_ip=self.external_server_ip, seller_mode=self.is_seller_mode)
            self.store.put('printer_config', name=p_name, mac=p_mac, auto=p_auto)
            if self.dialog:
                self.dialog.dismiss()
            self.notify('Paramètres enregistrés', 'success')
            self.check_server_heartbeat(0)
        else:
            self.notify('Adresse IP Locale invalide', 'error')

    def open_seller_auth_dialog(self, x):
        if self.dialog:
            self.dialog.dismiss()
        has_pass = self.store.exists('seller_config')
        title = 'Mot de passe Admin' if has_pass else 'Créer Mot de Passe'
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=dp(80))
        self.seller_pass_field = MDTextField(hint_text='Code PIN/Password', password=True, halign='center')
        content.add_widget(self.seller_pass_field)
        self.auth_dialog = MDDialog(title=title, type='custom', content_cls=content, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.auth_dialog.dismiss()), MDRaisedButton(text='OK', on_release=lambda x: self.check_create_seller_pass(has_pass))])
        self.auth_dialog.open()

    def check_create_seller_pass(self, exists):
        pwd = self.seller_pass_field.text
        if not pwd:
            return
        if exists:
            if pwd == self.store.get('seller_config')['password']:
                self.auth_dialog.dismiss()
                self.open_seller_toggle_dialog()
            else:
                self.notify('Mot de passe incorrect', 'error')
        else:
            self.store.put('seller_config', password=pwd)
            self.auth_dialog.dismiss()
            self.open_seller_toggle_dialog()

    def open_seller_toggle_dialog(self):
        content = MDBoxLayout(orientation='horizontal', spacing=20, size_hint_y=None, height=dp(50), padding=[20, 0])
        content.add_widget(MDLabel(text='Mode Vendeur (Restreint)'))
        chk = MDCheckbox(active=self.is_seller_mode, size_hint=(None, None), size=(dp(48), dp(48)))
        chk.bind(active=self.on_seller_mode_switch)
        content.add_widget(chk)
        self.toggle_dialog = MDDialog(title='Configuration Mode', type='custom', content_cls=content, buttons=[MDFlatButton(text='FERMER', on_release=lambda x: self.toggle_dialog.dismiss())])
        self.toggle_dialog.open()

    def on_seller_mode_switch(self, instance, value):
        self.is_seller_mode = value
        self.store.put('config', ip=self.local_server_ip, ext_ip=self.external_server_ip, seller_mode=value)
        self.update_dashboard_layout()
        self.notify(f"Mode Vendeur: {('Activé' if value else 'Désactivé')}", 'info')

    def fetch_products(self):
        UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/products', on_success=self.on_products_loaded)

    def on_products_loaded(self, req, res):
        try:
            self.all_products_raw = res
            Clock.schedule_once(lambda dt: self.cache_store.put('products', data=res), 0.1)
            self.prepare_products_for_rv(res)
        except Exception as e:
            print(f'Error loading products: {e}')

    def fetch_entities(self, type_):
        UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/entities?type={type_}', on_success=lambda r, x: self.on_entities_loaded(type_, x))

    def on_entities_loaded(self, type_, data):
        key = 'clients' if type_ == 'account' else 'suppliers'
        if type_ == 'account':
            self.all_clients = data
        else:
            self.all_suppliers = data
        Clock.schedule_once(lambda dt: self.cache_store.put(key, data=data), 0.1)
        if hasattr(self, 'mgmt_dialog') and self.mgmt_dialog:
            try:
                if self.current_entity_type_mgmt == type_:
                    self.filter_entities_for_manager('')
            except:
                pass

    def load_products_from_cache(self):
        if self.cache_store.exists('products'):
            self.all_products_raw = self.cache_store.get('products')['data']
            self.prepare_products_for_rv(self.all_products_raw)

    def filter_entities(self, instance, text=None):
        query = instance.get_value() if hasattr(instance, 'get_value') else text
        if self._entity_search_event:
            self._entity_search_event.cancel()
        self._entity_search_event = Clock.schedule_once(lambda dt: self._start_entity_background_search(query), 0.3)

    def _start_entity_background_search(self, query):
        threading.Thread(target=self._entity_search_worker, args=(query,), daemon=True).start()

    def _entity_search_worker(self, query):
        if not query:
            self.populate_entity_list(self.entities_source[:50])
            return
        txt = query.lower()
        filtered = [e for e in self.entities_source if txt in str(e.get('name', '')).lower() or txt in str(e.get('phone', '')).lower()]
        if not filtered:
            try:
                fixed_query = self.fix_text(txt)
                filtered = [e for e in self.entities_source if fixed_query in self.fix_text(str(e.get('name', '')))]
            except Exception:
                pass
        if len(filtered) > 50:
            filtered = filtered[:50]
        self.populate_entity_list(filtered)

    @mainthread
    def populate_entity_list(self, entities, next_action=None):
        server_default_names = ['Comptoir', 'Fournisseur', 'زبون افتراضي', 'مورد افتراضي']

        def is_default(name):
            return str(name).strip() in server_default_names
        defaults = [e for e in entities if is_default(e.get('name', ''))]
        others = [e for e in entities if not is_default(e.get('name', ''))]
        others.sort(key=lambda x: x.get('name', '').lower())
        if self.current_mode in ['client_payment', 'supplier_payment']:
            final_list = others
        else:
            final_list = defaults + others
        rv_data = []
        is_client_mode = self.current_mode in ['sale', 'return_sale', 'client_payment', 'invoice_sale', 'proforma']
        bal_color_hex = '00C853' if is_client_mode else 'D50000'
        for e in final_list:
            raw_name = e.get('name', '')
            is_def_acc = is_default(raw_name)
            if is_def_acc:
                display_name = 'COMPTOIR'
                balance_markup = ''
                icon_name = 'store'
                icon_col = [0.2, 0.2, 0.2, 1]
            else:
                display_name = raw_name
                balance = float(e.get('balance', 0))
                bal_text = f'{balance:.2f} DA'
                balance_markup = f'Solde: [color={bal_color_hex}][b]{bal_text}[/b][/color]'
                if balance <= 0:
                    icon_name = 'account-check'
                    icon_col = [0, 0.7, 0, 1]
                else:
                    icon_name = 'account-alert'
                    icon_col = [0.9, 0, 0, 1]
            rv_data.append({'raw_name': display_name, 'balance_text': balance_markup, 'icon': icon_name, 'icon_color': icon_col, 'raw_data': e})
        if hasattr(self, 'rv_entity'):
            self.rv_entity.data = rv_data
            self.rv_entity.refresh_from_data()

    def open_mode(self, mode):
        self.current_mode = mode
        self.cart = []
        self.update_cart_button()
        self.selected_location = 'store'
        self.selected_entity = None  # تصفير الزبون المختار لإجبار المستخدم على الاختيار
        
        # إعداد العناوين
        titles = {
            'sale': 'Vente', 
            'purchase': 'Achat', 
            'return_sale': 'Retour Client', 
            'return_purchase': 'Retour Frns', 
            'transfer': 'Transfert', 
            'manage_products': 'Gestion Produits', 
            'invoice_sale': 'Facture Vente', 
            'invoice_purchase': 'Facture Achat', 
            'proforma': 'Facture Proforma', 
            'order_purchase': 'Bon de Commande'
        }
        self.prod_toolbar.title = titles.get(mode, 'Produits')
        
        # إعداد الألوان
        colors = {
            'sale': 'Green', 'purchase': 'Orange', 
            'return_sale': 'Red', 'return_purchase': 'Teal', 
            'transfer': 'Purple', 'manage_products': 'Blue', 
            'invoice_sale': 'Blue', 'invoice_purchase': 'DeepOrange', 
            'proforma': 'Purple', 'order_purchase': 'Teal'
        }
        self.theme_cls.primary_palette = colors.get(mode, 'Blue')
        
        # إعداد الأزرار العلوية
        self.prod_toolbar.right_action_items = []
        if mode == 'manage_products':
            if self.btn_add_prod not in self.prod_search_layout.children:
                self.prod_search_layout.add_widget(self.btn_add_prod)
            if self.cart_bar:
                self.cart_bar.height = 0
                self.cart_bar.size_hint_y = None
                self.cart_bar.opacity = 0
                self.cart_bar.disabled = True
        else:
            if self.btn_add_prod in self.prod_search_layout.children:
                self.prod_search_layout.remove_widget(self.btn_add_prod)
            if self.cart_bar:
                self.cart_bar.height = dp(60)
                self.cart_bar.size_hint_y = None
                self.cart_bar.opacity = 1
                self.cart_bar.disabled = False

        # دالة داخلية لتنفيذ الدخول للشاشة وتحميل المنتجات (تُستدعى بعد اختيار الزبون)
        def enter_products_screen():
            self.sm.current = 'products'
            if self.is_server_reachable:
                self.fetch_products()
                # جلب البيانات في الخلفية للتحديث المستقبلي
                if mode != 'transfer' and mode != 'manage_products':
                    entity_type = 'supplier' if mode in ['purchase', 'return_purchase', 'invoice_purchase', 'order_purchase'] else 'account'
                    self.fetch_entities(entity_type)
            else:
                self.load_products_from_cache()
                self.prepare_products_for_rv(self.all_products_raw)
            
            if self.search_field:
                self.search_field.text = ''

        # المنطق الجديد: التحقق مما إذا كان الوضع يتطلب اختيار طرف ثالث
        modes_requiring_entity = [
            'sale', 'purchase', 'return_sale', 'return_purchase', 
            'invoice_sale', 'invoice_purchase', 'proforma', 'order_purchase'
        ]

        if mode in modes_requiring_entity:
            # تحديد نوع الكيانات المطلوبة وتحديث القائمة قبل العرض إذا أمكن
            entity_type = 'supplier' if mode in ['purchase', 'return_purchase', 'invoice_purchase', 'order_purchase'] else 'account'
            if self.is_server_reachable:
                self.fetch_entities(entity_type) # تحديث القائمة في الخلفية
            
            # فتح نافذة الاختيار، وتمرير دالة الدخول كإجراء تالٍ (next_action)
            self.show_entity_selection_dialog(None, next_action=enter_products_screen)
        else:
            # في حالة التحويل (Transfer) أو إدارة المنتجات، ادخل مباشرة
            enter_products_screen()

    def open_add_to_cart_dialog(self, product, mode):
        if mode == 'manage_products':
            self.show_manage_product_dialog(product)
            return

        def fmt_num(value):
            if not value:
                return '0'
            try:
                val_float = float(value)
                if val_float.is_integer():
                    return str(int(val_float))
                return str(val_float)
            except:
                return str(value)
        is_transfer = mode == 'transfer'
        is_sale_context = mode in ['sale', 'return_sale', 'invoice_sale', 'proforma']
        curr_price = 0
        if is_sale_context:
            cat = ''
            if self.selected_entity:
                cat = str(self.selected_entity.get('category', ''))
            if cat in ['Gros', 'جملة']:
                curr_price = product.get('price_wholesale', 0)
            elif cat in ['Demi-Gros', 'نصف جملة']:
                curr_price = product.get('price_semi', 0)
            if float(curr_price or 0) == 0:
                curr_price = product.get('price', 0)
        else:
            curr_price = product.get('purchase_price', product.get('price', 0))
        prod_name = self.fix_text(product.get('name'))
        price_val_str = fmt_num(curr_price or 0)
        self.active_input_target = 'qty'
        header_box = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing='5dp', padding=[0, 0, 0, '5dp'])
        lbl_prod = MDLabel(text=prod_name, halign='center', bold=True, font_style='Subtitle1', theme_text_color='Primary', adaptive_height=True)
        header_box.add_widget(lbl_prod)
        dialog_height = dp(420) if is_transfer else dp(500)
        content = MDBoxLayout(orientation='vertical', spacing='8dp', size_hint_y=None, height=dialog_height, padding=[0, '5dp', 0, 0])
        content.add_widget(header_box)
        if not is_transfer:
            price_row = MDBoxLayout(orientation='horizontal', spacing='0dp', size_hint_y=None, height='70dp', padding=[70, 0, 70, 0])
            self.price_field = MDTextField(text=price_val_str, hint_text='Prix Unitaire (DA)', font_size='26sp', halign='center', mode='fill', readonly=True, line_color_normal=(0, 0, 0, 0))

            def on_price_focus(instance, value):
                if value:
                    self.active_input_target = 'price'
                    self.price_field.line_color_normal = (0, 0.7, 0, 1)
                    if hasattr(self, 'qty_field'):
                        self.qty_field.line_color_normal = (0, 0, 0, 0)
                    instance.focus = False
            self.price_field.bind(focus=on_price_focus)
            price_row.add_widget(self.price_field)
            content.add_widget(price_row)
        qty_row = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp', padding=[40, 0])
        btn_minus = MDIconButton(icon='minus', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.9, 0.3, 0.3, 1), pos_hint={'center_y': 0.5}, icon_size='20sp')
        self.qty_field = MDTextField(text='1', hint_text='Qté', font_size='28sp', halign='center', readonly=True, size_hint_x=1, pos_hint={'center_y': 0.5}, mode='line', line_color_focus=(0, 0, 0, 0), line_color_normal=(0, 0.7, 0, 1))
        self.qty_field.get_value = lambda: self.qty_field.text

        def on_qty_focus(instance, value):
            if value:
                self.active_input_target = 'qty'
                self.qty_field.line_color_normal = (0, 0.7, 0, 1)
                if not is_transfer and hasattr(self, 'price_field'):
                    self.price_field.line_color_normal = (0, 0, 0, 0)
                instance.focus = False
        self.qty_field.bind(focus=on_qty_focus)
        btn_plus = MDIconButton(icon='plus', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.2, 0.7, 0.2, 1), pos_hint={'center_y': 0.5}, icon_size='20sp')
        qty_row.add_widget(btn_minus)
        qty_row.add_widget(self.qty_field)
        qty_row.add_widget(btn_plus)
        content.add_widget(qty_row)
        self.btn_add = MDRaisedButton(text='AJOUTER', md_bg_color=(0, 0.7, 0, 1), text_color=(1, 1, 1, 1), size_hint_x=0.7, size_hint_y=1, font_size='18sp', elevation=3)
        temp_product = product.copy()
        if is_sale_context and (not is_transfer):
            temp_product['price'] = float(curr_price or 0)

        def perform_add(x):
            try:
                if not is_transfer and hasattr(self, 'price_field'):
                    p_val = float(self.price_field.text)
                    temp_product['price'] = p_val
                self.add_to_cart(temp_product)
                if self.dialog:
                    self.dialog.dismiss()
            except ValueError:
                self.notify('Valeurs invalides', 'error')
        self.btn_add.bind(on_release=perform_add)

        def update_button_text():
            if is_transfer:
                self.btn_add.text = 'AJOUTER'
                return
            try:
                q = float(self.qty_field.text)
            except:
                q = 1.0
            try:
                p = float(self.price_field.text)
            except:
                p = 0.0
            total_line = q * p
            self.btn_add.text = f'AJOUTER\n{total_line:.2f} DA'

        def increase(x):
            try:
                v = float(self.qty_field.text)
                self.qty_field.text = fmt_num(v + 1)
            except:
                self.qty_field.text = '1'
            update_button_text()

        def decrease(x):
            try:
                v = float(self.qty_field.text)
                if v > 1:
                    self.qty_field.text = fmt_num(v - 1)
            except:
                self.qty_field.text = '1'
            update_button_text()
        btn_plus.bind(on_release=increase)
        btn_minus.bind(on_release=decrease)

        def get_active_field():
            if is_transfer:
                return self.qty_field
            return self.price_field if self.active_input_target == 'price' else self.qty_field

        def add_digit(digit):
            field = get_active_field()
            current = field.text
            if digit == '.':
                if '.' not in current:
                    field.text = (current or '0') + '.'
            elif current == '0' or (self.active_input_target == 'qty' and current == '1' and (len(current) == 1)):
                field.text = str(digit)
            else:
                field.text = current + str(digit)
            update_button_text()

        def backspace(instance=None):
            field = get_active_field()
            current = field.text
            if len(current) > 0:
                field.text = current[:-1]
            if not field.text:
                field.text = '0' if self.active_input_target == 'price' and (not is_transfer) else '1'
            update_button_text()
        grid = MDGridLayout(cols=3, spacing='8dp', size_hint_y=1, padding=[20, 0])
        keys = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0', 'DEL']
        for key in keys:
            if key == 'DEL':
                btn = MDIconButton(icon='backspace-outline', theme_text_color='Custom', text_color=(0, 0, 0, 1), md_bg_color=(0.8, 0.8, 0.8, 1), size_hint=(1, 1), icon_size='20sp', on_release=backspace)
            else:
                btn = MDRaisedButton(text=key, md_bg_color=(0.95, 0.95, 0.95, 1), theme_text_color='Custom', text_color=(0, 0, 0, 1), font_size='22sp', size_hint=(1, 1), elevation=1, on_release=lambda x, k=key: add_digit(k))
            grid.add_widget(btn)
        content.add_widget(grid)
        content.add_widget(MDLabel(text='', size_hint_y=None, height='10dp'))
        buttons_box = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='60dp')
        btn_cancel = MDFlatButton(text='ANNULER', theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1), size_hint_x=0.3, on_release=lambda x: self.dialog.dismiss())
        buttons_box.add_widget(btn_cancel)
        buttons_box.add_widget(self.btn_add)
        content.add_widget(buttons_box)
        update_button_text()
        self.dialog = MDDialog(title='', type='custom', content_cls=content, buttons=[], size_hint=(0.85, None))
        self.dialog.open()

    def show_manage_product_dialog(self, product):
        if not self.is_server_reachable:
            self.dialog = MDDialog(title='Hors Ligne', text='Impossible de gérer les produits en mode hors ligne.\nVeuillez vous connecter au serveur.', buttons=[MDFlatButton(text='OK', on_release=lambda x: self.dialog.dismiss())])
            self.dialog.open()
            return
        is_edit = product is not None
        title = 'Fiche Produit'
        val_name = product.get('name', '') if is_edit else ''
        val_ref = product.get('ref', product.get('product_ref', '')) if is_edit else ''
        val_barcode = product.get('barcode', '') if is_edit else ''
        val_desc = product.get('description', '') if is_edit else ''
        is_used = product.get('is_used', False) if is_edit else False

        def fmt(v):
            try:
                return f'{float(v):.2f}'
            except:
                return ''
        raw_stock = float(product.get('stock', 0) or 0) if is_edit else 0
        is_unlimited = raw_stock <= -900000
        val_stock = '' if is_unlimited else str(int(raw_stock)) if raw_stock.is_integer() else str(raw_stock)
        val_cost = fmt(product.get('purchase_price', 0)) if is_edit else ''
        val_p1 = fmt(product.get('price', 0)) if is_edit else ''
        val_p2 = fmt(product.get('price_semi', 0)) if is_edit else ''
        val_p3 = fmt(product.get('price_wholesale', 0)) if is_edit else ''
        scroll = MDScrollView(size_hint_y=None, height=dp(500))
        box = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=dp(10), padding=[0, 10, 0, 0])
        box.add_widget(MDLabel(text='Identification', font_style='Caption', theme_text_color='Primary', bold=True))
        row_id = MDBoxLayout(orientation='horizontal', spacing=dp(10), adaptive_height=True)
        self.field_num = MDTextField(text=val_ref, hint_text='Num de Produit', size_hint_x=0.3)
        self.field_bar = MDTextField(text=val_barcode, hint_text='Code-barres', size_hint_x=0.55)
        btn_gen = MDIconButton(icon='barcode', on_release=lambda x: setattr(self.field_bar, 'text', '7' + ''.join([str(random.randint(0, 9)) for _ in range(12)])), size_hint_x=0.15)
        row_id.add_widget(self.field_num)
        row_id.add_widget(self.field_bar)
        row_id.add_widget(btn_gen)
        box.add_widget(row_id)
        self.field_name = SmartTextField(text=val_name, hint_text='Désignation (Nom)', required=True)
        self.field_desc = SmartTextField(text=val_desc, hint_text='Référence (Description)')
        box.add_widget(self.field_name)
        box.add_widget(self.field_desc)
        box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))
        box.add_widget(MDLabel(text='Stock', font_style='Caption', theme_text_color='Primary', bold=True))
        row_stock_opts = MDBoxLayout(orientation='horizontal', spacing=dp(10), adaptive_height=True)
        self.chk_unlimited = MDCheckbox(active=is_unlimited, size_hint=(None, None), size=(dp(40), dp(40)))
        if is_used:
            self.chk_unlimited.disabled = True
        lbl_unlimited = MDLabel(text='Quantité Illimitée', valign='center')
        row_stock_opts.add_widget(self.chk_unlimited)
        row_stock_opts.add_widget(lbl_unlimited)
        box.add_widget(row_stock_opts)
        self.field_stock = SmartTextField(text=val_stock, hint_text='Quantité Stock', input_filter='float')

        def on_checkbox_active(checkbox, value):
            if value:
                self.field_stock.disabled = True
                self.field_stock.text = ''
                self.field_stock.hint_text = 'Illimité'
            elif is_used:
                self.field_stock.disabled = True
                self.field_stock.helper_text = 'Verrouillé (Mouvement détecté)'
                self.field_stock.helper_text_mode = 'persistent'
            else:
                self.field_stock.disabled = False
                self.field_stock.text = val_stock
                self.field_stock.hint_text = 'Quantité Stock'
                self.field_stock.helper_text = ''
        self.chk_unlimited.bind(active=on_checkbox_active)
        on_checkbox_active(self.chk_unlimited, is_unlimited)
        box.add_widget(self.field_stock)
        box.add_widget(MDLabel(text="Coût d'Achat", font_style='Caption', theme_text_color='Primary', bold=True))
        self.field_cost = SmartTextField(text=val_cost, hint_text='Prix Achat', input_filter='float')
        if is_used:
            self.field_cost.disabled = True
            self.field_cost.helper_text = 'Verrouillé (Mouvement détecté)'
            self.field_cost.helper_text_mode = 'persistent'
        box.add_widget(self.field_cost)
        box.add_widget(MDBoxLayout(size_hint_y=None, height=dp(5)))
        box.add_widget(MDLabel(text='Tarification de Vente', font_style='Caption', theme_text_color='Primary', bold=True))
        self.field_p1 = SmartTextField(text=val_p1, hint_text='Prix Détail (Vente)', input_filter='float')
        box.add_widget(self.field_p1)
        self.field_p2 = SmartTextField(text=val_p2, hint_text='Prix Demi-Gros', input_filter='float')
        box.add_widget(self.field_p2)
        self.field_p3 = SmartTextField(text=val_p3, hint_text='Prix Gros', input_filter='float')
        box.add_widget(self.field_p3)
        scroll.add_widget(box)
        if not is_edit:

            def on_ref_success(req, res):
                if res and 'ref' in res:
                    self.field_num.text = res['ref']
            UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/get_next_ref', on_success=on_ref_success)

        def save_product(x):
            # التحقق من الاسم
            if not self.field_name.get_value().strip():
                self.field_name.error = True
                return
            
            # التحقق من الأرقام
            try:
                stock_val = -999999999999 if self.chk_unlimited.active else float(self.field_stock.get_value() or 0)
                cost_val = float(self.field_cost.get_value() or 0)
                p1_val = float(self.field_p1.get_value() or 0)
                p2_val = float(self.field_p2.get_value() or 0)
                p3_val = float(self.field_p3.get_value() or 0)
            except ValueError:
                self.notify('Valeurs numériques invalides', 'error')
                return
            
            # تجهيز البيانات
            payload = {
                'name': self.field_name.get_value().strip(),
                'product_ref': self.field_num.text.strip(),
                'barcode': self.field_bar.text.strip(),
                'description': self.field_desc.get_value().strip(),
                'stock': stock_val,
                'cost': cost_val,
                'price': p1_val,
                'price_semi': p2_val,
                'price_wholesale': p3_val,
                'category': '',
                'unit': '',
                'user_name': self.current_user_name
            }
            
            endpoint = '/api/update_product' if is_edit else '/api/add_product'
            if is_edit:
                payload['id'] = product['id']

            # دالة النجاح
            def on_save_ok(req, res):
                if self.dialog:
                    self.dialog.dismiss()
                if self.search_field:
                    self.search_field.text = ''
                self.fetch_products()
                self.notify(f"Produit {('Modifié' if is_edit else 'Ajouté')} avec succès", 'success')

            # --- التصحيح هنا: تم تغيير on_save_ok إلى on_success ---
            UrlRequest(
                f'http://{self.active_server_ip}:{DEFAULT_PORT}{endpoint}',
                req_body=json.dumps(payload),
                req_headers={'Content-Type': 'application/json'},
                method='POST',
                on_success=on_save_ok,  # <--- التصحيح
                on_failure=lambda r, e: self.notify('Erreur serveur', 'error'),
                on_error=lambda r, e: self.notify('Erreur connexion', 'error')
            )

        def delete_product_flow(x):
            if is_used:
                self.notify('Impossible: Produit utilisé', 'error')
                return

            def confirm(y):
                if self.conf_diag:
                    self.conf_diag.dismiss()

                def on_del_ok(req, res):
                    if self.dialog:
                        self.dialog.dismiss()
                    if self.search_field:
                        self.search_field.text = ''
                    self.fetch_products()
                    self.notify('Produit supprimé', 'success')
                UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/delete_product', req_body=json.dumps({'id': product['id']}), req_headers={'Content-Type': 'application/json'}, method='POST', on_success=on_del_ok, on_failure=lambda r, e: self.notify('Erreur suppression', 'error'))
            name_disp = self.fix_text(val_name)
            self.conf_diag = MDDialog(title='Confirmation', text=f'Supprimer {name_disp} ?', buttons=[MDFlatButton(text='NON', on_release=lambda z: self.conf_diag.dismiss()), MDRaisedButton(text='OUI', md_bg_color=(1, 0, 0, 1), on_release=confirm)])
            self.conf_diag.open()
        btns = [MDFlatButton(text='FERMER', on_release=lambda x: self.dialog.dismiss())]
        if is_edit:
            btns.append(MDFlatButton(text='SUPPRIMER', theme_text_color='Error', on_release=delete_product_flow))
        btns.append(MDRaisedButton(text='ENREGISTRER', on_release=save_product))
        self.dialog = MDDialog(title=title, type='custom', content_cls=scroll, buttons=btns)
        self.dialog.open()

    def add_to_cart(self, product):
        try:
            if hasattr(self.qty_field, 'get_value'):
                qty = float(self.qty_field.get_value())
            else:
                qty = float(self.qty_field.text)
            if qty <= 0:
                raise ValueError
        except:
            self.notify('Quantité invalide', 'error')
            return
        try:
            final_price = float(product.get('price', 0))
        except:
            final_price = 0.0
        found = False
        for item in self.cart:
            if item['id'] == product['id']:
                item['qty'] += qty
                item['price'] = final_price
                found = True
                break
        if not found:
            self.cart.append({'id': product['id'], 'name': product['name'], 'price': final_price, 'qty': qty})
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()
        self.update_cart_button()
        self.notify('Ajouté au panier', 'success')
        if hasattr(self, 'search_field') and self.search_field:
            self.search_field.text = ''
            self.filter_products(None, '')
            Clock.schedule_once(lambda x: setattr(self.search_field, 'focus', True), 0.2)

    def update_cart_button(self):
        try:
            count = len(self.cart)
            total = sum((float(item['price'] or 0) * float(item['qty'] or 0) for item in self.cart))
            if self.lbl_cart_count:
                self.lbl_cart_count.text = f'PANIER ({count})'
            if self.current_mode == 'transfer':
                if self.lbl_cart_total:
                    self.lbl_cart_total.text = ''
            elif self.lbl_cart_total:
                self.lbl_cart_total.text = f'{total:.2f} DA'
        except:
            pass

    def remove_from_cart(self, item):
        if item in self.cart:
            self.cart.remove(item)
        self.refresh_cart_screen_items()
        self.update_cart_button()

    def start_payment_flow(self, mode):
        self.current_mode = mode
        entity_type = 'account' if mode == 'client_payment' else 'supplier'
        self.theme_cls.primary_palette = 'Teal' if mode == 'client_payment' else 'Brown'
        if self.is_server_reachable:
            self.fetch_entities(entity_type)
        else:
            key = 'clients' if entity_type == 'account' else 'suppliers'
            if self.cache_store.exists(key):
                if entity_type == 'account':
                    self.all_clients = self.cache_store.get('clients')['data']
                else:
                    self.all_suppliers = self.cache_store.get(key)['data']
        self.show_entity_selection_dialog(None, next_action=self.show_simple_payment_dialog)

    def show_simple_payment_dialog(self, amount=None):
        if not self.selected_entity:
            return
        if self.current_mode == 'client_payment':
            title = 'Versement Client'
            theme_col = (0, 0.6, 0, 1)
        else:
            title = 'Règlement Fournisseur'
            theme_col = (0.8, 0.4, 0, 1)
        content = MDBoxLayout(orientation='vertical', spacing='12dp', size_hint_y=None, height=dp(540), padding=[0, '10dp', 0, 0])
        header_box = MDBoxLayout(orientation='vertical', adaptive_height=True, padding=[0, 0, 0, '5dp'])
        ent_name = self.fix_text(self.selected_entity['name'])
        header_box.add_widget(MDLabel(text=ent_name, halign='center', font_style='H5', bold=True, theme_text_color='Primary', shorten=True, shorten_from='right'))
        content.add_widget(header_box)

        def backspace(x=None):
            current = self.txt_simple_amount.text
            if current:
                self.txt_simple_amount.text = current[:-1]
            if not self.txt_simple_amount.text:
                self.txt_simple_amount.text = ''

        def add_digit(digit):
            current = self.txt_simple_amount.text
            if digit == '.':
                if '.' in current:
                    return
                if not current:
                    self.txt_simple_amount.text = '0.'
                else:
                    self.txt_simple_amount.text = current + '.'
            elif digit == '-':
                if current.startswith('-'):
                    self.txt_simple_amount.text = current[1:]
                else:
                    self.txt_simple_amount.text = '-' + current
            elif current == '0':
                self.txt_simple_amount.text = str(digit)
            elif current == '-0':
                self.txt_simple_amount.text = '-' + str(digit)
            else:
                self.txt_simple_amount.text = current + str(digit)
        input_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(90), spacing='10dp', padding=[dp(20), 0])
        val = str(amount) if amount else ''
        self.txt_simple_amount = MDTextField(text=val, hint_text='Montant (DA)', font_size='44sp', halign='center', readonly=True, mode='fill', line_color_focus=theme_col, size_hint_x=0.8)
        self.txt_simple_amount.get_value = lambda: self.txt_simple_amount.text
        btn_del = MDIconButton(icon='backspace-outline', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.9, 0.1, 0.1, 1), size_hint=(0.2, 1), icon_size='32sp', on_release=backspace)
        input_row.add_widget(self.txt_simple_amount)
        input_row.add_widget(btn_del)
        content.add_widget(input_row)
        grid = MDGridLayout(cols=3, spacing='10dp', size_hint_y=1, padding=[dp(20), dp(10)])
        keys = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '-', '0', '.']
        for key in keys:
            btn = MDRaisedButton(text=key, md_bg_color=(0.96, 0.96, 0.96, 1), theme_text_color='Custom', text_color=(0.1, 0.1, 0.1, 1), font_size='28sp', elevation=1, size_hint=(1, 1), on_release=lambda x, k=key: add_digit(k))
            if key == '-':
                btn.font_size = '38sp'
                btn.text_color = (0, 0, 0, 1)
            grid.add_widget(btn)
        content.add_widget(grid)
        buttons_box = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='70dp', padding=[0, '10dp', 0, 0])
        btn_cancel = MDFlatButton(text='ANNULER', theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1), size_hint_x=0.25, on_release=lambda x: self.simple_pay_dialog.dismiss())
        btn_valid = MDRaisedButton(text='VALIDER', md_bg_color=theme_col, text_color=(1, 1, 1, 1), size_hint_x=0.75, size_hint_y=1, font_size='22sp', elevation=3, on_release=self.submit_simple_payment)
        buttons_box.add_widget(btn_cancel)
        buttons_box.add_widget(btn_valid)
        content.add_widget(buttons_box)
        self.simple_pay_dialog = MDDialog(title=title, type='custom', content_cls=content, size_hint=(0.92, None), buttons=[])
        self.simple_pay_dialog.open()

    def save_to_history(self, data, synced=False):
        if not synced:
            self.notify('Sauvegarde locale...', 'warning')
        key_name = None
        if self.editing_transaction_key:
            if self.editing_transaction_key != 'SERVER_EDIT_MODE':
                key_name = self.editing_transaction_key
                try:
                    if self.offline_store.exists(key_name):
                        old_item = self.offline_store.get(key_name)
                        old_data = old_item.get('order_data', {})
                        if old_data.get('entity_id'):
                            reversal_amount = 0
                            if old_data.get('is_simple_payment'):
                                reversal_amount = float(old_data.get('amount', 0))
                            else:
                                pass
                            if reversal_amount != 0:
                                self.update_local_entity_balance(old_data['entity_id'], -reversal_amount)
                except Exception as e:
                    print(f'History update error: {e}')
        if not key_name:
            timestamp_sec = int(time.time())
            unique_id = random.randint(1000, 9999)
            if data.get('is_simple_payment'):
                key_name = f'{timestamp_sec}_{unique_id}_PAY'
            else:
                doc_type = data.get('doc_type', 'BV')
                key_name = f'{timestamp_sec}_{unique_id}_{doc_type}'
        self.offline_store.put(key_name, order_data=data, synced=synced, sync_timestamp=time.time() if synced else 0)
        self.editing_transaction_key = None
        if not synced:
            try:
                if data.get('is_simple_payment') and data.get('entity_id'):
                    pass
            except:
                pass
            self._reset_notification_state(0)
            if self.pending_dialog:
                target_date = getattr(self, 'history_view_date', datetime.now().date())
                self.filter_history_list(specific_date=target_date)

    def toggle_location(self, x=None):
        self.selected_location = 'warehouse' if self.selected_location == 'store' else 'store'
        self.update_location_display()
        if self.current_mode == 'transfer' and hasattr(self, 'btn_ent_screen'):
            src = 'Magasin' if self.selected_location == 'store' else 'Dépôt'
            dst = 'Dépôt' if self.selected_location == 'store' else 'Magasin'
            self.btn_ent_screen.text = f'{src}  >>>  {dst}'

    def update_location_display(self):
        if hasattr(self, 'btn_loc_screen'):
            if self.selected_location == 'store':
                self.btn_loc_screen.text = 'Magasin'
                self.btn_loc_screen.md_bg_color = self.theme_cls.primary_color
            else:
                self.btn_loc_screen.text = 'Dépôt'
                self.btn_loc_screen.md_bg_color = (0.8, 0.4, 0, 1)

    def show_entity_selection_dialog(self, x, next_action=None):
        self.pending_entity_next_action = next_action
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(600))
        self.entity_search = SmartTextField(hint_text='Rechercher...', icon_right='magnify')
        self.entity_search.bind(text=self.filter_entities)
        content.add_widget(self.entity_search)
        self.rv_entity = EntityRecycleView()
        content.add_widget(self.rv_entity)
        if self.current_mode in ['sale', 'return_sale', 'client_payment', 'invoice_sale', 'proforma']:
            self.entities_source = self.all_clients
            title_text = 'Choisir un Client'
        else:
            self.entities_source = self.all_suppliers
            title_text = 'Choisir un Fournisseur'
        self.populate_entity_list(self.entities_source)
        self.entity_dialog = MDDialog(title=title_text, type='custom', content_cls=content, size_hint=(0.9, 0.8))
        self.entity_dialog.open()

    def recalculate_cart_prices(self):
        if not self.cart or not self.selected_entity:
            return
        cat = str(self.selected_entity.get('category', ''))
        price_key = 'price'
        if cat in ['Gros', 'جملة']:
            price_key = 'price_wholesale'
        elif cat in ['Demi-Gros', 'نصف جملة']:
            price_key = 'price_semi'
        for item in self.cart:
            original_product = next((p for p in self.all_products_raw if p['id'] == item['id']), None)
            if original_product:
                new_price = float(original_product.get(price_key, 0))
                if new_price == 0:
                    new_price = float(original_product.get('price', 0))
                item['price'] = new_price
        self.update_cart_button()
        self.notify('Prix mis à jour selon le client', 'info')

    def open_payment_dialog(self, x):
        current_time = time.time()
        if current_time - getattr(self, '_last_click_time', 0) < 1.0:
            return
        self._last_click_time = current_time
        if getattr(self, 'is_transaction_in_progress', False):
            return
        if not self.cart:
            return
        try:
            total = sum((float(i.get('price', 0)) * float(i.get('qty', 0)) for i in self.cart))
        except:
            total = 0
        saved_amount = 0
        if hasattr(self, 'editing_payment_amount') and self.editing_payment_amount is not None:
            saved_amount = self.editing_payment_amount
        try:
            default_val = f'{float(saved_amount):.2f}'
        except:
            default_val = '0.00'
        auto_pay_names = ['COMPTOIR', 'Comptoir', 'زبون افتراضي', 'مورد افتراضي', 'DEFAULT_CUSTOMER']
        current_name = self.selected_entity.get('name', '') if self.selected_entity else ''
        is_comptoir = False
        if current_name:
            is_comptoir = any((name.upper() == current_name.upper() for name in auto_pay_names))
        is_no_payment_doc = self.current_mode in ['proforma', 'order_purchase']
        should_skip = False
        if self.current_mode == 'transfer':
            should_skip = True
        elif is_no_payment_doc:
            should_skip = True
        elif is_comptoir:
            should_skip = True
        if should_skip:
            payment_val = 0 if is_no_payment_doc else total
            self.process_transaction(paid_amount=payment_val, total_amount=total)
            return
        content = MDBoxLayout(orientation='vertical', spacing='10dp', size_hint_y=None, height=dp(550), padding='10dp')
        total_card = MDCard(orientation='vertical', size_hint_y=None, height=dp(60), radius=[10], md_bg_color=(0.95, 0.95, 0.95, 1), elevation=1, padding='5dp')
        total_lbl_title = MDLabel(text='TOTAL À PAYER', halign='center', font_style='Caption', theme_text_color='Secondary')
        total_lbl_val = MDLabel(text=f'{total:.2f} DA', halign='center', font_style='H5', bold=True, theme_text_color='Primary')
        total_card.add_widget(total_lbl_title)
        total_card.add_widget(total_lbl_val)
        content.add_widget(total_card)
        self.txt_paid = MDTextField(text=default_val, hint_text='Montant Versé (DA)', font_size='36sp', halign='center', readonly=True, size_hint_y=None, height=dp(80), mode='fill', line_color_focus=(0, 0, 0, 0))
        self.txt_paid.get_value = lambda: self.txt_paid.text
        content.add_widget(self.txt_paid)
        self.lbl_rest = MDLabel(text='', halign='center', theme_text_color='Custom', font_style='H6', bold=True, size_hint_y=None, height=dp(30))
        content.add_widget(self.lbl_rest)

        def update_rest_logic():
            try:
                val_str = self.txt_paid.text
                paid = float(val_str) if val_str else 0
            except:
                paid = 0
            d = total - paid
            if d >= 0:
                self.lbl_rest.text = f'RESTE: {d:.2f} DA'
                self.lbl_rest.text_color = (0.8, 0, 0, 1)
            else:
                self.lbl_rest.text = f'RENDU: {abs(d):.2f} DA'
                self.lbl_rest.text_color = (0, 0.6, 0, 1)
        update_rest_logic()

        def add_digit(digit):
            current = self.txt_paid.text
            if digit == '.':
                if '.' in current:
                    return
                if not current:
                    self.txt_paid.text = '0.'
                else:
                    self.txt_paid.text = current + '.'
            elif current == '0' or current == '0.00':
                self.txt_paid.text = str(digit)
            else:
                self.txt_paid.text = current + str(digit)
            update_rest_logic()

        def backspace(instance=None):
            current = self.txt_paid.text
            if len(current) > 0:
                self.txt_paid.text = current[:-1]
            if not self.txt_paid.text:
                self.txt_paid.text = '0'
            update_rest_logic()
        grid = MDGridLayout(cols=3, spacing='10dp', size_hint_y=1)
        keys = ['7', '8', '9', '4', '5', '6', '1', '2', '3', '.', '0', 'DEL']
        for key in keys:
            if key == 'DEL':
                btn = MDIconButton(icon='backspace', theme_text_color='Custom', text_color=(1, 1, 1, 1), md_bg_color=(0.4, 0.4, 0.4, 1), size_hint=(1, 1), icon_size='24sp', on_release=backspace)
                grid.add_widget(btn)
            else:
                btn = MDRaisedButton(text=key, md_bg_color=(1, 1, 1, 1), theme_text_color='Custom', text_color=(0, 0, 0, 1), font_size='24sp', size_hint=(1, 1), elevation=1, on_release=lambda x, k=key: add_digit(k))
                grid.add_widget(btn)
        content.add_widget(grid)
        content.add_widget(MDLabel(text='', size_hint_y=1))
        buttons_box = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='65dp')
        btn_cancel = MDFlatButton(text='ANNULER', theme_text_color='Custom', text_color=(0.5, 0.5, 0.5, 1), size_hint_x=0.3, on_release=lambda x: self.pay_dialog.dismiss())
        btn_valid = MDRaisedButton(text='VALIDER', md_bg_color=(0, 0.7, 0, 1), text_color=(1, 1, 1, 1), size_hint_x=0.7, size_hint_y=1, font_size='22sp', elevation=3, on_release=lambda x: self.finalize_submission(total))
        buttons_box.add_widget(btn_cancel)
        buttons_box.add_widget(btn_valid)
        content.add_widget(buttons_box)
        self.pay_dialog = MDDialog(title='Paiement', type='custom', content_cls=content, buttons=[], size_hint=(0.94, 0.98))
        self.pay_dialog.open()

    def finalize_submission(self, total_amount):
        current_time = time.time()
        if current_time - getattr(self, '_last_click_time', 0) < 1.0:
            return
        self._last_click_time = current_time
        if getattr(self, 'is_transaction_in_progress', False):
            return
        if self.pay_dialog:
            self.pay_dialog.dismiss()
        if self.current_mode == 'transfer':
            paid_amount = 0
        else:
            try:
                paid_amount = float(self.txt_paid.get_value()) if self.txt_paid.get_value() else 0
            except:
                paid_amount = 0
            if paid_amount < total_amount:
                remaining = total_amount - paid_amount
                self.show_credit_warning(paid_amount, total_amount, remaining)
                return
            if paid_amount > total_amount and self.current_mode not in ['return_sale', 'return_purchase']:
                excess = paid_amount - total_amount
                self.show_overpayment_dialog(paid_amount, total_amount, excess)
                return
        self.process_transaction(paid_amount, total_amount)

    def show_overpayment_dialog(self, paid, total, excess):
        if self.current_mode in ['return_sale', 'return_purchase']:
            msg = f"Vous rendez {paid:.2f} DA pour un retour de {total:.2f} DA.\nL'excédent ({excess:.2f} DA) sera déduit du solde."
        else:
            msg = f"Montant saisi: {paid:.2f} DA\nTotal Facture: {total:.2f} DA\n\nL'excédent ({excess:.2f} DA) sera enregistré comme une opération séparée (VERSEMENT/RÈGLEMENT)."
        self.overpay_dialog = MDDialog(title="Création d'un Versement", text=msg, buttons=[MDFlatButton(text='CORRIGER', on_release=lambda x: [self.overpay_dialog.dismiss(), self.open_payment_dialog(None)]), MDRaisedButton(text='CONFIRMER', md_bg_color=(0, 0.6, 0, 1), on_release=lambda x: [self.overpay_dialog.dismiss(), self.process_transaction(paid, total)])])
        self.overpay_dialog.open()

    def show_credit_warning(self, paid, total, remaining):
        if self.current_mode in ['return_sale', 'return_purchase']:
            msg = f'Vous rendez {paid:.2f} DA.\nLe reste ({remaining:.2f} DA) sera déduit de la dette du tiers.'
        else:
            msg = f'Le montant versé ({paid:.2f} DA) est inférieur au total ({total:.2f} DA).\nLe reste ({remaining:.2f} DA) sera enregistré comme dette sur le compte.'
        self.debt_dialog = MDDialog(title='Attention: Crédit', text=msg, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.debt_dialog.dismiss()), MDRaisedButton(text='CONFIRMER', md_bg_color=(0.8, 0, 0, 1), on_release=lambda x: [self.debt_dialog.dismiss(), self.process_transaction(paid, total)])])
        self.debt_dialog.open()

    def process_transaction(self, paid_amount, total_amount):
        if getattr(self, 'is_transaction_in_progress', False):
            return
        self.is_transaction_in_progress = True
        try:
            excess_amount = 0
            invoice_paid_amount = paid_amount
            is_real_transaction = self.current_mode not in ['proforma', 'order_purchase', 'transfer']
            if is_real_transaction and self.current_mode in ['sale', 'purchase', 'invoice_sale', 'invoice_purchase'] and (paid_amount > total_amount):
                excess_amount = paid_amount - total_amount
                invoice_paid_amount = total_amount
            if is_real_transaction:
                if self.current_mode in ['sale', 'invoice_sale']:
                    self.stat_sales_today += invoice_paid_amount
                elif self.current_mode == 'return_sale':
                    self.stat_sales_today -= invoice_paid_amount
                elif self.current_mode in ['purchase', 'invoice_purchase']:
                    self.stat_purchases_today += invoice_paid_amount
                elif self.current_mode == 'return_purchase':
                    self.stat_purchases_today -= invoice_paid_amount
                self.calculate_net_total()
                self.save_local_stats()
            doc_type_map = {'sale': 'BV', 'purchase': 'BA', 'return_sale': 'RC', 'return_purchase': 'RF', 'transfer': 'TR', 'invoice_sale': 'FC', 'invoice_purchase': 'FF', 'proforma': 'FP', 'order_purchase': 'DP'}
            doc_type = doc_type_map.get(self.current_mode, 'BV')
            if hasattr(self, 'original_doc_type') and self.original_doc_type == 'BI' and (self.current_mode == 'purchase'):
                doc_type = 'BI'
            ent_id = self.selected_entity['id'] if self.selected_entity else None
            payment_info = {'amount': invoice_paid_amount, 'total': total_amount}
            server_id_to_update = None
            if self.editing_transaction_key:
                if self.editing_transaction_key == 'SERVER_EDIT_MODE':
                    server_id_to_update = self.current_editing_server_id
                elif self.offline_store.exists(self.editing_transaction_key):
                    old_item = self.offline_store.get(self.editing_transaction_key)
                    if old_item.get('synced') and old_item.get('order_data', {}).get('server_id'):
                        server_id_to_update = old_item['order_data']['server_id']
            final_timestamp = str(datetime.now())
            if server_id_to_update and hasattr(self, 'current_editing_date') and self.current_editing_date:
                final_timestamp = self.current_editing_date
            try:
                if '.' in final_timestamp:
                    final_timestamp = final_timestamp.split('.')[0]
            except:
                pass
            data = {'doc_type': doc_type, 'items': self.cart, 'user_name': self.current_user_name, 'timestamp': final_timestamp, 'purchase_location': self.selected_location, 'entity_id': ent_id, 'payment_info': payment_info, 'server_id': server_id_to_update}
            self.current_editing_server_id = None
            self.editing_payment_amount = None
            self.current_editing_date = None
            if hasattr(self, 'original_doc_type'):
                del self.original_doc_type

            def finalize_process(req=None, res=None):
                self.is_transaction_in_progress = False
                try:
                    printable_modes = ['sale', 'invoice_sale', 'return_sale', 'purchase', 'invoice_purchase', 'return_purchase', 'order_purchase', 'proforma', 'transfer']
                    if self.current_mode in printable_modes:
                        if self.store.exists('printer_config'):
                            conf = self.store.get('printer_config')
                            if conf.get('auto', False) and conf.get('mac', ''):
                                threading.Thread(target=self.print_ticket_bluetooth, args=(data,), daemon=True).start()
                except Exception as e:
                    print(f'Auto print error: {e}')
                self.on_submit_success_ui()

            def on_fail(req, err):
                self.is_transaction_in_progress = False
                self.save_offline_and_ui(data)

            def send_excess():
                if excess_amount <= 0:
                    finalize_process()
                    return
                p_type = 'client_pay' if self.current_mode in ['sale', 'invoice_sale'] else 'supplier_pay'
                c_label = 'Versement' if self.current_mode in ['sale', 'invoice_sale'] else 'Règlement'
                if p_type == 'client_pay':
                    self.stat_client_payments += excess_amount
                else:
                    self.stat_supplier_payments += excess_amount
                self.save_local_stats()
                pay_data = {'entity_id': ent_id, 'amount': excess_amount, 'type': p_type, 'custom_label': c_label, 'user_name': self.current_user_name, 'note': 'Automatique', 'is_simple_payment': True, 'timestamp': str(datetime.now()), 'server_id': None}
                UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/submit_payment', req_body=json.dumps(pay_data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, s: [self.notify(f'Reste ({excess_amount:.2f}) enregistré', 'success'), finalize_process()], on_failure=lambda r, e: finalize_process(), timeout=10)
            if self.is_server_reachable:

                def on_invoice_success(req, res):
                    if res.get('server_id'):
                        data['server_id'] = res.get('server_id')
                    if res.get('invoice_number'):
                        data['invoice_number'] = res.get('invoice_number')
                    self.save_to_history(data, synced=True)
                    if excess_amount > 0:
                        send_excess()
                    else:
                        finalize_process()
                UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/submit_order', req_body=json.dumps(data), req_headers={'Content-type': 'application/json'}, method='POST', on_success=on_invoice_success, on_error=on_fail, on_failure=on_fail, timeout=10)
            else:
                if excess_amount > 0:
                    p_type = 'client_pay' if self.current_mode in ['sale', 'invoice_sale'] else 'supplier_pay'
                    local_label = 'Versement' if self.current_mode in ['sale', 'invoice_sale'] else 'Règlement'
                    pay_data = {'entity_id': ent_id, 'amount': excess_amount, 'type': p_type, 'custom_label': local_label, 'user_name': self.current_user_name, 'is_simple_payment': True, 'timestamp': str(datetime.now())}
                    self.save_to_history(pay_data, synced=False)
                self.is_transaction_in_progress = False
                self.save_offline_and_ui(data)
        except Exception as e:
            self.is_transaction_in_progress = False
            self.notify(f'Erreur process: {e}', 'error')

    def on_submit_success_ui(self):
        self.notify('Succès ✅', 'success')
        self.cart = []
        self.selected_entity = None
        self.selected_location = 'store'
        self.update_cart_button()
        self.go_back()

    def save_offline_and_ui(self, data):
        self.save_to_history(data, synced=False)
        try:
            printable_modes = ['sale', 'invoice_sale', 'return_sale', 'purchase', 'invoice_purchase', 'return_purchase', 'order_purchase', 'proforma', 'transfer']
            if self.current_mode in printable_modes:
                if self.store.exists('printer_config'):
                    conf = self.store.get('printer_config')
                    if conf.get('auto', False) and conf.get('mac', ''):
                        threading.Thread(target=self.print_ticket_bluetooth, args=(data,), daemon=True).start()
        except Exception as e:
            print(f'Offline Print Error: {e}')
        try:
            doc_type = data.get('doc_type', 'BV')
            if doc_type not in ['TR', 'FP', 'DP', 'BI'] and data.get('entity_id'):
                total_amount = sum((float(i.get('price', 0)) * float(i.get('qty', 0)) for i in data.get('items', [])))
                balance_sign = -1 if doc_type in ['RC', 'RF'] else 1
                payment_info = data.get('payment_info', {})
                paid_amount = float(payment_info.get('amount', 0))
                net_change = total_amount * balance_sign - paid_amount
                self.update_local_entity_balance(data['entity_id'], net_change)
        except Exception as e:
            print(f'Error calculating offline balance update: {e}')
        self.cart = []
        self.selected_entity = None
        self.selected_location = 'store'
        self.update_cart_button()
        self.go_back()

    def show_pending_dialog(self):
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(550))
        tabs_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=5)
        self.btn_hist_today = MDRaisedButton(text='AUJ.', size_hint_x=0.33, elevation=0, on_release=lambda x: self.filter_history_list(day_offset=0))
        self.btn_hist_yesterday = MDRaisedButton(text='HIER', size_hint_x=0.33, elevation=0, md_bg_color=(0.5, 0.5, 0.5, 1), on_release=lambda x: self.filter_history_list(day_offset=1))
        self.btn_hist_date = MDRaisedButton(text='CALENDRIER', size_hint_x=0.33, elevation=0, md_bg_color=(0.5, 0.5, 0.5, 1), on_release=self.open_history_date_picker)
        tabs_box.add_widget(self.btn_hist_today)
        tabs_box.add_widget(self.btn_hist_yesterday)
        tabs_box.add_widget(self.btn_hist_date)
        content.add_widget(tabs_box)
        self.rv_history = HistoryRecycleView()
        content.add_widget(self.rv_history)
        self.pending_dialog = MDDialog(title='Historique', type='custom', content_cls=content, size_hint=(0.98, 0.98))
        self.pending_dialog.open()
        self.filter_history_list(day_offset=0)

    def filter_history_list(self, day_offset=None, specific_date=None):
        inactive_color = (0.5, 0.5, 0.5, 1)
        active_color = self.theme_cls.primary_color
        target_date = None
        if specific_date:
            target_date = specific_date
            self.btn_hist_today.md_bg_color = inactive_color
            self.btn_hist_yesterday.md_bg_color = inactive_color
            self.btn_hist_date.md_bg_color = active_color
        else:
            if day_offset is None:
                day_offset = 0
            target_date = datetime.now().date() - timedelta(days=day_offset)
            self.btn_hist_today.md_bg_color = active_color if day_offset == 0 else inactive_color
            self.btn_hist_yesterday.md_bg_color = active_color if day_offset == 1 else inactive_color
            self.btn_hist_date.md_bg_color = inactive_color
            self.btn_hist_date.text = 'CALENDRIER'
        self.history_view_date = target_date
        self.history_rv_data = []
        keys = list(self.offline_store.keys())
        local_items = []
        for k in keys:
            try:
                item_store = self.offline_store.get(k)
                if item_store.get('synced', False):
                    continue
                parts = k.split('_')
                if parts[0].isdigit():
                    ts_val = int(parts[0])
                    item_date = datetime.fromtimestamp(ts_val).date()
                    if item_date == target_date:
                        local_items.append((ts_val, k, item_store))
            except:
                continue
        local_items.sort(key=lambda x: x[0], reverse=True)
        for ts_val, k, item_store in local_items:
            data = item_store['order_data']
            doc_type = data.get('doc_type', 'BV')
            is_simple_payment = data.get('is_simple_payment', False)
            dt_str = datetime.fromtimestamp(ts_val).strftime('%H:%M')
            entity_name = 'Inconnu'
            ent_id = data.get('entity_id')
            if ent_id:
                found = next((c for c in self.all_clients if c['id'] == ent_id), None)
                if not found:
                    found = next((s for s in self.all_suppliers if s['id'] == ent_id), None)
                if found:
                    entity_name = found.get('name', 'Tiers')
            else:
                entity_name = 'COMPTOIR'
            amount = 0
            if is_simple_payment:
                amount = float(data.get('amount', 0))
            else:
                try:
                    amount = sum((float(i['price']) * float(i['qty']) for i in data.get('items', [])))
                except:
                    amount = 0
            full_doc_name = ''
            icon_name = 'file-document'
            icon_color = (0, 0.5, 0.8, 1)
            bg_col = (1, 1, 1, 1)
            amount_text = f'{amount:.2f} DA'
            if doc_type == 'TR':
                full_doc_name = 'Transfert Stock'
                icon_name = 'compare-horizontal'
                bg_col = (0.95, 0.9, 1, 1)
                icon_color = (0.5, 0, 0.5, 1)
                amount_text = 'Stock'
            elif is_simple_payment:
                p_type = data.get('type', 'client_pay')
                if amount >= 0:
                    full_doc_name = 'Règlement' if p_type == 'supplier_pay' else 'Versement'
                    icon_name = 'cash-plus'
                    icon_color = (0, 0.7, 0, 1)
                    amount_text = f'+ {abs(amount):.2f} DA'
                else:
                    full_doc_name = 'Crédit'
                    icon_name = 'notebook-edit'
                    icon_color = (0.8, 0, 0, 1)
                    amount_text = f'- {abs(amount):.2f} DA'
            else:
                full_doc_name = self.DOC_TRANSLATIONS.get(doc_type, doc_type)
                if doc_type == 'RC':
                    icon_color = (0.8, 0, 0, 1)
            header_text = f'{full_doc_name} - {entity_name}'
            self.history_rv_data.append({'raw_text': header_text, 'raw_sec': f'Local • {dt_str} • (Non Sync)', 'amount_text': amount_text, 'icon': icon_name, 'icon_color': icon_color, 'bg_color': bg_col, 'is_local': True, 'key': k, 'raw_data': None})
        self.rv_history.data = self.history_rv_data
        if self.is_server_reachable:
            url = f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/history?date={target_date}'
            UrlRequest(url, on_success=self.on_history_server_loaded)

    def on_history_server_loaded(self, req, result):
        if not result:
            if not any((item['is_local'] for item in self.history_rv_data)):
                self.history_rv_data.append({'raw_text': 'Aucune opération serveur.', 'raw_sec': '', 'amount_text': '', 'icon': 'alert-circle-outline', 'icon_color': (0.5, 0.5, 0.5, 1), 'bg_color': (1, 1, 1, 1), 'is_local': False, 'key': '', 'raw_data': None})
                self.rv_history.data = self.history_rv_data
            return
        main_doc_prefixes = ['BV', 'BA', 'RC', 'RF', 'TR', 'FP', 'DP', 'BI', 'FC', 'FF']
        default_names = ['زبون افتراضي', 'مورد افتراضي', 'DEFAULT_CUSTOMER', 'DEFAULT_SUPPLIER', 'Comptoir', 'Fournisseur']
        for item in result:
            desc = str(item.get('desc', '')).strip()
            prefix = desc[:2].upper() if len(desc) >= 2 else ''
            desc_lower = desc.lower()
            if self.is_seller_mode:
                is_allowed_doc = prefix in ['BV', 'RC']
                is_client_money = any((k in desc_lower for k in ['versement', 'client', 'تحصيل', 'دفعة', 'encaissement']))
                if not (is_allowed_doc or is_client_money):
                    continue
            is_transfer = item.get('is_transfer', False)
            amount = float(item.get('amount', 0))
            raw_entity_name = str(item.get('entity', ''))
            entity_display = raw_entity_name.replace('➔', ' -> ').replace('\uf0e0', ' -> ').replace('\uf0da', ' -> ')
            if is_transfer:
                lower_raw = raw_entity_name.lower()
                if 'dép' in lower_raw and 'mag' in lower_raw:
                    if lower_raw.find('dép') < lower_raw.find('mag'):
                        entity_display = 'Dépôt -> Magasin'
                    else:
                        entity_display = 'Magasin -> Dépôt'
            if any((name.lower() in raw_entity_name.lower() for name in default_names)):
                entity_display = 'COMPTOIR'
            is_main_doc = prefix in main_doc_prefixes or is_transfer
            has_doc_ref = any((ref in desc for ref in main_doc_prefixes))
            if is_main_doc:
                pass
            elif has_doc_ref:
                continue
            elif amount == 0:
                continue
            full_doc_name = self.DOC_TRANSLATIONS.get(prefix, desc)
            bg_col = (0.95, 0.98, 1, 1)
            icon_name = 'file-document'
            icon_color = (0, 0.5, 0.8, 1)
            amount_text = f'{abs(amount):.2f} DA'
            is_reglement_kw = any((k in desc_lower for k in ['règlement', 'reglement', 'سداد', 'supplier pay']))
            is_versement_kw = any((k in desc_lower for k in ['versement', 'تحصيل', 'دفعة', 'client pay']))
            if is_transfer:
                full_doc_name = 'Transfert Stock'
                icon_name = 'compare-horizontal'
                bg_col = (0.95, 0.9, 1, 1)
                amount_text = 'Stock'
                icon_color = (0.5, 0, 0.5, 1)
            elif not is_main_doc:
                if amount < 0 or is_versement_kw or is_reglement_kw:
                    full_doc_name = 'Règlement' if is_reglement_kw else 'Versement'
                    icon_name = 'cash-plus'
                    icon_color = (0, 0.7, 0, 1)
                    amount_text = f'+ {abs(amount):.2f} DA'
                else:
                    full_doc_name = 'Crédit'
                    icon_name = 'notebook-edit'
                    icon_color = (0.8, 0, 0, 1)
                    amount_text = f'- {abs(amount):.2f} DA'
            elif prefix == 'BV':
                icon_name = 'cart'
                full_doc_name = 'Bon de Vente'
            elif prefix == 'BA':
                icon_name = 'truck'
                icon_color = (1, 0.6, 0, 1)
            elif prefix == 'RC':
                icon_name = 'keyboard-return'
                bg_col = (1, 0.95, 0.95, 1)
                icon_color = (0.8, 0, 0, 1)
            elif prefix == 'RF':
                icon_name = 'undo'
                icon_color = (0, 0.6, 0.6, 1)
            elif prefix == 'FC':
                icon_name = 'file-document'
                full_doc_name = 'Facture Vente'
                icon_color = (0, 0, 0.8, 1)
            elif prefix == 'FP':
                icon_name = 'file-document-outline'
                icon_color = (0.5, 0, 0.5, 1)
                full_doc_name = 'Proforma'
            elif prefix == 'FF':
                icon_name = 'file-document-edit'
                icon_color = (1, 0.4, 0, 1)
                full_doc_name = 'Facture Achat'
            elif prefix == 'DP':
                icon_name = 'clipboard-list'
                icon_color = (0, 0.5, 0.5, 1)
                full_doc_name = 'Bon de Commande'
            elif prefix == 'BI':
                icon_name = 'database-plus'
                full_doc_name = 'Bon Initial'
            clean_desc = desc.replace('Versement (Excédent)', 'Versement').replace('Règlement (Excédent)', 'Règlement')
            final_title = f'{full_doc_name} - {entity_display}'
            final_desc = f"{clean_desc} • {item['user']} • {item['time']}"
            self.history_rv_data.append({'raw_text': final_title, 'raw_sec': final_desc, 'amount_text': amount_text, 'icon': icon_name, 'icon_color': icon_color, 'bg_color': bg_col, 'is_local': False, 'key': '', 'raw_data': item})
        self.rv_history.data = self.history_rv_data
        self.rv_history.refresh_from_data()

    def on_history_fail(self, req, err):
        self.history_rv_data.append({'raw_text': 'Erreur chargement serveur.', 'raw_sec': str(err), 'amount_text': '', 'icon': 'alert-circle', 'icon_color': (0.8, 0, 0, 1), 'bg_color': (1, 1, 1, 1), 'is_local': False, 'key': '', 'raw_data': None})
        self.rv_history.data = self.history_rv_data
        self.rv_history.refresh_from_data()

    def handle_pending_item(self, key, is_synced):
        if self.is_seller_mode:
            try:
                ts_val = int(key.split('_')[0])
                item_date = datetime.fromtimestamp(ts_val).date()
                today = datetime.now().date()
                if item_date != today:
                    self.notify('Modification interdite (Date passée)', 'error')
                    return
            except:
                pass
        if self.pending_dialog:
            self.pending_dialog.dismiss()
        if is_synced and self.is_seller_mode:
            try:
                data = self.offline_store.get(key)['order_data']
                self.view_synced_transaction(data)
            except:
                self.notify('Erreur lecture', 'error')
            return

        def do_delete(x):
            if self.action_dialog:
                self.action_dialog.dismiss()
            if is_synced:
                item_data = self.offline_store.get(key)
                server_id = item_data.get('order_data', {}).get('server_id')
                is_transfer = item_data.get('order_data', {}).get('doc_type') == 'TR'
                if server_id and self.is_server_reachable:
                    UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/delete_transaction', req_body=json.dumps({'server_id': server_id, 'is_transfer': is_transfer}), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, s: self.offline_store.delete(key) or self.notify('Supprimé du Serveur', 'success'), on_failure=lambda r, e: self.notify('Echec suppression serveur', 'error'))
                else:
                    self.offline_store.delete(key)
                    self.notify('Supprimé (Local)', 'info')
            else:
                self.offline_store.delete(key)
                self.notify('Supprimé (Local)', 'info')
            self._reset_notification_state(0)
            target_date = getattr(self, 'history_view_date', datetime.now().date())
            self.filter_history_list(specific_date=target_date)

        def do_load(x):
            if self.action_dialog:
                self.action_dialog.dismiss()
            try:
                self.editing_transaction_key = key
                item_data = self.offline_store.get(key)
                data = item_data['order_data']
                self.current_editing_date = data.get('timestamp')
                self.current_editing_server_id = data.get('server_id')
                if data.get('is_simple_payment'):
                    self.current_mode = data.get('type')
                    saved_ent_id = data.get('entity_id')
                    found_entity = next((c for c in self.all_clients if c['id'] == saved_ent_id), None)
                    if not found_entity:
                        found_entity = next((s for s in self.all_suppliers if s['id'] == saved_ent_id), None)
                    self.selected_entity = found_entity if found_entity else {'id': saved_ent_id, 'name': 'Client Inconnu'}
                    self.show_simple_payment_dialog(amount=abs(float(data.get('amount', 0))))
                    return
                doc_type = data.get('doc_type', 'BV')
                self.original_doc_type = doc_type
                mode_map = {'BV': 'sale', 'BA': 'purchase', 'RC': 'return_sale', 'RF': 'return_purchase', 'TR': 'transfer', 'FC': 'invoice_sale', 'FP': 'proforma', 'FF': 'invoice_purchase', 'DP': 'order_purchase', 'BI': 'purchase'}
                self.open_mode(mode_map.get(doc_type, 'sale'))
                self.cart = data.get('items', [])
                saved_loc = data.get('purchase_location')
                if not saved_loc:
                    saved_loc = data.get('location', 'store')
                self.selected_location = saved_loc
                saved_ent_id = data.get('entity_id')
                found_entity = None
                if saved_ent_id:
                    found_entity = next((c for c in self.all_clients if c['id'] == saved_ent_id), None)
                    if not found_entity:
                        found_entity = next((s for s in self.all_suppliers if s['id'] == saved_ent_id), None)
                    if found_entity:
                        self.selected_entity = found_entity
                    else:
                        self.selected_entity = {'id': saved_ent_id, 'name': 'Client (Cache)'}
                else:
                    self.selected_entity = {'id': None, 'name': 'COMPTOIR'}
                self.update_location_display()
                if self.selected_entity and hasattr(self, 'btn_ent_screen'):
                    display_name = self.fix_text(str(self.selected_entity.get('name', 'Client')))[:15]
                    self.btn_ent_screen.text = display_name
                    self.btn_ent_screen.disabled = False
                    if self.current_mode in ['sale', 'return_sale', 'client_payment', 'invoice_sale', 'proforma']:
                        self.btn_ent_screen.md_bg_color = (0, 0.6, 0.6, 1)
                    else:
                        self.btn_ent_screen.md_bg_color = (0.8, 0.4, 0, 1)
                payment_info = data.get('payment_info', {})
                try:
                    self.editing_payment_amount = float(payment_info.get('amount', 0))
                except:
                    self.editing_payment_amount = 0
                self.update_cart_button()
                self.open_cart_screen(None)
            except Exception as e:
                self.notify(f'Erreur chargement: {e}', 'error')

        def do_print(x):
            try:
                item_data = self.offline_store.get(key)
                data_to_print = item_data['order_data']
                threading.Thread(target=self.print_ticket_bluetooth, args=(data_to_print,), daemon=True).start()
                self.notify('Impression lancée...', 'info')
            except Exception as e:
                self.notify(f'Erreur Impression: {e}', 'error')
        title_text = 'Action (Synchronisé)' if is_synced else 'Action (Non Synchronisé)'
        if is_synced:
            title_text += ' [Admin]'
        content = MDBoxLayout(orientation='vertical', spacing='12dp', size_hint_y=None, height='140dp', padding=[0, '10dp', 0, 0])
        content.add_widget(MDLabel(text='Que voulez-vous faire avec cette opération ?', theme_text_color='Secondary', adaptive_height=True))
        top_row = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        btn_print = MDFillRoundFlatButton(text='IMPRIMER', md_bg_color=(0, 0.5, 0.8, 1), text_color=(1, 1, 1, 1), font_style='Button', size_hint_x=0.5, on_release=do_print)
        btn_edit = MDFillRoundFlatButton(text='MODIFIER', md_bg_color=(0, 0.7, 0, 1), text_color=(1, 1, 1, 1), font_style='Button', size_hint_x=0.5, on_release=do_load)
        top_row.add_widget(btn_print)
        top_row.add_widget(btn_edit)
        content.add_widget(top_row)
        btn_delete = MDFlatButton(text='SUPPRIMER', theme_text_color='Custom', text_color=(0.9, 0, 0, 1), font_style='Button', size_hint_x=1, on_release=do_delete)
        content.add_widget(btn_delete)
        self.action_dialog = MDDialog(title=title_text, type='custom', content_cls=content, radius=[20, 7, 20, 7])
        self.action_dialog.open()

    def view_synced_transaction(self, data):
        content = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(500))
        if data.get('is_simple_payment'):
            typ = 'Versement' if data.get('type') == 'client_pay' else 'Règlement'
            amount = data.get('amount', 0)
            content.add_widget(MDLabel(text=f'TYPE: {typ}', halign='center', font_style='H6'))
            content.add_widget(MDLabel(text=f'MONTANT: {amount:.2f} DA', halign='center', font_style='H4', theme_text_color='Custom', text_color=(0, 0.6, 0, 1)))
            content.add_widget(MDBoxLayout(size_hint_y=1))
        else:
            scroll = MDScrollView()
            lst = MDList()
            items = data.get('items', [])
            total = 0
            for item in items:
                p = float(item.get('price', 0))
                q = float(item.get('qty', 0))
                sub = p * q
                total += sub
                li = ThreeLineAvatarIconListItem(text=item.get('name', 'Produit'), secondary_text=f'{p:.2f} DA x {(int(q) if q.is_integer() else q)}', tertiary_text=f'Total: {sub:.2f} DA')
                li.add_widget(IconLeftWidget(icon='package-variant'))
                lst.add_widget(li)
            scroll.add_widget(lst)
            content.add_widget(MDLabel(text=f'TOTAL: {total:.2f} DA', halign='center', font_style='H5', bold=True, size_hint_y=None, height=dp(40)))

        def do_print(x):
            threading.Thread(target=self.print_ticket_bluetooth, args=(data,), daemon=True).start()
        buttons = [MDRaisedButton(text='IMPRIMER', on_release=do_print), MDFlatButton(text='FERMER', on_release=lambda x: x.parent.parent.parent.parent.dismiss())]
        MDDialog(title='Détails (Synchronisé)', type='custom', content_cls=content, size_hint=(0.95, 0.95), buttons=buttons).open()

    def handle_server_history_item(self, item_data):
        if self.pending_dialog:
            self.pending_dialog.dismiss()
        self.notify('Chargement des détails...', 'info')
        is_tr_str = 'true' if item_data.get('is_transfer') else 'false'
        url = f"http://{self.active_server_ip}:{DEFAULT_PORT}/api/get_transaction_details?id={item_data['id']}&is_transfer={is_tr_str}"

        def on_success_callback(req, res):
            if res.get('purchase_location'):
                item_data['purchase_location'] = res.get('purchase_location')
            if res.get('location'):
                item_data['location'] = res.get('location')
            if res.get('source_location'):
                item_data['source_location'] = res.get('source_location')
            self.show_server_transaction_details(item_data, res)
        UrlRequest(url, on_success=on_success_callback, on_failure=lambda r, e: self.notify('Erreur chargement détails', 'error'), on_error=lambda r, e: self.notify('Erreur connexion', 'error'))

    def show_server_transaction_details(self, header_data, result):
        items = result.get('items', [])
        real_paid_amount = result.get('paid_amount')
        if real_paid_amount is None:
            real_paid_amount = header_data.get('paid_amount', 0)
        header_data['paid_amount'] = real_paid_amount
        paid_val = real_paid_amount
        is_transfer = header_data.get('is_transfer', False)
        raw_entity_name = str(header_data.get('entity', ''))
        entity_name = raw_entity_name.replace('➔', ' -> ').replace('\uf0e0', ' -> ').replace('\uf0da', ' -> ')
        if is_transfer:
            lower_raw = raw_entity_name.lower()
            idx_dep = lower_raw.find('dép')
            idx_mag = lower_raw.find('mag')
            if idx_dep != -1 and idx_mag != -1:
                if idx_dep < idx_mag:
                    entity_name = 'Dépôt -> Magasin'
                else:
                    entity_name = 'Magasin -> Dépôt'
            elif 'dép' in lower_raw:
                entity_name = 'Dépôt -> Magasin'
            elif 'mag' in lower_raw:
                entity_name = 'Magasin -> Dépôt'
        auto_pay_names = ['COMPTOIR', 'Comptoir', 'زبون افتراضي', 'مورد افتراضي', 'DEFAULT_CUSTOMER']
        is_comptoir = any((n in entity_name for n in auto_pay_names))
        content_height = dp(500)
        content = MDBoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=content_height)
        prefix = header_data['desc'][:2]
        full_desc = header_data.get('desc', '').lower()
        amount = float(header_data.get('amount', 0))
        is_versement_kw = any((k in full_desc for k in ['versement', 'تحصيل', 'دفعة']))
        is_reglement_kw = any((k in full_desc for k in ['règlement', 'reglement', 'سداد']))
        main_docs = ['BV', 'BA', 'RC', 'RF', 'TR', 'FP', 'FC', 'FF', 'DP', 'BI']
        if not prefix in main_docs:
            if amount < 0 or is_versement_kw or is_reglement_kw:
                if is_reglement_kw:
                    type_str = 'Règlement'
                else:
                    type_str = 'Versement'
                amount_color = (0, 0.7, 0, 1)
                display_amount_str = f'+ {abs(amount):.2f} DA'
                is_financial_op = True
            else:
                type_str = 'Crédit'
                amount_color = (0.8, 0, 0, 1)
                display_amount_str = f'- {abs(amount):.2f} DA'
                is_financial_op = True
        else:
            type_str = self.DOC_TRANSLATIONS.get(prefix, 'Opération')
            amount_color = (0, 0, 0, 1)
            display_amount_str = f'{abs(amount):.2f} DA'
            is_financial_op = False
        header_height = dp(110) if not is_transfer else dp(80)
        header_box = MDCard(orientation='vertical', size_hint_y=None, height=header_height, padding=dp(10), md_bg_color=(0.95, 0.95, 0.95, 1), radius=[10])
        header_text = self.fix_text(f'{type_str} - {entity_name}')
        header_box.add_widget(MDLabel(text=header_text, bold=True, font_style='Subtitle1'))
        header_box.add_widget(MDLabel(text=f"Date: {header_data['time']}", font_style='Caption'))
        if not is_transfer:
            header_box.add_widget(MDLabel(text=f'Montant: {display_amount_str}', theme_text_color='Custom', text_color=amount_color, bold=True, font_style='H5'))
            if not is_financial_op:
                total_doc = float(abs(amount))
                if is_comptoir:
                    paid_val = total_doc
                diff = total_doc - float(paid_val)
                money_row = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
                money_row.add_widget(MDLabel(text=f'Versé: {float(paid_val):.2f} DA', theme_text_color='Custom', text_color=(0, 0.6, 0, 1), bold=True))
                if is_comptoir:
                    lbl_reste_text = 'Payée ✅'
                    lbl_reste_color = (0, 0.6, 0, 1)
                else:
                    lbl_reste_text = f'Crédit: {diff:.2f} DA' if diff > 0 else f'Rendu: {abs(diff):.2f} DA'
                    lbl_reste_color = (0.8, 0, 0, 1) if diff > 0 else (0, 0.6, 0, 1)
                money_row.add_widget(MDLabel(text=lbl_reste_text, theme_text_color='Custom', text_color=lbl_reste_color, bold=True, halign='right'))
                header_box.add_widget(money_row)
        else:
            header_box.add_widget(MDLabel(text='Transfert de stock', font_style='Caption', theme_text_color='Hint'))
        content.add_widget(header_box)
        content.add_widget(MDLabel(text='Détails:', font_style='Caption', size_hint_y=None, height=dp(20)))
        scroll = MDScrollView()
        list_layout = MDList()
        if not items:
            msg = 'Opération financière' if is_financial_op else 'Aucun article'
            list_layout.add_widget(OneLineListItem(text=msg))
        else:
            for item in items:
                qty_display = int(item['qty']) if item['qty'].is_integer() else item['qty']
                item_name = self.fix_text(item['name'])
                if is_transfer:
                    li = TwoLineAvatarIconListItem(text=item_name, secondary_text=f'[color=#0000FF][b][size=18sp]Qté: {qty_display}[/size][/b][/color]')
                    li.add_widget(IconLeftWidget(icon='transfer'))
                else:
                    total_item = item['price'] * item['qty']
                    li = ThreeLineAvatarIconListItem(text=item_name, secondary_text=f"[b][size=16sp]{item['price']:.2f} DA x {qty_display}[/size][/b]", tertiary_text=f'Total: {total_item:.2f} DA')
                    li.add_widget(IconLeftWidget(icon='package-variant-closed'))
                list_layout.add_widget(li)
        scroll.add_widget(list_layout)
        content.add_widget(scroll)
        try:
            item_date_str = str(header_data.get('time', '')).split(' ')[0]
            today_str = str(datetime.now().date())
            is_today = item_date_str == today_str
        except:
            is_today = False
        can_edit = True
        if self.is_seller_mode and (not is_today):
            can_edit = False

        def do_print(x):
            print_data = {'server_id': header_data.get('id'), 'invoice_number': header_data.get('desc'), 'timestamp': header_data.get('time'), 'user_name': header_data.get('user'), 'entity': header_data.get('entity'), 'entity_id': header_data.get('entity_id'), 'amount': header_data.get('amount'), 'doc_type': prefix, 'items': items, 'is_simple_payment': is_financial_op, 'type': 'client_pay' if amount > 0 else 'credit', 'payment_info': {'amount': paid_val}}
            threading.Thread(target=self.print_ticket_bluetooth, args=(print_data,), daemon=True).start()
        actions_layout = MDBoxLayout(orientation='vertical', spacing='10dp', adaptive_height=True, padding=[0, '15dp', 0, 0])
        top_row = MDBoxLayout(orientation='horizontal', spacing='10dp', size_hint_y=None, height='50dp')
        show_edit = can_edit
        print_width = 0.5 if show_edit else 1.0
        btn_print = MDFillRoundFlatButton(text='IMPRIMER', md_bg_color=(0, 0.5, 0.8, 1), text_color=(1, 1, 1, 1), font_style='Button', size_hint_x=print_width, on_release=do_print)
        top_row.add_widget(btn_print)
        if show_edit:
            btn_edit = MDFillRoundFlatButton(text='MODIFIER', md_bg_color=(0, 0.6, 0.4, 1), text_color=(1, 1, 1, 1), font_style='Button', size_hint_x=0.5, on_release=lambda x: self.load_server_transaction_for_edit(header_data, items))
            top_row.add_widget(btn_edit)
        actions_layout.add_widget(top_row)
        if can_edit:
            btn_delete = MDFlatButton(text='SUPPRIMER CETTE OPÉRATION', theme_text_color='Custom', text_color=(0.9, 0, 0, 1), font_style='Button', size_hint_x=1, on_release=lambda x: self.confirm_delete_server_transaction(header_data))
            actions_layout.add_widget(btn_delete)
        else:
            actions_layout.add_widget(MDLabel(text='Modification impossible (Date passée)', halign='center', theme_text_color='Error', font_style='Caption', adaptive_height=True))
        content.add_widget(actions_layout)
        self.srv_dialog = MDDialog(title='Détails', type='custom', content_cls=content, size_hint=(0.95, 0.95), buttons=[MDFlatButton(text='FERMER', on_release=lambda x: self.srv_dialog.dismiss())])
        self.srv_dialog.open()

    def confirm_delete_server_transaction(self, item_data):
        is_transfer = item_data.get('is_transfer', False)
        msg = 'Êtes-vous sûr de vouloir supprimer cette opération ?\nLe stock et le solde seront ajustés.'
        if is_transfer:
            msg = "Supprimer ce transfert de stock ?\nLes quantités seront restituées à l'origine."
        confirm_dialog = MDDialog(title='Confirmer Suppression', text=msg, buttons=[MDFlatButton(text='NON', on_release=lambda x: confirm_dialog.dismiss()), MDRaisedButton(text='OUI', md_bg_color=(0.8, 0, 0, 1), on_release=lambda x: [confirm_dialog.dismiss(), self._execute_delete(item_data)])])
        confirm_dialog.open()

    def _execute_delete(self, item_data):
        if self.srv_dialog:
            self.srv_dialog.dismiss()
        self._do_delete_api(item_data)

    def _do_delete_api(self, item_data_or_id):
        if isinstance(item_data_or_id, dict):
            trans_id = item_data_or_id['id']
            is_transfer = item_data_or_id.get('is_transfer', False)
        else:
            trans_id = item_data_or_id
            is_transfer = False
        UrlRequest(f'http://{self.active_server_ip}:{DEFAULT_PORT}/api/delete_transaction', req_body=json.dumps({'server_id': trans_id, 'is_transfer': is_transfer}), req_headers={'Content-type': 'application/json'}, method='POST', on_success=lambda r, s: self.notify('Supprimé avec succès', 'success') or self.filter_history_list(0), on_failure=lambda r, e: self.notify('Echec suppression', 'error'))

    def load_server_transaction_for_edit(self, header_data, items):
        if hasattr(self, 'srv_dialog') and self.srv_dialog:
            self.srv_dialog.dismiss()
        if hasattr(self, 'entity_hist_dialog') and self.entity_hist_dialog:
            self.entity_hist_dialog.dismiss()
        if hasattr(self, 'mgmt_dialog') and self.mgmt_dialog:
            self.mgmt_dialog.dismiss()
        if hasattr(self, 'pending_dialog') and self.pending_dialog:
            self.pending_dialog.dismiss()
        self.current_editing_date = header_data.get('time') or header_data.get('timestamp')
        found_entity = None
        search_name = header_data.get('entity', '').strip()
        search_id = header_data.get('entity_id')
        if search_id:
            found_entity = next((e for e in self.all_clients if e['id'] == search_id), None)
            if not found_entity:
                found_entity = next((e for e in self.all_suppliers if e['id'] == search_id), None)
        if not found_entity and search_name:
            found_entity = next((e for e in self.all_clients if e.get('name') == search_name), None)
            if not found_entity:
                found_entity = next((e for e in self.all_suppliers if e.get('name') == search_name), None)
        prefix = header_data['desc'][:2]
        mode_map = {'BV': 'sale', 'BA': 'purchase', 'RC': 'return_sale', 'RF': 'return_purchase', 'TR': 'transfer', 'FC': 'invoice_sale', 'FP': 'proforma', 'FF': 'invoice_purchase', 'DP': 'order_purchase', 'BI': 'purchase'}
        mode = mode_map.get(prefix)
        amount = float(header_data.get('amount', 0))
        full_desc = header_data.get('desc', '').lower()
        is_financial = False
        if not mode or not items:
            is_supplier_op = any((k in full_desc for k in ['règlement', 'reglement', 'سداد', 'fournisseur']))
            if found_entity:
                if any((s['id'] == found_entity['id'] for s in self.all_suppliers)):
                    is_supplier_op = True
            self.current_mode = 'supplier_payment' if is_supplier_op else 'client_payment'
            is_financial = True
        if is_financial:
            self.editing_transaction_key = 'SERVER_EDIT_MODE'
            self.current_editing_server_id = header_data['id']
            if found_entity:
                self.selected_entity = found_entity
            elif search_name:
                self.selected_entity = {'id': None, 'name': search_name}
            else:
                self.selected_entity = {'id': None, 'name': 'Client Inconnu'}
            if self.selected_entity and hasattr(self, 'btn_ent_screen'):
                self.btn_ent_screen.text = self.fix_text(str(self.selected_entity.get('name', 'Client')))[:15]
            self.show_simple_payment_dialog(amount=abs(amount))
            return
        if not mode:
            if 'Initial' in header_data.get('desc', '') or 'BI' in header_data.get('desc', ''):
                mode = 'purchase'
                self.original_doc_type = 'BI'
            else:
                self.notify("Type d'opération non modifiable", 'error')
                return
        self.open_mode(mode)
        if prefix == 'BI':
            self.original_doc_type = 'BI'
        if found_entity:
            self.selected_entity = found_entity
        elif search_name:
            self.selected_entity = {'id': None, 'name': search_name}
        else:
            self.selected_entity = {'id': None, 'name': 'COMPTOIR'}
        if self.selected_entity and hasattr(self, 'btn_ent_screen'):
            self.btn_ent_screen.text = self.fix_text(str(self.selected_entity.get('name', 'Client')))[:15]
            self.btn_ent_screen.disabled = False
            if self.current_mode in ['sale', 'return_sale', 'client_payment', 'invoice_sale', 'proforma']:
                self.btn_ent_screen.md_bg_color = (0, 0.6, 0.6, 1)
            else:
                self.btn_ent_screen.md_bg_color = (0.8, 0.4, 0, 1)
        raw_loc = header_data.get('purchase_location')
        if not raw_loc:
            raw_loc = header_data.get('location')
        if not raw_loc and prefix == 'TR':
            raw_loc = header_data.get('source_location')
        target_loc = 'store'
        if raw_loc:
            loc_str = str(raw_loc).lower().strip()
            warehouse_keywords = ['warehouse', 'depot', 'dépôt', 'stock_warehouse']
            if any((k in loc_str for k in warehouse_keywords)):
                target_loc = 'warehouse'
        self.selected_location = target_loc
        self.update_location_display()
        if prefix == 'TR' and hasattr(self, 'btn_ent_screen'):
            src = 'Magasin' if self.selected_location == 'store' else 'Dépôt'
            dst = 'Dépôt' if self.selected_location == 'store' else 'Magasin'
            self.btn_ent_screen.text = f'{src}  >>>  {dst}'
        self.cart = []
        for item in items:
            self.cart.append({'id': item['id'], 'name': item['name'], 'price': item['price'], 'qty': item['qty']})
        self.editing_transaction_key = 'SERVER_EDIT_MODE'
        self.current_editing_server_id = header_data['id']
        try:
            self.editing_payment_amount = float(header_data.get('paid_amount', 0))
        except:
            self.editing_payment_amount = 0
        self.update_cart_button()
        self.notify('Modification: Données chargées', 'success')
        self.open_cart_screen()

    def manual_sync(self):
        self.try_sync_offline_data()
        self.notify('Synchronisation...')

    def go_back(self):
        try:
            Window.release_all_keyboards()
            self.editing_transaction_key = None
            self.current_editing_server_id = None
            self.editing_payment_amount = None
            if self.search_field:
                self.search_field.text = ''
            self.cart = []
            self.update_cart_button()
            self.sm.current = 'dashboard'
            self._reset_notification_state(0)
        except:
            self.sm.current = 'dashboard'

# ---------------------------------------------------------
    # BARCODE SCANNER LOGIC (ANDROID / pyzbar)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # تعديل جديد: طلب الصلاحية قبل فتح الكاميرا
    # ---------------------------------------------------------
    def open_barcode_scanner(self, instance):
        if not decode:
            self.notify("Erreur: Librairie pyzbar manquante", "error")
            return

        # التحقق: هل نحن على أندرويد؟
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            
            def on_permission_result(permissions, grants):
                # إذا وافق المستخدم (True)
                if grants and grants[0]:
                    Clock.schedule_once(lambda dt: self._launch_camera_widget(), 0.1)
                else:
                    self.notify("Permission Caméra Refusée !", "error")
            
            # طلب إذن الكاميرا
            request_permissions([Permission.CAMERA], on_permission_result)
        else:
            # إذا كنا على الكمبيوتر، افتح مباشرة
            self._launch_camera_widget()

    def _launch_camera_widget(self):
        self.temp_scanned_cart = []
        self.last_scan_time = 0
        
        try:
            # الكاميرا بدون تحديد دقة (تلقائي) لضمان العمل
            self.camera_widget = Camera(play=True, index=0, allow_stretch=True, keep_ratio=False)
            
            # تدوير الكاميرا
            with self.camera_widget.canvas.before:
                PushMatrix()
                self.rotation = Rotate(angle=-90, origin=self.camera_widget.center)
            with self.camera_widget.canvas.after:
                PopMatrix()
            self.camera_widget.bind(center=lambda instance, value: setattr(self.rotation, 'origin', instance.center))

        except Exception as e:
            self.notify("Erreur init caméra", "error")
            return
        
        # --- التصميم الجديد (Vertical Split) ---
        # يقسم الشاشة إلى جزئين لا يتداخلان
        root_layout = MDBoxLayout(orientation='vertical', spacing=0)
        
        # 1. الجزء العلوي: الكاميرا (45% من الشاشة)
        # استخدام FloatLayout يسمح للكاميرا بالتمدد داخله بالكامل
        camera_area = MDFloatLayout(size_hint_y=0.45)
        
        # نجبر الكاميرا على أخذ حجم هذا الجزء
        self.camera_widget.size_hint = (1, 1)
        self.camera_widget.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        camera_area.add_widget(self.camera_widget)
        
        # زر الإغلاق (فوق الكاميرا)
        close_btn = MDIconButton(
            icon="close",
            icon_size="32sp",
            md_bg_color=(0, 0, 0, 0.4),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            pos_hint={'top': 0.95, 'right': 0.95},
            on_release=self.close_barcode_scanner
        )
        camera_area.add_widget(close_btn)
        
        # إضافة منطقة الكاميرا للشاشة الرئيسية
        root_layout.add_widget(camera_area)
        
        # 2. الجزء السفلي: القائمة (55% من الشاشة - الباقي)
        list_container = MDCard(
            orientation='vertical', 
            size_hint_y=0.55, 
            radius=[20, 20, 0, 0], # تدوير الزوايا العلوية فقط
            md_bg_color=(1, 1, 1, 1),
            elevation=0
        )
        
        # هيدر القائمة
        header_box = MDBoxLayout(size_hint_y=None, height=dp(45), padding=[dp(20), 0])
        self.lbl_scan_count = MDLabel(text="Articles scannés: 0", bold=True, theme_text_color="Primary", font_style="Subtitle1")
        header_box.add_widget(self.lbl_scan_count)
        list_container.add_widget(header_box)
        
        # القائمة
        scroll = MDScrollView()
        self.scan_list_widget = MDList()
        scroll.add_widget(self.scan_list_widget)
        list_container.add_widget(scroll)
        
        # زر التأكيد
        btn_confirm = MDRaisedButton(
            text="CONFIRMER & AJOUTER",
            font_size="18sp",
            size_hint=(1, None),
            height=dp(60),
            md_bg_color=(0, 0.7, 0, 1),
            elevation=0,
            on_release=self.finish_continuous_scan
        )
        list_container.add_widget(btn_confirm)
        
        root_layout.add_widget(list_container)
        
        # فتح النافذة
        self.scan_dialog = ModalView(size_hint=(1, 1), auto_dismiss=False, background_color=(0,0,0,1))
        self.scan_dialog.add_widget(root_layout)
        self.scan_dialog.open()
        
        # الفحص
        self.scan_event = Clock.schedule_interval(self.detect_barcode_frame, 1.0/10.0)

    def close_barcode_scanner(self, *args):
        if hasattr(self, 'scan_event') and self.scan_event:
            self.scan_event.cancel()
        
        if hasattr(self, 'camera_widget'):
            self.camera_widget.play = False
            
        if hasattr(self, 'scan_dialog') and self.scan_dialog:
            self.scan_dialog.dismiss()
            self.scan_dialog = None # تفريغ المتغير

    def detect_barcode_frame(self, dt):
        # التحقق من وجود المكتبات والكاميرا
        if not hasattr(self, 'camera_widget') or not self.camera_widget.texture:
            return
            
        # التحقق من الفاصل الزمني (Cooldown) - 1.5 ثانية
        if time.time() - self.last_scan_time < 1.5:
            return

        try:
            texture = self.camera_widget.texture
            size = texture.size
            pixels = texture.pixels
            pil_image = PILImage.frombytes(mode='RGBA', size=size, data=pixels)
            
            found_code = None
            
            # كود القراءة (يدعم pyzbar و zxing)
            if 'pyzbar' in sys.modules and decode:
                barcodes = decode(pil_image)
                if barcodes:
                    found_code = barcodes[0].data.decode("utf-8")
            elif read_barcodes:
                results = read_barcodes(pil_image)
                if results:
                    found_code = results[0].text

            if found_code:
                # تحديث وقت آخر مسح
                self.last_scan_time = time.time()
                print(f"Barcode Found: {found_code}")
                # معالجة الكود بدون إغلاق الكاميرا
                self.process_continuous_scan(found_code)

        except Exception as e:
            print(f"Scan Error: {e}")

    def process_continuous_scan(self, code):
        found_product = None
        for p in self.all_products_raw:
            p_code = str(p.get('barcode', '')).strip()
            if p_code == code:
                found_product = p
                break
        
        if found_product:
            # 1. التحقق من التكرار
            for item in self.temp_scanned_cart:
                if item['id'] == found_product['id']:
                    # تشغيل صوت "مكرر"
                    self.play_sound('duplicate')
                    self.show_duplicate_alert(found_product.get('name', 'Produit'))
                    return

            # 2. الإضافة (نجاح)
            self.temp_scanned_cart.append(found_product)
            self.update_scan_list_ui()
            
            # تشغيل صوت "نجاح"
            self.play_sound('success')
            
        else:
            # 3. غير موجود
            # تشغيل صوت "خطأ"
            self.play_sound('error')
            self.show_not_found_alert(code)

    def show_duplicate_alert(self, product_name):
        # دالة لإظهار نافذة تنبيه عند تكرار المنتج
        # نستخدم مخزن مؤقت (Flag) لمنع ظهور النافذة مرتين في نفس اللحظة
        if hasattr(self, 'is_showing_alert') and self.is_showing_alert:
            return
            
        self.is_showing_alert = True
        
        def close_alert(*args):
            self.dup_dialog.dismiss()
            self.is_showing_alert = False

        short_name = self.fix_text(product_name)[:30]
        self.dup_dialog = MDDialog(
            title="Déjà scanné !",
            text=f"Le produit:\n[b]{short_name}[/b]\n\nest déjà dans la liste.",
            buttons=[
                MDRaisedButton(
                    text="OK", 
                    md_bg_color=(0.8, 0, 0, 1), 
                    on_release=close_alert
                )
            ],
            size_hint=(0.85, None)
        )
        self.dup_dialog.open()

    def update_scan_list_ui(self):
        self.scan_list_widget.clear_widgets()
        count = len(self.temp_scanned_cart)
        self.lbl_scan_count.text = f"Articles scannés: {count}"
        
        if count == 0:
            return

        for index, prod in enumerate(reversed(self.temp_scanned_cart)):
            real_number = count - index
            prod_name = self.fix_text(prod.get('name', 'Inconnu'))
            final_price = prod.get('price', 0)
            
            # عنصر خفيف
            item = TwoLineAvatarIconListItem(
                text=f"[b]{real_number}.[/b] {prod_name}",
                secondary_text=f"Prix: {final_price} DA",
                theme_text_color="Custom",
                text_color=(0, 0, 0, 1)
            )
            
            icon_box = IconLeftWidget(icon="cube-outline")
            item.add_widget(icon_box)
            
            del_btn = IconRightWidget(
                icon="delete",
                theme_text_color="Custom",
                text_color=(0.9, 0, 0, 1),
                on_release=lambda x, p=prod: self.remove_temp_item(p)
            )
            item.add_widget(del_btn)
            self.scan_list_widget.add_widget(item)

    def show_not_found_alert(self, code):
        if hasattr(self, 'is_showing_alert') and self.is_showing_alert:
            return
        self.is_showing_alert = True
        
        def close(*args):
            self.not_found_dialog.dismiss()
            self.is_showing_alert = False

        self.not_found_dialog = MDDialog(
            title="Introuvable !",
            text=f"Le code-barres:\n[b]{code}[/b]\n\nn'existe pas dans la base de données.",
            buttons=[MDRaisedButton(text="OK", md_bg_color=(0.2, 0.2, 0.2, 1), on_release=close)],
            size_hint=(0.85, None)
        )
        self.not_found_dialog.open()

    def remove_temp_item(self, product_to_remove):
        # دالة لحذف عنصر من القائمة المؤقتة
        if product_to_remove in self.temp_scanned_cart:
            self.temp_scanned_cart.remove(product_to_remove)
            self.update_scan_list_ui() # إعادة الترقيم

    def finish_continuous_scan(self, instance):
        # إيقاف الكاميرا أولاً
        self.close_barcode_scanner()
        
        if not self.temp_scanned_cart:
            return

        count = 0
        # نقل المنتجات من القائمة المؤقتة للسلة الرئيسية
        for product in self.temp_scanned_cart:
            self.add_scanned_item_to_cart(product)
            count += 1
            
        self.notify(f"{count} Articles ajoutés au panier", "success")
        # تفريغ القائمة المؤقتة
        self.temp_scanned_cart = []

    def process_scanned_barcode(self, code):
        found_product = None
        for p in self.all_products_raw:
            p_code = str(p.get('barcode', '')).strip()
            if p_code == code:
                found_product = p
                break
        
        if found_product:
            self.add_scanned_item_to_cart(found_product)
        else:
            self.notify(f"Produit introuvable: {code}", "error")

    def add_scanned_item_to_cart(self, product):
        try:
            is_sale_context = self.current_mode in ['sale', 'return_sale', 'invoice_sale', 'proforma']
            final_price = 0.0
            
            if is_sale_context:
                curr_price = product.get('price', 0)
                if self.selected_entity:
                    cat = str(self.selected_entity.get('category', ''))
                    if cat in ['Gros', 'جملة']:
                        curr_price = product.get('price_wholesale', 0)
                    elif cat in ['Demi-Gros', 'نصف جملة']:
                        curr_price = product.get('price_semi', 0)
                    if float(curr_price or 0) == 0:
                         curr_price = product.get('price', 0)
                final_price = float(curr_price)
            else:
                final_price = float(product.get('purchase_price', product.get('price', 0)))

            qty = 1.0 
            found = False
            for item in self.cart:
                if item['id'] == product['id']:
                    item['qty'] += qty
                    item['price'] = final_price
                    found = True
                    break
            
            if not found:
                self.cart.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': final_price,
                    'qty': qty
                })
            
            self.update_cart_button()
            self.notify(f"{product['name']} Ajouté (1)", "success")
        except Exception as e:
            self.notify(f"Erreur ajout panier: {e}", "error")

if __name__ == '__main__':
    StockApp().run()
