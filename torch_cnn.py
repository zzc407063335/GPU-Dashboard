import torch,sys
from torch import nn, optim
from torch.autograd import Variable
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# 超参数
data_set = sys.argv[1]
print(data_set)

batch_size = 64
learning_rate = 0.02
num_eporches = 20

data_ft = transforms.Compose([transforms.ToTensor(), transforms.Normalize([0.5], [0.5])])

train_dataset = datasets.MNIST("./data", train=True, transform=data_ft, download=True)
test_dataset = datasets.MNIST("./data", train=False, transform=data_ft)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)


class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.layer1 = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True))
        self.layer2 = nn.Sequential(
            nn.Conv2d(16, 32, kernel_size=3),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2))
        self.layer3 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True))
        self.layer4 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2))

        self.fc = nn.Sequential(
            nn.Linear(128 * 4 * 4, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 10))

    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = x.view(x.size(0), -1)  # 第二次卷积的输出拉伸为一行
        x = self.fc(x)
        return x


model = CNN()
if torch.cuda.is_available():
    model = model.cuda()

criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=learning_rate)

epoch = 0
for data in train_loader:
    img, label = data

    # 与全连接网络不同，卷积网络不需要将所像素矩阵转换成一维矩阵
    # img = img.view(img.size(0), -1)

    if torch.cuda.is_available():
        img = img.cuda()
        label = label.cuda()
    else:
        img = Variable(img)

        label = Variable(label)

    out = model(img)
    loss = criterion(out, label)
    print_loss = loss.data.item()

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    epoch += 1
    if epoch % 50 == 0:
        print('epoch: {}, loss: {:.4}'.format(epoch, loss.data.item()))

model.eval()
eval_loss = 0
eval_acc = 0
for data in test_loader:
    img, label = data

    # 与全连接网络不同，卷积网络不需要将所像素矩阵转换成一维矩阵
    # img = img.view(img.size(0), -1)

    if torch.cuda.is_available():
        img = img.cuda()
        label = label.cuda()

    out = model(img)
    loss = criterion(out, label)
    eval_loss += loss.data.item() * label.size(0)
    _, pred = torch.max(out, 1)
    num_correct = (pred == label).sum()
    eval_acc += num_correct.item()
print('Test Loss: {:.6f}, Acc: {:.6f}'.format(
    eval_loss / (len(test_dataset)),
    eval_acc / (len(test_dataset))
))