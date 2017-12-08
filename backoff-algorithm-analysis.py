# This is a simpy based  simulation of a M/M/1 queue system
# ***********************
# My Nguyen: 914329026
# Jasmin Adzic: 999883011
# ***********************

# **** INSTRUCTION ****
# To execute the program for both exponential and linear backoff algorithm
# run the following:
# python3 backoff-algorithm-analysis.py

import random
import simpy
import math

RANDOM_SEED = 29
SIM_TIME = 1000000
MU = 1
HOSTS = 10
BUFFER_SIZE = float('inf')
Ts = 1

""" Queue system  """		
class server_queue:
	def __init__(self, env, arrival_rate, Packet_Delay, Server_Idle_Periods, buffer_size, slot_number):
		self.server = simpy.Resource(env, capacity = 1)
		self.env = env
		self.queue_len = 0
		self.flag_processing = 0
		self.packet_number = 0
		self.sum_time_length = 0
		self.start_idle_time = 0
		self.arrival_rate = arrival_rate
		self.Packet_Delay = Packet_Delay
		self.Server_Idle_Periods = Server_Idle_Periods

		self.dropped = 0
		self.processed = 0
		self.buffer_size = buffer_size

		self.collisions = 0
		self.slot_number = slot_number
		
	def process_packet(self, env, packet):
		with self.server.request() as req:
			start = env.now
			yield req
			yield env.timeout(random.expovariate(MU))
			latency = env.now - packet.arrival_time
			self.Packet_Delay.addNumber(latency)
			#print("Packet number {0} with arrival time {1} latency {2}".format(packet.identifier, packet.arrival_time, latency))
			self.queue_len -= 1
			self.slot_number += 1
			self.collision_number = 0

			if self.queue_len == 0:
				self.flag_processing = 0
				self.start_idle_time = env.now
				
	def packets_arrival(self, env):
		# packet arrivals 
		
		while True:
		     # Infinite loop for generating packets
			yield env.timeout(random.expovariate(self.arrival_rate))
			  # arrival time of one packet

			self.packet_number += 1
			  # packet id
			arrival_time = env.now  
			#print(self.num_pkt_total, "packet arrival")
			new_packet = Packet(self.packet_number,arrival_time)
			if self.flag_processing == 0:
				self.flag_processing = 1
				idle_period = env.now - self.start_idle_time
				self.Server_Idle_Periods.addNumber(idle_period)
				#print("Idle period of length {0} ended".format(idle_period))
			
			
			if self.queue_len < self.buffer_size:					
				self.queue_len += 1
				self.processed += 1
				# env.process(self.process_packet(env, new_packet))
			else:
				self.dropped += 1

	

""" Packet class """			
class Packet:
	def __init__(self, identifier, arrival_time):
		self.identifier = identifier
		self.arrival_time = arrival_time
		

class StatObject:
    def __init__(self):
        self.dataset =[]

    def addNumber(self,x):
        self.dataset.append(x)
    def sum(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum
    def mean(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum/n
    def maximum(self):
        return max(self.dataset)
    def minimum(self):
        return min(self.dataset)
    def count(self):
        return len(self.dataset)
    def median(self):
        self.dataset.sort()
        n = len(self.dataset)
        if n//2 != 0: # get the middle number
            return self.dataset[n//2]
        else: # find the average of the middle two numbers
            return ((self.dataset[n//2] + self.dataset[n//2 + 1])/2)
    def standarddeviation(self):
        temp = self.mean()
        sum = 0
        for i in self.dataset:
            sum = sum + (i - temp)**2
        sum = sum/(len(self.dataset) - 1)
        return math.sqrt(sum)


""" Server """
class Server:
	def __init__(self, env, queues):
		self.env = env
		self.queues = queues

		self.success_number = 0
		self.collision_number = 0
		self.current_slot = 0

	def backoff_algorithm(self, env, algorithm):
		while True:

			transmittion = []

			# Iterate over each queue to see if they have pkt to transmit
			for q in self.queues:
				if q.queue_len > 0:
					# Only transmit if slot number of q is the same as current slot
					if q.slot_number == self.current_slot:
						transmittion.append(q)
					# Otherwise, skip that current slot
					elif q.slot_number < self.current_slot:
						q.slot_number = self.current_slot+1

			if len(transmittion) == 1:
				transmittion[0].queue_len -= 1
				transmittion[0].collisions = 0
				transmittion[0].slot_number = self.current_slot+1
				self.success_number += 1
			else:
				self.collision_number += 1

				# Apply backoff algorithm on slot number
				for q in transmittion:
					# Exponential backoff algorithm
					if algorithm == "exp":
						k = min(q.collisions, 10)
						r = random.randint(0, pow(2, k))
					# Linear backoff algorithm
					else:
						k = min(q.collisions, 1024)
						r = random.randint(0, k)

					# Update collisions and slot number
					q.collisions += 1
					q.slot_number += (1 + r) # + q.slot_number

				yield env.timeout(Ts)
				self.current_slot += 1



def simulation(arrival_rates, algorithm):
	random.seed(RANDOM_SEED)

	for lamda in arrival_rates:
		env = simpy.Environment()
		Packet_Delay = StatObject()
		Server_Idle_Periods = StatObject()

		queues = []

		#Create HOSTS queues one for each host
		for q in range(0, HOSTS):
			queues.append(server_queue(env, lamda, Packet_Delay, Server_Idle_Periods, BUFFER_SIZE, 0))
			env.process(queues[q].packets_arrival(env))				#Simulate pkt arrival for each host

		server = Server(env, queues)
		env.process(server.backoff_algorithm(env, algorithm))
		env.run(until=SIM_TIME)

		throughPut = float(server.success_number)/server.current_slot
	
		print('Lamda: ', lamda, '	Success: ', server.success_number, '	collisions: ', server.collision_number, '	Slots: ', server.current_slot, '	throughPut: ', throughPut)

def main():
	arrival_rates = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]
	
	print("*** Exponential Backoff Algorithm ***")
	simulation(arrival_rates, "exp")

	print("*** Linear Backoff Algorithm ***")
	simulation(arrival_rates, "lin")

	
if __name__ == '__main__': main()