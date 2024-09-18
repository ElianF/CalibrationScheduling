import datetime
from calibrationScheduling import Solution
import re
import os
import itertools
import json
from matplotlib import pyplot as plt
import math


def main(plot=True):
    ylim = [math.inf, 0]

    with open('config.json', 'r') as file:
        config = json.load(file)
    
    files = [file for file in os.listdir(os.getcwd()) if file.endswith('.md') and file != 'ground.txt']

    for filename in files:
        with open(filename, 'r') as file:
            content = file.read()
        
        solution = Solution(weights=config['weights'])
        timePat = '\\d{2}:\\d{2}:\\d{2}'
        pattern = f'({timePat}) Answer: \\d+\\n{timePat} ([\\w|\\W]*?)\\n{timePat} Optimization: (\\d+)\\n'

        for timeStr, model, score in re.findall(pattern, content):
            solution.addModel(model, quiet=plot, score=score, now=datetime.datetime.strptime(timeStr, '%H:%M:%S'))
        
        if plot:
            min, percentile = solution.plot(show=False)
            if min < ylim[0]:
                ylim[0] = min
            if ylim[1] < percentile:
                ylim[1] = percentile
        else:
            input(filename)

    if plot:
        plt.gca().set(ylim=ylim)
        plt.grid
        plt.show()


if __name__ == '__main__':
    main()