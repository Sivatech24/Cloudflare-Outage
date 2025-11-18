from PIL import Image, ImageDraw, ImageFont
import csv

csv_file = "cloudflare_ping_report.csv"
output_image = "cloudflare_ping_report.png"

# ---- READ CSV ----
rows = []
with open(csv_file, "r") as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

# ---- SETTINGS ----
font_size = 20
padding = 20
row_height = 40
font = ImageFont.load_default()

# Calculate image size
max_columns = len(rows[0])
max_width = max(len(",".join(r)) for r in rows) * 10

image_width = max_width + padding * 2
image_height = (len(rows) * row_height) + padding * 2

# ---- CREATE IMAGE ----
img = Image.new("RGB", (image_width, image_height), "white")
draw = ImageDraw.Draw(img)

y = padding

for i, row in enumerate(rows):
    text = "   ".join(row)
    color = "black"
    
    # Header bold
    if i == 0:
        color = "blue"

    draw.text((padding, y), text, fill=color, font=font)
    y += row_height

# ---- SAVE IMAGE ----
img.save(output_image)

print("Image saved as:", output_image)
