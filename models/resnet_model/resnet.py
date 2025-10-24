import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

model = models.resnet18(pretrained=True)
model.eval()

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor()
])

img = Image.open('../../assets/images/hen.webp')

img_tensor = transform(img).unsqueeze(0)


with torch.no_grad():
    output = model(img_tensor)

pred = torch.argmax(output, 1).item()

with open('../../assets/utils_files/imagenet1000_classes_to_labels.txt', 'r') as f:
    labels = f.read().splitlines()

print('Predicted: ', labels[pred])
