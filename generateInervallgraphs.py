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

    ax.hlines(y=0, xmin=min(0, totalbounds[0]-padding), xmax=min(100, totalbounds[1]+padding), colors='lightgrey')
    ax.hlines(y=0, xmin=bounds[0], xmax=bounds[1], colors='black')
    ax.plot(points, np.zeros_like(points), "ko")
    # for b in bounds:
    #     ax.vlines(b, ymin=-0.5, ymax=0.5, colors='black')
    
    for date in points:
        ax.annotate(str(date), xy=(date, 0), xytext=(date, -0.04))


def main():
    graphsJson = pathlib.Path('intervallgraphs.json')

    graphs = json.loads(graphsJson.read_bytes())

    totalbounds = [100, 0]
    for bound in map(lambda g: g['bounds'], graphs):
        if bound[0] < totalbounds[0]:
            totalbounds[0] = bound[0]
        if bound[1] > totalbounds[1]:
            totalbounds[1] = bound[1]

    fig, ax = plt.subplots(nrows=len(graphs), figsize=(6, 1*len(graphs)), layout="constrained")
    for i, d in enumerate(graphs):
        title, bounds, pointsGroup = [d[key] for key in d]

        drawGraph(ax[i], totalbounds=totalbounds, bounds=bounds, points=pointsGroup[0], title=title)
    plt.savefig('test.png')
    plt.show()


if __name__ == '__main__':
    main()