import datetime
from calibrationScheduling import Solution
import re
import os
import itertools
import json
from matplotlib import pyplot as plt
import math


def main(plot=True, show=True):
    os.makedirs('plots', exist_ok=True)

    with open('config.json', 'r') as file:
        config = json.load(file)
    with open('plots.json', 'r') as file:
        plots = json.load(file)

    for real in [False, True]:
        # totalFiles = [file for file in os.listdir(os.getcwd()) if (file.endswith('.md') or file.endswith('.txt')) and file != 'ground.txt']
        # for title, files in [(None, len(totalFiles), totalFiles)]:
        for title, threshold, files in itertools.chain(*[[(test, i, list(map(lambda x: x+'.md', totalFiles))) for i in range(1, 1+len(totalFiles))] for test, totalFiles in plots.items()]):

            xlim = [3650, 1]
            ylim = [math.inf, 0]

            for filename in files:
                with open(filename, 'r') as file:
                    content = file.read()
                
                solution = Solution(weights=config['weights'])
                timePat = '\\d{2}:\\d{2}:\\d{2}'
                pattern = f'({timePat}) Answer: \\d+\\n{timePat} ([\\w|\\W]*?)\\n{timePat} Optimization: (\\d+)\\n'

                for timeStr, model, score in re.findall(pattern, content):
                    solution.addModel(model, score=score, now=datetime.datetime.strptime(timeStr, '%H:%M:%S'))
                
                solution.isOptimal = re.search('OPTIMUM FOUND', content) != None

                if plot:
                    (xmin, xmax), (ymin, ymax) = solution.plot(show=False, label=filename, dry=(filename not in files[:threshold]))
                    if real: solution.plot(show=False, trueScore=True, color=plt.gca().lines[-1].get_color(), dry=(filename not in files[:threshold]))
                    if xmin < xlim[0]:
                        xlim[0] = xmin
                    if xlim[1] < xmax:
                        xlim[1] = xmax
                    if ymin < ylim[0]:
                        ylim[0] = ymin
                    if ylim[1] < ymax:
                        ylim[1] = ymax
                else:
                    input(filename)

            if plot:
                plt.gca().set(xlim=xlim, ylim=ylim)
                plt.xscale('log')
                plt.grid()
                plt.legend()
                plt.savefig(os.path.join('plots', f'{title}{"+" if real else ""}_{str(threshold).zfill(1+int(math.log10(len(files))//1))}.png'))
                if show: 
                    plt.show()
                else:
                    plt.close()


if __name__ == '__main__':
    main(plot=True, show=False)