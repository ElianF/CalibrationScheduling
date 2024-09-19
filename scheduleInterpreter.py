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
    
    files = [file for file in os.listdir(os.getcwd()) if (file.endswith('.md') or file.endswith('.txt')) and file != 'ground.txt']

    for filename in files:
        with open(filename, 'r') as file:
            content = file.read()
        
        solution = Solution(weights=config['weights'])
        timePat = '\\d{2}:\\d{2}:\\d{2}'
        pattern = f'({timePat}) Answer: \\d+\\n{timePat} ([\\w|\\W]*?)\\n{timePat} Optimization: (\\d+)\\n'

        for timeStr, model, score in re.findall(pattern, content):
            solution.addModel(model, quiet=plot, score=score, now=datetime.datetime.strptime(timeStr, '%H:%M:%S'))
        
        solution.isOptimal = re.search('OPTIMUM FOUND', content) != None

        if plot:
            min, percentile = solution.plot(show=False, label=filename)
            solution.plot(show=False, trueScore=True, color=plt.gca().lines[-1].get_color())
            if min < ylim[0]:
                ylim[0] = min
            if ylim[1] < percentile:
                ylim[1] = percentile
        else:
            input(filename)

    if plot:
        plt.gca().set(xlim=(0, 3650), ylim=ylim)
        plt.xscale('symLog')
        plt.grid()
        plt.legend()
        plt.show()


if __name__ == '__main__':
    main()