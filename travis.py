#!/usr/bin/env python

import requests
import json
import re
import os
import time

class travis():

    def __init__(self, token, verbose=False):

        self.headers = {
            "User-Agent" : "TravisActivate/1.0",
            "Content-Type" : "application/json",
            "Accept" : "application/json",
            "Travis-API-Version" : "3",
            "Authorization" : "token " + token
        }

        self.settings = {
            "settings": {
                "builds_only_with_travis_yml": True,
                "build_pushes": True,
                "build_pull_requests": True,
                "maximum_number_of_builds": 1,
                "auto_cancel_pushes": True
            }
        }

        
        self.build = {
            "request": {
                "branch": "master"
            }
        }


        self.classroom_repo_list = []
        self.build_state = {}

        self.limit = 100
        self.offset = 0

        self.verbose = verbose

        self.sync()
        
    def get_build_state(self):
        return self.build_state

    def get_user(self):
        return requests.get('https://api.travis-ci.com/user/', headers = self.headers)

    def sync(self):
        """ Syncs user's GitHub repositories so they are seen by Travis CI """

        user = self.get_user()
        if not user:
            return

        response = requests.post('https://api.travis-ci.com/' + "user/{}/sync".format(user["id"]),
                                 headers = self.headers)

        if response.status_code != 200:
            return

        # block 'til syncing is done or timeout
        for i in range(20):
            user = self.get_user()
            if not user["is_syncing"]:
                return True
            time.sleep(1)

        return

    def get_classroom_repos(self, classroom_string):

        last_repo = False
        while not last_repo:
            if self.verbose:
                print("Fetching repos: " + str(self.offset) + " -> " + str(self.offset+self.limit))

            repos = requests.get('https://api.travis-ci.com/owner/' + classroom_string + '/repos',
                                    headers = self.headers,
                                    params = {'limit': self.limit, 'offset': self.offset})
            
            if repos.status_code != 200:
                print("Failed to load repo list from Travis: " + repos.content)
                return
            
            self.classroom_repo_list += repos.json()['repositories']

            pagination = repos.json()['@pagination']

            if pagination['is_last']:
                last_repo = True
            else:
                self.limit = pagination['next']['limit']
                self.offset = pagination['next']['offset']

        return


    def filter_repo_list(self, filter_string):

        if not self.classroom_repo_list:
            print("Classroom repository list is empty")
            return

        filtered_repo_list = [repo for repo in self.classroom_repo_list if re.search(filter_string, repo['slug'])]

        if self.verbose:
            print("Filtered list of repos:")
            for repo in filtered_repo_list:
                print("   " + str(repo['slug']))

        self.classroom_repo_list = filtered_repo_list

        return


    def activate_classroom(self):
        
        active = False
        for repo in self.classroom_repo_list:
            if not repo['active']:
                active = True
                owner = str(repo['id'])
                if self.verbose:
                    print("Activating: " + repo['slug'])
                # activate Travis for the repo
                requests.post('https://api.travis-ci.com/repo/' + owner + '/activate',
                              headers = self.headers,
                              data = json.dumps(self.build))
                # set all the build flags 
                requests.patch('https://api.travis-ci.com/repos/' + owner + "/settings",
                               headers = self.headers,
                               data = json.dumps(self.settings))

                # request rebuild
                requests.post('https://api.travis-ci.com/repo/' + owner + "/requests",
                              headers = self.headers,
                              data = json.dumps(self.build))

        if self.verbose:
            if not active:
                print("All repositories active, nothing to do.")

        return


    def trigger_rebuild(self):
        
        for repo in self.classroom_repo_list:
            owner = str(repo['id'])
            if not repo['active']:
                if self.verbose:
                    print("Activating: " + repo['slug'])
                # activate Travis for the repo
                requests.post('https://api.travis-ci.com/repo/' + owner + '/activate',
                              headers = self.headers,
                              data = json.dumps(self.build))
                # set all the build flags 
                requests.patch('https://api.travis-ci.com/repos/' + owner + "/settings",
                               headers = self.headers,
                               data = json.dumps(self.settings))

                # request rebuild
                requests.post('https://api.travis-ci.com/repo/' + owner + "/requests",
                              headers = self.headers,
                              data = json.dumps(self.build))
            else:
                if self.verbose:
                    print("Rebuilding: " + repo['slug'])
                requests.post('https://api.travis-ci.com/repo/' + owner + "/requests",
                              headers = self.headers,
                              data = json.dumps(self.build))
        return


    def check_build_status(self):
        
        for repo in self.classroom_repo_list:
            if repo['active']:
                owner = str(repo['id'])
                # get build status
                request = requests.get('https://api.travis-ci.com/repo/' + owner + '/builds',
                              headers = self.headers)

                # create dict of build state
                if request.status_code == 200:
                    if len(request.json()['builds']) != 0:
                        self.build_state[str(repo['slug'])] = str(request.json()['builds'][0]['state'])
                    else:
                        if self.verbose:
                            print("Triggering build: " + repo['slug'])

                        requests.post('https://api.travis-ci.com/repo/' + owner + "/requests",
                                      headers = self.headers,
                                      data = json.dumps(self.build))

        return 


    def rebuild_failing(self):

        self.check_build_status()

        failed_repo_list = [repo for repo in self.classroom_repo_list if self.build_state[str(repo['slug'])] == 'failed']

        self.classroom_repo_list = failed_repo_list

        self.trigger_rebuild()

        return

    



if __name__ == "__main__":
    token = os.environ['TRAVIS_TOKEN'] 
    classroom = travis(token, verbose=True)
    classroom.get_classroom_repos('PGE323M-Fall2017')
    classroom.filter_repo_list('assignment*-.*')
    classroom.activate_classroom()
    # classroom.rebuild_failing()
