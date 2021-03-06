# -*- coding: utf-8 -*-
"""bundlenet_distributed_2022April09.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1oAAEZVClCCX1csttqxSQziqGQHs56pb9

**Project codes for Property Inference Paper (use CPU node on google colab)**

Note: The following codes are applied on one specific fold, one network split ratio. 
The paper's results were generated on department server by running following codes in parallel

**(1) Load the packages**
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import subprocess
import warnings
warnings.filterwarnings('ignore')

# Training settings
torch.manual_seed(1)
device = torch.device("cpu")
modeldir = './models'
datadir = './data_practice'

os.makedirs(datadir, exist_ok=True) 
os.makedirs(modeldir, exist_ok=True)

torch.set_printoptions(profile="full")
        
'''
First part of bundlenet, this function should be deployed on server
'''
class firstpart_bundleNet2(nn.Module):
    def __init__(self,num_classes=10, prior_percent=0.8):
        super(firstpart_bundleNet2, self).__init__()

        image_channels = 1
        middle_percent = 0.8
        
        
        #self.inputlayer = nn.Conv2d(image_channels, 32, kernel_size=3, stride=1)

        self.inputlayer2 = nn.Sequential(
            nn.Conv2d(image_channels, 64, kernel_size=3, stride=2, padding=3,bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )
        self.inputlayer = nn.Sequential(
            nn.Conv2d(image_channels, 16, kernel_size=3),
            nn.BatchNorm2d(16),
            nn.ReLU()
        )
        self.convlayer1 = self.__make_convlayer(16,32)
        self.convlayer2 = self.__make_convlayer(32,32)
        self.convlayer3 = self.__make_convlayer(32,64)
        self.convlayer4 = self.__make_convlayer(64,128)
        
        self.inplanes = 64
        self.resnetlayer1 = self._make_resnetlayer(BasicBlock, 64, 1)
        self.resnetlayer2 = self._make_resnetlayer(BasicBlock, 128, 1, stride=2)
        self.resnetlayer3 = self._make_resnetlayer(BasicBlock, 256, 1, stride=2)
        self.resnetlayer4 = self._make_resnetlayer(BasicBlock, 512, 1, stride=2)
        
        self.before_fc = [self.inputlayer, self.convlayer1]


        self.flatten = Flatten()
        self.fc1 = self.__make_fclayer(1920, 128)
        self.fch = self.__make_fclayer(128, 128)

        self.fc2 = self.__make_fclayer_nodrop(128, num_classes)

        self.model = self.before_fc + [self.flatten,self.fc1,self.fc2]
        

        prior_part = int(math.ceil(prior_percent * len(self.model)))
        if prior_part < 1:
          prior_part = 1
        if prior_part >= len(self.model)-1:
          prior_part = len(self.model)-1 # set at least one layer to server 

        self.client_modules = self.model[0:prior_part] # prior network
        self.normlayer1D = self.__make_norm1Dlayer(1920)
        #print("Setting prior modules: ",self.client_modules)


    def forward(self, x):
        for layer in self.client_modules:
          #print('x.shape: ',x.size(), ' layer: ',layer)
          x = layer(x)
        return x
               
    def __make_convlayer(self, in_channels, out_channels):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3), 
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )
        
    
    def __make_convlayer_nopool(self, in_channels, out_channels):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3), 
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            #nn.MaxPool2d(kernel_size=2)
        )


    def _make_resnetlayer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)    
    
    def __make_norm1Dlayer(self, in_channels):
        return nn.Sequential(
            nn.BatchNorm1d(in_channels),
            nn.ReLU()
        )
    
    def __make_fclayer(self, in_channels, out_channels, dropout=0):
        return nn.Sequential(
            nn.Linear(in_channels, out_channels), 
            nn.ReLU(),
            nn.Dropout2d(dropout)
        )
    
        
    def __make_fclayer_nodrop(self, in_channels, out_channels, dropout=0):
        return nn.Sequential(
            nn.Linear(in_channels, out_channels)
        )

class Flatten(torch.nn.Module):
    def forward(self, x):
        batch_size = x.shape[0]
        return x.view(batch_size, -1)



def runcmd(cmd, verbose = False, *args, **kwargs):

        process = subprocess.Popen(
            cmd,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            shell = True
        )
        std_out, std_err = process.communicate()

runcmd('curl http://gateway.openfaas:8080/function/subfeature-2 -o out.txt', verbose=False)
f2 = open('out.txt')
subfeature2 = f2.read()
f2.close

from torch import Tensor as tensor

server2_tensor = eval(subfeature2)

runcmd('wget https://cs.slu.edu/~hou/downloads/PropertyInferenceAttack/data_practice.tar.gz --no-check-certificate', verbose = False)
runcmd('wget https://cs.slu.edu/~hou/downloads/PropertyInferenceAttack/models.tar.gz --no-check-certificate', verbose = False)
runcmd('tar -zxf data_practice.tar.gz', verbose = False)
runcmd('tar -zxf models.tar.gz', verbose=False)

def conv3x3(in_planes, out_planes, stride=1):
    """3x3 convolution with padding"""
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=1, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(BasicBlock, self).__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out


class ResNet(nn.Module):

    def __init__(self, block, layers, num_classes, grayscale):
        self.inplanes = 64
        if grayscale:
            in_dim = 1
        else:
            in_dim = 3
        super(ResNet, self).__init__()
        self.conv1 = nn.Conv2d(in_dim, 64, kernel_size=3, stride=2, padding=3,
                               bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(block, 64, layers[0])
        self.layer2 = self._make_layer(block, 128, layers[1], stride=2)
        self.layer3 = self._make_layer(block, 256, layers[2], stride=2)
        self.layer4 = self._make_layer(block, 512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(7, stride=1)
        self.fc = nn.Linear(512 * block.expansion, num_classes)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, (2. / n)**.5)
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()

    def _make_layer(self, block, planes, blocks, stride=1):
        downsample = None
        if stride != 1 or self.inplanes != planes * block.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * block.expansion,
                          kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * block.expansion),
            )

        layers = []
        layers.append(block(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * block.expansion
        for i in range(1, blocks):
            layers.append(block(self.inplanes, planes))

        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        # because MNIST is already 1x1 here:
        # disable avg pooling
        #x = self.avgpool(x)
        
        x = x.view(x.size(0), -1)
        logits = self.fc(x)
        probas = F.softmax(logits, dim=1)
        return logits, probas


"""**(8) Configure the deep learning models in individual servers**

"""

### Step 2: configure server's deep learning architecture in each of distributed nodes 




## server 2
def server_function2(subfeature2):
    server2_function = torch.load('models/server_model_part2.pt')
    server2_function.eval()
    server2_output = server2_function(subfeature2) # accept subfeature 2
    return server2_output

final_result = server_function2(server2_tensor)

runcmd('rm -rf models.tar.gz data_practice.tar.gz models data_practice out.txt', verbose=False)
print(final_result)

