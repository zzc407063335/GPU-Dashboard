import tarfile,os

# tar = tarfile.open("./MNIST.tar.gz")
# names = tar.getnames()
# for name in names:
#   tar.extract(name,path="./")
# tar.close()


def make_targz_one_by_one(output_filename, source_dir):
    tar = tarfile.open(output_filename,"w:gz")
    for root,dir,files in os.walk(source_dir):
        for file in files:
            print(file)
            pathfile = os.path.join(root, file)
            tar.add(pathfile)
    tar.close()


make_targz_one_by_one("result.tar.gz",'./result')



import zipfile,os

z = zipfile.ZipFile('my-archive.zip', 'w', zipfile.ZIP_DEFLATED)
startdir = "./result"
for dirpath, dirnames, filenames in os.walk(startdir):
    for filename in filenames:
        z.write(os.path.join(dirpath, filename))
z.close()



# import time
# import asyncio
# from threading import Thread

# now = lambda : time.time()

# async def _sleep(x):
#     print("_sleep")
#     await asyncio.sleep(x)
#     print('暂停了{}秒！'.format(x))

# def callback(future):
#     print('这里是回调函数，获取返回结果是：', future.result())

# def start_loop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()

# async def do_some_work(x):
#     print('Waiting {}'.format(x))
#     await asyncio.sleep(x)
#     print('Done after {}s'.format(x))

# def more_work(x):
#     print('More work {}'.format(x))
#     time.sleep(x)
#     print('Finished more work {}'.format(x))

# start = now()
# new_loop = asyncio.new_event_loop()
# t = Thread(target=start_loop, args=(new_loop,))
# t.start()
# print('TIME: {}'.format(time.time() - start))

# asyncio.run_coroutine_threadsafe(_sleep(6), new_loop)
# asyncio.run_coroutine_threadsafe(_sleep(4), new_loop)
# print('TIME: {}'.format(time.time() - start))


# import asyncio
# import random
# import time
# from threading import Thread

# async def worker(sleep_for, queue):
#     # Get a "work item" out of the queue.
#     # sleep_for = await queue.get()
#     # print(queue.qsize())
#     # Sleep for the "sleep_for" seconds.
#     await asyncio.sleep(sleep_for)

#     # Notify the queue that the "work item" has been processed.
#     queue.task_done()
#     print("worker:",queue.qsize())

#     print(f'Task has slept for {sleep_for:.2f} seconds')


# def start_task_loop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()

# async def run_task_in_loop(task_loop, queue):
#     asyncio.set_event_loop(task_loop)
#     while True:
#         print(queue.qsize())
#         sleep_for = await queue.get()
#         asyncio.run_coroutine_threadsafe(worker(sleep_for,queue), task_loop)

# def main():
#     # Create a queue that we will use to store our "workload".
    
#     main_loop = asyncio.get_event_loop()
#     queue = asyncio.Queue(loop=main_loop maxsize=5)
#     # Generate random timings and put them into the queue.
#     total_sleep_time = 0
#     for i in range(5):
#         sleep_for = random.uniform(1.0, 2.0)
#         total_sleep_time += sleep_for
#         queue.put_nowait(sleep_for)
#         # print(queue.qsize())

#     task_loop = asyncio.new_event_loop()
#     t = Thread(target=start_task_loop, args=(task_loop,))
#     t.start()

#     # t = Thread(target=run_task_in_loop, args=(main_loop, task_loop, queue,))
#     # t.start()
#     asyncio.run_coroutine_threadsafe(run_task_in_loop(task_loop,queue), task_loop)

#      # Create three worker tasks to process the queue concurrently.
#     tasks = []
#     # for i in range(3):
#     #     task = loop.create_task(worker(f'worker-{i}', queue))
#     #     tasks.append(task)

#     # Wait until the queue is fully processed.
#     # started_at = time.monotonic()
#     # total_slept_for = time.monotonic() - started_at

#     # Cancel our worker tasks.
#     # for task in tasks:
#     #     task.cancel()
#     # Wait until all worker tasks are cancelled.
#     # await asyncio.gather(*tasks, return_exceptions=True)

#     # print('====')
#     # print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
#     # print(f'total expected sleep time: {total_sleep_time:.2f} seconds')
#     while True:
#         # import ipdb; ipdb.set_trace()
#         time.sleep(0.5)
#         sleep_for = random.uniform(1.0, 2.0)
#         main_loop.run_until_complete(queue.put(sleep_for))

#         print(f'put {sleep_for:.2f} in queue')
#         print(queue.qsize())

# main()


# loop = asyncio.get_event_loop()
# loop.run_until_complete(main(loop))

# import threading
# import asyncio


# def thread_loop_task(loop):

#     # 为子线程设置自己的事件循环
#     asyncio.set_event_loop(loop)

#     async def work_2():
#         while True:
#             print('work_2 on loop:%s' % id(loop))
#             await asyncio.sleep(2)

#     async def work_4():
#         while True:
#             print('work_4 on loop:%s' % id(loop))
#             await asyncio.sleep(4)

#     future = asyncio.gather(work_2(), work_4())
#     loop.run_until_complete(future)


# if __name__ == '__main__':

#     # 创建一个事件循环thread_loop
#     thread_loop = asyncio.new_event_loop()

#     # 将thread_loop作为参数传递给子线程
#     t = threading.Thread(target=thread_loop_task, args=(thread_loop,))
#     t.daemon = True
#     t.start()

#     main_loop = asyncio.get_event_loop()


#     async def main_work():
#         while True:
#             print('main on loop:%s' % id(main_loop))
#             await asyncio.sleep(4)


#     main_loop.run_until_complete(main_work())

# import asyncio
# import random
# import time


# async def newsProducer(myQueue):
#     while True:
#         await asyncio.sleep(5)
#         await myQueue.put(random.randint(1, 2))
#         print("Putting news item onto queue",myQueue.qsize())



# async def newsConsumer(id, myQueue):
#     print(myQueue)
#     while True:
#         print("Consumer: {} Attempting to get from queue".format(id))
#         item = await myQueue.get()
#         if item is None:
#             # the producer emits None to indicate that it is done
#             break
#         await asyncio.sleep(item)
#         print("Consumer: {} consumed article with id: {}".format(id, item))


# loop = asyncio.get_event_loop()
# myQueue = asyncio.Queue(loop=loop, maxsize=5)
# coroutine = newsProducer(myQueue)
# tasks = []
# tasks.append(asyncio.ensure_future(coroutine))
# for i in range(5):
#   tasks.append(asyncio.ensure_future(newsConsumer(i,myQueue)))
# print(tasks)
# try:
#     loop.run_until_complete(asyncio.gather(*tasks))
# except KeyboardInterrupt:
#     pass
# finally:
#     loop.close()


# import asyncio

# import time

# now = lambda: time.time()

# async def do_some_work(x):
#     print('Waiting: ', x)

#     await asyncio.sleep(x)
#     return 'Done after {}s'.format(x)

# start = now()

# coroutine1 = do_some_work(3)
# coroutine2 = do_some_work(2)
# coroutine3 = do_some_work(4)

# tasks = [
#     asyncio.ensure_future(coroutine1),
#     asyncio.ensure_future(coroutine2),
#     asyncio.ensure_future(coroutine3)
# ]

# loop = asyncio.get_event_loop()
# loop.run_until_complete(asyncio.wait(tasks))

# for task in tasks:
#     print('Task ret: ', task.result())

# print('TIME: ', now() - start)