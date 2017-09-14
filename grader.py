#!/usr/bin/env python


from travis import travis
from canvas import canvas
import csv
import sys
import os

TRAVIS_TOKEN = os.environ['TRAVIS_TOKEN']
CANVAS_TOKEN = os.environ['CANVAS_TOKEN']
TRAVIS_CLASS_NAME = 'PGE323M-Fall2017'
CANVAS_CLASS_ID = '1207029'

# token = os.environ['TRAVIS_TOKEN'] 
classroom = travis(TRAVIS_TOKEN, verbose=True)
classroom.get_classroom_repos(TRAVIS_CLASS_NAME)
classroom.filter_repo_list(sys.argv[-1] + '-.*')
classroom.check_build_status()
bs = classroom.get_build_state()

gradebook = canvas(CANVAS_TOKEN, verbose=True)
gradebook.get_students(CANVAS_CLASS_ID)

# user = re.search('assignment[1-9][0-0]*-(.*)', str(repo['slug'])).group(1)
with open("canvas_template.csv") as f:
    reader = csv.reader(f)
    data = [row for row in reader]


data[0] = data[0] + [sys.argv[-1]]
data[0].remove(data[0][4])

for row in data[1:]:

    repo = TRAVIS_CLASS_NAME + '/' + sys.argv[-1] + '-' + row[4]

    if repo in bs:
        if bs[repo] == 'passed':
            row += [1]
            gradebook.update_assignment_grade(CANVAS_CLASS_ID, sys.argv[-1], gradebook.students[row[3]], 1)
        elif bs[repo] == 'failed':
            row += [0]
            gradebook.update_assignment_grade(CANVAS_CLASS_ID, sys.argv[-1], gradebook.students[row[3]], 0)

    row.remove(row[4])

with open(sys.argv[-1] + '.csv', 'wb') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, delimiter=',', quotechar='"', escapechar='')
    for row in data:
        writer.writerow(row)



