import json

# JSON file is laid out with top (north) rows first.
#
#
class ElevationParser(object):

  def __init__(self):
      pass

  def parse(self, filename):
      data = json.load(open(filename, "r"))
      print(data['windowHeight'])
      print(len(data['allHeights']) / data['windowHeight'])
      pos = 0
      landRows = 0
      firstPrint = False
      for row in range(0, data['windowHeight']):
          hasLand = False
          row = ''
          for col in range(0, data['windowWidth']):
              if data['allHeights']['%s' % pos] > 0:
                row = row + "x"
                hasLand = True
              else:
                row = row + " "
              pos = pos + 1
          if hasLand:
            landRows = landRows + 1
            if not firstPrint:
              print(row)
              firstPrint = True
      print("LandRows: %d of %d" % (landRows,data['windowHeight']))



if __name__ == "__main__":
    print("laserUp")
    e = ElevationParser()
    e.parse("testdata/catalina.json")