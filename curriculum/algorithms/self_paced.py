import math
import torch
from torch.utils.data import Subset, DataLoader

from .base import BaseTrainer, BaseCL



class SelfPaced(BaseCL):
    def __init__(self, start_rate, grow_epochs, 
                 grow_fn, weight_fn):
        super(SelfPaced, self).__init__()

        self.name = 'selfpaced'
        self.epoch = 0
        self.net = None
        self.device = None
        self.criterion = None
        self.weights = None

        self.start_rate = start_rate
        self.grow_epochs = grow_epochs
        self.grow_fn = grow_fn
        self.weight_fn = weight_fn


    def model_prepare(self, net, device, epochs, 
                      criterion, optimizer, lr_scheduler):
        if self.net is None:
            self.net = net
        self.device = device
        self.criterion = criterion


    def data_curriculum(self, loader):
        self.epoch += 1

        data_rate = min(1.0, self._subset_grow())
        data_size = int(self.data_size * data_rate)

        data_loss = self._loss_measure()
        data_indices = torch.argsort(data_loss)[:data_size]
        data_threshold = data_loss[data_indices[-1]]

        if self.weight_fn == 'hard':
            dataset = Subset(self.dataset, tuple(range(data_size)))
        else:
            self.weights = self._data_weight(data_loss, data_threshold)
            dataset = self.dataset
        return DataLoader(dataset, self.batch_size, shuffle=True)


    def loss_curriculum(self, criterion, outputs, labels, indices):
        if self.weight_fn == 'hard':
            return torch.mean(criterion(outputs, labels))
        else:
            return torch.mean(criterion(outputs, labels) * self.weights[indices])


    def _subset_grow(self):
        if self.grow_fn == 'linear':
            return self.start_rate + (1.0 - self.start_rate) / self.grow_epochs * self.epoch
        elif self.grow_fn == 'geom':
            return 2.0 ** ((math.log2(1.0) - math.log2(self.start_rate)) / self.grow_epochs * self.epoch + math.log2(self.start_rate))
        elif self.grow_fn[:5] == 'root-' and self.grow_fn[5:].isnumeric():
            p = int(self.grow_fn[5:])
            return (self.start_rate ** p + (1.0 - self.start_rate ** p) / self.grow_epochs * self.epoch) ** 0.5
        else:
            raise NotImplementedError()


    def _loss_measure(self):
        return torch.cat([self.criterion(self.net(
            data[0].to(self.device)), data[1].to(self.device)).detach() 
            for data in DataLoader(self.dataset, self.batch_size)])


    def _data_weight(self, loss, threshold):
        mask = loss < threshold
        if self.weight_fn == 'linear':
            return mask * (1.0 - loss / threshold)
        elif self.weight_fn == 'logarithmic':
            return mask * (torch.log(loss + 1.0 - threshold) / torch.log(1.0 - threshold))
        elif self.weight_fn == 'logistic':
            return (1.0 + torch.exp(-threshold)) / (1.0 + torch.exp(loss - threshold))
        elif self.weight_fn[:11] == 'polynomial-' and self.weight_fn[11:].isnumeric():
            t = int(self.weight_fn[11:])
            return mask * ((1.0 - loss / threshold) ** 1.0 / (t - 1.0))      
        else:
            raise NotImplementedError()


class SelfPacedTrainer(BaseTrainer):
    def __init__(self, data_name, net_name, device_name, num_epochs, random_seed, 
                 start_rate, grow_epochs, grow_fn, weight_fn):
        
        cl = SelfPaced(start_rate, grow_epochs, grow_fn, weight_fn)

        super(SelfPacedTrainer, self).__init__(
            data_name, net_name, device_name, num_epochs, random_seed, cl
        )