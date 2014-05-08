def worker(queue):
    while True:
        event = queue.get()
        if event.is_term():
            break
        else:
            metric = event.metric
            ip, port = metric.channel
            print("{:f}\t{}\t{:d}\t{:f}\t{:f}".format(
                metric.timestamp, ip, port, metric.bitrate, metric.packets))
            queue.task_done()
