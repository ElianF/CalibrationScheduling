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
        # totalFiles = [(file, os.path.basename(file)) for file in os.listdir(os.getcwd()) if (file.endswith('.md') or file.endswith('.txt')) and file != 'ground.txt']
        # for name, threshold, title, files in [(None, len(totalFiles), None, totalFiles)]:
        for name, threshold, title, files in itertools.chain(*[[(test, i, db['title'], list(map(lambda x: (x[0]+'.md', x[1]), db['content'].items()))) for i in range(1, 1+len(db['content']))] for test, db in plots.items()]):

            # if name not in []:
            #     continue

            xlim = [1*3600 + 50, 1]
            ylim = [math.inf, 0]

            for filename, label in files:
                if not os.path.exists(filename):
                    break

                with open(filename, 'r') as file:
                    content = file.read()
                
                solution = Solution(weights=config['weights'])
                timePat = '\\d{2}:\\d{2}:\\d{2}'
                pattern = f'({timePat}) Answer: \\d+\\n{timePat} ([\\w|\\W]*?)\\n{timePat} Optimization: (\\d+)\\n'

                for timeStr, model, score in re.findall(pattern, content):
                    solution.addModel(model, score=score, now=datetime.datetime.strptime(timeStr, '%H:%M:%S'))
                
                solution.isOptimal = re.search('OPTIMUM FOUND', content) != None

                if plot:
                    dry = (filename not in [filename for filename, _ in files][:threshold])
                    (xmin, xmax), (ymin, ymax) = solution.plot(show=False, label=label, dry=dry)
                    if real: solution.plot(show=False, trueScore=True, color=plt.gca().lines[-1].get_color(), dry=dry)
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
            else:
                if plot:
                    plt.gca().set(xlim=xlim, ylim=ylim)
                    plt.xscale('log')
                    plt.xlabel('time [s]')
                    plt.ylabel('score [a.u.]')
                    plt.grid()
                    if all([label != '' for _, label in files]):
                        plt.legend()
                    plt.title(title)
                    plt.savefig(os.path.join('plots', f'{title.replace(" ", "-")}{"+" if real else ""}_{str(threshold).zfill(1+int(math.log10(len(files))//1))}.png'))
                    if show: 
                        plt.show()
                    else:
                        plt.close()


if __name__ == '__main__':
    main(plot=True, show=False)