import argparse
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
            if self.displayedPredicates != None and predicate not in self.displayedPredicates:
                solutions.remove((predicate, args))
        
        solutions.sort()
        solutions = [f'{predicate}({args})' for predicate, args in solutions]
        out = '\n'.join(solutions)

        return out
    
    def setModel(self, model):
        if self.model:
            return
        self.model = model
        while not self.done:
            time.sleep(0.1) # there may be a better approach to active wating


def processCommandLineArguments():
    def validate(pattern, string, converter):
        if (result:=re.findall(pattern, string)) == list():
            raise argparse.ArgumentTypeError('invalid value')
        return converter(result[0])

    parser = argparse.ArgumentParser(prog='CalibrationScheduling', 
                                     description='')

    # add all arguments
    parser.add_argument('-p', '--pumps', nargs='+', action='extend', type=lambda s: validate('\((\w+), (\d+), (\d+), (\d+)\)', s, lambda x: (str(x[0]), int(x[1]), int(x[2]), int(x[3]))))
    parser.add_argument('-c', '--components', nargs='+', action='extend', type=lambda s: validate('\((\w+), (\d+), (\d+), (\d+)\)', s, lambda x: (str(x[0]), int(x[1]), int(x[2]), int(x[3]))))
    
    args = parser.parse_args()

    # apply semnatic rules
    for name, lo, hi, count in args.components:
        if not (0 <= lo <= hi <= 100):
            parser.error(f'bounds of component {name} must be in interval [0, 100]')
        if count < 2:
            parser.error(f'minimum count of component {name} must be an integer greater or equal to 2')
    for name, start, end, step in args.pumps:
        if not (0 <= start <= end):
            parser.error(f'range of pump {name} must be of the form (name, start, end, step)')
        elif step <= 0:
            parser.error(f'step of pump {name} must be a positive number')
    
    return args


def generateFacts(args, templates:dict):
    for type, template in templates.items():
        i = 0
        while re.search('\{\w+?\}', template) != None:
            template = re.sub('\{\w+?\}', '{x['+str(i)+']}', template, count=1)
            i += 1
        for x in args.__dict__[type]:
            if type == 'pumps':
                for y in range(x[1], x[2]+1, x[3]):
                    yield template.format(x=[x[0], y])
            elif type == 'components':
                yield template.format(x=x)


def main():
    with open('config.json', 'r') as file:
        config = json.load(file)
    
    ctl = clingo.Control()

    # insert facts from command line arguments
    args = processCommandLineArguments()
    facts = generateFacts(args, config['templates'])
    ctl.add('base', [], ' '.join(facts))
    # insert clingo code into ctl
    ctl.load('calibrationScheduling.cl')
    # ground it with some helper methods in Context
    ctl.ground([("base", [])], context=Context())

    # solve it and save model
    # threading is necessary because the solved model will be terminated as soon as setModel terminates
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