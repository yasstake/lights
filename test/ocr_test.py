import unittest
from loader.ocr import Reader
from PIL import Image

class MyTestCase(unittest.TestCase):
    def test_load(self):
        reader = Reader()
        reader.open('../TESTDATA/light.png')

        r = reader.rotate_degree()
        print(r)

        reader.open('../TESTDATA/light.png', r)
        r = reader.rotate_degree()
        print(r)



    def test_col(self):
        reader = Reader()
        reader.open('../TESTDATA/light.png')
        start_x, end_x = reader.chop_lines()

        print(start_x, end_x)

        for c in reader.col:
            print(c)

    def test_split_image(self):
        reader = Reader()
        reader.open('../TESTDATA/light.png')

        r = reader.rotate_degree()
        reader.open('../TESTDATA/light.png', r)

        index, other = reader.split_image()

        i = reader.chop_colums(index)
        print(i)
        o = reader.chop_colums(other)
        print(o)

        for pos in i:
            index[:, pos] = 200

        for pos in o:
            other[:, pos] = 200

        img = Image.fromarray(index)
        img.save('index.png')

        img = Image.fromarray(other)
        img.save('other.png')

        i = reader.chop_colums(index)
        print(i)
        o = reader.chop_colums(other)
        print(o)


    def test_chop(self):
        reader = Reader()
        reader.open('../TESTDATA/light.png')
        c = reader.chop_colums(reader.img_lines[0])
        print(c)

        c = reader.chop_colums(reader.img_lines[1])
        print(c)

        c = reader.chop_colums(reader.img_lines[2])
        print(c)

        c = reader.chop_colums(reader.img_lines[3])
        print(c)

        c = reader.chop_colums(reader.img_lines[4])
        print(c)

        c = reader.chop_colums(reader.img_lines[5])
        print(c)

        c = reader.chop_colums(reader.img_lines[6])
        print(c)


    def test_ocr(self):
        bb, bb_char = self.bb_list(2)
        print(bb)
        print(bb_char)

        bb, bb_char  = self.bb_list(3)
        print(bb)
        print(bb_char)

        bb, bb_char  = self.bb_list(4)
        print(bb)
        print(bb_char)



    def bb_list(self, index):
        reader = Reader()
        reader.open('../TESTDATA/light.png')

        bb = reader.text_bb(index)

        bb_index = []
        bb_char = []
        last_end = 0
        for b in bb:
            # print(b.position, end='  ')
            start = b.position[0][0]
            space = start - last_end
            last_end = start
            # print(space, end=' ')

            if 30 < space:
                bb_index.append(start)
                bb_char.append(b.content)

            # print(b.content)

        return bb_index, bb_char



    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
