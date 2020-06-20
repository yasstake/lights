import glob
import sys

for file in glob.glob(sys.argv[1] + '*.png'):
    print(sys.argv[2] + '/' + file, end='')
    print(':' + file)


print('out:', end='')
for file in glob.glob(sys.argv[1] + '*.png'):
    print(sys.argv[2] + '/' + file, end=' ')

print()

