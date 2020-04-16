import math
from DQN import *
from gridworld import *
import torch

va = 0.6
vg = 0.25


def hash_state(state):
    hash_value = list(state[0].numpy().astype(int))
    hash_value = bin(int(''.join(map(str, hash_value)), 2) << 1)
    return hash_value


def probability_ask_with_ypsilon(ypsilon):
    return (1 + va) ** -ypsilon


def psi_visit(number_of_visits):
    if number_of_visits <= 1:
        # TODO fix this workaround, normally it should be minus infinity
        return 0
    return math.log(number_of_visits, 2)


def advising_probability(psi):
    return 1 - (1 + vg) ** -psi


class Miner:

    def __init__(self, number_heads):
        self.number_heads = number_heads
        self.model = Bootstrapped_DQN(number_heads, 80, [164, 150], 4, hidden_unit)
        self.times_asked_for_advise = 0
        self.times_given_advise = 0
        self.state_counter = {}

    # model.load_state_dict(torch.load('/Users/Lukas/repositories/Reinforcement-Learning-Q-learning-Gridworld-Pytorch/graph_output/model_a.pth'))
    # model.eval()

    def set_partner(self, other_agent):
        self.other_agent = other_agent

    def give_advise(self, state):
        prob_give = self.advising_probability_in_state(state)
        if np.random.random() > prob_give:
            return None
        # give advise
        # print("give advise")
        self.times_given_advise += 1
        inv_state = get_grid_for_player(state, np.array([0, 0, 0, 0, 1]))
        action = self.choose_best_action(inv_state)
        return action

    def advising_probability_in_state(self, state):
        inverse_state = get_grid_for_player(state, np.array([0, 0, 0, 0, 1]))
        hash_of_inverse_state = hash_state(inverse_state)
        if hash_of_inverse_state in self.state_counter:
            number_of_visits = self.state_counter[hash_of_inverse_state]
        else:
            number_of_visits = 0
        # print("visited=%s" % number_of_visits)
        psi = psi_visit(number_of_visits)
        return advising_probability(psi)

    def probability_ask_with_state(self, state):
        # TODO: Is it necessary to convert the state to a tensor and back when hasing?
        hash_of_state = hash_state(state)
        ypsilon = self.ypsilon_visit(hash_of_state)
        return probability_ask_with_ypsilon(ypsilon)

    def ypsilon_visit(self, hash_of_state):
        if hash_of_state in self.state_counter:
            number_of_visits = self.state_counter[hash_of_state]
        else:
            number_of_visits = 0
        # print("visited=%s" % number_of_visits)
        result = math.sqrt(number_of_visits)
        return result

    def count_state(self, state):
        hash_of_state = hash_state(state)
        if hash_of_state in self.state_counter:
            self.state_counter[hash_of_state] += 1
        else:
            self.state_counter[hash_of_state] = 1

    def exploration_strategy(self, state, epsilon):
        # choose random action
        if np.random.random() < epsilon:
            action = np.random.randint(0, 4)
            # print("A takes random action {}".format(action_a))
        else:  # choose best action from Q(s,a) values
            action = self.choose_best_action(state)
            # print("A takes best action {}".format(action_a))
        return action

    # This is choosing an action
    def choose_training_action(self, state, epsilon):
        action = None
        prob_ask = self.probability_ask_with_state(state)
        if np.random.random() < prob_ask*0:
            # ask for advice
            # print("ask for advice")
            self.times_asked_for_advise += 1
            action = self.other_agent.give_advise(state)
        if action is None:
            action = self.exploration_strategy(state, epsilon)
        return action

    def choose_best_action(self, state):
        qval = self.model(state)
        # q-values derived from all heads, compare with
        # Uncertainty-Aware Action Advising for Deep Reinforcement Learning Agents
        # page 5
        final_q_function = qval[0]
        for i in range(self.number_heads - 1):
            final_q_function += qval[i + 1]
        # print(qval)
        # take action with highest Q-value
        final_q_function = final_q_function.data / self.number_heads
        return np.argmax(final_q_function.data)

    def get_qval_for_best_action_in(self, state):
        qval = self.model.q_circumflex(state)
        return qval.max(1)[0]

    def get_state_action_value(self, state, action):
        qval = self.model(state)
        result = []
        for i in range(self.number_heads):
            result.append(qval[i].gather(1, action))
        return result
