import simpy
import numpy as np, matplotlib.pyplot as plt


env = simpy.Environment()


tid = 60
lambda_faktor = 1
request_count = 0 
timeactive = 10
antall_aktive = 1
antall_interruptions = 0
liste_over_aktive = []
# m = 5
n = 5

#Oppgave 5
price_time_low = 1
price_time_medium = 1
price_time_high = 2
price = 0

#Oppgave 7
num_replications = 10

gsla_violation = False
time_until_gsla_violation = None

active_user_bool = False

price_low = 0.1
price_medium = 1
price_high = 5
cost_server = 0
cost_user = 0
energy_per_user = 0.2


aktive_servere = simpy.Container(env, init=2, capacity=10)

#A.8
datacenter_quality_list = [] #Used to plot the quality level in data center. 
datacenter_price_list = [] #Used to plot the price over time in the data center.
time_list_new = [] #Used to plot the time over time in the data center.   

#A.1
def user3_generator(env):
    while True:
        yield env.timeout(np.random.exponential(1/lambda_faktor))
        global request_count
        request_count += 1
        # print(f"Generated user number [{request_count}] at time {env.now}")
        env.process(user3(request_count, env))


#A.4
def user3(antall_genererte, env):
    pid = env.active_process    
    try:
        global antall_aktive, gsla_violation, time_until_gsla_violation
        # # if antall_aktive > 50:
        bandwidth4 = min(1,(aktive_servere.level)*n/antall_aktive)
        # if MOS_Score(antall_aktive) <= 1:
        if bandwidth4 < 0.8:
            gsla_violation = True
            time_until_gsla_violation = env.now
            # print(f"####################|GSLA violation at time {env.now}|####################")
        
        if bandwidth4 < 0.5:
            if aktive_servere.level < aktive_servere.capacity:
                yield env.process(add_server())
                env.process(user3(antall_genererte, env))

            else:
                # print(f"no more servers available, user [{antall_genererte}] denied access")
                # print(f"antall aktive: {antall_aktive-1} \n")
                return

        else:
            global active_user_bool
            antall_aktive = antall_aktive + 1
            liste_over_aktive.append(pid)
            bandwidth = min(1,(aktive_servere.level)*n/antall_aktive)
            active_user_bool = True
            datacenter_quality_list.append(bandwidth)
            datacenter_price_list.append(price)
            time_list_new.append(env.now)
            # print(f"User {request_count} [{pid}], granted access and started at time {env.now}, bandwidth is now {bandwidth} and antall aktive is {antall_aktive-1} \n")
            yield env.timeout(timeactive)
            liste_over_aktive.remove(pid)
            antall_aktive = antall_aktive - 1
            bandwidth2 = min(1,(aktive_servere.level)*n/(antall_aktive))
            # print(f"User [{pid}] left at time {env.now}, bandwidth is now {bandwidth2} and antall aktive is {antall_aktive-1} \n")
            yield env.process(remove_server())
            if bandwidth2 < 1:
                for i in liste_over_aktive:
                    i.interrupt()

    except simpy.Interrupt:
            # user3(k, env)
            liste_over_aktive.remove(pid)
            antall_aktive = antall_aktive - 1
            global antall_interruptions
            antall_interruptions += 1
            env.process(user3(antall_genererte, env))
            # print(f"User [{request_count}] and pid {pid}interrupted at time {env.now}, interruption no. [{antall_interruptions}]") #, bandwidth is now {bandwidth3} \n
    


def add_server(): # add_server(env)
    global aktive_servere
    if aktive_servere.level < aktive_servere.capacity: 
        yield aktive_servere.put(1)
        # print(f"####################|Added 1 server, aktive servere: {aktive_servere.level} |####################")
        for i in liste_over_aktive: #interrupter alle aktive brukere slik fordi de må se om de kan få bedre båndbredde
                    i.interrupt()
    else:
        # print("No more servers can be added")
        return

def remove_server(): # remove_server(env)
    global aktive_servere
    if aktive_servere.level > 2: 
        yield aktive_servere.get(1)
        # print(f"####################|Removed 1 server, aktive servere: {aktive_servere.level}|####################")
        for i in liste_over_aktive: #interrupter alle aktive brukere slik fordi de må se om de fortsatt har plass
                    i.interrupt()
    else:
        # print("No more servers can be removed")
        return



def elprice():
    global price
    global price_time_low
    global price_time_medium
    global price_time_high
    global cost_server
    global cost_user

    price = 0 #price is low
    cost_server = price_low*price_time_low
    cost_user = antall_aktive * energy_per_user * price_low
    # print(f"####################|Price is [{price}] low at time {env.now}|####################")
    yield env.timeout(price_time_low)

    price = 1 #price is medium
    cost_server = price_medium*price_time_medium
    cost_user = antall_aktive * energy_per_user * price_medium
    # print(f"####################|Price is [{price}] medium at time {env.now}, removing 1 server|####################")
    env.process(remove_server())
    yield env.timeout(price_time_medium)

    env.process(decide_next_price())

def decide_next_price():
    global price
    global price_time_low
    global price_time_medium
    global price_time_high
    global cost_server
    global cost_user
    if next_high():

        price = 2 #price is high
        cost_server = price_high*price_time_high
        cost_user = antall_aktive * energy_per_user * price_high
        # print(f"####################|Price is [{price}] high at time {env.now}|####################")
        env.process(remove_server())
        yield env.timeout(price_time_high)

        price = 1 #price is medium
        cost_server = price_medium*price_time_medium
        cost_user = antall_aktive * energy_per_user * price_medium
        # print(f"####################|Price is [{price}] medium at time {env.now}|####################")
        env.process(add_server())
        yield env.timeout(price_time_medium)

        env.process(decide_next_price())
    else:

        env.process(add_server())
        env.process(elprice())

def next_high():
    p_high = 0.5
    if np.random.uniform(0,1) < p_high:
        return True
    else:
        return False


#A.2
def MOS_Score(antall_aktive):
    Q = min(1,(aktive_servere.level)*n/antall_aktive)
    if Q <=1.0 and Q >= 0.9:
        return 5
    elif Q < 0.9 and Q >= 0.8:
        return 4
    elif Q < 0.8 and Q >= 0.6:
        return 3
    elif Q < 0.6 and Q >= 0.5:
        return 2
    elif Q < 0.5 and Q >= 0.0:
        return 1
    else:
        return 0
    
def MOS_Score_by_bandwidth(bandwidth):
    if bandwidth <=1.0 and bandwidth >= 0.9:
        return 5
    elif bandwidth < 0.9 and bandwidth >= 0.8:
        return 4
    elif bandwidth < 0.8 and bandwidth >= 0.6:
        return 3
    elif bandwidth < 0.6 and bandwidth >= 0.5:
        return 2
    elif bandwidth < 0.5 and bandwidth >= 0.0:
        return 1
    else:
        return 0


def run_simulation(env):
    user3_gen_proc = env.process(user3_generator(env))   
    elprice_proc = env.process(elprice())   
    yield user3_gen_proc & elprice_proc


if __name__ == "__main__":
    env.process(run_simulation(env))
    env.run(until=tid)
    
    #A.8, plot 
    ### Plot Price Over Time ###
    plt.figure(figsize=(10,6))
    plt.step(time_list_new, datacenter_price_list, linestyle='-', color='g')
    plt.title('Price Over Time')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.show()

    ### Plot Quality Over Time ###
    plt.figure(figsize=(10,6))
    plt.plot(time_list_new, datacenter_quality_list, linestyle='-', color='b')
    plt.title('Bandwith Over Time')
    plt.xlabel('Time')
    plt.ylabel('Bandwith')
    plt.show()

    ### Plot Quality vs. Price
    plt.figure(figsize=(10,6))
    plt.step(time_list_new, datacenter_price_list, linestyle='-', color='g', label='Price Over Time')
    plt.plot(time_list_new, datacenter_quality_list, linestyle='-', color='b', label='Quality Over Time')
    plt.title('Price vs. Quality Over Time')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.legend()
    plt.show() 

# Uncomment the following code to run the simulations (comment out the code above):

# Replications
# if __name__ == "__main__":
#     num_gsla_violations = 0
#     time_until_gsla_violations = []

#     total_active_users = 0
#     total_bandwidth_used = 0

#     server_cost = 0
#     user_cost = 0
#     total_cost = 0


#     for i in range(num_replications):
#         env = simpy.Environment()
#         env.process(run_simulation(env))
#         env.run(until=tid)

#         if gsla_violation:
#             num_gsla_violations += 1
#             time_until_gsla_violations.append(time_until_gsla_violation)
#         # if active_user_bool:
#         #     total_active_users += 1
#         #     bandwidth2 = min(1,(aktive_servere.level)*n/(antall_aktive))
#         #     total_bandwidth_used += bandwidth2
#         if active_user_bool:
#             total_active_users += 1
#             bandwidth2 = min(1,(aktive_servere.level)*n/(antall_aktive))
#             total_bandwidth_used += bandwidth2*antall_aktive

#             server_cost += aktive_servere.level * cost_server
#             user_cost += cost_user
#             total_cost += server_cost + user_cost

#             # bandwidth_per_user = min(1, (aktive_servere.level * 10) / antall_aktive)
#             bandwidth_per_user = min(1, (aktive_servere.level * 100) / antall_aktive)
#             print(f"bandwidth per user: {bandwidth_per_user}")
#             quality_levels += [MOS_Score_by_bandwidth(bandwidth2)]

#     # print(num_gsla_violations)
#     # print(time_until_gsla_violations)
#     prob_gsla_violation = num_gsla_violations/num_replications
#     mean_time_until_gsla_violation = np.mean(time_until_gsla_violations)
#     average_bandwidth = total_bandwidth_used/total_active_users
#     average_quality = MOS_Score_by_bandwidth(average_bandwidth)
#     average_cost = total_cost/num_replications

    # print(f"Probability of GSLA violation: {prob_gsla_violation}")
    # print(f"Mean time until GSLA violation: {mean_time_until_gsla_violation} \n")

    # print(f"total active users: {total_active_users}")
    # print(f"total bandwidth used: {total_bandwidth_used}")
    # print("Average bandwidth used: ", average_bandwidth)
    # print("Average quality: ", average_quality, "\n")
    # print(f"server cost: {server_cost}")
    # print(f"user cost: {user_cost}")
    # print(f"total cost: {total_cost}")
    # print("Average cost: ", average_cost)

   





