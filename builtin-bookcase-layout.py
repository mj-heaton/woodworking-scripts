from dataclasses import dataclass
from rectpack import newPacker
import matplotlib.pyplot as plt


width = 1345
height = 1600
depth = 300

number_columns = 2
number_shelves = [5, 4]


# width = 960
# height = 960
# depth = 350
# number_columns = 5
# number_shelves = [6, 6, 6, 6, 6]

blade_width = 3
sheet_thickness = 18

assert(len(number_shelves) == number_columns)


@dataclass
class Piece:
    width: int
    height: int
    name: str
    thickness: int = 18

    def __repr__(self) -> str:
        return f"Piece({self.width}, {self.height}, {self.name}, {self.thickness})"

    def __str__(self) -> str:
        return f"Piece `{self.name}`: {self.width} x {self.height} x {self.thickness}"

    def area(self) -> int:
        return self.width * self.height


# 1. Create a list of pieces
side_left = Piece(height - 2 * sheet_thickness, depth, "side_left")
side_right = Piece(height - 2 * sheet_thickness, depth, "side_right")

# The width of the top pieces is half the width of the cabinet minus the thickness of the side pieces
top = Piece(width , depth, "top")
bottom = Piece(width, depth, "bottom")

n_shelves = sum(number_shelves)
n_centres = number_columns - 1

width_consumed_by_verticals = sheet_thickness * (2 + n_centres)

shelve_width = (width - width_consumed_by_verticals) / number_columns

shelves = [Piece(shelve_width, depth, f"shelf_{i}") for i in range(n_shelves)]

# The height of the centre piece is the height of the cabinet minus the thickness of the top and bottom pieces
centre_height = height - 2 * sheet_thickness
centres = [Piece(centre_height, depth, f"centre_{i}") for i in range(n_centres)]

all_pieces = [side_left, side_right, top, bottom] + shelves + centres

print(f"Require a total of {len(all_pieces)} pieces:")
for piece in all_pieces:
    print(piece)

print(f"Total area: {sum([piece.area() for piece in all_pieces]):,.2f}mm")
full_size_board_area = 2440 * 1220
n_sheets = sum([piece.area() for piece in all_pieces]) / full_size_board_area
print(f"Estimate of total boards required: {n_sheets:,.2f} (2440 x 1220)")

packer = newPacker()

rectangles = [(p.width, p.height) for p in all_pieces]
sheets = [(2440, 320) for _ in range(7)]

# Add the rectangles to the packer, taking the blade width into account
for r in all_pieces:
    packer.add_rect(r.width + blade_width, r.height + blade_width, rid=r.name)

# Add the sheets (bins) to the packer
for s in sheets:
    packer.add_bin(*s)

# Start packing
packer.pack()

# Full rectangle list
packed_rectangles = list(packer.rect_list())

print(f"Total packed rectangles: {len(packed_rectangles)}")

if len(packed_rectangles) != len(all_pieces):
    print(f"Error: {len(packed_rectangles)} rectangles packed, but {len(all_pieces)} required")
    exit(1)

for rect in packed_rectangles:
    b, x, y, w, h, rid = rect
    # b is the bin index, x,y are the coordinates
    # w,h are the rectangle dimensions, rid is the rectangle id
    print(f"Bin: {b}, x: {x}, y: {y}, w: {w}, h: {h}, id: {rid}")

# Number of sheets
n_sheets = len(sheets)

# Create a separate plot for each sheet
for i in range(n_sheets):
    fig, ax = plt.subplots(figsize=(12, 8))
    # Filter rectangles for the current sheet
    rects_for_sheet = [rect for rect in packed_rectangles if rect[0] == i]

    # Colors for different pieces
    colors = plt.cm.get_cmap('tab20', len(rects_for_sheet))

    for j, rect in enumerate(rects_for_sheet):
        _, x, y, w, h, rid = rect
        ax.add_patch(plt.Rectangle((x, y), w, h, edgecolor='black', facecolor=colors(j), fill=True))
        # Adding rectangle ID text in the middle of the rectangle
        text_x, text_y = x + w / 2, y + h / 2
        ax.text(text_x, text_y, rid, ha='center', va='center', color='white', fontsize=8)

    ax.set_xlim(0, sheets[i][0])
    ax.set_ylim(0, sheets[i][1])
    ax.set_aspect('equal')
    ax.set_title(f'Visualization of Shelf Cuts on Board {i+1}')
    plt.show()

def generate_openscad_code(pieces: list[Piece], width, height):
    openscad_code = "union() {\n"

    # Function to create a cube in OpenSCAD format
    def cube_str(x, y, z, w, h, d, name):
        return f"    // {name}\n    translate([{x}, {y}, {z}]) cube([{w}, {d}, {h}]);\n"

    # Assume all pieces start from the bottom left front corner (0,0,0)
    for piece in pieces:
        if 'side' in piece.name:
            x = 0 if 'left' in piece.name else width - piece.thickness
            y = 0
            z = 0
            openscad_code += cube_str(x, y, z, piece.thickness, piece.height, piece.thickness, piece.name)
        elif 'top' in piece.name or 'bottom' in piece.name:
            x = 0
            y = 0 if 'bottom' in piece.name else height - piece.thickness
            z = 0
            openscad_code += cube_str(x, y, z, width, piece.thickness, piece.thickness, piece.name)
        elif 'shelf' in piece.name:
            # Example positioning for shelves. Adjust based on your design needs.
            shelf_height = 200  # adjust this based on actual positioning logic
            x = 0
            y = shelf_height
            z = 0
            openscad_code += cube_str(x, y, z, piece.width, piece.thickness, piece.thickness, piece.name)
        elif 'centre' in piece.name:
            # Position centers. Adjust according to your layout.
            centre_x_position = 200  # example positioning, adjust as needed
            x = centre_x_position
            y = 0
            z = 0
            openscad_code += cube_str(x, y, z, piece.thickness, height, piece.thickness, piece.name)

    openscad_code += "}\n"
    return openscad_code

scad_code = generate_openscad_code(all_pieces, width, height)

with open('cabinet.scad', 'w') as f:
    f.write(scad_code)
