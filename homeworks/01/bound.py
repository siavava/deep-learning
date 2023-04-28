import torch
import math
from torch import nn

# This module calculates different measures on your trained model and returns a dictionary whose keys are the measure names
def calculate(model, init_model, device, train_loader, margin):

    # switch to evaluate mode
    model.eval()
    init_model.eval()

    modules = list(model.children())
    init_modules = list(init_model.children())

    D = modules[0].weight.size(1) # data dimension
    H = modules[0].weight.size(0) # number of hidden units
    C = modules[2].weight.size(0) # number of classes (output dimension)
    num_param = sum(p.numel() for p in model.parameters()) # number of parameters of the model

    with torch.no_grad():
        # Eigenvalues of the weight matrix in the first layer
        _,S1,_ = modules[0].weight.svd()
        # Eigenvalues of the weight matrix in the second layer
        _,S2,_ = modules[2].weight.svd()
        # Eigenvalues of the initial weight matrix in the first layer
        _,S01,_ = init_modules[0].weight.svd()
        # Eigenvalues of the initial weight matrix in the second layer
        _,S02,_ = init_modules[2].weight.svd()
        # Frobenius norm of the weight matrix in the first layer
        #************You will compute Fr1 below*******************
        Fr1 = modules[0].weight.norm()

        #*************Your code ends here*************************
        # Frobenius norm of the weight matrix in the second layer
        Fr2 = modules[2].weight.norm()
        # difference of final weights to the initial weights in the first layer
        #*************You will compute diff1 below***************** 
        diff1 = modules[0].weight - init_modules[0].weight

        #***************Your code ends here************************
        #Euclidean distance of the weight matrix in the first layer to the initial weight matrix
        #**************You will compute Dist1 below using your diff1***************
        Dist1 = diff1.norm()

        #***************Your code ends here*************************
        # difference of final weights to the initial weights in the second layer
        diff2 = modules[2].weight - init_modules[2].weight
        # Euclidean distance of the weight matrix in the second layer to the initial weight matrix
        Dist2 = diff2.norm()
        # L_{1,infty} norm of the weight matrix in the first layer
        L1max1 = modules[0].weight.norm(p=1, dim=1).max()
        # L_{1,infty} norm of the weight matrix in the second layer
        L1max2 = modules[2].weight.norm(p=1, dim=1).max()
        # L_{2,1} distance of the weight matrix in the first layer to the initial weight matrix
        L1Dist1 = diff1.norm(p=2, dim=1 ).sum()
        # L_{2,1} distance of the weight matrix in the second layer to the initial weight matrix
        L1Dist2 = diff2.norm(p=2, dim=1 ).sum()

        measure = {}
        measure['Frobenius1'] = Fr1
        measure['Frobenius2'] = Fr2
        measure['Distance1'] = Dist1
        measure['Distance2'] = Dist2
        measure['Spectral1'] = S1[0]
        measure['Spectral2'] = S2[0]
        measure['Fro_Fro'] = Fr1 * Fr2
        measure['L1max_L1max'] = L1max1 * L1max2
        measure['Spec_Dist'] = S1[0] * Dist2 * math.sqrt(C)
        measure['Dist_Spec'] = S2[0] * Dist1 * math.sqrt(H)
        measure['Spec_Dist_sum'] = measure['Spec_Dist'] + measure['Dist_Spec']
        measure['Spec_L1max'] = S1[0] * L1Dist2
        measure['L1max_Spec'] = S2[0] * L1Dist1
        measure['Spec_L1max_sum'] = measure['Spec_L1max'] + measure['L1max_Spec']
        #****************You will compute the Frobenius Distance using the provided instruction************
        measure['Dist_Fro'] = Dist1 * Fr2
        
        #******************Your code ends here***********************
        # delta is the probability that the generalization bound does not hold
        delta = 0.01
        # m is the number of training samples
        m = len(train_loader.dataset)
        layer_norm, data_L2, data_Linf, domain_L2 = 0, 0, 0, 0
        for i, (data, target) in enumerate(train_loader):
            data = data.to(device).view(target.size(0),-1)
            layer_out = torch.zeros(target.size(0), H).to(device)

            # calculate the norm of the output of the first layer in the initial model
            def fun(m, i, o): layer_out.copy_(o.data)
            h = init_modules[1].register_forward_hook(fun)
            output = init_model(data)
            layer_norm += layer_out.norm(p=2, dim=0) ** 2
            h.remove()

            # L2 norm squared of the data 
            data_L2 += data.norm() ** 2
            # maximum L2 norm squared on the training set. We use this as an approximation of this quantity over the domain
            domain_L2 = max(domain_L2, data.norm(p=2, dim = 1).max() ** 2)
            # L_infty norm squared of the data
            data_Linf += data.max(dim = 1)[0].max() ** 2

        # computing the average
        data_L2 /= m
        data_Linf /= m
        layer_norm /= m

        # number of parameters
        measure['#parameter'] = num_param

        # Generalization bound based on the VC dimension by Harvey et al. 2017
        VC = (2 + num_param * math.log(8 * math.e * ( H + 2 * C ) * math.log( 4 * math.e * ( H + 2 * C ) ,2), 2)
                * (2 * (D + 1) * H + (H + 1) * C) / ((D + 1) * H + (H + 1) * C))
        measure['VC bound'] = 8 * (C * VC * math.log(math.e * max(m / VC, 1))) + 8 * math.log(2 / delta)

        # Generalization bound by Bartlett and Mendelson 2002
        R = 8 * C * L1max1 * L1max2 * 2 * math.sqrt(math.log(D)) * math.sqrt(data_Linf) / margin
        measure['L1max bound'] = (R + 3 * math.sqrt(math.log(m / delta))) ** 2

        # Here is the below part you will complete 
        #********************Compute the Generalization bound as provided in the instruction***************
        measure['Your computed bound'] = ( (8 * math.sqrt(C) * Fr1 * Fr2 * (math.sqrt(data_L2) / margin)) + (3 * math.sqrt(math.log(m / delta)))) ** 2
        
        #*********************Your code ends here*********************
        
    return measure
