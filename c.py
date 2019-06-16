def g1():     
     yield  range(5)
def g2():
     yield  from range(5)

it1 = g1()
it2 = g2()
for x in it1:
    print(x)

for x in it2:
    print(x)



import zipfile
zip_ref = zipfile.ZipFile('./ywb_MNIST.zip', 'r')
zip_ref.extractall('./')
zip_ref.close()