import tarfile,os

tar = tarfile.open("./MNIST.tar.gz")
names = tar.getnames()
for name in names:
  tar.extract(name,path="./")
tar.close()


def make_targz_one_by_one(output_filename, source_dir): 
    tar = tarfile.open(output_filename,"w:gz")
    for root,dir,files in os.walk(source_dir):
        for file in files:
            print(file)
            pathfile = os.path.join(root, file)
            tar.add(pathfile)
    tar.close()

make_targz_one_by_one("zzc_MNIST_test.tar.gz",'./MNIST')
