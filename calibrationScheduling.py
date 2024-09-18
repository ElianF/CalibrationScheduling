import argparse
import datetime
import clingo
import time
import re
import json
import numpy as np
import pandas as pd


class Context:
    pass


class Solution:
    def __init__(self, classicDisplay=False, weights={'aCov':1,'eCov':1}):
        self.classicDisplay = classicDisplay
        self.weights = weights
        self.models = list()
        self.lenModels = 0
        self.t0 = None

        if self.classicDisplay:
            with open('solved.txt', 'w') as file:
                file.write('')
 
    def __str__(self):
        return '\n'.join([f'# {n}\n{model}\n' for n, model in enumerate(self)])
    
    def __iter__(self):
        for model, _ in self.models:
            yield self.traverseModel(str(model))


    def traverseModel(self, model) -> tuple[str, int]:
        pattern = '(\w+)\((\w+[, \w+]*)\)' # matches: "<predicate>(<attribute>, ...) "
        solutions = re.findall(pattern, str(model))

        comps = pd.DataFrame(index=list(), columns=list(), dtype=str)
        settings = pd.DataFrame(index=list(), columns=list(), dtype=int)
        realRatios = pd.DataFrame(index=list(), columns=list(), dtype=int)
        ratios = pd.DataFrame(index=list(), columns=list(), dtype=str)
        realCoverage = pd.DataFrame(index=list(), columns=['eCov', 'max'], dtype=int)
        coverage = pd.DataFrame(index=list(), columns=['eCov', 'max'], dtype=str)
        messCount = dict()
        for predicate, args in solutions.copy():
            if predicate == 'validMess':
                m, p, s, c = args.split(',')
                m = int(m)
                s = int(s)
                messCount[c] = messCount.setdefault(c, 0) + 1
                comps.loc[m, p] = c
                settings.loc[m, p] = s
                solutions.remove((predicate, args))
        for predicate, args in solutions.copy():
            if predicate == 'isRatio':
                m, c, r = args.split(',')
                m = int(m)
                r = int(r)
                mask = comps.loc[m] == c
                p = comps.loc[m, mask].index[0]
                real_r = int(100 * settings.fillna(0).loc[m, p] / sum(settings.fillna(0).loc[m]))
                realRatios.loc[m, p] = real_r
                ratios.loc[m, p] = f'{r}[{real_r}]'
                solutions.remove((predicate, args))
        for predicate, args in solutions.copy():
            if predicate == 'effectiveCoverage':
                c, d = args.split(',')
                d = int(d)
                values = realRatios[comps == c].to_numpy().flatten()
                sortedValues = np.sort(values[~np.isnan(values)]).astype(int).flatten()
                real_d = int((sortedValues[1:]-sortedValues[:-1]).min() * (messCount[c]-1))
                realCoverage.loc[c, 'eCov'] = real_d
                coverage.loc[c, 'eCov'] = f'{d}{[real_d]}'
                solutions.remove((predicate, args))
            elif predicate == 'defComp':
                c, lo, hi, d, n, z = args.split(',')
                lo = int(lo)
                hi = int(hi)
                d = int(d)
                n = int(n)
                z = int(z)
                if c == 'x':
                    continue
                realCoverage.loc[c, 'max'] = d
                coverage.loc[c, 'max'] = d
                solutions.remove((predicate, args))

        realScore = 0
        for c in realCoverage.index:
            if c == 'x':
                continue
            d = realCoverage.loc[c, 'max']
            cov = realCoverage.loc[c, 'eCov']
            realScore += int(self.weights['eCov'] * 100 * d / (cov+1))
        
        for df in [comps, settings, ratios, coverage]:
            for i in range(2):
                df.sort_index(axis=i, inplace=True)
        for i in range(2):
            settings.sort_index(axis=i, inplace=True)
        solutions = ['\n'.join(map(lambda x: str(x.astype(str).fillna('').transpose()), [comps, settings, ratios, coverage]))]
        
        return '\n'.join(solutions), realScore


    def addModel(self, model, score=-1, now=datetime.datetime.now()):
        self.lenModels += 1

        if self.classicDisplay:
            timeStr = datetime.datetime.now().time().strftime('%H:%M:%S')
            answer = f'{timeStr} Answer: {self.lenModels}\n{timeStr} {str(model)}\n{timeStr} Optimization: {str(model.cost[0])}\n'
            with open('solved.txt', 'a') as file:
                file.write(answer)
            print(answer, end='')

        else:
            if self.t0 == None:
                self.t0 = now
            print(f'{int((now-self.t0).total_seconds()//1)}s # {self.lenModels}')

            modelStats, realScore = self.traverseModel(model)
            print(modelStats)
            if type(model) != str: 
                score = model.cost[0]
            print(f'Optimization: {score}[{realScore}]')
            print('')

        if type(model) != str: 
            self.models.append((model, model.symbols(atoms=True)))
        
    
    def plot(self):
        pass



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
    parser.add_argument('-a', '--accuracy', default=1, type=lambda s: validate('\d+', s, int))
    
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
    if args.accuracy == 0:
        parser.error('accuracy must be strictly greater than 0')
    
    return args


def generateFacts(args, templates:dict):
    specificTemplates = dict()
    for type, template in templates.items():
        if type == 'components':
            template = template['modes'][template['active']]
        i = 0
        while re.search('\{\w+?\}', template) != None:
            template = re.sub('\{\w+?\}', '{x['+str(i)+']}', template, count=1)
            i += 1
        specificTemplates[type] = template
    
    maxSum = 0
    for k, x in enumerate(args.__dict__['pumps']):
        p, start, end, step = x
        maxSum += end
        for s in range(start, end+1, step):
            yield specificTemplates['pumps'].format(x=[p, s])
    
    yield f'#const maxSges = {maxSum}.'
    
    for k, x in enumerate(args.__dict__['components']):
        c, lo, hi, n = x
        yield specificTemplates['components'].format(x=[c, n, 2**k, lo, hi, hi, lo])
    
    c, lo, hi, n = ('x', 0, 100, 0)
    k += 1
    yield specificTemplates['components'].format(x=[c, n, 2**k, lo, hi, hi, lo])


def main(dry:bool=False):
    with open('config.json', 'r') as file:
        config = json.load(file)

    # insert facts from command line arguments
    args = processCommandLineArguments()
    ctl = clingo.Control(['-c', f'acc={args.accuracy}'])
    facts = list(generateFacts(args, config['templates']))
    ctl.add('base', [], ' '.join(facts))
    # insert clingo code into ctl
    ctl.load('calibrationScheduling.cl')
    # output program for manual analysis
    with open('init.cl', 'w') as file:
        file.write('% initialisation\n')
        file.write('\n'.join(facts))
        file.write('\n\n% programm\n')
        with open('calibrationScheduling.cl', 'r') as cl:
            file.write(cl.read())

    if dry:
        return

    # ground it with some helper methods in Context
    print('Grounding')
    ctl.ground([("base", [])], context=Context())
    ctl.configuration.solve.models = "0"

    print('Solving')
    solution = Solution(config['classicDisplay'], config['weights'])
    if (n:=config['count']) <= 0:
        # solve it and total number of models and time necessary
        t0 = time.time()
        ctl.solve(on_model=solution.addModel)
        t1 = time.time() - t0

    else:
        # solve it partially and print every calculated without statistics
        with ctl.solve(yield_=True) as handle:
            t0 = time.time()
            for _, model in zip(range(n), handle):
                solution.addModel(model)
            t1 = time.time() - t0
    
    print(t1, end='s\n')


if __name__ == '__main__':
    main(True)
    # try:
    #     main()
    # except:
    #     pass