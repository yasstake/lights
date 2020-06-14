import numpy as np
from PIL import Image
import pyocr

WHITE_LEVEL = 150
BLANK_LINE_LEVEL = 5
PADDING = 2
HEADER_LINES = 2
FOOTER_LINES = 1


class Reader:
    def __init__(self):
        self.img = None
        self.img_lines = []
        self.col = []

    def chop_lines(self):
        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            c = self.chop_colums(img)
            self.col.append(c)

    def chop_colums(self, img):
        img = np.where(WHITE_LEVEL < img, 255, img)
        img = np.where(img <= WHITE_LEVEL, 0, img)
        column = np.average(img, axis=0)
        height = img.shape[0]
        th = (255 * height*0.99) / height
        column = th < column

        in_char = False
        char_pos = []
        start = 0

        for pos in range(10, len(column)-10):
            if column[pos]:
                if not in_char:
                    in_char = True
                    start = pos
            else:
                if in_char:
                    end = pos
                    width = end - start
                    if 10 < width:
                        char_pos.append(pos)

                in_char = False

        return char_pos

    def text_bb(self, index):
        tools = pyocr.get_available_tools()

        if len(tools) == 0:
            print("No OCR tool found")

        tool = tools[0]

        img = Image.fromarray(np.uint8(self.img_lines[index]))

        res = tool.image_to_string(img,
                                   lang="jpn",
                                   builder=pyocr.builders.WordBoxBuilder(tesseract_layout=4))

        return res

    def open(self, file):
        img = Image.open(file)
        img = img.rotate(0, fillcolor=(255, 255, 255))
        img = np.array(img.convert('L'))
        self.img = img
        img = np.where(WHITE_LEVEL < img, 255, img)

        line_width = img.shape[0]
        level = (line_width - BLANK_LINE_LEVEL) * 255 / line_width

        s = np.average(img, axis=1)
        line = s < level

        in_line = False
        line_count = 0
        start = 0

        for l in line:
            if l:
                if not in_line:
                    start = line_count
                    in_line = True
            else:
                if in_line:
                    end = line_count
                    height = end - start

                    if height < 30:
                        img = self.img[start - PADDING :end + PADDING, :]
                        self.img_lines.append(img)
                    else:
                        half = int(height / PADDING)

                        img = self.img[start - PADDING:start + half + PADDING, :]
                        self.img_lines.append(img)

                        img = self.img[start + half - PADDING:end + PADDING, :]
                        self.img_lines.append(img)

                    in_line = False

            line_count += 1
