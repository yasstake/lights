import sys
import numpy as np
from PIL import Image
from PIL import ImageDraw
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

LINE_HEIGHT = 100

CHAR_WIDTH = 17

'''
c[123, 347]
w[90, 190, 356]

c[232, 289, 515, 563, 590, 644]
w[206, 242, 308, 539, 576, 631, 659]
'''

C1 = [134]
W1 = [85, 185]
C2 = [224, 280, 504, 554, 636, 795, 1064]
W2 = [198, 234, 299, 530, 628, 649, 809, 1095]

LIGHT_NUMBER_WIDTH = C1[0] - W1[0]
LIGHT_NAME_OFFSET = W1[1] - W1[0]
LIGHT_NAME_WIDTH = CHAR_WIDTH * 30

LIGHT_TYPE_OFFSET = W2[2] - W1[0]
LIGHT_TYPE_WIDTH = C2[2] - W2[2]

LIGHT_STRUCTURE_OFFSET = W2[5] - W1[0]
LIGHT_STRUCTURE_WIDTH = C2[5] - W2[5]

LIGHT_REMARK_OFFSET = W2[6] - W1[0]
LIGHT_REMARK_WIDTH = CHAR_WIDTH * 18

FIND_OFFSET = 3

OUTPUT_START_OFFSET = 30
OUTPUT_TYPE_OFFSET = OUTPUT_START_OFFSET + 120
OUTPUT_STRUCTURE_OFFSET = OUTPUT_START_OFFSET + 300
OUTPUT_REMARK_OFFSET = OUTPUT_START_OFFSET + 800


def find_pos(pos_array, start):
    start -= FIND_OFFSET

    for pos in pos_array:
        if start <= pos:
            return pos
    return None


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

        for r in range(-200, 200):
            rotate = r/400
            j = self.evaluate_rotate(img, rotate)
            if j < j_max:
                skip += 1
            else:
                j_max = j
                r_max = rotate

            if 100 < skip:
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
        if w[0] < 70:
           start_pos = w[1]
        else:
            start_pos = w[0]

        self.lights_no_start = start_pos
        self.lights_no_end = find_pos(c, self.lights_no_start + LIGHT_NUMBER_WIDTH)
        self.lights_name_start = find_pos(w, start_pos + LIGHT_NAME_OFFSET)
        self.lights_name_end = self.lights_name_start + LIGHT_NAME_WIDTH

        print('ID  ', self.lights_no_start, self.lights_no_end)
        print('name', self.lights_name_start, self.lights_name_end)

        c, w = self.chop_colums(other)

        self.lights_type_start = find_pos(w, start_pos + LIGHT_TYPE_OFFSET)
        self.lights_type_end = find_pos(c, self.lights_type_start + LIGHT_TYPE_WIDTH)

        self.lights_remark_start = find_pos(w, start_pos + LIGHT_REMARK_OFFSET)
        if self.lights_remark_start:
            self.lights_remark_end = self.lights_remark_start + LIGHT_REMARK_WIDTH
        else:
            self.lights_remark_start = 0
            self.lights_remark_end = 0

        self.lights_structure_start = find_pos(w, start_pos + LIGHT_STRUCTURE_OFFSET)
        self.lights_structure_end = find_pos(c, self.lights_structure_start)
        if not self.lights_structure_end:
            self.lights_structure_end = self.lights_structure_start + LIGHT_STRUCTURE_WIDTH

        if self.lights_structure_start == self.lights_remark_start:
            self.lights_structure_end = self.lights_structure_start

        print('TYPE', self.lights_type_start, self.lights_type_end)
        print('STRU', self.lights_structure_start, self.lights_structure_end)
        print('REM ', self.lights_remark_start, self.lights_remark_end)

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
                canvas.paste(parts, (OUTPUT_START_OFFSET, pos*LINE_HEIGHT - int(img.shape[0]/2)))

                # lights name
                parts = Image.fromarray(img[:, self.lights_name_start:self.lights_name_end])
                # canvas.paste(parts, (1200, pos*LINE_HEIGHT))
                # canvas.paste(img, (10, pos*LINE_HEIGHT))

                draw = ImageDraw.Draw(canvas)
                draw.line((0, pos*LINE_HEIGHT + 30, canvas.width, pos*LINE_HEIGHT + 30), fill=200)
                del draw

            elif self.img_type[index] == OTHER_LINE:
                if other_line_index == 0:
                    # major lights no
                    #parts = Image.fromarray(img[:, self.lights_no_start:self.lights_no_end])
                    #canvas.paste(parts, (70, pos*LINE_HEIGHT))

                    parts = Image.fromarray(img[:, self.lights_type_start:self.lights_type_end])
                    canvas.paste(parts, (OUTPUT_TYPE_OFFSET, pos*LINE_HEIGHT - int(img.shape[0]/2)))

                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    canvas.paste(parts, (OUTPUT_STRUCTURE_OFFSET, pos*LINE_HEIGHT - int(img.shape[0]/2)))

                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    canvas.paste(parts, (OUTPUT_REMARK_OFFSET, pos * LINE_HEIGHT - int(img.shape[0]/2)))
                elif other_line_index == 1:
                    # lights structure
                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    width = self.lights_structure_end - self.lights_structure_start
                    canvas.paste(parts, (OUTPUT_STRUCTURE_OFFSET + width, pos*LINE_HEIGHT - int(img.shape[0]/2)))

                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    width = self.lights_remark_end - self.lights_remark_start
                    canvas.paste(parts, (OUTPUT_REMARK_OFFSET + width, pos * LINE_HEIGHT - int(img.shape[0]/2)))
                elif other_line_index == 2:
                    parts = Image.fromarray(img[:, self.lights_structure_start:self.lights_structure_end])
                    width = self.lights_structure_end - self.lights_structure_start
                    canvas.paste(parts, (OUTPUT_STRUCTURE_OFFSET + width*2, pos*LINE_HEIGHT - int(img.shape[0]/2)))

                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    width = self.lights_remark_end - self.lights_remark_start
                    canvas.paste(parts, (OUTPUT_REMARK_OFFSET + width*2, pos * LINE_HEIGHT - int(img.shape[0]/2)))

                elif other_line_index == 3:
                    parts = Image.fromarray(img[:, self.lights_remark_start: self.lights_remark_end])
                    width = self.lights_remark_end - self.lights_remark_start
                    canvas.paste(parts, (OUTPUT_REMARK_OFFSET + width*3, pos * LINE_HEIGHT - int(img.shape[0]/2)))

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

        in_index = False

        for index in range(HEADER_LINES, len(self.img_lines)-FOOTER_LINES):
            img = self.img_lines[index]
            c, w = self.chop_colums(img)

            if not start_pos:
                print('start->', w[0])
                if (w[0] < 60) or (120 < w[0]):
                    start_pos = 110 + CHAR_WIDTH * 3
                else:
                    start_pos = w[0] + CHAR_WIDTH * 3

                print('startpos', start_pos)

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

        print('image lines', line_count, len(self.img_lines))

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
