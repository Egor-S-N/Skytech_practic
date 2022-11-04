import json
import serial
import serial.tools.list_ports as pl
from serial import Serial
from jsonrpcserver import dispatch, method, Success, Error
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from os import walk
from kivy.core.window import Window
import cashreg


class Program(Widget):
    count = 1
    speed = 9600
    port = "COM3"
    file = ""
    ti_list = {}

    @method
    def TestConnection(name: str = "\\.\COM3", speed: int = 9600, id: int = count):
        try:
            s = Serial(port=name, baudrate=speed, bytesize=serial.EIGHTBITS,
                       stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, timeout=2)
            return Success("OK")
        except:
            return Error("Not connect")

    def inc(self):
        self.count += 1

    def choise_port(self, value):
        self.port = value
        self.ids.enter_adress.text = value

    def portList(self):
        box = StackLayout()
        for item in pl.comports():
            label = Label(
                text=f"Порт: {item.device} VID: {item.vid} PID: {item.pid} Serial number: {item.serial_number}")
            label.size_hint = (0.8, 0.1)

            box.add_widget(label)

            btn = Button(text='выбрать')
            btn.size_hint = (0.2, 0.1)
            btn.bind(on_press=lambda x: self.choise_port(item.device))
            box.add_widget(btn)

        popup = Popup(title='Список COM устройств',
                      size_hint=(None, None),
                      size=(600, 400),
                      )

        popup.content = box
        popup.open()

    def spinner_click(self, value):
        self.speed = int(value)

    def connection_click(self):

        payload = {"jsonrpc": "2.0",
                   "method": "TestConnection",
                   "id": self.count,
                   "params": [self.ids.enter_adress.text, self.speed, self.count]
                   }
        self.inc()

        payload = json.dumps(payload).encode('utf-8')
        response = dispatch((payload))

        self.ids.lab_res.text = str(response)
        self.inc()

    def create_buttons(self):
        self.ids.bl.clear_widgets()
        files = []
        for (dirpath, dirnames, filenames) in walk('templates'):
            files.extend(filenames)
            break

        self.ids.spinner_files.values = files

    def save_to_json(self, instance):

        param = str(instance.text) 
        param = param[5:]
        try:
                data = []
                with open("templates//" + self.file, 'r') as file:
                    content = file.read()
                    data = json.loads(content)
                    data['params'][param] = self.ti_list[param].text

                    with open("templates//" + self.file, 'w') as file:
                        json.dump(data, file, indent=4)
                self.ids.bl.clear_widgets()
                self.open_files(self.file)
        except:
                pass

    def open_files(self, text):
        self.file = text
        with open("templates//" + self.file) as file:
            file_content = file.read()
            template = json.loads(file_content)
            self.ids.enter_messsage.text = json.dumps(template, indent=4)
            id_count = 0
            try:
                box = StackLayout()
                for i in template['params']:
                    lab = Label(text=str(i))
                    lab.size_hint = (1, 0.07)
                    lab.color = (0, 0, 0,1)
                    lab.font_size = 15
                    ti = TextInput(text=str(template['params'][str(i)]))

                    ti.size_hint = (0.4, 0.1)
                    self.ti_list[str(i)] = ti
                    btn = Button(text=f'save {str(i)}')

                    btn.bind(on_press=self.save_to_json)
                    btn.size_hint = (0.6, 0.1)
                    box.add_widget(lab)
                    box.add_widget(ti)
                    box.add_widget(btn)
                    id_count += 1
                self.ids.bl.add_widget(box)

                self.ids.bl.add_widget(box)

            except:
                pass



    def send_message(self, value):
        
        self.ids.lab_res.text = str(cashreg.main(self.ids.enter_adress.text, f"templates//{value}"))
        # cashreg.main()


class MyApp(App):
    def build(self):
        Window.clearcolor = (0.5, 0.5, 0.5, 0.5)
        return Program()


if __name__ == "__main__":
    app = MyApp()

    app.run()

