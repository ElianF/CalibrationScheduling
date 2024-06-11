import clingo
from threading import Thread
import time
import re
import json


class Context:
    def id(self, x):
        return x
    def seq(self, x, y):
        return [x, y]


class Model:
    def __init__(self, displayedPredicates):
        self.done = False
        self.model = None
        self.displayedPredicates = displayedPredicates
    
    def __str__(self):
        inp = str(self.model)

        pattern = '(\w+)\((\w+[, \w+]*)\)' # matches: "<predicate>(<attribute>, ...) "
        solutions = re.findall(pattern, inp)

        for predicate, args in solutions.copy():
            if predicate not in self.displayedPredicates:
                solutions.remove((predicate, args))
        
        solutions.sort()
        solutions = [f'{predicate}({args})' for predicate, args in solutions]
        out = ' '.join(solutions)

        return out
    
    def setModel(self, model):
        if self.model:
            return
        self.model = model
        while not self.done:
            time.sleep(0.1) # there may be a better approach to active wating


def main():
    ctl = clingo.Control()

    # insert clingo code into ctl
    with open('calibrationScheduling.cl', 'r') as file:
        ctl.add("base", [], file.read())
    # ground it with some helper methods in Context
    ctl.ground([("base", [])], context=Context())

    # solve it and save model
    # threading is necessary because the solved model will be terminated as soon as setModel terminates
    with open('config.json', 'r') as file:
        config = json.load(file)
    model = Model(config['displayedPredicates'])
    thread = Thread(target=ctl.solve, args=[tuple(), model.setModel])
    thread.start()
    while not model.model:
        time.sleep(0.1) # there may be a better approach to active wating

    # print results to terminal; one may alter the output within the __str__ method of Model
    print(model)

    # terminate program
    model.done = True
    thread.join()


if __name__ == '__main__':
    main()