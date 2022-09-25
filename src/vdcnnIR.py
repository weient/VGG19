# -*- coding: utf-8 -*-
"""
@author: Prabhu <prabhu.appalapuri@gmail.com>
"""
import torch
import torch.nn as nn


class ConvBlock(nn.Module):
    def __init__(self, input_features, output_features, kernel, padding, stride, conv1_1=False):
        super(ConvBlock,self).__init__()
        self.input_features = input_features
        self.output_features = output_features
        self.kernel = kernel
        self.padding = padding
        self.stride = stride
        self.conv1_1 = conv1_1
        if conv1_1:
            self.conv = nn.Conv2d(in_channels=input_features, out_channels=output_features, kernel_size=1, padding=padding, stride=stride)
        else:
            self.conv = nn.Conv2d(in_channels=input_features,out_channels=output_features, kernel_size= kernel, padding=padding, stride= stride)
        self.bNorm= nn.BatchNorm2d(output_features)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        # print(x.size())
        output = self.conv(x)
        output = self.bNorm(output)
        output = self.relu(output)
        return output

class SaveLayer(nn.Module):
    def __init__(self):
        super(SaveLayer, self).__init__()
        self.maps = []
    
    def forward(self, x):
        # Do your print / debug stuff here
        self.maps.append(x)
        return x
    def get_maps(self):
        return self.maps

class Vgg(nn.Module):
    def __init__(self, num_channels, num_classes, depth, conv1_1= False, initialize_weights=True ):
        super(Vgg,self).__init__()
        self.num_channels = num_channels
        self.num_classes = num_classes
        self.depth = depth
        self.save_layer = SaveLayer()
        layers = []
        fc_layers = []
        base_features = 64
        if depth==11:
            num_conv_blocks = [0, 0, 1, 1, 2]
        elif depth== 13:
            num_conv_blocks = [1, 1, 1, 1, 2]
        elif depth == 16:
            num_conv_blocks = [1, 1, 2, 2, 3]
        elif depth==19:
            num_conv_blocks = [1, 1, 3, 3, 4]

        layers.append(ConvBlock(input_features=num_channels, output_features=base_features, kernel=3, padding=1, stride=1))
        layers.append(self.save_layer)
        for _ in range(num_conv_blocks[0]):
            layers.append(ConvBlock(input_features=base_features, output_features=base_features, kernel=3, padding=1,stride=1))
        layers.append(nn.MaxPool2d(kernel_size=2,stride=2))

        layers.append(ConvBlock(input_features=base_features, output_features=2*base_features, kernel=3, padding=1, stride=1))
        layers.append(self.save_layer)
        for _ in range(num_conv_blocks[1]):
            layers.append(ConvBlock(input_features=2*base_features, output_features=2*base_features, kernel=3, padding=1,stride=1))
        layers.append(nn.MaxPool2d(kernel_size=2,stride=2))

        layers.append(ConvBlock(input_features=2*base_features, output_features=4*base_features, kernel=3, padding=1, stride=1))
        layers.append(self.save_layer)
        if conv1_1:
            for _ in range(num_conv_blocks[2]-1):
                layers.append(
                    ConvBlock(input_features=4 * base_features, output_features=4 * base_features, kernel=3, padding=1,
                              stride=1))
            layers.append(ConvBlock(input_features=4 * base_features, output_features=4 * base_features, kernel=3,
                                    padding=1, stride=1, conv1_1=True))
        else:
            for _ in range(num_conv_blocks[2]):
                layers.append(ConvBlock(input_features=4 * base_features, output_features=4 * base_features, kernel=3, padding=1, stride=1))
        layers.append(nn.MaxPool2d(kernel_size=2,stride=2))

        layers.append(ConvBlock(input_features=4*base_features, output_features=8*base_features, kernel=3, padding=1, stride=1))
        layers.append(self.save_layer)
        if conv1_1:
            for _ in range(num_conv_blocks[3]-1):
                layers.append(
                    ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3, padding=1,
                              stride=1))
            layers.append(ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3,
                                    padding=1, stride=1, conv1_1=True))
        else:
            for _ in range(num_conv_blocks[3]):
                layers.append(
                    ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3, padding=1,
                              stride=1))
        layers.append(nn.MaxPool2d(kernel_size=2,stride=2))
        first = True
        if conv1_1:
            for _ in range(num_conv_blocks[4] - 1):
                layers.append(
                    ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3, padding=1,
                              stride=1))
            layers.append(
                ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3, padding=1,
                          stride=1, conv1_1=True))
        else:
            for _ in range(num_conv_blocks[4]):
                layers.append(
                    ConvBlock(input_features=8 * base_features, output_features=8 * base_features, kernel=3, padding=1,
                              stride=1))
                if first:
                  layers.append(self.save_layer)
                  first = False
        layers.append(nn.AdaptiveAvgPool2d(2))
        fc_layers.extend([nn.Linear(in_features=2*2*(8*base_features), out_features= base_features*base_features),nn.ReLU()])
        fc_layers.extend([nn.Linear(in_features=base_features*base_features, out_features= base_features*base_features),nn.ReLU()])
        fc_layers.append(self.save_layer)
        fc_layers.extend([nn.Linear(in_features=base_features*base_features, out_features= self.num_classes)])
        self.layers = nn.Sequential(*layers)
        self.fc_layers = nn.Sequential(*fc_layers)
        if initialize_weights:
            self._init_weights()

    def _init_weights(self):
        for  m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out',nonlinearity='relu')
                if m.bias is None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias,0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # print(x.size())
        output = self.layers(x)
        output = output.view(output.size(0), -1)
        # print(output.size())
        output = self.fc_layers(output)
        maps = self.save_layer.maps
        self.save_layer.maps = []
        # print("maps : ", len(maps))
        return output, maps


