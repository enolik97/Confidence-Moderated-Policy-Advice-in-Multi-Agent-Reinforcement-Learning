import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
import numpy as np
from collections import namedtuple
import random
from keras.models import load_model

class hidden_unit(nn.Module):
    def __init__(self, in_channels, out_channels, activation):
        super(hidden_unit, self).__init__()
        self.activation = activation
        # linear transformation to the incoming data
        self.nn = nn.Linear(in_channels, out_channels, bias=False)
        nn.init.normal_(self.nn.weight, std=0.07)

    def forward(self, x):
        out = self.nn(x)
        out = self.activation(out)   
        return out
        
class Q_learning(nn.Module):
    def __init__(self, in_channels, hidden_layers, out_channels, unit=hidden_unit, activation=F.relu):
        super(Q_learning, self).__init__()
        assert type(hidden_layers) is list
        self.hidden_units = nn.ModuleList()
        self.in_channels = in_channels
        prev_layer = in_channels
        for hidden in hidden_layers:
            self.hidden_units.append(unit(prev_layer, hidden, activation))
            prev_layer = hidden
        self.final_unit = nn.Linear(prev_layer, out_channels, bias=False)
        nn.init.normal_(self.final_unit.weight, std=0.07)
        model_load = load_model('/Users/Lukas/repositories/Reinforcement-Learning-Q-learning-Gridworld-Keras/simpleModel.h5')
        weights = model_load.get_weights()
        self.hidden_units[0].nn.weight.data = torch.from_numpy(np.transpose(weights[0]))
        self.hidden_units[1].nn.weight.data = torch.from_numpy(np.transpose(weights[2]))
        self.final_unit.weight.data = torch.from_numpy(np.transpose(weights[4]))

    def forward(self, x):
        out = x.view(-1, self.in_channels).float()
        for unit in self.hidden_units:
            out = unit(out)
        out = self.final_unit(out)
        return out


Transition = namedtuple('Transition',
                        ('state', 'action', 'new_state', 'reward'))


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

    