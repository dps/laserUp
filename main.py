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

  def parse(self, filename, material_height_mm=1.0, design_width_mm=250.0):
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
      interpolate_slice_count = int(data['windowHeight'] / desired_slices)
      if interpolate_slice_count < 1:
        interpolate_slice_count = 1
      eprint("Interpolate every: %d" % interpolate_slice_count)
      retrows = []
      for i in range(0, int(desired_slices)):
        irows = []
        for z in range(0, interpolate_slice_count):
          irows.append(rows.pop(0))
        retrows.append(linear_interpolate(irows))
      eprint("Total slices: %d" % len(retrows))
      return (retrows, data)

class SVGGenerator(object):

  TEMPLATE = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="50.0cm" height="30.0cm" viewBox="0 0 5000 3000"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
 %s

</svg>
  """

  def __init__(self, row_data, json, material_height_mm=1, design_width_mm=250, max_height_mm=30):
    self._material_height_mm = material_height_mm
    self._design_width_mm = design_width_mm
    self._max_height_mm = max_height_mm
    self._row_data = row_data
    self._json = json
    self._scale = (self._max_height_mm * 10.0) / self._json['maxHeight']


  def svg_file(self, row_nums):
    y_offset = 0
    x_offset = 0
    polygon = ""
    for rn in row_nums:
      pg, yadjust = self.svg(rn, y_offset=y_offset, x_offset=x_offset)
      polygon = polygon + pg + "\n"
      y_offset = y_offset + 610 - yadjust
      if y_offset + 600 > 3000:
        y_offset = 0
        x_offset += 2500
    print(self.TEMPLATE % polygon)

  def svg(self, row_num, y_offset=0, x_offset=0):
    DEPTH = 600
    WIDTH = 2500
    row = self._row_data[row_num]
    max_height = max(row)
    max_scaled = max_height * self._scale
    y_offset = y_offset - (500 - max_scaled)
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

    polygon = polygon + '<circle cx="%d" cy="%d" r="32.5" fill="none" stroke="blue"/>' % (100 + x_offset, 550 + y_offset)
    polygon = polygon + '<circle cx="%d" cy="%d" r="32.5" fill="none" stroke="blue"/>' % (2400 + x_offset, 550 + y_offset)

    return polygon, (500 - max_scaled)


if __name__ == "__main__":
    #print("laserUp")
    e = ElevationParser()
    rows, data = e.parse("testdata/catalina.json")
    s = SVGGenerator(rows, data)
    s.svg_file(range(28,59))
