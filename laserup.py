#!/usr/bin/python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import json
import sys
import os
import shutil

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

  def parse(self, filename, material_height_mm=1.0, design_width_mm=200.0, land_only=False):
      data = json.load(open(filename, "r"))
      pos = 0
      landRows = 0
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
          if (not land_only) or hasLand:
            rows.append(row)
      eprint("Source rows containing land: %d of %d" % (landRows, data['windowHeight']))
      # interpolate to maintain aspect ratio of the data
      aspect_ratio = (data['windowWidth'] * 1.0) / (data['windowHeight'] * 1.0)
      desired_slices = design_width_mm / (material_height_mm * aspect_ratio)
      eprint("Source total slices at this thickness before considering interpolation: %f" % desired_slices)
      interpolate_slice_count = round(data['windowHeight'] / desired_slices)
      if interpolate_slice_count < 1:
        interpolate_slice_count = 1
        desired_slices = data['windowHeight']
      else:
        desired_slices = data['windowHeight'] / interpolate_slice_count
      eprint("Source total slices at this thickness after interpolation: %f" % desired_slices)
      eprint("Interpolating every: %d" % (interpolate_slice_count))
      retrows = []
      for i in range(0, len(rows) / int(interpolate_slice_count)):
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
<svg width="40.0cm" height="25.0cm" viewBox="0 0 5000 3125"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
 %s

</svg>
  """

  def __init__(self, row_data, json, design_width_mm=200, max_height_mm=60):
    self._max_height_px = max_height_mm * 10 # there is a bug in the conversion factor here but not fixing until catalina design made.
    self._row_data = row_data
    self._json = json
    self._scale = (self._max_height_px * 1.0) / self._json['maxHeight']
    self._vspacing_px = 10
    self._workspace_height_px = 3000
    self._workspace_width_px = 5000
    self._design_width_px = design_width_mm * (self._workspace_width_px / 400.0)


  def svg_file(self, row_nums, base_name):
    current_file_num = 0
    outfile = open("%s_%04d.svg" % (args.outfile, current_file_num), 'w')
    y_offset = 0
    x_offset = 0
    polygon = ""
    for rn in row_nums:
      pg, yadjust = self.svg(rn, y_offset=y_offset, x_offset=x_offset)
      polygon = polygon + pg + "\n"
      y_offset = y_offset + 100 + self._max_height_px + self._vspacing_px - yadjust
      if y_offset + (100 + self._max_height_px - yadjust) > self._workspace_height_px:
        if x_offset + self._design_width_px*2 > self._workspace_width_px:
          current_file_num += 1
          outfile.write(self.TEMPLATE % polygon)
          outfile.close()
          outfile = open("%s_%04d.svg" % (args.outfile, current_file_num), 'w')
          polygon = ""
          x_offset = 0
        else:
          x_offset += self._design_width_px
        y_offset = 0
    outfile.write(self.TEMPLATE % polygon)
    outfile.close()
    return current_file_num + 1

  def svg(self, row_num, y_offset=0, x_offset=0):
    DEPTH = self._max_height_px + 100
    WIDTH = self._design_width_px
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
    parser = ArgumentParser(description="🏔 Create 3D relief map slices for Glowforge. " +
                            "🌎Generate input files at http://singleton.io/peak-map/",
                            epilog="")
    parser.add_argument("-i", "--input", dest="infile",
                    help="read JSON input from FILE", required=True)
    parser.add_argument("-t", "--material_thickness_mm", dest="thickness_mm", type=float,
                    help="material thickness in mm", required=True)
    parser.add_argument("-m", "--max_height_mm", dest="max_height_mm", type=float,
                    help="max design height in mm", default=60)
    parser.add_argument("-o", "--out", dest="outfile",
                    help="Output DIRECTORY and file name BASE. e.g. 'foo' -> writes SVG to files foo/foo_0000.svg, foo/foo_0001.svg etc.",
                    required=True)
    parser.add_argument("-s", "--start_slice", dest="start_slice",
                    help="First slice number for this sheet", type=int, default=0)
    parser.add_argument("-c", "--slice_count", dest="slice_count",
                    help="Number of slices for this sheet", type=int)
    parser.add_argument("-f", "--force", dest="force", action='store_true',
                    help="Delete and overwrite existing output if already exists")
    parser.add_argument("-l", "--land_only", dest="land_only", action='store_true',
                    help="Ignore rows in source data containing no land (not recommended if your design has multiple islands)")
    
    args = parser.parse_args()

    existing_output = True
    try:
      os.listdir(args.outfile)
    except OSError:
      existing_output = False
    
    if existing_output:
      if args.force:
        eprint('-f: deleting existing output directory.')
        shutil.rmtree(args.outfile)
      else:
        eprint('%s/ already exists. Use -f to overwrite.' % args.outfile)
        quit()

    os.mkdir(args.outfile)

    e = ElevationParser()
    rows, data = e.parse(args.infile, material_height_mm=args.thickness_mm, land_only=args.land_only)
    s = SVGGenerator(rows, data, max_height_mm=args.max_height_mm)
    this_pass=[x for x in range(0,len(rows))]
    if args.start_slice or args.slice_count:
      if not args.slice_count:
        this_pass = [x for x in range(args.start_slice, len(rows))]
      else:
        this_pass = [x for x in range(args.start_slice, args.start_slice + args.slice_count)]
    
    os.chdir(args.outfile)
    num_files = s.svg_file(this_pass, args.outfile)
    eprint("Wrote %d files to %s/" % (num_files, args.outfile))