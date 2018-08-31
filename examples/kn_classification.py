# -*- coding: utf-8 -*-

import kernet.backend as K
from kernet.models.kn import KNClassifier
from kernet.layers.kerlinear import kerLinear
from kernet.layers.multicomponent import kerLinearEnsemble, kerLinearStack

import numpy as np
import torch
from torch.autograd import Variable
from sklearn.datasets import load_iris, load_breast_cancer, load_digits
from sklearn.preprocessing import StandardScaler

torch.manual_seed(1234)
np.random.seed(1234)

if __name__=='__main__':
    """
    This example demonstrates how a KN classifier works. Everything in here
    including the architecture of the learning machine and the training
    algorithm strictly follows this paper: https://arxiv.org/abs/1802.03774.
    """
    #########
    # MKL benchmarks
    #########
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    x, y = load_breast_cancer(return_X_y=True) # 1.40 (acc grad)/ 2.11
    # x, y = load_digits(return_X_y=True) # 5.23 (acc grad)/ 5.45
    # x, y = load_iris(return_X_y=True) # 9.33 (acc grad)/ 8.00

    # for other Multiple Kernel Learning benchmarks used in the paper, you could
    # do:
    # x = np.load('../kernet/datasets/mkl/name_of_dataset.npy')
    # y = np.load('../kernet/datasets/mkl/name_of_dataset_labels.npy')
    # note that for some of the datasets, the results reported are only on a
    # subset of the data with size given in Table 1. This is to keep consistency
    # with the original paper that reported most of the results.
    # A random subset is chosen at each one of the 20 runs.

    # standardize features to zero-mean and unit-variance
    normalizer = StandardScaler()
    x = normalizer.fit_transform(x)
    n_class = int(np.amax(y) + 1)

    # X, Y does not require grad by default
    X = torch.tensor(x, dtype=torch.float, device=device)
    Y = torch.tensor(y, dtype=torch.int64, device=device).view(-1,)

    # randomly permute data
    X, Y = K.rand_shuffle(X, Y)

    # split data evenly into training and test
    index = len(X)//2
    x_train, y_train = X[:index], Y[:index]
    x_test, y_test = X[index:], Y[index:]
    kn = KNClassifier()

    ensemble = False # whether to use ensemble layer, see below
    batch_size=100 # batch size for ensemble layer, not for training

    # sparsify the kernel machines on the second layer
    """
    x_train_, y_train_ = K.get_subset(
        X=x_train,
        Y=y_train,
        n=x_train.shape[0],
        shuffle=True
        )
    """
    
    # see kernet/layers/kerlinear.py for details for kerLinear
    layer0 = kerLinear(X=x_train, out_dim=15, sigma=5, bias=True)
    layer1 = kerLinear(X=x_train, out_dim=15, sigma=3, bias=True)
    layer2 = kerLinear(X=x_train, out_dim=n_class, sigma=1, bias=True)

    # for non-input layers, pass to X the
    # set of raw data you want to center the kernel machines on,
    # for layer n, layer.X will be updated in runtime to
    # F_n-1(...(F_0(layer.X))...)

    # you could also build a stack layer (see documentation in kernet/layers/ensemble.py)
    layer0_ = kerLinearStack()
    layer0_.add(layer0)
    layer0_.add(layer1)

    if not ensemble:
        # add layers to the model

        kn.add_layer(layer0_)

        # kn.add_layer(layer0)
        # kn.add_layer(layer1)
        kn.add_layer(layer2)

    else:
        # create ensemble layers so that large datasets can be fitted into memory

        layer0_.to_ensemble_(batch_size)
        kn.add_layer(layer0_)
        kn.add_layer(layer2.to_ensemble(batch_size))

    # specify loss function for the output layer, this works with any
    # PyTorch loss function but it is recommended that you use CrossEntropyLoss
    kn.add_loss(torch.nn.CrossEntropyLoss())

    # also add a metric to evaluate the model, this is not used for training.
    # here we use classification error rate.
    kn.add_metric(K.L0Loss())

    kn.to(device)

    # add optimizer for each layer, this works with any torch.optim.Optimizer
    # note that this model is trained with the proposed layerwise training
    # method by default
    kn.add_optimizer(
        torch.optim.Adam(params=kn.parameters(), lr=1e-3, weight_decay=0.1)
        )
    kn.add_optimizer(
        torch.optim.Adam(params=kn.parameters(), lr=1e-3, weight_decay=0.1)
        )
    # kn.add_optimizer(
    #     torch.optim.Adam(params=kn.parameters(), lr=1e-3, weight_decay=.1)
    #     )

    # fit the model
    kn.fit(
        n_epoch=(20, 20, 20),
        batch_size=30,
        shuffle=True,
        X=x_train,
        Y=y_train,
        n_class=n_class,
        accumulate_grad=True,
        hidden_cost='MSE',
        cluster_class=True,
        X_val=x_train,
        Y_val=y_train,
        val_window=5,
        verbose=True
        )
    # make a prediction on the test set and print error
    print('\ntest:')
    kn.evaluate(X_test=x_test, Y_test=y_test, batch_size=15)