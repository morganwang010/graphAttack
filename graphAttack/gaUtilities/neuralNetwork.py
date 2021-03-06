"""Neural networks utilities"""
import numpy as np
from ..coreDataContainers import Variable
from ..operations.activationOperations import *
from ..operations.costOperations import *
from ..operations.twoInputOperations import *
from ..operations.singleInputOperations import *
from ..operations.convolutionOperation import *
from ..operations.transformationOperations import *
from ..operations.multipleInputOperations import *
from .misc import generateRandomVariable, generateZeroVariable


def addDenseLayer(mainGraph, nOutputNodes,
                  inputOperation=None,
                  activation=ReLUActivation,
                  dropoutRate=0,
                  batchNormalisation=False):
    """Append a dense layer to the graph

    Parameters
    ----------
    mainGraph : ga.Graph
        computation graph to which append the dense layer
    nOutputNodes : int
        Number of output nodes
    inputOperation : ga.Operation
        operation feeding the data to the layer
    activation : ga.SingleInputOperation
        activatin operation of choice
    dropoutRate : float
        dropout rate at the end of this layer
    batchNormalisation: bool
        Whether to use Batch normalisation
    w : np.array
        weigthts in shape (nOutputNodes, nFeatures)
        if None randomly initialized
    b : np.array
        biases, in shape (nOutputNodes, )
        if None, randomly initialized

    Returns
    -------
    ga.Operation
        Last operation of the dense layer
    """
    N, D = inputOperation.shape
    if (inputOperation is None):
        inputOperation = mainGraph.operations[-1]

    w = generateRandomVariable(shape=(nOutputNodes, D),
                               transpose=True, nInputs=D)
    b = generateRandomVariable(shape=nOutputNodes,
                               transpose=False, nInputs=1)

    wo = mainGraph.addOperation(w, doGradient=True)
    bo = mainGraph.addOperation(b, doGradient=True)

    mmo = mainGraph.addOperation(MatMatmulOperation(inputOperation, wo),
                                 doGradient=False,
                                 finalOperation=False)
    addo = mainGraph.addOperation(AddOperation(mmo, bo),
                                  doGradient=False,
                                  finalOperation=False)

    if (dropoutRate > 0):
        dpo = mainGraph.addOperation(DropoutOperation(addo, dropoutRate),
                                     doGradient=False,
                                     finalOperation=False)
    else:
        dpo = addo

    if (batchNormalisation):
        beta = mainGraph.addOperation(generateRandomVariable((1, nOutputNodes)), doGradient=True)
        gamma = mainGraph.addOperation(generateRandomVariable((1, nOutputNodes)), doGradient=True)
        bnorm = mainGraph.addOperation(BatchNormalisationOperation(dpo, beta, gamma))
    else:
        bnorm = dpo

    acto = mainGraph.addOperation(activation(bnorm),
                                  doGradient=False,
                                  finalOperation=False)
    return acto


def addConv2dLayer(mainGraph,
                   inputOperation=None,
                   nFilters=1,
                   filterHeigth=2,
                   filterWidth=2,
                   padding="SAME",
                   convStride=1,
                   activation=ReLUActivation,
                   batchNormalisation=False,
                   pooling=MaxPoolOperation,
                   poolHeight=2,
                   poolWidth=2,
                   poolStride=2):
    """Append a convolution2D layer with pooling

    Parameters
    ----------
    mainGraph : ga.Graph
        computation graph to which append the dense layer
    inputOperation : ga.Operation
        operation feeding the data to the layer
    nFilters : int
        number of filter to be applied for the convolution
    filterHeigth : int
        convolution filter heigth
    filterWidth : int
        convolution filter width
    padding: "SAME" or "VALID"
        padding method for the convolution
    convStride : int
        stride for the convolution filter
    activation : ga.SingleInputOperation
        activatin operation of choice
    batchNormalisation: bool
        Whether to use Batch normalisation
    pooling : ga.SingleInputOperation
        pooling operation of choice
    poolHeight : int
        heigth of the pooling filter
    poolWidth : int
        width of the pooling filter
    poolStride : int
        stride of the pooling operation

    Returns
    -------
    ga.Operation
        Last operation of the dense layer
    """

    N, C, H, W = inputOperation.shape

    w = generateRandomVariable(shape=(nFilters, C, filterHeigth, filterWidth),
                               transpose=False, nInputs=(filterHeigth * filterWidth * C))
    b = generateRandomVariable(shape=(1, nFilters, 1, 1), transpose=False, nInputs=1)

    filterWop = mainGraph.addOperation(w, doGradient=True, feederOperation=False)
    opConv2d = mainGraph.addOperation(Conv2dOperation(
        inputOperation, filterWop, stride=convStride, paddingMethod=padding))

    filterBop = mainGraph.addOperation(b, doGradient=True, feederOperation=False)
    addConv2d = mainGraph.addOperation(AddOperation(opConv2d, filterBop))

    if (batchNormalisation):
        beta = mainGraph.addOperation(generateRandomVariable((1, *addConv2d.shape[1:])), doGradient=True)
        gamma = mainGraph.addOperation(generateRandomVariable((1, *addConv2d.shape[1:])), doGradient=True)
        bnorm = mainGraph.addOperation(BatchNormalisationOperation(addConv2d, beta, gamma))
    else:
        bnorm = addConv2d

    actop = mainGraph.addOperation(activation(bnorm),
                                   doGradient=False,
                                   finalOperation=False)

    poolOP = mainGraph.addOperation(pooling(inputA=actop,
                                            poolHeight=poolHeight,
                                            poolWidth=poolWidth,
                                            stride=poolStride))

    return poolOP
