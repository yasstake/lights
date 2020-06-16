import sys
import numpy as np
from PIL import Image
import pyocr


WHITE_LEVEL = 150
BLANK_LINE_LEVEL = 5
PADDING = 1
PADDING_X = 0
HEADER_LINES = 2
FOOTER_LINES = 1

NONE_LINE = 0
INDEX_LINE = 1
OTHER_LINE = 2

LINE_HEIGHT = 100

CHAR_WIDTH = 16

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

    def find_best_roate(self, file):
        j_max = 0
        r_max = 0
        img = Image.open(file)
        skip = 0

        for r in range(-100, 100):
            rotate = r/400
            j = self.evaluate_rotate(img, rotate)
            if j < j_max:
                skip += 1
            else:
                j_max = j
                r_max = rotate

            if 5 < skip:
                break

        return r_max


    def evaluate_rotate(self, img, r):
        img = img.rotate(r, fillcolor=(255, 255, 255))

        img = np.array(img.convert('L'))
        img = np.where(100 < img, 0, 255)
        x = np.average(img, axis=0)
        y = np.average(img, axis=1)

        x_blank = len(x) - np.count_nonzero(x)
        y_blank = len(y) - np.count_nonzero(y)

        return x_blank + y_blank


    def analyze(self):
        index, other = self.split_image()

        c, w = self.chop_colums(index)
        self.lights_no_start = w[0] - PADDING_X
        self.lights_no_end = c[0] + PADDING_X

        self.lights_name_start = w[1] - PADDING_X
        self.lights_name_end = self.lights_name_start + 350

        c, w = self.chop_colums(other)

        p = 0
        self.lights_pos_start = w[p] - PADDING_X
        self.lights_pos_end = c[p] - PADDING_X

        if c[p] - w[p] < 70:
            p += 2
        else:
            p += 1

        self.lights_type_start = w[p] - PADDING_X
        self.lights_type_end = c[p] - PADDING_X

        p += 1
        self.lights_height_start = w[p] - PADDING_X
        self.lights_height_end = c[p] - PADDING_X

        p += 1
        self.lights_range_start = w[p] - PADDING_X
        self.lights_range_end = c[p] - PADDING_X

        p += 1
        self.lights_structure_start = w[p] - PADDING_X
        self.lights_structure_end = c[p] - PADDING_X

        p += 1
        self.lights_remark_start = w[p] - PADDING_X
        self.lights_remark_end = self.lights_range_start + CHAR_WIDTH * 30

    def make_new_page(self):
        canvas = Image.new('L', (2100, 2300), 255)

        pos = 0
        other_line_index = 0
        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            if self.img_type[index] == INDEX_LINE:
                pos += 1
                other_line_index = 0
                # lights no

                parts = Image.fromarray(img[:, self.lights_no_start:self.lights_no_end])
                canvas.paste(parts, (10, pos*LINE_HEIGHT))

                # lights name
                parts = Image.fromarray(img[:, self.lights_name_start:self.lights_name_end])
                # canvas.paste(parts, (1200, pos*LINE_HEIGHT))
                # canvas.paste(img, (10, pos*LINE_HEIGHT))
            elif self.img_type[index] == OTHER_LINE:
                if other_line_index == 0:
                    # major lights no
                    #parts = Image.fromarray(img[:, self.lights_no_start:self.lights_no_end])
                    #canvas.paste(parts, (70, pos*LINE_HEIGHT))

                    # lights type
                    # print('lights', self.lights_type_start, self.lights_type_end)
                    parts = Image.fromarray(img[:, self.lights_type_start:self.lights_type_end])
                    canvas.paste(parts, (83, pos*LINE_HEIGHT))

                    # lights structure
                    # print('lights type', self.lights_structure_start, self.lights_structure_end)
                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    canvas.paste(parts, (190, pos*LINE_HEIGHT))


                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])

                    canvas.paste(parts, (650, pos * LINE_HEIGHT))
                    #canvas.paste(img, (0, pos*LINE_HEIGHT + 40))
                elif other_line_index == 1:
                    # lights structure
                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    canvas.paste(parts, (190+146, pos*LINE_HEIGHT))

                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    canvas.paste(parts, (650+300, pos * LINE_HEIGHT))
                    #canvas.paste(img, (0, pos*LINE_HEIGHT + 60))

                elif other_line_index == 2:
                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    canvas.paste(parts, (190 + 146 + 133, pos * LINE_HEIGHT))

                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    canvas.paste(parts, (650+300+300, pos * LINE_HEIGHT))
                    #canvas.paste(img, (0, pos*LINE_HEIGHT + 80))
                else:
                    print("out of bound")

                other_line_index += 1

        return canvas

    def rotate_degree(self):
        start_x, end_x = self.chop_lines()

        rad = (end_x - start_x) / self.img.shape[0]
        print("rad", rad)
        rad = np.arctan(rad)
        print(rad)

        rad = np.rad2deg(rad)
        print(rad)

        return rad
        # return rad

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
        start_pos = 0

        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            c, w = self.chop_colums(img)

            in_index = False

            if not start_pos:
                start_pos = w[0] + 30

            if w[0] < start_pos:
                if not in_index:
                    in_index = True
                    self.img_type[index] = INDEX_LINE
                    index_line = np.r_[index_line, img]
                else:
                    print('--MAJRO--')
                    in_index = False
                    self.img_type[index] = OTHER_LINE
                    other_line = np.r_[other_line, img]
            else:
                in_index = False
                self.img_type[index] = OTHER_LINE
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
                if in_white:
                    pass
                else:
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

                    if height < 10:
                        in_line = False
                    elif height < 30:
                        img = self.img[start - PADDING :end + PADDING, :]
                        self.img_lines.append(img)
                        in_line = False
                    else:
                        half = int(height / PADDING)

                        img = self.img[start - PADDING:start + half + PADDING, :]
                        self.img_lines.append(img)

                        img = self.img[start + half - PADDING:end + PADDING, :]
                        self.img_lines.append(img)

                        in_line = False

            line_count += 1


def debug(reader):
    index, other = reader.split_image()

    s, e = reader.chop_colums(index)
    print(s)
    print(e)
    for pos in s:
        index[:, pos] = 230

    for pos in e:
        index[:, pos] = 120

    s, e = reader.chop_colums(other)
    print(s)
    print(e)
    for pos in s:
        other[:, pos] = 230

    for pos in e:
        other[:, pos] = 120

    img = Image.fromarray(index)
    img.save('index.png')

    img = Image.fromarray(other)
    img.save('other.png')


def convert(original_file, new_file):
    reader = Reader()
    r = reader.find_best_roate(original_file)
    print('rotate', r)
    reader.open(original_file, r)

    debug(reader)

    reader.analyze()

    canvas = reader.make_new_page()
    canvas.save(new_file)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        from_file = sys.argv[1]
        to_file = from_file + 'new.png'
    elif len(sys.argv) == 3:
        from_file = sys.argv[1]
        to_file = sys.argv[2]
    else:
        print('from, to')
        exit(1)

    print('convert', from_file, to_file)
    convert(from_file, to_file)
