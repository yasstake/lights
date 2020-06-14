import numpy as np
from PIL import Image
import pyocr

WHITE_LEVEL = 150
BLANK_LINE_LEVEL = 5
PADDING = 1
PADDING_X = 1
HEADER_LINES = 2
FOOTER_LINES = 1

NONE_LINE = 0
INDEX_LINE = 1
OTHER_LINE = 2

class Reader:
    def __init__(self):
        self.img = None
        self.img_lines = []
        self.img_type = []
        self.col = []
        self.col_end = []

        self.lights_no_start = 0
        self.lights_no_end = 0

        self.lights_name_start = 0
        self.lights_name_end = 0

        self.lights_pos_start = 0
        self.lights_pos_end = 0

        self.lights_type_start = 0
        self.lights_type_end = 0

        self.lights_height_start = 0
        self.lights_height_end = 0

        self.lights_range_start = 0
        self.lights_range_end = 0

        self.lights_structure_start = 0
        self.lights_structure_end = 0

        self.lights_remark_start = 0
        self.lights_remark_end = 0

    def analyze(self):
        index, other = self.split_image()

        c, w = self.chop_colums(index)
        self.lights_no_start = w[0] - PADDING_X
        self.lights_no_end = c[0] + PADDING_X

        self.lights_name_start = w[1] - PADDING_X
        self.lights_name_end = self.lights_name_start + 300

        c, w = self.chop_colums(other)

        self.lights_pos_start = w[0] - PADDING_X
        self.lights_pos_end = c[0] - PADDING_X

        self.lights_type_start = w[2] - PADDING_X
        self.lights_type_end = c[2] - PADDING_X

        self.lights_height_start = w[3] - PADDING_X
        self.lights_height_end = c[3] - PADDING_X

        self.lights_range_start = w[4] - PADDING_X
        self.lights_range_end = c[4] - PADDING_X

        self.lights_structure_start = w[5] - PADDING_X
        self.lights_structure_end = c[5] - PADDING_X

        self.lights_remark_start = w[6] - PADDING_X
        self.lights_remark_end = self.lights_range_start + 300


    def rotate_degree(self):
        start_x, end_x = self.chop_lines()

        rad = (start_x - end_x) / 3000

        return rad * 180

    def chop_lines(self):
        self.col = []
        self.col_end = []
        start_x = 0
        end_x = 0

        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            c, w = self.chop_colums(img)
            self.col.append(c)
            self.col_end.append(w)

            if w[0] < 100:
                if start_x == 0:
                    start_x = c[0]
                else:
                    end_x = c[0]

        return start_x, end_x

    def split_image(self):
        index_line = self.img[0:1, :]
        other_line = self.img[0:1, :]
        self.img_type = np.zeros(len(self.img_lines))

        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            c, w = self.chop_colums(img)

            in_index = False
            if w[0] < 100:
                if not in_index:
                    self.img_type[index] = INDEX_LINE
                    index_line = np.r_[index_line, img]
                    in_index = True
                else:
                    self.img_type[index] = OTHER_LINE
                    other_line = np.r_[other_line, img]
            else:
                in_index = False
                other_line = np.r_[other_line, img]

            self.col.append(c)

        return index_line, other_line

    def chop_colums(self, img):
        img = np.where(WHITE_LEVEL < img, 255, img)
        img = np.where(img <= WHITE_LEVEL, 0, img)
        column = np.average(img, axis=0)
        height = img.shape[0]
        th = (255 * height*0.99) / height
        column = th < column

        in_white = False
        char_pos = []
        white_pos = []

        start = 0
        start_pos = 10
        for pos in range(start_pos, len(column)-10):
            if column[pos]:
                if not in_white:
                    in_white = True
                    start = pos
            else:
                if in_white:
                    end = pos
                    width = end - start
                    if 6 < width:
                        white_pos.append(end)
                        if start != start_pos:
                            char_pos.append(start)

                in_white = False

        return char_pos, white_pos

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

    def open(self, file, r=0):
        self.img_lines = []
        self.col = []

        img = Image.open(file)
        img = img.rotate(r, fillcolor=(255, 255, 255))
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
