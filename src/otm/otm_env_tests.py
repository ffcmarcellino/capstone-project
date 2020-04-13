import os
import inspect
import numpy as np
from otm_env import otmEnv

def get_env():
	this_folder = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	root_folder = os.path.dirname(os.path.dirname(this_folder))
	configfile = os.path.join(root_folder,'cfg', 'network_1.xml')
	return otmEnv({"state_division": 2, "time_step": 60, "plot_precision": 4, "buffer": True}, configfile)

def test_random_queues():
	env = get_env()
	print(env.random_queues())
	print(env.random_queues())
	del env

def test_q2state():
	env = get_env()
	env.otm4rl.otm.advance(float(100))
	queues = env.otm4rl.get_queues()
	print(queues)
	print(env.otm4rl.in_link_info)
	print(env.q2state(queues))
	del env

def test_add_queue_buffer():
	env = get_env()
	env.queue_buffer = dict(list(zip(env.otm4rl.link_ids, [{"waiting": [], "transit": []} for i in env.otm4rl.link_ids])))
	env.otm4rl.otm.advance(float(100))
	print(env.otm4rl.get_queues())
	env.add_queue_buffer()
	print(env.queue_buffer)
	env.otm4rl.otm.advance(float(100))
	print(env.otm4rl.get_queues())
	env.add_queue_buffer()
	print(env.queue_buffer)
	del env

def test_set_state():
	env = get_env()
	env.queue_buffer = dict(list(zip(env.otm4rl.link_ids, [{"waiting": [], "transit": []} for i in env.otm4rl.link_ids])))
	env.otm4rl.otm.advance(float(100))
	print(env.otm4rl.get_queues())

	state = env.random_queues()
	env.set_state(state)
	print(env.queue_buffer)
	print(env.state)

	state = env.random_queues()
	env.set_state(state)
	print(env.queue_buffer)
	print(env.state)

	del env

def test_reset():
	env = get_env()
	print(env.q2state(env.otm4rl.get_queues()))
	print(env.reset("current"))
	print(env.reset("random"))
	print(env.reset({2: {"waiting": 10, "transit": 11}}))
	del env

def test_add_signal_buffer():
	env = get_env()
	env.reset()
	print(env.otm4rl.get_control())
	env.add_signal_buffer()
	print(env.signal_buffer)
	env.otm4rl.otm.advance(float(150))
	print(env.otm4rl.get_control())
	env.add_signal_buffer()
	print(env.signal_buffer)
	del env

def test_decode_action():
    env = get_env()
    for i in range(4):
    	print(env.decode_action(i))
    del env

def test_step():
	env = get_env()

	env.reset()

	print(env.queue_buffer)
	action = np.random.choice(env.action_space)
	state, reward = env.step(action)
	print("Next state:", env.state)
	print("Reward:", reward)
	print(env.signal_buffer)

	print(env.queue_buffer)
	action = np.random.choice(env.action_space)
	state, reward = env.step(action)
	print("Next state:", env.state)
	print("Reward:", reward)
	print(env.signal_buffer)

	del env

def test_close():
	env = get_env()
	env.close()
	env.start()
	print(env.otm4rl.get_queues())
	del env
# def test_get_signal_positions():
# 	env = get_env()
# 	env.reset()
# 	env.otm4rl.advance(100)
# 	control = env.otm4rl.get_control()
# 	state = env.otm4rl.get_queues()
# 	lines = env.build_network_lines(state)[0]
# 	print(env.get_signal_positions(lines, control))
#
# 	del env
#
# def test_plot_environment():
# 	env = get_env()
#
# 	env.reset()
# 	action = np.random.choice(env.action_space)
# 	state, reward = env.step(action)
# 	action = np.random.choice(env.action_space)
# 	state = env.otm4rl.get_queues()
# 	print(env.decode_action(action))
# 	env.plot_environment(state, env.decode_action(action))
# 	state, reward = env.step(action)
# 	action = np.random.choice(env.action_space)
# 	state = env.otm4rl.get_queues()
# 	print(env.decode_action(action))
# 	env.plot_environment(state, env.decode_action(action))
# 	state, reward = env.step(action)
# 	action = np.random.choice(env.action_space)
# 	state = env.otm4rl.get_queues()
# 	print(env.decode_action(action))
# 	env.plot_environment(state, env.decode_action(action))
#
# 	del env
#
# def test_plot_queues(link_id):
# 	env = get_env()
# 	env.reset(set_state = "current")
# 	t = 0
# 	print("t=" + str(t), env.otm4rl.get_queues()[link_id])
#
# 	for k in range(4):
# 		for i in range(2):
# 			env.otm4rl.set_control({1: i, 2: 0})
# 			print(env.otm4rl.get_control())
# 			env.add_signal_buffer()
# 			for j in range(env.plot_precision):
# 				env.otm4rl.advance(env.time_step/env.plot_precision)
# 				t += env.time_step/env.plot_precision
# 				print("t=" + str(t), env.otm4rl.get_queues()[link_id])
# 				env.add_queue_buffer()
#
# 	print(env.signal_buffer)
# 	# env.plot_queues(link_id, "transit")
# 	env.plot_queues(link_id, "waiting")
#
# 	del env

if __name__ == '__main__':
	# test_random_queues()
	# test_q2state()
	# test_add_queue_buffer()
	# test_set_state()
	# test_reset()
	# test_add_signal_buffer()
	# test_decode_action()
	# test_step()
	test_close()
