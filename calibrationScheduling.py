import argparse
import datetime
import os
import clingo
import time
import re
import json
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


class Context:
    pass


class Solution:
    def __init__(self, classicDisplay=False, weights={'aCov':1,'eCov':1}):
        self.classicDisplay = classicDisplay
        self.weights = weights
        self.models = list()
        self.lenModels = 0
        self.t0 = None
        self.modelScores = dict()

        self.resultFile = os.path.join('results', datetime.datetime.now().isoformat(timespec="seconds").replace(":", "") + '.txt')
        os.makedirs('results', exist_ok=True)
        with open(self.resultFile, 'w') as file:
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
        realCoverage = pd.DataFrame(index=list(), columns=['eCov', 'max', 'var'], dtype=int)
        coverage = pd.DataFrame(index=list(), columns=['eCov', 'max', 'var'], dtype=str)
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
            if predicate == 'hasRatio':
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
                r = realRatios[comps == c].values
                r = np.ravel(r[~np.isnan(r)])
                my = r.sum() / r.size
                if d == 0:
                    var = -1
                else:
                    var = np.power(r-my, 2).sum() / r.size / d
                realCoverage.loc[c, 'var'] = var
                coverage.loc[c, 'var'] = int(var)
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
        
        var = int(realCoverage.loc[:, 'var'].sum())

        for df in [comps, settings, ratios, coverage]:
            for i in range(2):
                df.sort_index(axis=i, inplace=True)
        for i in range(2):
            settings.sort_index(axis=i, inplace=True)
        solutions = ['\n'.join(map(lambda x: str(x.astype(str).fillna('').transpose()), [comps, settings, ratios, coverage]))]
        
        return '\n'.join(solutions), realScore, var


    def addModel(self, model, quiet=False, score=-1, now=datetime.datetime.now()):
        self.lenModels += 1

        if self.t0 == None:
            self.t0 = now
        
        timeDiff = int((now-self.t0).total_seconds()//1)

        timeStr = now.time().strftime('%H:%M:%S')
        modelStats = str(model)
        if type(model) != str: 
            score = str(model.cost[0])

        answer  = f'{timeStr} Answer: {self.lenModels}\n'
        answer += f'{timeStr} {modelStats}\n'
        answer += f'{timeStr} Optimization: {score}\n'

        with open(self.resultFile, 'a') as file:
            file.write(answer)
    
        if not self.classicDisplay:
            modelStats, realScore, var = self.traverseModel(model)
            if type(model) != str: 
                score = model.cost[0]
            
            answer  = f'{timeDiff}s # {self.lenModels}\n'
            answer += f'{modelStats}\n'
            answer += f'Optimization: {score}[{realScore}|{var}]\n'

            self.modelScores[timeDiff] = (timeDiff, modelStats, score, realScore, var)
        
        if not quiet: print(answer)

        if type(model) != str: 
            self.models.append((model, model.symbols(atoms=True)))
    

    def finish(self, result):
        self.isOptimal = not result.interrupted
    

    def plot(self, show=True, trueScore=False, variance=False, label=None, color=None, dry=False):
        timeDiffs, modelStats, scores, realScores, vars = np.split(np.array(list(self.modelScores.values())), 5, 1)
        timeDiffs = timeDiffs.squeeze(1).astype(int) + 1
        modelStats = modelStats.squeeze(1)
        scores = scores.squeeze(1).astype(int)
        if trueScore:
            scores = realScores.squeeze(1).astype(int)
        if variance:
            scores = vars.squeeze(1).astype(int)

        if not self.isOptimal:
            timeDiffs = np.concatenate((timeDiffs, [4000]))
            modelStats = np.concatenate((modelStats, ['']))
            scores = np.concatenate((scores, [scores[-1]]))

        xmin = timeDiffs.min()
        xmax = timeDiffs.max()
        ymin = max(1, scores.min() - 50)
        ymax = np.percentile(scores, 90, method='lower') + 50
        # ymax = np.percentile(scores, 100, method='lower') + 50

        if not dry:
            if trueScore:
                plt.plot(timeDiffs, scores, linestyle='--', marker='o', label=label, color=color)
            else:
                plt.plot(timeDiffs, scores, marker='o', label=label, color=color)

            if show: 
                plt.gca().set(xlim=(1, plt.gca().get_xlim()[1]), ylim=(min, ymax))
                plt.xscale('symLog')
                plt.grid()
                plt.show()
        
        return (xmin, xmax), (ymin, ymax)


def processCommandLineArguments():
    def validate(pattern, string, converter):
        if (result:=re.findall(pattern, string)) == list():
            raise argparse.ArgumentTypeError('invalid value')
        return converter(result[0])

    parser = argparse.ArgumentParser(prog='CalibrationScheduling', 
                                     description='')

    # add all arguments
    parser.add_argument('-p', 
                        '--pumps', 
                        nargs='+', 
                        action='extend', 
                        type=lambda s: validate('\((\w+), (\d+), (\d+), (\d+)\)', 
                        s, 
                        lambda x: (str(x[0]), int(x[1]), int(x[2]), int(x[3]))), 
                        help="sequence of pumps according to the scheme (<name>, <startInterval>, <endInterval>, <stepSize>) which needs to be quoted. The intervall is a fully closed one."
    )
    parser.add_argument('-c', 
                        '--components', 
                        nargs='+', 
                        action='extend', 
                        type=lambda s: validate('\((\w+), (\d+), (\d+), (\d+)\)', 
                        s, 
                        lambda x: (str(x[0]), int(x[1]), int(x[2]), int(x[3]))),
                        help="sequence of components according to the scheme (<name>, <startInterval>, <endInterval>, <count>) which needs to be quoted. The intervall is a fully closed one."
    )
    parser.add_argument('-e', 
                        '--error', 
                        default=1, 
                        type=lambda s: validate('\d+', 
                        s, 
                        int),
                        help="An integer specifying the allowed error in the calculation of the ratios. Higher values typically yield lower quality solution but cuts down on execution time and memory usage. Thus higher values might be required for larger problem instances. In general errors exceeding any components interval in forced rounding or errors exceeding half of any components interval in safe rounding should be avoided."
    )
    parser.add_argument('--force', action="store_true")
    parser.add_argument('--safe', action="store_true")
    parser.add_argument('--raw', action="store_true")
    
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
    if args.error == 0:
        parser.error('error must be strictly greater than 0')
    if args.force == args.safe:
        parser.error('either force or safe rounding must be set via "--force" or "--safe" respectively')
    
    return args


def generateFacts(args, templates:dict):
    specificTemplates = dict()
    for type, template in templates.items():
        if type == 'components':
            template = template['modes']["force" if args.force else "safe"]
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
    ctl = clingo.Control(['-c', f'err={args.error}'])
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
    solution = Solution(args.raw, config['weights'])
    if (n:=config['count']) <= 0:
        # solve it and total number of models and time necessary
        t0 = time.time()
        ctl.solve(on_model=solution.addModel, on_finish=solution.finish)
        t1 = time.time() - t0

    else:
        # solve it partially and print every calculated without statistics
        with ctl.solve(yield_=True, on_finish=solution.finish) as handle:
            t0 = time.time()
            for _, model in zip(range(n), handle):
                solution.addModel(model)
            t1 = time.time() - t0
    
    # print(t1, end='s\n')


if __name__ == '__main__':
    main(False)