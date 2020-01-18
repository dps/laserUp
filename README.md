# 🏔laserUp
create 3D relief maps for laser cutting.
See https://github.com/dps/peak-map for a UI to generate the raw input data (hosted here: http://singleton.io/peak-map )

![Example](imgs/example.jpg)

## Usage
```
🚀 python laserup.py --help                                                
usage: laserup.py [-h] -i INFILE -t THICKNESS_MM [-m MAX_HEIGHT_MM] -o OUTFILE
                  [-s START_SLICE] [-c SLICE_COUNT] [-f] [-l]

🏔 Create 3D relief map slices for Glowforge. 🌎Generate input files at
http://singleton.io/peak-map/

optional arguments:
  -h, --help            show this help message and exit
  -i INFILE, --input INFILE
                        read JSON input from FILE
  -t THICKNESS_MM, --material_thickness_mm THICKNESS_MM
                        material thickness in mm
  -m MAX_HEIGHT_MM, --max_height_mm MAX_HEIGHT_MM
                        max design height in mm
  -o OUTFILE, --out OUTFILE
                        Output DIRECTORY and file name BASE. e.g. 'foo' ->
                        writes SVG to files foo/foo_0000.svg, foo/foo_0001.svg
                        etc.
  -s START_SLICE, --start_slice START_SLICE
                        First slice number for this sheet
  -c SLICE_COUNT, --slice_count SLICE_COUNT
                        Number of slices for this sheet
  -f, --force           Delete and overwrite existing output if already exists
  -l, --land_only       Ignore rows in source data containing no land (not
                        recommended if your design has multiple islands)
```

## Example
```
$ $ python laserup.py -t 3.175 -i testdata/catalina.json -o out
Source rows containing land: 670 of 1085
Source total slices at this thickness before considering interpolation: 59.900488
Source total slices at this thickness after interpolation: 60.277778
Interpolating every: 18
Total slices: 60
Wrote 4 files to out/
```

```
$ python laserup.py -t 0.508 -i testdata/catalina.json -m 40 -o cata -s 63 -c 225 -f
-f: deleting existing output directory.
Source rows containing land: 670 of 1085
Source total slices at this thickness before considering interpolation: 374.378049
Source total slices at this thickness after interpolation: 361.666667
Interpolating every: 3
Total slices: 361
Wrote 16 files to cata/
```
