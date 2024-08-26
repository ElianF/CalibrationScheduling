from calibrationScheduling import Solution
import re
import os
import itertools
import json


def main():
    with open('config.json', 'r') as file:
        config = json.load(file)
    
    files = list(itertools.chain.from_iterable([[os.path.join(root, file) for file in files if file.startswith('solved')] for root, dirs, files in os.walk(os.getcwd())]))
    
    for filename in files:
        with open(filename, 'r') as file:
            content = file.read()
        
        solution = Solution(weights=config['weights'])
        pattern = 'Answer: \\d+\\n([\\w|\\W]*?)Optimization: (\\d+)\\n'
        for model, score in re.findall(pattern, content):
            solution.addModel(model, score)
    
        input(filename)
        


if __name__ == '__main__':
    main()