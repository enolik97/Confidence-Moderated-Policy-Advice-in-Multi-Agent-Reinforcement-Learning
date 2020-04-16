import torch.nn as nn
import torch
import torch.nn.functional as F
from collections import namedtuple
import random


class hidden_unit(nn.Module):
    def __init__(self, in_channels, out_channels, activation):
        super(hidden_unit, self).__init__()
        self.activation = activation
        # linear transformation to the incoming data
        self.nn = nn.Linear(in_channels, out_channels)
        nn.init.normal_(self.nn.weight, std=0.07)

    def forward(self, x):
        out = self.nn(x)
        out = self.activation(out)
        return out


class Body_net(nn.Module):
    def __init__(self, in_channels, hidden_layers, out_channels, unit=hidden_unit, activation=F.relu):
        super(Body_net, self).__init__()
        assert type(hidden_layers) is list
        self.hidden_units = nn.ModuleList()
        self.in_channels = in_channels
        self.activation = activation
        prev_layer = in_channels
        for hidden in hidden_layers:
            self.hidden_units.append(unit(prev_layer, hidden, activation))
            prev_layer = hidden
        self.final_unit = nn.Linear(prev_layer, out_channels)
        nn.init.normal_(self.final_unit.weight, std=0.07)

    def forward(self, x):
        out = x.view(-1, self.in_channels).float()
        for unit in self.hidden_units:
            out = unit(out)
        out = self.final_unit(out)
        out = self.activation(out)
        return out


class DQN_from_net(nn.Module):
    def __init__(self, net, out_channels):
        super(DQN_from_net, self).__init__()
        self.net = net
        self.final_unit = nn.Linear(self.net.final_unit.out_features, out_channels)
        nn.init.normal_(self.final_unit.weight, std=0.07)

    def forward(self, x):
        # out = x.view(-1, self.in_channels).float()
        out = self.net(x)
        out = self.final_unit(out)
        return out


class Bootstrapped_DQN(nn.Module):
    def __init__(self, number_heads, in_channels, hidden_layers, out_channels, unit=hidden_unit, activation=F.relu):
        super(Bootstrapped_DQN, self).__init__()
        self.number_heads = number_heads
        hidden_layer_out = hidden_layers.pop()
        body = Body_net(in_channels, hidden_layers, hidden_layer_out, unit, activation)
        self.heads = []
        for i in range(self.number_heads):
            self.heads.append(DQN_from_net(body, out_channels))

    def forward(self, x):
        result = []
        for i in range(self.number_heads):
            result.append(self.heads[i](x))
        return result


Transition = namedtuple('Transition',
                        ('state', 'action_a', 'action_b', 'new_state', 'reward', 'non_final'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.capacity = capacity
        self.memory = []
        self.position = 0

    def push(self, *args):
        """Saves a transition."""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
