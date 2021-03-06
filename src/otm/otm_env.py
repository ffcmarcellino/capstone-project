import numpy as np
from OTM4RL import OTM4RL
from env_plot import plotEnv
from random import sample

class otmEnv:

    def __init__(self, env_init_info):

        self.configfile = env_init_info["configfile"]
        self.state_division = env_init_info.get("state_division", None)
        self.time_step = env_init_info["time_step"]
        self.plot_precision = env_init_info.get("plot_precision", 1)
        assert (type(self.plot_precision) == int and self.plot_precision >= 1), "plot_precision must be an integer greater than or equal to 1"
        assert self.time_step % self.plot_precision == 0, "time_step must be a multiple of plot_precision"
        self.buffer = env_init_info.get("buffer", False)
        self.start()
        self.action_space = range(self.otm4rl.num_stages ** self.otm4rl.num_intersections)
        if self.buffer:
            self.network_lines = self.otm4rl.get_network_lines()
        self.plot = plotEnv()
        # self.seed()

    # def seed(self, seed=None):
    #     self.np_random, seed = seeding.np_random(seed)
    #     return [seed]

    def start(self):
        try:
            self.close()
        except:
            pass
        self.otm4rl = OTM4RL(self.configfile)
        self.otm4rl.initialize(float(0))
        self.otm4rl.otm.advance(float(1))

    def reset(self, set_queues = "random"):
         if self.buffer:
             self.queue_buffer = dict(list(zip(self.otm4rl.link_ids, [{"waiting": [], "transit": []} for i in self.otm4rl.link_ids])))
             self.signal_buffer = dict(list(zip(self.otm4rl.controllers.keys(), [[] for i in self.otm4rl.controllers.keys()])))
         if set_queues == "random":
             self.set_state(self.random_queues())
         elif set_queues == "current":
             self.state = self.q2state(self.otm4rl.get_queues())
             self.add_queue_buffer()
         elif set_queues == "initial":
             self.start()
             self.state = self.q2state(self.otm4rl.get_queues())
             self.add_queue_buffer()
         else:
             self.set_state(set_queues)

         return self.state

    def advance(self, duration, compute_reward = False):

        reward_sum = 0
        if compute_reward:
            for i in range(duration):
                self.otm4rl.otm.advance(float(1))
                queues = self.otm4rl.get_queues()
                state = self.q2state(queues)
                reward_sum -= np.sum(state)
        else:
            self.otm4rl.otm.advance(float(duration))

        return reward_sum


    def step(self, action, compute_reward = False):
        assert action in self.action_space, "%r (%s) invalid" % (action, type(action))

        self.otm4rl.set_control(self.decode_action(action))
        self.add_signal_buffer()

        if self.buffer:
            num_runs = self.plot_precision
        else:
            num_runs = 1
        duration = int(self.time_step/num_runs)
        avg_reward = 0
        for i in range(num_runs):
            avg_reward += self.advance(duration, compute_reward)
            self.add_queue_buffer()
        avg_reward /=  self.time_step

        queues = self.otm4rl.get_queues()

        self.state = self.q2state(queues)

        try:
            reward = -np.sum(np.where(self.state >= 1, self.state_division - 1, (self.state * self.state_division).astype(int)))
        except:
            reward = -np.sum(self.state)

        return self.state, reward, avg_reward

    def set_state(self, queues):
        self.otm4rl.set_queues(queues)
        self.state = self.q2state(self.otm4rl.get_queues())
        self.add_queue_buffer()

    def q2state(self, queues):
        state_vec = []
        i = 0
        for c_id, controller in self.otm4rl.controllers.items():
            stages = controller["stages"]
            for i, stage in enumerate(stages):
                agg_queue = 0
                max_queue = 0
                for link_id in self.otm4rl.in_link_ids[c_id][i]:
                    agg_queue += queues[link_id]["waiting"]
                    max_queue += self.otm4rl.max_queues[link_id]
                state_vec.append(agg_queue/max_queue)
        return np.array(state_vec)

    def decode_action(self, action):
        a = action
        controller_ids = list(self.otm4rl.controllers.keys())
        signal_command = dict(list(zip(controller_ids, np.zeros(self.otm4rl.num_stages).astype(int))))
        i = - 1
        while a != 0:
            controller_id = controller_ids[i]
            signal_command[controller_id] = a % self.otm4rl.num_stages
            a = a // self.otm4rl.num_stages
            i -= 1

        return signal_command

    def random_queues(self):
        rand_q = dict()
        for link_id in self.otm4rl.max_queues.keys():
           if link_id in self.otm4rl.out_links:
               rand_q[link_id] = {"waiting": int(0), "transit": int(0)}
           else:
               p = np.random.random()
               waiting_queue = p*self.otm4rl.max_queues[link_id]
               q = np.random.random()
               transit_queue = q*(self.otm4rl.max_queues[link_id] - waiting_queue)
               rand_q[link_id] = {"waiting": round(waiting_queue), "transit": round(transit_queue)}
        return rand_q

    def add_queue_buffer(self):

        if self.buffer == True:
            queues = self.otm4rl.get_queues()
            for link_id in queues.keys():
                self.queue_buffer[link_id]["waiting"].append(queues[link_id]["waiting"])
                self.queue_buffer[link_id]["transit"].append(queues[link_id]["transit"])
        else:
            pass

    def add_signal_buffer(self):

        if self.buffer == True:
            signals = self.otm4rl.get_control()
            for c_id in signals:
                self.signal_buffer[c_id].append(signals[c_id])
        else:
            pass

    def plot_agg_queue(self, c_id, stage_id, queue_type, plot_hlines = True, plot_signals = True, start = 0, end = None):

        link_ids = self.otm4rl.in_link_ids[c_id][stage_id]
        ymax = np.sum([self.otm4rl.max_queues[link_id] for link_id in link_ids])
        ylim = (0, ymax*1.05)
        if plot_hlines and self.state_division != None:
            if queue_type == "waiting":
                ybars = [ymax*i/self.state_division for i in range(1, self.state_division + 1)]
            else:
                ybars = [ymax]
        else:
            ybars = None
        title = "Agg. Queue Dynamics: Controller " + str(c_id) + ", Stage " + str(stage_id) + " - " + queue_type + " queue"
        green_stages = [stage_id]
        start_signal = int(start/self.time_step)
        start_queue = start_signal * self.plot_precision
        end_signal = end
        end_queue = end
        if end != None:
            end_signal = int(end/self.time_step)
            end_queue = end_signal * self.plot_precision
        queue_vec = np.array([self.queue_buffer[link_id][queue_type][start_queue:end_queue] for link_id in link_ids]).sum(axis=0)
        queue_times = [i*self.time_step/self.plot_precision for i in range(len(queue_vec))]
        if plot_signals:
            signal_vec = self.signal_buffer[c_id][start_signal:end_signal]
            signal_times = np.array(range(len(signal_vec)))*self.time_step
        else:
            signal_vec = None
            signal_times = None

        self.plot.plot_queue(ylim, title, green_stages, queue_vec, queue_times, signal_vec, signal_times, ybars)

    def plot_link_queue(self, link_id, queue_type, plot_hlines = True, plot_signals = True, start = 0, end = None):

        try:
            link_controller = self.otm4rl.in_link_info[link_id]["controller"]
            green_stages = self.otm4rl.in_link_info[link_id]["stages"]
        except:
            print("This link is leaving the network or it is a demand link, so it is not impacted by traffic lights")
            return

        ymax = self.otm4rl.max_queues[link_id]
        ylim = (0, ymax*1.05)
        if plot_hlines:
            ybars = [ymax]
        else:
            ybars = None
        title = "Queue Dynamics: Link " + str(link_id) + " - " + queue_type + " queue"
        start_signal = int(start/self.time_step)
        start_queue = start_signal * self.plot_precision
        end_signal = end
        end_queue = end
        if end != None:
            end_signal = int(end/self.time_step)
            end_queue = end_signal * self.plot_precision
        queue_vec = self.queue_buffer[link_id][queue_type][start_queue:end_queue]
        queue_times = [i*self.time_step/self.plot_precision for i in range(len(queue_vec))]
        if plot_signals:
            signal_vec = self.signal_buffer[link_controller][start_signal:end_signal]
            signal_times = np.array(range(len(signal_vec)))*self.time_step
        else:
            signal_vec = None
            signal_times = None

        self.plot.plot_queue(ylim, title, green_stages, queue_vec, queue_times, signal_vec, signal_times, ybars)

    # def plot_network_gradient(self):
    #     self.plot.network_gradient(self.otm4rl.get_queues(), self.otm4rl.get_control())

    def close(self):
        self.otm4rl.conn.close()

    # def render(self, mode='human'):
    #     #plot the queue profile over time
    #     #render the network
    #     pass
    #
    # def close(self):
    #     #stop rendering
    #     pass
