# create 32x32 yellow box and save as icon.png

from PIL import Image

img = Image.new('RGB', (32, 32), color = 'yellow')

img.save('icon-yellow.png')