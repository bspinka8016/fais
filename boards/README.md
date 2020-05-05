# Boards

## How to add boards

To add a board, simply make a directory for the board in here. Create two
files:

+ `board.csv`
+ `board.jpg`

### board.csv

This file needs to contain a list of all snakes and ladders as `start,end`.
There is no distinction between `snakes` and `ladders` other than that for
`snakes`, `end` is less than `start` and for ladders, `end` is greater than
`start`. Sample file:

```csv
1,10
15,30
31,16
90,44
```

This shows a board where there are two ladders, one from 1 to 10 and the other
from `15` to `30` and two snakes, one from `31` to `16` and one from `90` to
`44`.


### board.jpg

This file must be an `800x800` pixels image with no padding at all. Each square
must be `80x80` pixels. It must follow the standard zig zag pattern of snakes
and ladders as show below.

```
   100   99   98   97   96   95   94   93   92   91

    81   82   83   84   85   86   87   88   89   80

    80   79   78   77   76   75   74   73   72   71

    61   62   63   64   65   66   67   68   69   70

    60   59   58   57   55   55   54   53   52   51

    41   42   43   44   46   45   47   48   49   50

    40   39   38   37   35   36   34   33   32   31

    21   22   23   24   26   25   27   28   29   30

    20   19   18   17   15   16   14   13   12   11

     1    2    3    4    5    5    7    8    9   10
```
