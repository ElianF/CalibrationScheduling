import argparse
import clingo
import time
import re
import json
import pandas as pd


class Context:
    pass


class Solution:
    def __init__(self, classicDisplay):
        self.classicDisplay = classicDisplay
        self.models = list()
        self.lenModels = 0
 
    def __str__(self):
        return '\n'.join([f'# {n}\n{model}\n' for n, model in enumerate(self)])
    
    def __iter__(self):
        for model, _ in self.models:
            pattern = '(\w+)\((\w+[, \w+]*)\)' # matches: "<predicate>(<attribute>, ...) "
            solutions = re.findall(pattern, model)

            if self.classicDisplay:
                solutions.sort()
                solutions = [f'{predicate}({args})' for predicate, args in solutions]
                if len(solutions) == 0:
                    solutions = ['.']
            else:
                comps = pd.DataFrame(index=list(), columns=list())
                settings = pd.DataFrame(index=list(), columns=list())
                ratios = pd.DataFrame(index=list(), columns=list())
                distances = pd.DataFrame(index=list(), columns=['min', 'max'])
                for predicate, args in solutions.copy():
                    if predicate == 'validMess':
                        m, p, s, c = args.split(',')
                        comps.loc[m, p] = c
                        settings.loc[m, p] = s
                        solutions.remove((predicate, args))
                for predicate, args in solutions.copy():
                    if predicate == 'isRatio':
                        m, c, r = args.split(',')
                        mask = comps.loc[m] == c
                        p = comps.loc[m, mask].index[0]
                        ratios.loc[m, p] = r
                        solutions.remove((predicate, args))
                for predicate, args in solutions.copy():
                    if predicate in ['maximalDistance', 'minimalDistance']:
                        c, d = args.split(',')
                        distances.loc[c, predicate[:3]] = d
                        solutions.remove((predicate, args))
                for df in [comps, settings, ratios, distances]:
                    for i in range(2):
                        df.sort_index(axis=i, inplace=True)
                solutions = ['\n'.join(map(lambda x: str(x.transpose()), [comps, settings, ratios, distances]))]
            
            yield '\n'.join(solutions)

    def addModel(self, model):
        self.lenModels += 1
        print(f'# {self.lenModels}')
        print(model)
        print()
        self.models.append((str(model), model.symbols(atoms=True)))



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
        for n, x in enumerate(args.__dict__[type]):
            if type == 'pumps':
                for y in range(x[1], x[2]+1, x[3]):
                    yield template.format(x=[x[0], y])
            elif type == 'components':
                yield template.format(x=[*x, 2**n])


def main():
    with open('config.json', 'r') as file:
        config = json.load(file)
    
    ctl = clingo.Control()

    # insert facts from command line arguments
    args = processCommandLineArguments()
    facts = list(generateFacts(args, config['templates']))
    ctl.add('base', [], ' '.join(facts))
    # insert clingo code into ctl
    ctl.load('calibrationScheduling.cl')
    # output program for manual analysis
    with open('out.cl', 'w') as file:
        file.write('% initialisation\n')
        file.write('\n'.join(facts))
        file.write('\n\n% programm\n')
        with open('calibrationScheduling.cl', 'r') as cl:
            file.write(cl.read())

    # ground it with some helper methods in Context
    ctl.ground([("base", [])], context=Context())
    ctl.configuration.solve.models = "0"

    solution = Solution(config['classicDisplay'])
    if (n:=config['count']) <= 0:
        # solve it and total number of models and time necessary
        t0 = time.time()
        ctl.solve(on_model=solution.addModel)
        t1 = time.time() - t0
      
        print(solution.lenModels)

    else:
        # solve it partially and print every calculated without statistics
        with ctl.solve(yield_=True) as handle:
            t0 = time.time()
            for _, model in zip(range(n), handle):
                solution.addModel(model)
            t1 = time.time() - t0
    
    print(t1)


if __name__ == '__main__':
    main()
    # try:
    #     main()
    # except:
    #     pass