# -*- coding: utf-8 -*-
# torch 0.3.1

import torch
from torch.autograd import Variable
import torch_backend as K # TODO: relative import
from mlkn import MLKNClassifier
from kerlinear import kerLinear
from sklearn.datasets import load_iris, load_breast_cancer, load_digits
from sklearn.preprocessing import Normalizer, StandardScaler
import numpy as np

torch.manual_seed(1234)

if __name__=='__main__':

    # x, y = load_breast_cancer(return_X_y=True)
    # x, y = load_digits(return_X_y=True)
    x, y = load_iris(return_X_y=True)
    # x = np.load("sonar.npy")
    # y = np.load("sonar_labels.npy")
    # x = np.load("diabetes.npy")
    # y = np.load("diabetes_labels.npy")
    # x = np.load("heart.npy")
    # y = np.load("heart_labels.npy")
    # x = np.load("liver.npy")
    # y = np.load("liver_labels.npy")
    # x = np.load("australian.npy")
    # y = np.load("australian_labels.npy")
    # x = np.load("splice.npy")
    # y = np.load("splice_labels.npy")
    # x = np.load("iono.npy")
    # y = np.load("iono_labels.npy")
    # x = np.load("german.npy")
    # y = np.load("german_labels.npy")
    # x = np.load("banana.npy")
    # y = np.load("banana_labels.npy")
    # x = np.load("ringnorm.npy")
    # y = np.load("ringnorm_labels.npy")
    # x = np.load("waveform.npy")
    # y = np.load("waveform_labels.npy")
    # x = np.load("thyroid.npy")
    # y = np.load("thyroid_labels.npy")
    # x = np.load("titanic.npy")
    # y = np.load("titanic_labels.npy")
    # x = np.load("fsolar.npy")
    # y = np.load("fsolar_labels.npy")

    normalizer = StandardScaler()
    x = normalizer.fit_transform(x)
    n_class = np.amax(y) + 1

    ############################
    """
    # addr = '/Users/michael/Github/data/mnist/' #TODO: change local names, put Github/ on iCloud
    # addr = '/home/michaelshiyu/Github/data/mnist/' # for miner
    addr = '/home/administrator/Github/data/mnist/' # for lab linux machine
    # addr = '/home/paperspace/Github/data/mnist/' # for paperspace
    x_train = np.load(addr+'mnist_train_img.npy') # when change datasets, change size of validation set
    y_train = np.load(addr+'mnist_train_label.npy')
    x_test = np.load(addr+'mnist_test_img.npy')
    y_test = np.load(addr+'mnist_test_label.npy')
    x_val = x_train[10000:]
    y_val = y_train[10000:]
    x_train = x_train[0:3000]
    y_train = y_train[0:3000]
    # TODO: get balanced subset

    x = x_train
    y = y_train
    """
    ############################

    dtype = torch.FloatTensor
    if torch.cuda.is_available():
        dtype = torch.cuda.FloatTensor

    X = Variable(torch.from_numpy(x).type(dtype), requires_grad=False)
    Y = Variable(torch.from_numpy(y).type(dtype), requires_grad=False)
    new_index = torch.randperm(X.shape[0])
    X, Y = X[new_index].clone(), Y[new_index].clone()
    # NOTE: cloning turns X, Y into leaf variables

    index = 50
    x_train, y_train = X[:index].clone(), Y[:index].clone()
    x_test, y_test = X[index:].clone(), Y[index:].clone()

    # x = Variable(torch.FloatTensor([[0, 7], [1, 2]]).type(dtype), requires_grad=False)
    # X = Variable(torch.FloatTensor([[1, 2], [3, 4]]).type(dtype), requires_grad=False)
    # y = Variable(torch.FloatTensor([[1], [1]]).type(dtype), requires_grad=False)
    mlkn = MLKNClassifier()
    mlkn.add_layer(kerLinear(ker_dim=X.shape[0], out_dim=15, sigma=5, bias=True))
    mlkn.add_layer(kerLinear(ker_dim=X.shape[0], out_dim=3, sigma=.1, bias=True))

    mlkn.add_optimizer(torch.optim.Adam(params=mlkn.parameters(), lr=1e-3, weight_decay=0.1))
    mlkn.add_optimizer(torch.optim.Adam(params=mlkn.parameters(), lr=1e-3, weight_decay=.1))

    mlkn.add_loss(torch.nn.CrossEntropyLoss())

    mlkn.fit(
        n_epoch=(10, 10),
        batch_size=50,
        x=x_train,
        X=X,
        y=y_train,
        n_class=3
        )
    y_pred = mlkn.predict(x_test, X)
    err = mlkn.get_error(y_pred, y_test)
    print('{:.2f}%'.format(err.data[0] * 100))