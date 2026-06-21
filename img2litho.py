# SPDX-FileCopyrightText: 2026 Carter Nelson
#
# SPDX-License-Identifier: MIT

from cadquery.func import *
from PIL import Image, ImageOps

#-- USER CONFIG ---------------------------------------
IMG_FILE = "your_image_file_here.jpg"
PMM = 5         # pixels per mm
ZMIN = 0.0      # height in mm for 255 (brightest) pixel value
ZMAX = 3.0      # height in mm for 0 (darkest) pixel value
BPT = 0.8       # backplane thickness in mm
FW = 2.0        # frame width in mm
FTU = 4.0       # frame upper thickness in mm
FTL = BPT       # frame lower thickness in mm
#------------------------------------------------------

# lists used for storing geometry
top = []   # this will be the image litho surface
left = []
right = []
front = []
back = []
bottom = []

# open image
img = Image.open(IMG_FILE).convert("L")     # open image and convert to 8 bit grayscale
img = ImageOps.flip(img)                    # flip img coords to match cad coords
WPX = img.width
HPX = img.height
print(f"{IMG_FILE} = {WPX}x{HPX} pix")
WMM = (WPX-1) / PMM
HMM = (HPX-1) / PMM
print(f"lithophane size = {WMM}x{HMM} mm")

# return image pixel index and height as mm
def pix2mm(ix, iy):
    xmm = ix / PMM
    ymm = iy / PMM
    zmm = ZMIN + (img.getpixel((ix,iy))/255)*(ZMAX - ZMIN)
    return (xmm, ymm, zmm)

# loop over image pixels and create lithophane surface
print("creating top lithophane faces")
for x in range(WPX-1):
    print(f"{x+1}/{WPX-1}", end="")
    for y in range(HPX-1):
        if not y % 10:
            print(".", end="", flush=True)

        # create list of 4 points
        p = [pix2mm(x+i,y+j) for j in range(2) for i in range(2)]

        # lower triangle
        top.append(face(wire(segment(p[0], p[1]),
                             segment(p[1], p[2]),
                             segment(p[2], p[0])
                            ).close()))
        # upper triangle
        top.append(face(wire(segment(p[1], p[2]),
                             segment(p[2], p[3]),
                             segment(p[3], p[1])
                            ).close()))

        # build edges for other sides
        if x==0:
            if y==0:
                left.append(segment(p[0], (p[0][0], p[0][1], -BPT)))
            left.append(segment(p[0], p[2]))
            if y==HPX-2:
                left.append(segment(p[2], (p[2][0], p[2][1], -BPT)))
        if x==WPX-2:
            if y==0:
                right.append(segment(p[1], (p[1][0], p[1][1], -BPT)))
            right.append(segment(p[1], p[3]))
            if y==HPX-2:
                right.append(segment(p[3], (p[3][0], p[3][1], -BPT)))
        if y==0:
            if x==0:
                front.append(segment(p[0], (p[0][0], p[0][1], -BPT)))
            front.append(segment(p[0], p[1]))
            if x==WPX-2:
                front.append(segment(p[1], (p[1][0], p[1][1], -BPT)))
        if y==HPX-2:
            if x==0:
                back.append(segment(p[2], (p[2][0], p[2][1], -BPT)))
            back.append(segment(p[2], p[3]))
            if x==WPX-2:
                back.append(segment(p[3], (p[3][0], p[3][1], -BPT)))
    print()

# add other side faces and make solid
print("creating side faces")
left = face(wire(left).close())
right = face(wire(right).close())
front = face(wire(front).close())
back = face(wire(back).close())
bottom = face(wire(
    segment((0, 0, -BPT), (0, HMM, -BPT)),
    segment((0, HMM, -BPT), (WMM, HMM, -BPT)),
    segment((WMM, HMM, -BPT), (WMM, 0, -BPT)),
    segment((WMM, 0, -BPT), (0,0,-BPT))
).close())

print("creating solid")
litho = solid(*top, left, right, front, back, bottom)

# border frame
print("adding frame")
inner = face(polygon(
    (0,0,0),(WMM,0,0),(WMM,HMM,0),(0,HMM,0)
))
outer = face(polygon(
    (-FW,-FW,0),(WMM+FW,-FW,0),(WMM+FW,HMM+FW,0),(-FW,HMM+FW,0)
))
border = cut(outer, inner)
frame = extrude(border, (0,0,FTU)) + extrude(border, (0,0,-FTL))

# combine
s = litho + frame

# save
out_file = IMG_FILE.split(".")[0]+".stl"
print("saving to", out_file)
s.export(out_file)

print("DONE")
