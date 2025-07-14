from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from functools import partial
from kivy.lang import Builder

import database
Builder.load_file('my.kv')

class LoginScreen(Screen):
    def do_login(self, login_text, password_text):
        user = database.check_user(login_text, password_text)
        if user:
            App.get_running_app().current_user_id = user['id'] # Guarda o ID do usuário
            self.manager.current = 'home'
        else:
            self.show_popup("Erro de Login", "Usuário ou senha incorretos.")

    def do_register(self, login_text, password_text):
        if not login_text or not password_text:
            self.show_popup("Erro de Registro", "Usuário e senha não podem estar vazios.")
            return

        if database.add_user(login_text, password_text):
            self.show_popup("Sucesso", "Usuário registrado com sucesso!")
        else:
            self.show_popup("Erro de Registro", "Usuário já existe.")

    def show_popup(self, title, text):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=text))
        close_button = Button(text='Fechar', size_hint_y=None, height=40)
        content.add_widget(close_button)

        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class HomeScreen(Screen):
    def on_enter(self, *args):
        # Atualiza o saldo total quando a tela é exibida
        user_id = App.get_running_app().current_user_id
        total_saved = database.get_total_saved(user_id)
        self.ids.total_saved_label.text = f'Saldo Total: R$ {total_saved:.2f}'

class GoalsScreen(Screen):
    def on_enter(self, *args):
        self.update_goals_list()

    def add_goal(self, name, amount):
        if not name or not amount:
            print("Nome e valor da meta são obrigatórios.")
            return

        try:
            amount_float = float(amount)
            user_id = App.get_running_app().current_user_id
            database.add_goal(user_id, name, amount_float)
            self.update_goals_list()
            # Limpa os campos de texto após adicionar
            self.ids.goal_name.text = ""
            self.ids.goal_amount.text = ""
        except ValueError:
            print("Valor da meta inválido.")

    def update_goals_list(self):
        self.ids.goals_list.clear_widgets()
        user_id = App.get_running_app().current_user_id
        goals = database.get_goals(user_id)
        for goal in goals:
            goal_text = f"{goal['name']} - R$ {goal['current_amount']:.2f} / R$ {goal['target_amount']:.2f}"
            self.ids.goals_list.add_widget(Label(text=goal_text, size_hint_y=None, height=40))

class ProgressViewScreen(Screen):
    def create_ascii_bar(self, percentage, length=20):
        """Tentativa de criação de uma string de barra de progresso em ASCII."""
        filled_length = int(length * percentage / 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}]"

    def on_enter(self, *args):
        self.update_progress_view()

    def deposit_to_goal(self, goal_id, amount_text, *args):
        try:
            amount_to_add = float(amount_text)
            if amount_to_add > 0:
                database.update_goal_progress(goal_id, amount_to_add)
                self.update_progress_view() 
            else:
                print("O valor deve ser positivo.")
        except ValueError:
            print("Valor de depósito inválido.")

    def update_progress_view(self):
        self.ids.progress_list.clear_widgets()
        user_id = App.get_running_app().current_user_id
        goals = database.get_goals(user_id)

        for goal in goals:
            # Layout para as netas
            goal_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=5)

            # Nome da meta e porcentagem
            current = goal['current_amount']
            target = goal['target_amount']
            percentage = (current / target * 100) if target > 0 else 0
            ascii_bar = self.create_ascii_bar(percentage)
            info_label = Label(text=f"{goal['name']} {ascii_bar} ({percentage:.1f}%)", size_hint_y=None, height=30)

            progress_bar = ProgressBar(max=target, value=current, size_hint_y=None, height=20)

            deposit_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
            amount_input = TextInput(hint_text='Valor a depositar', input_filter='float')
            deposit_button = Button(text='Depositar', size_hint_x=0.4)
            deposit_button.bind(on_press=partial(self.deposit_to_goal, goal['id'], amount_input.text))
            def make_callback(goal_id, text_input):
                return lambda instance: self.deposit_to_goal(goal_id, text_input.text)
            deposit_button.bind(on_press=make_callback(goal['id'], amount_input))


            deposit_layout.add_widget(amount_input)
            deposit_layout.add_widget(deposit_button)

            goal_layout.add_widget(info_label)
            goal_layout.add_widget(progress_bar)
            goal_layout.add_widget(deposit_layout)

            self.ids.progress_list.add_widget(goal_layout)

class MainApp(App):
    current_user_id = None 

    def build(self):
        # Inicializa o banco de dados ao iniciar o app
        database.init_db()

        # Gerenciador de Telas
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(GoalsScreen(name='goals'))
        sm.add_widget(ProgressViewScreen(name='progress_view'))
        return sm

if __name__ == '__main__':
    MainApp().run()