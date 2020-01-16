#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import json
import sys

def eprint(arg):
    sys.stderr.write(arg + "\n")

def linear_interpolate(list_of_lists):
  return [(1.0 * sum(e))/len(e) for e in zip(*list_of_lists)]

numeral_points = {
  '0': [(0,0), (25,0), (25,50), (0,50), (0,0)],
  '1': [(25,0), (25,50)],
  '2': [(0,0), (25,0), (25,25), (0,25), (0, 50), (25,50)],
  '3': [(0,0), (25,0), (25,25), (10,25), (25,25), (25, 50), (0,50)],
  '4': [(0,0), (0, 25), (25,25), (25,0), (25,50)],
  '5': [(25,0), (0, 0), (0,25), (25,25), (25,50), (0, 50)],
  '6': [(0, 0), (0,25), (25,25), (25,50), (0, 50), (0, 25)],
  '7': [(0,0), (25, 0), (25,50)],
  '8': [(0, 25), (25,25), (25,0), (0,0), (0,50), (25,50), (25,25)],
  '9': [(25,50), (25,0), (0,0), (0, 25), (25,25)],
}

def digit(ch, xo, yo):
  points = "".join(["%f,%f " % (a + xo, b + yo) for (a,b) in numeral_points[ch]])
  return '<polyline points="%s" fill="none" stroke="red" />' % points

def number_to_svg_fragment(num, xo, yo):
  result = ''
  s = str(num)
  for d in s:
    result = result + digit(d, xo, yo)
    xo += 60
  return result


# JSON file is laid out with top (north) rows first.
#
#
class ElevationParser(object):

  def __init__(self):
      pass

  def parse(self, filename, material_height_mm=1.0, design_width_mm=200.0):
      data = json.load(open(filename, "r"))
      pos = 0
      landRows = 0
      firstPrint = False
      rows = []
      for row in range(0, data['windowHeight']):
          hasLand = False
          row = []
          for col in range(0, data['windowWidth']):
              row.append(data['allHeights']['%s' % pos])
              if data['allHeights']['%s' % pos] > 0:
                hasLand = True
              pos = pos + 1
          if hasLand:
            landRows = landRows + 1
            if not firstPrint:
              firstPrint = True
          rows.append(row)
      eprint("LandRows: %d of %d" % (landRows,data['windowHeight']))
      # interpolate to maintain aspect ratio of the data
      aspect_ratio = (data['windowWidth'] * 1.0) / (data['windowHeight'] * 1.0)
      desired_slices = design_width_mm / (material_height_mm * aspect_ratio)
      eprint("Desired slices: %f" % desired_slices)
      interpolate_slice_count = round(data['windowHeight'] / desired_slices)
      if interpolate_slice_count < 1:
        interpolate_slice_count = 1
        desired_slices = data['windowHeight']
      else:
        desired_slices = data['windowHeight'] / interpolate_slice_count
      eprint("Desired slices after interpolation: %f" % desired_slices)
      eprint("Interpolate every: %d %f" % (interpolate_slice_count, data['windowHeight'] / desired_slices ))
      retrows = []
      for i in range(0, int(desired_slices)):
        irows = []
        for z in range(0, int(interpolate_slice_count)):
          irows.append(rows.pop(0))
        retrows.append(linear_interpolate(irows))
      eprint("Total slices: %d" % len(retrows))
      return (retrows, data)

class SVGGenerator(object):

  TEMPLATE = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="40.0cm" height="24.0cm" viewBox="0 0 5000 3000"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
 %s

</svg>
  """

  def __init__(self, row_data, json, design_width_mm=200, max_height_mm=60):
    self._max_height_px = max_height_mm * 10
    self._row_data = row_data
    self._json = json
    self._scale = (self._max_height_px * 1.0) / self._json['maxHeight']
    self._vspacing_px = 10
    self._workspace_height_px = 3000
    self._workspace_width_px = 2500


  def svg_file(self, row_nums):
    y_offset = 0
    x_offset = 0
    polygon = ""
    for rn in row_nums:
      pg, yadjust = self.svg(rn, y_offset=y_offset, x_offset=x_offset)
      polygon = polygon + pg + "\n"
      y_offset = y_offset + 100 + self._max_height_px + self._vspacing_px - yadjust
      if y_offset + (100 + self._max_height_px - yadjust) > self._workspace_height_px:
        y_offset = 0
        x_offset += self._workspace_width_px
    return (self.TEMPLATE % polygon)

  def svg(self, row_num, y_offset=0, x_offset=0):
    DEPTH = self._max_height_px + 100
    WIDTH = self._workspace_width_px
    row = self._row_data[row_num]
    max_height = max(row)
    max_scaled = max_height * self._scale
    y_offset = y_offset - (self._max_height_px - max_scaled)
    points = [(0 + x_offset,DEPTH + y_offset),(0 + x_offset ,DEPTH - 100 + y_offset)]

    step = (WIDTH * 1.0) / len(row)
    curr = 0.0
    for point in row:
      points.append((x_offset + curr, y_offset + DEPTH - 100 - (point * self._scale)))
      curr = curr + step
    points.append((x_offset + WIDTH, y_offset + DEPTH - 100))
    points.append((x_offset + WIDTH, y_offset + DEPTH))
    l = ["%f,%f " % (a,b) for (a,b) in points]
    polygon = '<polygon points="%s" fill="none" stroke="blue" />' % (''.join(l))
    polygon = polygon + number_to_svg_fragment(row_num, x_offset + 400, y_offset + DEPTH - 80)

    polygon = polygon + '<circle cx="%d" cy="%d" r="40" fill="none" stroke="blue"/>' % (100 + x_offset, DEPTH - 50 + y_offset)
    polygon = polygon + '<circle cx="%d" cy="%d" r="40" fill="none" stroke="blue"/>' % (2400 + x_offset, DEPTH - 50 + y_offset)

    return polygon, (self._max_height_px - max_scaled)


if __name__ == "__main__":
    parser = ArgumentParser(description="Create 3D relief map slices for Glowforge.")
    parser.add_argument("-i", "--input", dest="infile",
                    help="read JSON input from FILE", required=True)
    parser.add_argument("-t", "--material_thickness_mm", dest="thickness_mm", type=float,
                    help="material thickness in mm", required=True)
    parser.add_argument("-m", "--max_height_mm", dest="max_height_mm", type=float,
                    help="max design height in mm", default=60)
    parser.add_argument("-o", "--out", dest="outfile",
                    help="write SVG to FILE")
    parser.add_argument("-s", "--start_slice", dest="start_slice",
                    help="First slice number for this sheet", type=int)
    parser.add_argument("-c", "--slice_count", dest="slice_count",
                    help="Number of slices for this sheet", type=int)
    
    args = parser.parse_args()

    e = ElevationParser()
    rows, data = e.parse(args.infile, material_height_mm=args.thickness_mm)
    s = SVGGenerator(rows, data, max_height_mm=args.max_height_mm)
    this_pass=[x for x in range(0,len(rows))]
    if args.start_slice:
      if not args.slice_count:
        this_pass = [x for x in range(args.start_slice, len(rows))]
      else:
        this_pass = [x for x in range(args.start_slice, args.start_slice + args.slice_count)]
    
    svg = s.svg_file(this_pass)
    if args.outfile == None:
      print(svg)
    else:
      outfile = open(args.outfile, 'w')
      outfile.write(svg)
      outfile.close()
