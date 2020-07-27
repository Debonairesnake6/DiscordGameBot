from PIL import Image, ImageDraw

# Create basic image
x = 500
y = 500
border = 10
columns = 6
rows = 6
image = Image.new('RGBA', (x, y))

# Create border
ImageDraw.Draw(image).rectangle([(0, 0), (x, y)], fill=(26, 9, 0))

# Create Item slots
x = x - (border * 2)
y = y - (border * 2)
item_locations = []
for row in range(rows):
    for column in range(columns):
        x_min = int(border + (x / columns * column))
        y_min = int(border + (x / rows * row))
        x_max = int(border + (x / columns * (column + 1)))
        y_max = int(border + (x / rows * (row + 1)))
        item_locations.append([x_min, y_min, x_max, y_max])
        ImageDraw.Draw(image).rectangle([(x_min, y_min), (x_max, y_max)], fill=(50, 50, 50))
        ImageDraw.Draw(image).rectangle([(x_min + 2, y_min + 2), (x_max - 2, y_max - 2)], fill=(77, 26, 0))

# Highlight item
highlight = 22
x_min = item_locations[highlight][0]
y_min = item_locations[highlight][1]
x_max = item_locations[highlight][2]
y_max = item_locations[highlight][3]
ImageDraw.Draw(image).rectangle([(x_min, y_min), (x_max, y_max)], fill=(255, 255, 255))
ImageDraw.Draw(image).rectangle([(x_min + 2, y_min + 2), (x_max - 2, y_max - 2)], fill=(77, 26, 0))

# Add items
items = [0, 4, 22]
sword = Image.open('../extra_files/icons/sword.png')
sword = sword.resize([70, 70])
for item_spot in items:
    x_min = item_locations[item_spot][0] + 5
    y_min = item_locations[item_spot][1] + 5
    x_max = item_locations[item_spot][2] - 5
    y_max = item_locations[item_spot][3] - 5
    image.paste(sword, [x_min, y_min, x_max, y_max], sword)


image.save('test.png')
