import torch
from torch.utils.data import Dataset, DataLoader

from ..trainers import *



class BaseCL():
    """The base class of CL Algorithm class.

    Each CL Algorithm class has a CLDataset and five key member functions.

    Attributes:
        name: A string for the name of a CL algorithm.
        dataset: A CLDataset build by the original training dataset.
        data_size: An integer for the number of training data samples.
        batch_size: An integer for the number of a mini-batch.
        n_batches: An integer for the number of batches.
    """

    class CLDataset(Dataset):
        """A dataset for CL Algorithm.

        It attaches the original training dataset with data index,
        which is commonly used for data sampling or reweighting.
        """
        def __init__(self, dataset):
            self.dataset = dataset

        def __getitem__(self, index):
            data = self.dataset[index]
            return [part for part in data] + [index]    # Attach data index.

        def __len__(self):
            return len(self.dataset)


    def __init__(self):
        self.name = 'No Curriculum'


    def data_prepare(self, loader):
        """Pass training data to CL Algorithm.
        
        Initiate the CLDataset and record training data attributes.
        """
        self.dataset = self.CLDataset(loader.dataset)
        self.data_size = len(self.dataset)
        self.batch_size = loader.batch_size
        self.n_batches = (self.data_size - 1) // self.batch_size + 1


    def model_prepare(self, net, device, epochs, 
                      criterion, optimizer, lr_scheduler):
        """Pass model information to CL Algorithm."""
        pass


    def data_curriculum(self, loader):
        """Measure data difficulty and schedule the training set."""
        return DataLoader(self.dataset, self.batch_size, shuffle=True)


    def model_curriculum(self, net):
        """Schedule the model changing."""
        return net


    def loss_curriculum(self, criterion, outputs, labels, indices):
        """Reweight loss."""
        return torch.mean(criterion(outputs, labels))



class BaseTrainer():
    """The base class of CL Trainer class.

    It initiates the Model Trainer and CL Algorithm, 
    and provide the functions for training and evaluation.

    Attributes:
        trainer: A image classifier, language model, recommendation system, etc.
    """

    def __init__(self, data_name, net_name, device_name, 
                 num_epochs, random_seed, cl=BaseCL()):
        """Initiate the Model Trainer according to data_name.

        If the dataset is CIFAR-10, CIFAR-100, ImageNet or their variants, the Model Trainer can be a Image Classifier.
        If the dataset is PTB, WikiText or their variants, the Model Trainer can be a Language Model.
        If the dataset is not a predefined one, users can create a custom Model Trainer.
        """
        if data_name.startswith('cifar') or data_name.startswith('imagenet'):
            self.trainer = ImageClassifier(
                data_name, net_name, device_name, num_epochs, random_seed,
                cl.name, cl.data_prepare, cl.model_prepare,
                cl.data_curriculum, cl.model_curriculum, cl.loss_curriculum)
        else:
            raise NotImplementedError()
        

    def fit(self):
        return self.trainer.fit()


    def evaluate(self, net_dir=None):
        """Evaluate the net performance given its path, else evaluate the trained net."""
        return self.trainer.evaluate(net_dir)

    
    def export(self, net_dir=None):
        """Load the net state dict given its path, else load the trained net."""
        return self.trainer.export(net_dir)