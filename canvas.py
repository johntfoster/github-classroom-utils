#!/usr/bin/env python

import requests
import json
import re
import os
import time

class canvas():

    def __init__(self, token, verbose=False):

        self.headers = {
            'Authorization' : 'Bearer ' + token,
            "Content-Type" : "application/json",
            "Accept" : "application/json",
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36' 
        }

        self.base_url = 'https://utexas.instructure.com/api/v1/'

        self.id = self.get_id()

        self.students = {}
        self.verbose = verbose

        return

        
    def check_token(self):

        response = requests.get(self.base_url, headers = self.headers)

        return response.status_code == 200


    def create_gradebook_column(self, course_id):

        # response = requests.post(self.base_url + course_id + '/custom_gradebook_columns', 
                                 # headers = self.headers, 
                                 # params = {'column[title]' : 'assignment100'})
        response = requests.delete(self.base_url + 'courses/' + course_id + '/custom_gradebook_columns/2281', 
                                 headers = self.headers)
                                 

        print(response.json())


        return

    def get_id(self):

        response = requests.get(self.base_url + 'course_accounts', headers = self.headers)

        return response.json()[0]['id']


    def get_students(self, course_id):

        response = requests.get(self.base_url + 'courses/' + course_id + '/enrollments', headers = self.headers, params = {'per_page' : 10000})

        students = response.json()

        for student in students:

            self.students[str(student['sis_user_id'])] = student['user_id']


    def get_assignment_id(self, course_id, assignment_name):

        response = requests.get(self.base_url + 'courses/' + course_id + '/assignments', headers = self.headers, params = {'per_page' : 10000})

        assignments = response.json()

        for assignment in assignments:

            if str(assignment['name']) == assignment_name:
                return assignment['id']
        
        print("No assignment id with corresponding name: " + assignment_name)
        return


    def update_assignment_grade(self, course_id, assignment_name, student_id, grade):

        assignment_id = self.get_assignment_id(course_id, assignment_name)

        response = requests.post(self.base_url + 'courses/' + course_id + '/assignments/' + str(assignment_id) + '/submissions/update_grades', 
                headers = self.headers, 
                params = {'grade_data[{}][posted_grade]'.format(student_id) : grade})

        if self.verbose:
            print("Updated grade: " + str(student_id) + " = " + str(grade))

        return


if __name__ == "__main__":
    token = os.environ['CANVAS_TOKEN']
    classroom = canvas(token, verbose=True)
    # classroom.create_gradebook_column('1207029')
    # classroom.get_students('1207029')
    # print(classroom.get_assignment_id('1207029', 'assignment2'))
    # print(classroom.students)
    # classroom.update_assignment_grade('1207029', 'assignment1', classroom.students['sa42284'], 1)

