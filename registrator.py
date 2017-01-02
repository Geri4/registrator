#!/usr/bin/env python

import docker, consul, time


class MyDocker(object):
    def __init__(self):
        self.client = docker.from_env()
        self.nodename = self.client.info()['Name']
    def getConsulAddress(self):
        for container in self.client.containers.list():
            if container.attrs['Name'][1:] == 'consul':
                return container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        return None
    def getContainerList(self):
        return self.client.containers.list()



class MyConsul(object):
    def __init__(self, consulAddress, nodename):
        self.consulAddress = consulAddress
        self.nodename = nodename
        self.connConsul = consul.Consul(host=consulAddress)
        self.agent = self.connConsul.agent

    def getServiceIdSet(self):
        serviceIdSet = set()
        for service in self.connConsul.agent.services():
            serviceIdSet.add(service)
        return serviceIdSet

    def fillServiceList(self, containerList):
        updatedServiceSet = {'consul'}
        for container in containerList:
            self.agent.service.register(container.attrs['Name'][1:], service_id=container.attrs['Id'], address=container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress'], tags=['nginx', 'letsencrypt'])
            updatedServiceSet.add(container.attrs['Id'])
        oldServiceSet = self.getServiceIdSet()
        self.removeUnexistServices(oldServiceSet.difference(updatedServiceSet))

    def removeUnexistServices(self, containerSet):
        for container in containerSet:
            print('Remove service: ', container)
            self.agent.service.deregister(container)

def main():
    while True:

        localDocker = MyDocker()
        #    print(localDocker.getConsulAddress())
        #    print(localDocker.nodename)
        localConsul = MyConsul(consulAddress = localDocker.getConsulAddress(), nodename = localDocker.nodename)
        #    print(localConsul.consulAddress)
        #    print(localConsul.getServiceIdSet())
        localConsul.fillServiceList(containerList = localDocker.getContainerList())
        #    localConsul.registerNode()
        time.sleep(5)

if __name__ == '__main__':
    main()
