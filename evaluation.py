# Here is the test of AI
from gridworld import Goldmine


def evaluate_agents(agent_a, agent_b):
    reward_sum = 0
    env = Goldmine()
    for state_id in range(50):
        observation = env.reset(state_id)
        # env.render()
        steps = 0
        done = False
        while not done:
            action_a = agent_a.choose_best_action(observation)
            action_b = agent_b.choose_best_action(observation)
            observation, reward, done, info = env.step(action_a, action_b)
            # env.render()
            reward_sum += reward
            steps += 1
            if steps > 10:
                done = True
    return reward_sum / 50
