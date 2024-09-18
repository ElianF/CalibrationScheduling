import datetime
from calibrationScheduling import Solution
import re
import os
import itertools
import json


def main(fullLog=False):
    with open('config.json', 'r') as file:
        config = json.load(file)
    
    files = list(itertools.chain.from_iterable([[os.path.join(root, file) for file in files if file.startswith('solved')] for root, dirs, files in os.walk(os.getcwd())]))
    
    for filename in files:
        with open(filename, 'r') as file:
            content = file.read()
        
        solution = Solution(weights=config['weights'])
        timePat = '\\d{2}:\\d{2}:\\d{2}'
        pattern = f'({timePat}) Answer: \\d+\\n{timePat} ([\\w|\\W]*?)\\n{timePat} Optimization: (\\d+)\\n'

        iterModels = re.findall(pattern, content)
        
        if not fullLog:
            tmp = dict()
            for timeStr, model, score in iterModels:
                tmp[timeStr] = (timeStr, model, score)
            iterModels = tmp.values()

        for timeStr, model, score in iterModels:
            solution.addModel(model, score, now=datetime.datetime.strptime(timeStr, '%H:%M:%S'))
        
        solution.plot()
    
        input(filename)
        


if __name__ == '__main__':
    main()