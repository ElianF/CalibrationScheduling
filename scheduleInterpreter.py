from calibrationScheduling import Solution
import re



def main():
    with open('solved.txt', 'r') as file:
        content = file.read()
    
    solution = Solution(False)
    pattern = 'Answer: \\d+\\n([\\w|\\W]*?)Optimization: \\d+\\n'
    for model in re.findall(pattern, content):
        solution.addModel(model, False)
        


if __name__ == '__main__':
    main()