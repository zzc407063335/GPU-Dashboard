## 测试说明
1. 修改测试文件中conn_file_*.py中的logs和task路径
2. 修改测试包中logs文件下logfile.py，引入logfile_test.conf
3. 修改logfile_test.conf指向本测试文件夹下的logs文件夹
4. sh start_test.sh
# 待解决问题
1. TaskProducer 测试协程时，会停在最后的阶段不退出
2. 测试Consumer时，trainbox的测试需要测试人员定期docker stop trainbox1模拟容器训练结束，待添加自动化的方式