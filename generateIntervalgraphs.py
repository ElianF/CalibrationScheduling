from matplotlib import pyplot as plt
import json
import pathlib
import numpy as np


def drawGraph(ax, totalbounds:list[int], bounds:list[int], points:list[int], title:str, padding:int=2):
    ax.set_title(title, loc='left')

    ax.margins(y=0.1)
    # Remove the y-axis and some spines.
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    ax.spines[["left", "top", "right", "bottom"]].set_visible(False)

    ax.hlines(y=0, xmin=max(0, totalbounds[0]-padding), xmax=min(100, totalbounds[1]+padding), colors='lightgrey')
    ax.hlines(y=0, xmin=bounds[0], xmax=bounds[1], colors='black')
    
    ax.plot(points, np.zeros_like(points), "ko")
    for date in points:
        ax.annotate(str(date), xy=(date, 0), xytext=(date, -0.04))


def main(show=False):
    graphsJson = pathlib.Path('intervalgraphs.json')
    savePath = lambda name: pathlib.Path('intervalgraphs', name+'.png')
    savePath('').parent.mkdir(exist_ok=True)

    graphsJson = json.loads(graphsJson.read_bytes())

    for name, graphs in graphsJson.items():
        totalbounds = [100, 0]
        for bound in map(lambda g: g['bounds'], graphs):
            if bound[0] < totalbounds[0]:
                totalbounds[0] = bound[0]
            if bound[1] > totalbounds[1]:
                totalbounds[1] = bound[1]

        for j in range(len(graphs[0]['points'])):
            fig, ax = plt.subplots(nrows=len(graphs), figsize=(6, 1*len(graphs)), layout="constrained")
            for i, d in enumerate(graphs):
                title, bounds, pointsGroup = [d[key] for key in d]

                drawGraph(ax[i], totalbounds=totalbounds, bounds=bounds, points=pointsGroup[j], title=title)
            plt.savefig(str(savePath('_'.join([name, str(j)]))))
            if show: plt.show()


if __name__ == '__main__':
    main(show=False)