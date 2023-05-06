import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from utility import *

class SelectThread(QThread):
    select_result = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.area = None

    def run(self):
        self.area = select_screenshot_area()
        self.select_result.emit(self.area)


class OCRThread(QThread):
    ocr_result = pyqtSignal(str)

    def __init__(self, mode, monitor):
        super().__init__()
        self.mode = mode
        self.monitor = monitor

    def run(self):
        if self.mode == "Pytesseract":
            text = pytesseract_ocr(self.monitor)
            self.ocr_result.emit(text)
        elif self.mode == "Baidu":
            text = baidu_ocr(self.monitor)
            self.ocr_result.emit(text)
        elif self.mode == "PaddleOCR":
            text = paddle_ocr(self.monitor)
            self.ocr_result.emit(text)

class TranslationThread(QThread):
    translation_result = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        text = openai_translate(self.text)
        self.translation_result.emit(text)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR翻译工具")
        self.setGeometry(50, 50, 800, 1200)

        self.monitor_top_edit = QLineEdit(self)
        self.monitor_top_edit.setGeometry(100, 540, 100, 30)
        self.monitor_top_edit.setPlaceholderText("距离顶部")
        self.monitor_left_edit = QLineEdit(self)
        self.monitor_left_edit.setGeometry(210, 540, 100, 30)
        self.monitor_left_edit.setPlaceholderText("距离左侧")
        self.monitor_width_edit = QLineEdit(self)
        self.monitor_width_edit.setGeometry(320, 540, 100, 30)
        self.monitor_width_edit.setPlaceholderText("截图宽度")
        self.monitor_height_edit = QLineEdit(self)
        self.monitor_height_edit.setGeometry(430, 540, 100, 30)
        self.monitor_height_edit.setPlaceholderText("截图高度")

        # 截图显示框
        self.image_label = QLabel(self)
        self.image_label.setGeometry(100, 70, 600, 400)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black")

        # OCR工具选择框
        self.ocr_mode = "Pytesseract"
        self.ocr_combobox = QComboBox(self)
        self.ocr_combobox.addItem("Pytesseract")
        self.ocr_combobox.addItem("Baidu")
        self.ocr_combobox.addItem("PaddleOCR")
        self.ocr_combobox.move(100, 500)
        self.ocr_combobox.currentIndexChanged.connect(self.on_ocr_mode_changed)

        self.ocr_or_translate = "OCR"
        self.ocr_or_translate_combobox = QComboBox(self)
        self.ocr_or_translate_combobox.addItem("仅识别")
        self.ocr_or_translate_combobox.addItem("识别翻译")
        self.ocr_or_translate_combobox.move(210, 500)
        self.ocr_or_translate_combobox.currentIndexChanged.connect(self.on_ocr_or_translate_mode_changed)

        self.select_button = QPushButton("框选截图区域", self)
        self.select_button.setGeometry(320, 500, 150, 30)
        self.select_button.clicked.connect(self.on_select_button_clicked)

        self.ocr_button = QPushButton("RUN", self)
        self.ocr_button.setGeometry(550, 480, 150, 50)
        self.ocr_button.clicked.connect(self.on_ocr_button_clicked)
        
        # OCR 结果显示
        self.result_ocredit = QTextEdit(self)
        self.result_ocredit.setGeometry(100, 580, 600, 100)
        self.result_ocredit.setReadOnly(True)

        # 翻译 结果显示
        self.result_textedit = QTextEdit(self)
        self.result_textedit.setGeometry(100, 700, 600, 450)
        self.result_textedit.setReadOnly(True)


    def on_select_button_clicked(self):
        self.select_thread = SelectThread()
        self.select_thread.select_result.connect(self.on_select_result)
        self.select_thread.start()

    def on_ocr_button_clicked(self):
        self.result_ocredit.clear()
        self.image_label.clear()
        monitor = self.get_monitor()
        self.ocr_thread = OCRThread(self.ocr_mode, monitor)
        self.ocr_thread.ocr_result.connect(self.on_ocr_result)
        self.ocr_thread.start()

    def on_select_result(self, area):
        self.monitor_top_edit.setText(str(area[0]))
        self.monitor_left_edit.setText(str(area[1]))
        self.monitor_width_edit.setText(str(area[2]))
        self.monitor_height_edit.setText(str(area[3]))

    def on_ocr_mode_changed(self):
        self.ocr_mode = self.ocr_combobox.currentText()
        print("当前OCR工具: ", self.ocr_mode)

    def on_ocr_or_translate_mode_changed(self):
        self.ocr_or_translate = self.ocr_or_translate_combobox.currentText()
        print("当前模式: ", self.ocr_or_translate)

    def get_monitor(self):
        if self.monitor_top_edit.text() == "" or self.monitor_left_edit.text() == "" or self.monitor_width_edit.text() == "" or self.monitor_height_edit.text() == "":
            print('使用默认设置{"top": 1237, "left": 610, "width": 1530, "height": 200}')
            monitor = {"top": 1237, "left": 610, "width": 1530, "height": 200}
        else:
            top, left, width, height = int(self.monitor_top_edit.text()), int(self.monitor_left_edit.text()), int(self.monitor_width_edit.text()), int(self.monitor_height_edit.text())
            monitor = {"top": top, "left": left, "width": width, "height": height}
        return monitor

    def on_ocr_result(self, text):
        self.result_ocredit.setText(text)
        self.show_image()
        # 识别并翻译
        if self.ocr_or_translate == "识别翻译":
            self.translation_thread = TranslationThread(text)
            self.translation_thread.translation_result.connect(self.on_translation_result)
            self.translation_thread.start()
        else:
            pass

    def on_translation_result(self, text):
        self.result_textedit.setText(text)

    def show_image(self):       
        pixmap = QPixmap('screenshot.png')
        resized_pixmap = pixmap.scaled(600, 400, Qt.KeepAspectRatio)
        self.image_label.setPixmap(resized_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
