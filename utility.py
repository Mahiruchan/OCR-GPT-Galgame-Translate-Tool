import base64
import requests
import openai
from mss import mss
from PIL import Image
from paddleocr import PaddleOCR
import pytesseract
import tkinter as tk

api_count = 0

def screenshot(monitor):
    with mss() as sct:
        sct_image = sct.grab(monitor)
        img_path = 'screenshot.png'
        Image.frombytes('RGB', sct_image.size, sct_image.bgra, 'raw', 'BGRX').save(img_path)
    return img_path

def pytesseract_ocr(monitor):
    img_path = screenshot(monitor)
    text = pytesseract.image_to_string(Image.open(img_path), lang='jpn')
    print("OCR 文本：", text)
    return text

def baidu_ocr(monitor):
    img_path = screenshot(monitor)
    with open(img_path, 'rb') as f:
        img_data = f.read()
        image = base64.b64encode(img_data).decode('utf-8')
        ocr_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        #access_token = ""
        #从access_token.txt中读取access_token
        with open("access_token.txt", "r") as f:
            access_token = f.read()
        data = {"image": image, "language_type": "JAP"}
        ocr_url = ocr_url + "?access_token=" + access_token
        response = requests.post(ocr_url, data=data, headers=headers)
        text = ""
        if 'words_result' in response.json() and response.json()['words_result'] != '':
            for i in response.json()['words_result']:
                text = text + i['words']
            print("OCR 文本：", text)
            return text

def paddle_ocr(monitor):
    ocr = PaddleOCR(use_angle_cls=True, lang="japan")
    img_path = screenshot(monitor)
    result = ocr.ocr(img_path, cls=True)
    text = ""
    for res in result:
        for line in res:
            text += line[1][0] + " "
    print("OCR 文本：", text)
    return text

def openai_translate(text):
    global api_count
    with open("openai_apikeys.txt", "r") as f:
        openai_apikeys = f.read().splitlines()
    openai_key = openai_apikeys[api_count % len(openai_apikeys)]
    openai.api_key = openai_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                    {"role": "system", "content": "你是一个翻译家，帮我从由OCR识别而来的可能有错误的日文准确翻译成中文"},
                    {"role": "user", "content": text},])
    translation = response['choices'][0]['message']['content']
    print(api_count, "翻译结果：", translation)
    api_count += 1
    return translation

#当前屏幕缩放比例
SCALE = 1

class SelectionBox(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.configure(bg="gray")
        self.attributes("-alpha", 0.3)
        self.attributes('-fullscreen', True) # 添加全屏属性
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

        self.bind("<Button-1>", self.on_button_press)
        self.bind("<B1-Motion>", self.on_button_motion)
        self.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root

    def on_button_motion(self, event):
        self.end_x = event.x_root
        self.end_y = event.y_root
        self.draw_selection_box()

    def on_button_release(self, event):
        self.quit()

    def draw_selection_box(self):
        if self.start_x and self.start_y:
            canvas = tk.Canvas(self, width=self.winfo_screenwidth(), height=self.winfo_screenheight(), bg="white", highlightthickness=0)
            canvas.place(x=0, y=0)
            canvas.create_rectangle(self.start_x, self.start_y, self.end_x, self.end_y, outline="red", width=2)

def select_screenshot_area():
    root = tk.Tk()
    root.withdraw()

    selection_box = SelectionBox(master=root)
    selection_box.mainloop()

    top = min(selection_box.start_y, selection_box.end_y)*SCALE
    left = min(selection_box.start_x, selection_box.end_x)*SCALE
    width = abs(selection_box.start_x - selection_box.end_x)*SCALE
    height = abs(selection_box.start_y - selection_box.end_y)*SCALE

    root.destroy()
    area = (top, left, width, height)
    return area