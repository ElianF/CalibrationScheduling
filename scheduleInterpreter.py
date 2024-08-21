from calibrationScheduling import Solution
import re



def main():
    with open('solved.txt', 'r') as file:
        content = file.read()
    
    solution = Solution()
    pattern = 'Answer: \\d+\\n([\\w|\\W]*?)Optimization: (\\d+)\\n'
    for model, score in re.findall(pattern, content):
        solution.addModel(model, score)
    
    input('')
        


if __name__ == '__main__':
    main()