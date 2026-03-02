import os
import json
import math
import random
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.core.text import LabelBase
from lunar_python import Lunar, Solar

# --- 基础配置与路径 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, 'font.ttf')
JSON_PATH = os.path.join(BASE_DIR, 'birthday.json')
WISH_PATH = os.path.join(BASE_DIR, 'wishes.json')
DESTINY_PATH = os.path.join(BASE_DIR, 'destiny.json')

# 字体注册
if os.path.exists(FONT_PATH):
    LabelBase.register(name='CyberFont', fn_regular=FONT_PATH)
else:
    win_font = "C:\\Windows\\Fonts\\msyh.ttc"
    if os.path.exists(win_font):
        LabelBase.register(name='CyberFont', fn_regular=win_font)

Window.clearcolor = (0.05, 0.05, 0.07, 1)


# --- 核心逻辑：余爱随机宿命 ---
def get_love_count(age):
    """
    余爱逻辑重构：
    1. 初始随机 1-3 个名额。
    2. 每 30 年为一个观测周期。
    3. 每个周期随机抽 0 或 1，抽中 1 则扣除一个余额。
    """
    if not os.path.exists(DESTINY_PATH):
        initial = random.randint(1, 3)
        # 记录初始值和已经判定的周期，防止每次刷新都重新扣除
        with open(DESTINY_PATH, 'w') as f:
            json.dump({"total": initial, "checked_periods": []}, f)

    with open(DESTINY_PATH, 'r') as f:
        data = json.load(f)

    total = data["total"]
    checked = data["checked_periods"]
    current_period = int(age / 30)

    # 检查是否有新的 30 年周期需要判定
    changed = False
    for p in range(1, current_period + 1):
        if str(p) not in checked:
            # 抽签：0 留，1 删
            if random.choice([0, 1]) == 1:
                total = max(0, total - 1)
            checked.append(str(p))
            changed = True

    if changed:
        with open(DESTINY_PATH, 'w') as f:
            json.dump({"total": total, "checked_periods": checked}, f)

    return total


# --- UI 组件: 古典死之钟 ---
class DeathClock(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.progress = 0

    def update_clock(self, progress):
        self.progress = progress
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Line(circle=(self.center_x, self.center_y, self.width / 2), width=1.2)
            for i in range(12):
                angle = math.radians(90 - i * 30)
                r_out, r_in = self.width / 2, self.width / 2 - dp(8)
                Line(points=[self.center_x + math.cos(angle) * r_in, self.center_y + math.sin(angle) * r_in,
                             self.center_x + math.cos(angle) * r_out, self.center_y + math.sin(angle) * r_out], width=1)

        self.canvas.clear()
        with self.canvas:
            total_sec = self.progress * 24 * 3600
            s_ang = math.radians(90 - (total_sec % 60) * 6)
            m_ang = math.radians(90 - ((total_sec / 60) % 60) * 6)
            h_ang = math.radians(90 - ((total_sec / 3600) % 12) * 30)
            Color(0.5, 0.5, 0.5, 1)
            Line(points=[self.center_x, self.center_y, self.center_x + math.cos(h_ang) * dp(25),
                         self.center_y + math.sin(h_ang) * dp(25)], width=2.5)
            Line(points=[self.center_x, self.center_y, self.center_x + math.cos(m_ang) * dp(40),
                         self.center_y + math.sin(m_ang) * dp(40)], width=1.5)
            Color(0.8, 0.1, 0.1, 1)
            Line(points=[self.center_x, self.center_y, self.center_x + math.cos(s_ang) * dp(50),
                         self.center_y + math.sin(s_ang) * dp(50)], width=1)


# --- 屏幕 1: 生辰录入 ---
class BirthdayInputScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(15))
        l.add_widget(Label(text="[ 开启因果 ]", font_size=dp(24), font_name='CyberFont'))
        self.ins = []
        for h in ['年 (YYYY)', '月 (MM)', '日 (DD)', '时 (0-23)']:
            ti = TextInput(hint_text=h, multiline=False, input_filter='int', font_name='CyberFont', size_hint_y=None,
                           height=dp(45))
            self.ins.append(ti);
            l.add_widget(ti)
        b = Button(text="锁定", font_name='CyberFont', size_hint_y=None, height=dp(60),
                   background_color=(0.1, 0.4, 0.7, 1))
        b.bind(on_press=self.save_data);
        l.add_widget(b);
        self.add_widget(l)

    def save_data(self, *args):
        try:
            d = {'year': int(self.ins[0].text), 'month': int(self.ins[1].text), 'day': int(self.ins[2].text),
                 'hour': int(self.ins[3].text)}
            with open(JSON_PATH, 'w') as f:
                json.dump(d, f)
            self.manager.current = 'main'
        except:
            pass


# --- 屏幕 2: 主界面 ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_dead = False
        self.layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(20))
        self.age_label = Label(markup=True, font_size=dp(42), font_name='CyberFont', size_hint_y=0.3)
        mid = BoxLayout(orientation='horizontal', size_hint_y=0.4)
        self.stats = Label(text='', font_name='CyberFont', size_hint_x=0.6, halign='left', valign='middle')
        self.stats.bind(size=self.stats.setter('text_size'))
        self.clock_w = DeathClock(size_hint=(None, None), size=(dp(150), dp(150)))
        mid.add_widget(self.stats);
        mid.add_widget(self.clock_w)
        self.layout.add_widget(self.age_label);
        self.layout.add_widget(mid)
        self.hint = Label(text="下滑天命 | 左滑愿望", font_size=dp(12), color=(0.3, 0.3, 0.3, 1), font_name='CyberFont')
        self.layout.add_widget(self.hint);
        self.add_widget(self.layout)

    def on_enter(self):
        self.ev = Clock.schedule_interval(self.update, 1 / 60)

    def on_leave(self):
        self.ev.cancel()

    def update(self, dt):
        if not os.path.exists(JSON_PATH) or self.is_dead: return
        with open(JSON_PATH) as f:
            d = json.load(f)
        born = datetime(d['year'], d['month'], d['day'], d.get('hour', 0))
        age = (datetime.now() - born).total_seconds() / (365.2425 * 24 * 3600)

        if age >= 100: self.trigger_death(); return

        p = f"{age:.12f}".split('.')
        self.age_label.text = f"[b]{p[0]}[/b][size=22sp].{p[1]}[/size]"
        self.clock_w.update_clock(age / 100)
        rem = 100 - age
        love = get_love_count(age)
        self.stats.text = f"余饭: {int(rem * 1095)} 顿\n余觉: {int(rem * 365)} 次\n余爱: {love} 人"

    def trigger_death(self):
        self.is_dead = True
        Window.clearcolor = (0.5, 0, 0, 1)
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="死之钟已满", font_name='CyberFont', font_size=dp(40)))
        btn = Button(text="我还活着", size_hint=(0.6, 0.2), pos_hint={'center_x': .5}, font_name='CyberFont')
        btn.bind(on_press=self.resurrect);
        self.layout.add_widget(btn)

    def resurrect(self, *args):
        Window.clearcolor = (0.05, 0.05, 0.07, 1)
        self.layout.clear_widgets()
        sv = ScrollView();
        box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(20), spacing=dp(10))
        box.bind(minimum_height=box.setter('height'))
        if os.path.exists(WISH_PATH):
            wishes = json.load(open(WISH_PATH, 'r', encoding='utf-8'))
            for w in wishes:
                color = (1, 1, 1, 1) if w['done'] else (0.4, 0.4, 0.4, 1)
                box.add_widget(
                    Label(text=f"{'★' if w['done'] else '○'} {w['text']}", font_name='CyberFont', size_hint_y=None,
                          height=dp(40), color=color))
        sv.add_widget(box);
        self.layout.add_widget(sv)

    def on_touch_move(self, touch):
        if self.is_dead: return
        if touch.x - touch.ox < -dp(50): self.manager.current = 'wishlist'
        if touch.y - touch.oy < -dp(50): self.manager.current = 'bazi'


# --- 屏幕 3: 隐藏八字 (修复五行显示) ---
class BaziScreen(Screen):
    def on_enter(self):
        self.clear_widgets();
        l = BoxLayout(orientation='vertical', padding=dp(50), spacing=dp(20))
        d = json.load(open(JSON_PATH))
        sol = Solar.fromYmdHms(d['year'], d['month'], d['day'], d.get('hour', 12), 0, 0)
        lun = Lunar.fromSolar(sol);
        bz = lun.getEightChar()

        # 重新计算五行缺失
        all_wx = bz.getYearWuXing() + bz.getMonthWuXing() + bz.getDayWuXing() + bz.getTimeWuXing()
        miss = "".join([wx for wx in "金木水火土" if wx not in all_wx])

        l.add_widget(Label(text="[ 乾坤八字 ]", color=(0.4, 0.4, 0.4, 1), font_name='CyberFont'))
        l.add_widget(Label(text=f"{bz.getYear()} {bz.getMonth()}\n{bz.getDay()} {bz.getTime()}", font_size=dp(22),
                           font_name='CyberFont', halign='center'))
        l.add_widget(Label(text=f"缺: {miss if miss else '均衡'}", color=(0.8, 0.2, 0.2, 1), font_name='CyberFont'))

        btn = Button(text="归位", size_hint_y=0.2, font_name='CyberFont');
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        l.add_widget(btn);
        self.add_widget(l)


# --- 屏幕 4: 心愿清单 ---
class WishItem(BoxLayout):
    def __init__(self, index, text, is_done, on_delete, on_check, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, height=dp(50), **kwargs)
        self.index = index
        self.cb = CheckBox(active=is_done, size_hint_x=0.15)
        self.cb.bind(active=lambda cb, v: on_check(self.index, v))
        self.ti = TextInput(text=text, font_name='CyberFont', multiline=False, readonly=is_done,
                            background_color=(0, 0, 0, 0),
                            foreground_color=(1, 1, 1, 1) if not is_done else (0.5, 0.5, 0.5, 1))
        self.ti.bind(focus=lambda ins, v: on_check(self.index, self.cb.active, ins.text) if not v else None)
        self.btn = Button(text='×', size_hint_x=0.15);
        self.btn.bind(on_press=lambda x: on_delete(self.index))
        self.add_widget(self.cb);
        self.add_widget(self.ti);
        self.add_widget(self.btn)


class WishlistScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=dp(10))
        head = BoxLayout(size_hint_y=0.1);
        head.add_widget(Label(text="心愿清单", font_name='CyberFont'))
        add = Button(text="+", size_hint_x=0.2);
        add.bind(on_press=self.add)
        head.add_widget(add);
        self.layout.add_widget(head)
        self.sv = ScrollView();
        self.list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        self.list.bind(minimum_height=self.list.setter('height'));
        self.sv.add_widget(self.list)
        self.layout.add_widget(self.sv);
        self.add_widget(self.layout)

    def on_touch_move(self, touch):
        if touch.x - touch.ox > dp(50): self.manager.current = 'main'

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.wishes = json.load(open(WISH_PATH, 'r', encoding='utf-8')) if os.path.exists(WISH_PATH) else []
        self.list.clear_widgets()
        for i, w in enumerate(self.wishes):
            self.list.add_widget(WishItem(i, w['text'], w['done'], self.delete, self.update_w))

    def add(self, *args):
        self.wishes.append({"text": "新愿望", "done": False}); self.save()

    def update_w(self, idx, done, text=None):
        self.wishes[idx]['done'] = done
        if text: self.wishes[idx]['text'] = text
        self.save()

    def delete(self, idx):
        if 0 <= idx < len(self.wishes):
            self.wishes.pop(idx)
            self.save()

    def save(self):
        with open(WISH_PATH, 'w', encoding='utf-8') as f: json.dump(self.wishes, f, ensure_ascii=False)
        self.refresh()


# --- APP 主程序 ---
class BirthApp(App):
    def build(self):
        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(BirthdayInputScreen(name='input'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(BaziScreen(name='bazi'))
        sm.add_widget(WishlistScreen(name='wishlist'))
        sm.current = 'main' if os.path.exists(JSON_PATH) else 'input'
        return sm


if __name__ == '__main__':
    BirthApp().run()