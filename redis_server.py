import subprocess

def startServer():
    # Start the Redis server using subprocess
    subprocess.Popen(['wsl', 'redis-server', '--daemonize', 'yes'])
    # Check if the Redis server is up by attempting a connection
    redis_up = False
    while not redis_up:
        try:
            # Attempt to connect to the Redis server
            subprocess.run(['wsl', 'redis-cli', 'ping'], check=True)
            redis_up = True
        except subprocess.CalledProcessError:
        # Connection failed, wait for a few seconds and try again
           exit()

    if redis_up:
        print("Redis server is up and running!")
    else:
        print("Failed to start Redis server.")
