# This is a simpy based  simulation of a M/M/1 queue system

import random
import simpy
import math

RANDOM_SEED = 29
SIM_TIME = 1000000
MU = 1
Ts = 1

TOTAL_SLOTS = 0
TOTAL_SUCCESSES = 0
TOTAL_COLLISIONS = 0

def Delayed_Slots(numCollisions):
	# Uncomment line 17 & 18 if running Linear Backoff 
	# K = min(numCollisions, 2014)
	# delaySlots = random.randint(0, K)

	# Uncomment line 22 & 23 if running Exponential Backoff 
	K = min(numCollisions, 10)
	delaySlots = random.randint(0, math.pow(2,K))
	return delaySlots

class csma(object):
	global TOTAL_SLOTS
	global TOTAL_SUCCESSES
	global TOTAL_COLLISIONS

	def __init__(self, env):
		self.env = env

	def getThroughPut(self):
		return (float(TOTAL_SUCCESSES)/TOTAL_SLOTS)


class Node:
	def __init__ (self, env, rate):
		self.N = 0
		self.arrivalRate = rate
		self.packet_number = 0
		self.slotNum = 0
		self.env = env

	def arrivalToBuffer(self, env):
		while True: #infinite look for generating packets
			yield env.timeout(random.expovariate(self.arrivalRate))
			self.packet_number += 1
			arrival_time = env.now


class backOffAlgorithm:
	def __init__ (self, env, nodes, numNodes):
		self.env = env
		self.nodes = nodes
		self.numNodes = numNodes

	def process_packet(self, env):
		global TOTAL_SLOTS
		global TOTAL_SUCCESSES
		global TOTAL_COLLISIONS

		while True:
			yield env.timeout(Ts) #This is the time slot

			duplicates = []
			
			for i in range(0,self.numNodes):
				if self.nodes[i].slotNum == TOTAL_SLOTS:
					duplicates.append(i)

			#Packet successfully transmits
			if len(duplicates) == 1:
				x = duplicates[0]
				if self.nodes[duplicates[0]].packet_number > 0:
					TOTAL_SUCCESSES += 1
					self.nodes[x].packet_number -= 1
					self.nodes[x].slotNum += 1
					self.nodes[x].N = 0
				else:
					self.nodes[x].slotNum += 1

			#if collision detected
			if len(duplicates) > 1:
				for i in range(0,len(duplicates)):
					TOTAL_COLLISIONS += 1
					x = int(duplicates[i])   #index of host that collided
					self.nodes[x].N += 1 
					self.nodes[x].slotNum += Delayed_Slots( self.nodes[x].N ) + 1       

			TOTAL_SLOTS += 1

def main():
	
	arrivalRateList = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]
	numNodes = 10

	for rate in  arrivalRateList:
		env = simpy.Environment()
		c = csma(env)

		nodes = []
		for i in range(0,numNodes):
			nodes.append(Node(env, rate))

		simulator = backOffAlgorithm(env, nodes, numNodes)	

		for i in range(0,numNodes):
			env.process(nodes[i].arrivalToBuffer(env))
		env.process(simulator.process_packet(env))
	
		env.run(until=SIM_TIME)
		
		print ('Throughput for lambda = %f is %f' % (rate,c.getThroughPut()))
		
if __name__ == '__main__': main()