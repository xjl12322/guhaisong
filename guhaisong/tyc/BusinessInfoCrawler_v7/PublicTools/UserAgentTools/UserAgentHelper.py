# coding=utf-8
import yaml
from random import sample
import os

path = os.path.dirname(__file__)


class UserAgent:
    def __init__(self):
        self.UserAgents = yaml.load(open(path + '/UaSources.yml'))

    def UA(self, browser=None):
        aggregate, user_agents = [], self.UserAgents['pc']
        if browser is None:
            [aggregate.extend(UserAgent) for UserAgent in user_agents.values()]
        elif browser not in user_agents.keys():
            raise Exception("No browser found,the browser out of range")
        else:
            aggregate = user_agents[browser]
        return sample(aggregate, 1)[0]

    def Phone(self):
        aggregate, user_agents = [], self.UserAgents['phone']
        [aggregate.extend(UserAgent) for UserAgent in user_agents.values()]
        return sample(aggregate, 1)[0]

    def WeChat(self):
        aggregate = self.UserAgents['phone']['weixin']
        return sample(aggregate, 1)[0]


if __name__ == '__main__':
    start = UserAgent()
