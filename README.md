# Calibration Scheduling

This repository provides some tools to create and analyze calibration schedulings. 

## creation - calibrationScheduling.py

This script is a command line script. The overall usage can be seen in the helppage (calibrationScheduling.py --help)

### a basic example

```calibrationScheduling.py --pumps "(a, 1, 5, 1)" "(b, 3, 12, 3)" --components "(c1, 20, 60, 4)" "(c2, 10, 50, 4)" --error 3 --force```

This initializes an instance with 2 pumps a and b with the settings {1, 2, 3, 4, 5} and {3, 6, 9, 12}, as well as 2 components c1 and c2 with each needing 4 calibration points and the intervalls [20; 60] and [10; 50]. The intervalls are force-rounded to [18; 60] and [9; 51] such that each limit is divisible by the error.

The results are shown in the command line and saved in "./results/".

### output format

The output format is as follows:
- seconds since first model and number of current found ones
- table showing pump-component allocation per measurement
- table showing pump-setting allocation per measurement
- table showing resulting ratios of every pump per measurement
- table showing analysis statistics across calibration

## convergence evaluation and raw interpreter - scheduleInterpreter.py

This script evaluates raw output of programs, converting them to the common output of (non-raw) calibrationScheduling and generates graphs of the convergence over time.

### advanced graphs

One can refine the graphs over a collection of raw output files through editing "./plots.json".

The following snipped should illustrate the idea:
```{
    "evaluation1": {
        "title": "heading",
        "content": {
            "file1": "description1",
            "file2": "description2",
            "file3": "description3"
        }
    }
}
```
file1, file2 and file3 are files in "./", the title will be diplayed above the graph and the legend will be filled with the file descriptions accordingly.

## distribution evaluation - generateIntervalGraphs.py

This script generates intervalgraphs, i.e. graphs visualizing the distribution of the components calibration points over their corresponding interval.
The generation is not yet based on the raw file output but on manual input of the ratios into "./intervalgraphs.json".

The following illustrates its input language:
```{
        "evaluation1": [
        {
            "title": "Component c1",
            "bounds": [20, 80],
            "points": [
                [33],
                [33, 20],
                [33, 80],
                [33, 67]
            ]
        },
        {
            "title": "Component c2",
            "bounds": [20, 80],
            "points": [
                [67],
                [67, 80],
                [67, 20],
                [67, 33]
            ]
        }
    ]
}
```
Where "points" is a (indexed) list of values for each measurement. Thus there are 4 measurements in the example.

# Installation

The repository was setup with a virtual environment. Thus the installation boils down to the following command:
`pip install -r requirements.txt`s
The scripts should work as soon as the command terminates.

This project was developed with python version 3.10.2
Feel free to create an issue following some [guidelines](https://github.com/orgs/community/discussions/147722) if you believe something doesn't work as it should.