import subprocess
import os


def main():
    if os.path.isdir('solves'):
        for filename in os.listdir('solves'):
            os.remove(os.path.join('solves', filename))
    else:
        os.makedirs('solves')
    
    for acc in range(30, 0, -1):
        with open(os.path.join('solves', f'solved_{str(acc).zfill(2)}.txt'), 'w') as file:
            command = f'clingo -c acc={acc} init.cl'
            if os.name == 'posix':
                command = ', ' + command
            subprocess.call(command.split(' '), stdout=file)


if __name__ == '__main__':
    main()