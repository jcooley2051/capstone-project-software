from subprocess import call

''' start aggregator '''
call('python3 /home/admin/Documents/capstone-project-software/software/Formatting/aggregator.py')

''' start analyzer '''
call('python3 /home/admin/Documents/capstone-project-software/software/testing/analysis.py')

''' start gui '''
call('python3 /home/admin/Documents/capstone-project-software/software/GUI/GUIv5.py')