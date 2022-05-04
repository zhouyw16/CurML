import torch
from torch.utils.data import Dataset, DataLoader

from ..solvers import *



class BaseCL():

    class CLDataset(Dataset):
        def __init__(self, dataset):
            self.dataset = dataset

        def __getitem__(self, index):
            data = self.dataset[index]
            return [part for part in data] + [index]

        def __len__(self):
            return len(self.dataset)


    def __init__(self):
        self.name = 'base'
        self.dataset = None


    def model_curriculum(self, net, device):
        return net.to(device)


    def data_curriculum(self, loader):
        if self.dataset is None:
            self.dataset = self.CLDataset(loader.dataset)
            self.data_size = len(self.dataset)
            self.batch_size = loader.batch_size
            self.n_batches = (self.data_size - 1) // self.batch_size + 1

        return DataLoader(self.dataset, self.batch_size, shuffle=True)


    def loss_curriculum(self, criterion, outputs, labels, indices):
        return torch.mean(criterion(outputs, labels))



class BaseTrainer():

    def __init__(self, data_name, net_name, 
                 device_name, random_seed, 
                 cl=BaseCL()):
        
        if data_name in ['cifar10']:
            self.trainer = ImageClassifier(
                data_name, net_name, 
                device_name, random_seed,
                cl.name, cl.data_curriculum, 
                cl.model_curriculum, cl.loss_curriculum,
            )
        else:
            raise NotImplementedError()
        

    def fit(self):
        return self.trainer.fit()


    def evaluate(self):
        return self.trainer.evaluate()

    
    def export(self):
        return self.trainer.export()