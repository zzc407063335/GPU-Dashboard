import urllib.request
url="https://www.baidu.com/"
file=urllib.request.urlopen(url)
print('获取当前url:',file.geturl() )
print('file.getcode,HTTPResponse类型:',file.getcode )
print('file.info 返回当前环境相关的信息：' ,file.info())
print("content:",file.read())
