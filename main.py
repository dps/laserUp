import json

# JSON file is laid out with top (north) rows first.
#
#
class ElevationParser(object):

  def __init__(self):
      pass

  def parse(self, filename):
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
      #print("LandRows: %d of %d" % (landRows,data['windowHeight']))
      return (rows, data)

class SVGGenerator(object):

  TEMPLATE = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="25.0cm" height="60.0cm" viewBox="0 0 2500 6000"
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
    offset = 0
    polygon = ""
    for rn in row_nums:
      polygon = polygon + self.svg(rn, y_offset=offset) + "\n"
      offset = offset + 610
    print(self.TEMPLATE % polygon)

  def svg(self, row_num, y_offset=0, x_offset=0):
    DEPTH = 600
    WIDTH = 2500
    points = [(0 + x_offset,DEPTH + y_offset),(0 + x_offset ,DEPTH - 100 + y_offset)]
    row = self._row_data[row_num]
    max_height = max(row)
    max_scaled = max_height * self._scale
    y_offset = y_offset - (500 - max_scaled)

    step = (WIDTH * 1.0) / len(row)
    curr = 0.0
    for point in row:
      points.append((x_offset + curr, y_offset + DEPTH - 100 - (point * self._scale)))
      curr = curr + step
    points.append((x_offset + WIDTH, y_offset + DEPTH - 100))
    points.append((x_offset + WIDTH, y_offset + DEPTH))
    l = ["%f,%f " % (a,b) for (a,b) in points]
    polygon = '<polygon points="%s" fill="none" stroke="blue" />' % (''.join(l))
    polygon = polygon + '<circle cx="100" cy="%d" r="32.5" fill="none" stroke="blue"/>' % (550 + y_offset)
    polygon = polygon + '<circle cx="2400" cy="%d" r="32.5" fill="none" stroke="blue"/>' % (550 + y_offset)

    return polygon


if __name__ == "__main__":
    #print("laserUp")
    e = ElevationParser()
    rows, data = e.parse("testdata/catalina.json")
    s = SVGGenerator(rows, data)
    s.svg_file([300, 569, 570, 571])
