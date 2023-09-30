import requests
import threading

from ElasticCluster.config import BASE_URL

with open('Input/indices.txt', 'r') as file:
    INDICES = [line.strip() for line in file]

max_concurrent_threads = 3
semaphore = threading.Semaphore(max_concurrent_threads)

def force_merge(index_name):
    semaphore.acquire()
    try:
        url = f"{BASE_URL}/{index_name}/_forcemerge?max_num_segments=3"
        response = requests.post(url,timeout=5200)
        if response.status_code == 200:
            print(f"Started forcemerge for {index_name}")
        else:
            print(f"Error merging {index_name}: {response.text}")
    finally:
        semaphore.release()

threads = []
for index in INDICES:
    t = threading.Thread(target=force_merge, args=(index,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("All forcemerge operations initiated.")
